"""State synchronization between real devices and digital twins."""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_async_session
from ..models.entities import Device, DeviceEntity
from ..models.events import ControlAction, Event, SensorReading
from .models import (
    DeviceState,
    DigitalTwinDevice,
    SyncStatus,
    TwinState,
)


class StateSynchronizer:
    """Manages synchronization between real devices and their digital twins."""
    
    def __init__(self, sync_interval: float = 5.0):
        self.sync_interval = sync_interval
        self.is_running = False
        self.sync_queue: asyncio.Queue[str] = asyncio.Queue()
        self.device_mappings: Dict[int, str] = {}  # real_id -> twin_id
        self.twin_mappings: Dict[str, int] = {}  # twin_id -> real_id
        self.sync_states: Dict[str, TwinState] = {}
        self.error_counts: Dict[str, int] = {}
        self.max_retries = 3
        
    async def start(self):
        """Start the synchronization service."""
        self.is_running = True
        asyncio.create_task(self._sync_loop())
        asyncio.create_task(self._error_recovery_loop())
        
    async def stop(self):
        """Stop the synchronization service."""
        self.is_running = False
        
    def register_device_mapping(self, real_device_id: int, twin_device_id: str):
        """Register a mapping between real device and digital twin."""
        self.device_mappings[real_device_id] = twin_device_id
        self.twin_mappings[twin_device_id] = real_device_id
        
        # Initialize sync state
        self.sync_states[twin_device_id] = TwinState(
            entity_id=twin_device_id,
            entity_type="device",
            sync_status=SyncStatus.OUT_OF_SYNC,
            real_state={},
            virtual_state={},
            last_sync=datetime.utcnow(),
        )
        
        # Queue for immediate sync
        asyncio.create_task(self.sync_queue.put(twin_device_id))
        
    def unregister_device_mapping(self, twin_device_id: str):
        """Remove device mapping."""
        if twin_device_id in self.twin_mappings:
            real_id = self.twin_mappings[twin_device_id]
            del self.device_mappings[real_id]
            del self.twin_mappings[twin_device_id]
            
        if twin_device_id in self.sync_states:
            del self.sync_states[twin_device_id]
            
        if twin_device_id in self.error_counts:
            del self.error_counts[twin_device_id]
            
    async def _sync_loop(self):
        """Main synchronization loop."""
        while self.is_running:
            try:
                # Process queued sync requests
                while not self.sync_queue.empty():
                    twin_id = await self.sync_queue.get()
                    await self._sync_device(twin_id)
                    
                # Periodic sync for all devices
                await self._sync_all_devices()
                
                await asyncio.sleep(self.sync_interval)
                
            except Exception as e:
                print(f"Error in sync loop: {e}")
                await asyncio.sleep(1)
                
    async def _error_recovery_loop(self):
        """Handle devices with sync errors."""
        while self.is_running:
            try:
                # Check devices with errors
                error_devices = [
                    twin_id for twin_id, state in self.sync_states.items()
                    if state.sync_status == SyncStatus.ERROR
                ]
                
                for twin_id in error_devices:
                    if self.error_counts.get(twin_id, 0) < self.max_retries:
                        await self.sync_queue.put(twin_id)
                        
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"Error in recovery loop: {e}")
                await asyncio.sleep(5)
                
    async def _sync_all_devices(self):
        """Sync all registered devices."""
        tasks = []
        for twin_id in self.twin_mappings:
            tasks.append(self._sync_device(twin_id))
            
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            
    async def _sync_device(self, twin_device_id: str) -> bool:
        """Sync a single device."""
        if twin_device_id not in self.twin_mappings:
            return False
            
        real_device_id = self.twin_mappings[twin_device_id]
        sync_state = self.sync_states[twin_device_id]
        
        try:
            sync_state.sync_status = SyncStatus.SYNCING
            
            async with get_async_session() as session:
                # Get real device state
                real_state = await self._get_real_device_state(session, real_device_id)
                if not real_state:
                    sync_state.sync_status = SyncStatus.ERROR
                    sync_state.sync_errors.append("Real device not found")
                    return False
                    
                sync_state.real_state = real_state
                
                # Update sync status
                sync_state.last_sync = datetime.utcnow()
                sync_state.sync_status = SyncStatus.SYNCHRONIZED
                sync_state.sync_errors.clear()
                
                # Reset error count on successful sync
                self.error_counts[twin_device_id] = 0
                
                return True
                
        except Exception as e:
            sync_state.sync_status = SyncStatus.ERROR
            sync_state.sync_errors.append(str(e))
            self.error_counts[twin_device_id] = self.error_counts.get(twin_device_id, 0) + 1
            return False
            
    async def _get_real_device_state(
        self, session: AsyncSession, device_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get current state of real device."""
        # Get device info
        device = await session.get(Device, device_id)
        if not device:
            return None
            
        state = {
            "status": device.status,
            "current_state": device.current_state,
            "last_seen": device.last_seen.isoformat() if device.last_seen else None,
        }
        
        # Get device entities
        from sqlalchemy import select
        
        entities = await session.execute(
            select(DeviceEntity).where(DeviceEntity.device_id == device_id)
        )
        entities = entities.scalars().all()
        
        entity_states = {}
        for entity in entities:
            entity_states[entity.entity_id] = {
                "state": entity.state,
                "attributes": entity.attributes,
            }
            
        state["entities"] = entity_states
        
        # Get recent sensor readings
        recent_time = datetime.utcnow() - timedelta(minutes=5)
        readings = await session.execute(
            select(SensorReading)
            .where(SensorReading.device_id == device_id)
            .where(SensorReading.reading_time > recent_time)
            .order_by(SensorReading.reading_time.desc())
            .limit(10)
        )
        readings = readings.scalars().all()
        
        sensor_data = {}
        for reading in readings:
            if reading.sensor_type not in sensor_data:
                sensor_data[reading.sensor_type] = {
                    "value": reading.value,
                    "unit": reading.unit,
                    "timestamp": reading.reading_time.isoformat(),
                }
                
        state["sensors"] = sensor_data
        
        return state
        
    async def sync_from_twin(
        self, twin_device: DigitalTwinDevice, changes: Dict[str, Any]
    ) -> bool:
        """Sync changes from digital twin to real device."""
        if twin_device.id not in self.twin_mappings:
            return False
            
        real_device_id = self.twin_mappings[twin_device.id]
        
        try:
            async with get_async_session() as session:
                # Create control actions for each change
                for key, value in changes.items():
                    action = ControlAction(
                        device_id=real_device_id,
                        action_type="update_state",
                        command=f"set_{key}",
                        parameters={"value": value},
                        status="pending",
                    )
                    session.add(action)
                    
                # Log sync event
                event = Event(
                    event_type="twin_sync",
                    category="synchronization",
                    severity="low",
                    title=f"Digital twin sync for {twin_device.name}",
                    description=f"Syncing {len(changes)} changes from digital twin",
                    source="digital_twin",
                    event_data={
                        "twin_id": twin_device.id,
                        "real_device_id": real_device_id,
                        "changes": changes,
                    },
                )
                session.add(event)
                
                await session.commit()
                
                # Queue for sync verification
                await self.sync_queue.put(twin_device.id)
                
                return True
                
        except Exception as e:
            print(f"Error syncing from twin: {e}")
            return False
            
    def get_sync_state(self, twin_device_id: str) -> Optional[TwinState]:
        """Get current sync state for a device."""
        return self.sync_states.get(twin_device_id)
        
    def get_all_sync_states(self) -> Dict[str, TwinState]:
        """Get all sync states."""
        return self.sync_states.copy()
        
    async def force_sync(self, twin_device_id: str) -> bool:
        """Force immediate synchronization of a device."""
        if twin_device_id in self.twin_mappings:
            await self.sync_queue.put(twin_device_id)
            return True
        return False
        
    def is_synchronized(self, twin_device_id: str) -> bool:
        """Check if device is synchronized."""
        state = self.sync_states.get(twin_device_id)
        return state is not None and state.sync_status == SyncStatus.SYNCHRONIZED
        
    async def get_sync_metrics(self) -> Dict[str, Any]:
        """Get synchronization metrics."""
        total_devices = len(self.twin_mappings)
        synchronized = sum(
            1 for state in self.sync_states.values()
            if state.sync_status == SyncStatus.SYNCHRONIZED
        )
        errors = sum(
            1 for state in self.sync_states.values()
            if state.sync_status == SyncStatus.ERROR
        )
        
        avg_sync_age = 0
        if self.sync_states:
            sync_ages = [
                (datetime.utcnow() - state.last_sync).total_seconds()
                for state in self.sync_states.values()
            ]
            avg_sync_age = sum(sync_ages) / len(sync_ages)
            
        return {
            "total_devices": total_devices,
            "synchronized": synchronized,
            "errors": errors,
            "sync_percentage": (synchronized / total_devices * 100) if total_devices > 0 else 0,
            "average_sync_age_seconds": avg_sync_age,
            "queue_size": self.sync_queue.qsize(),
            "error_counts": dict(self.error_counts),
        }
        
    async def handle_real_device_update(self, device_id: int, update_data: Dict[str, Any]):
        """Handle updates from real devices."""
        if device_id not in self.device_mappings:
            return
            
        twin_id = self.device_mappings[device_id]
        
        # Update sync state
        if twin_id in self.sync_states:
            self.sync_states[twin_id].real_state.update(update_data)
            
        # Queue for sync
        await self.sync_queue.put(twin_id)