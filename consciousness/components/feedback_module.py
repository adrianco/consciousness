"""SAFLA Feedback Module - Control actions and responses with safety validation."""

import asyncio
import uuid
from collections import deque
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ..database import get_async_session
from ..digital_twin.core import DigitalTwinManager
from ..models.events import ControlAction as ControlActionModel
from .analyze_module import AnalysisResult, Anomaly, Pattern, Prediction


class ActionType(Enum):
    """Types of control actions."""
    LIGHTING_CONTROL = "lighting_control"
    CLIMATE_CONTROL = "climate_control"
    SECURITY_CONTROL = "security_control"
    ENERGY_OPTIMIZATION = "energy_optimization"
    COMFORT_ADJUSTMENT = "comfort_adjustment"
    EMERGENCY_RESPONSE = "emergency_response"
    MAINTENANCE_ACTION = "maintenance_action"


class Priority(Enum):
    """Action priority levels."""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    LOWEST = 1


class ActionStatus(Enum):
    """Status of control actions."""
    PENDING = "pending"
    VALIDATING = "validating"
    TWIN_TESTING = "twin_testing"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SafetyConstraint:
    """Base safety constraint interface."""

    def __init__(self, name: str, severity: str, description: str):
        self.name = name
        self.severity = severity
        self.description = description

    def evaluate(self, action: "ControlAction") -> bool:
        """Evaluate if action violates this constraint."""
        raise NotImplementedError

    def get_mitigation(self) -> str:
        """Get mitigation strategy for violation."""
        return f"Review and modify {self.name} parameters"


class TemperatureSafetyConstraint(SafetyConstraint):
    """Temperature safety constraint."""

    def __init__(self, min_temp: float = 10, max_temp: float = 35):
        super().__init__("temperature_limit", "critical", "Maintains safe temperature range")
        self.min_temp = min_temp
        self.max_temp = max_temp

    def evaluate(self, action: "ControlAction") -> bool:
        """Check temperature limits."""
        if action.action_type == ActionType.CLIMATE_CONTROL:
            target_temp = action.parameters.get("target_temperature")
            if target_temp is not None:
                return self.min_temp <= target_temp <= self.max_temp
        return True


class RateLimitConstraint(SafetyConstraint):
    """Rate limiting constraint."""

    def __init__(self, max_rate: int = 10, time_window: int = 60):
        super().__init__("rate_limit", "high", "Prevents excessive action frequency")
        self.max_rate = max_rate
        self.time_window = time_window
        self.action_history: deque = deque(maxlen=100)

    def evaluate(self, action: "ControlAction") -> bool:
        """Check rate limits."""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.time_window)

        # Count recent actions
        recent_actions = [
            a for a in self.action_history
            if a["timestamp"] > cutoff and a["target"] == action.target
        ]

        # Record current action
        self.action_history.append({
            "timestamp": now,
            "target": action.target,
            "action_type": action.action_type
        })

        return len(recent_actions) < self.max_rate


class PowerLimitConstraint(SafetyConstraint):
    """Power consumption limit constraint."""

    def __init__(self, max_power: float = 5000):  # 5kW default
        super().__init__("power_limit", "high", "Prevents excessive power consumption")
        self.max_power = max_power

    def evaluate(self, action: "ControlAction") -> bool:
        """Check power limits."""
        power_increase = action.parameters.get("power_increase", 0)
        current_power = action.context.get("current_power_consumption", 0)

        return (current_power + power_increase) <= self.max_power


class ControlAction:
    """Control action with metadata and safety information."""

    def __init__(
        self,
        action_id: str,
        action_type: ActionType,
        target: str,
        parameters: Dict[str, Any],
        priority: Priority,
        deadline: Optional[datetime] = None,
        context: Optional[Dict[str, Any]] = None,
        generated_from: Optional[str] = None
    ):
        self.action_id = action_id
        self.action_type = action_type
        self.target = target
        self.parameters = parameters
        self.priority = priority
        self.deadline = deadline or (datetime.now() + timedelta(minutes=5))
        self.context = context or {}
        self.generated_from = generated_from

        # Execution tracking
        self.status = ActionStatus.PENDING
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error: Optional[str] = None

        # Safety and validation
        self.safety_validations: List[Dict[str, Any]] = []
        self.twin_test_result: Optional[Dict[str, Any]] = None
        self.rollback_data: Optional[Dict[str, Any]] = None


class ExecutionResult:
    """Result of action execution."""

    def __init__(
        self,
        action_id: str,
        success: bool,
        timestamp: datetime,
        execution_time: float,
        result_data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        self.action_id = action_id
        self.success = success
        self.timestamp = timestamp
        self.execution_time = execution_time
        self.result_data = result_data or {}
        self.error = error


class PriorityQueue:
    """Priority queue for control actions."""

    def __init__(self):
        self.items: List[ControlAction] = []

    def enqueue(self, action: ControlAction):
        """Add action to queue based on priority."""
        # Insert in priority order (highest first)
        inserted = False
        for i, item in enumerate(self.items):
            if action.priority.value > item.priority.value:
                self.items.insert(i, action)
                inserted = True
                break

        if not inserted:
            self.items.append(action)

    def dequeue(self) -> Optional[ControlAction]:
        """Remove and return highest priority action."""
        if self.items:
            return self.items.pop(0)
        return None

    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return len(self.items) == 0

    def peek(self) -> Optional[ControlAction]:
        """Look at next action without removing."""
        if self.items:
            return self.items[0]
        return None


class ActionExecutor:
    """Executes control actions safely."""

    def __init__(self, twin_manager: DigitalTwinManager):
        self.twin_manager = twin_manager

    async def execute(self, action: ControlAction) -> ExecutionResult:
        """Execute a control action."""
        start_time = datetime.now()
        action.started_at = start_time
        action.status = ActionStatus.EXECUTING

        try:
            # Execute based on action type
            if action.action_type == ActionType.LIGHTING_CONTROL:
                result = await self._execute_lighting_control(action)
            elif action.action_type == ActionType.CLIMATE_CONTROL:
                result = await self._execute_climate_control(action)
            elif action.action_type == ActionType.SECURITY_CONTROL:
                result = await self._execute_security_control(action)
            elif action.action_type == ActionType.ENERGY_OPTIMIZATION:
                result = await self._execute_energy_optimization(action)
            elif action.action_type == ActionType.COMFORT_ADJUSTMENT:
                result = await self._execute_comfort_adjustment(action)
            elif action.action_type == ActionType.EMERGENCY_RESPONSE:
                result = await self._execute_emergency_response(action)
            else:
                raise ValueError(f"Unknown action type: {action.action_type}")

            action.status = ActionStatus.COMPLETED
            action.completed_at = datetime.now()

            execution_time = (datetime.now() - start_time).total_seconds()
            return ExecutionResult(
                action_id=action.action_id,
                success=True,
                timestamp=datetime.now(),
                execution_time=execution_time,
                result_data=result
            )

        except Exception as e:
            action.status = ActionStatus.FAILED
            action.error = str(e)
            action.completed_at = datetime.now()

            execution_time = (datetime.now() - start_time).total_seconds()
            return ExecutionResult(
                action_id=action.action_id,
                success=False,
                timestamp=datetime.now(),
                execution_time=execution_time,
                error=str(e)
            )

    async def _execute_lighting_control(self, action: ControlAction) -> Dict[str, Any]:
        """Execute lighting control action."""
        house_id = action.context.get("house_id")
        device_id = action.target

        state_update = {}

        if "brightness" in action.parameters:
            state_update["brightness"] = action.parameters["brightness"]
        if "power" in action.parameters:
            state_update["power"] = action.parameters["power"]
        if "color" in action.parameters:
            state_update["color"] = action.parameters["color"]

        if house_id and state_update:
            await self.twin_manager.update_device_state(house_id, device_id, state_update)

        return {"device_id": device_id, "state_update": state_update}

    async def _execute_climate_control(self, action: ControlAction) -> Dict[str, Any]:
        """Execute climate control action."""
        house_id = action.context.get("house_id")
        device_id = action.target

        state_update = {}

        if "target_temperature" in action.parameters:
            state_update["temperature"] = action.parameters["target_temperature"]
        if "hvac_mode" in action.parameters:
            state_update["hvac_mode"] = action.parameters["hvac_mode"]
        if "fan_speed" in action.parameters:
            state_update["fan_speed"] = action.parameters["fan_speed"]

        if house_id and state_update:
            await self.twin_manager.update_device_state(house_id, device_id, state_update)

        return {"device_id": device_id, "state_update": state_update}

    async def _execute_security_control(self, action: ControlAction) -> Dict[str, Any]:
        """Execute security control action."""
        house_id = action.context.get("house_id")
        device_id = action.target

        state_update = {}

        if "locked" in action.parameters:
            state_update["locked"] = action.parameters["locked"]
        if "armed" in action.parameters:
            state_update["armed"] = action.parameters["armed"]
        if "recording" in action.parameters:
            state_update["recording"] = action.parameters["recording"]

        if house_id and state_update:
            await self.twin_manager.update_device_state(house_id, device_id, state_update)

        return {"device_id": device_id, "state_update": state_update}

    async def _execute_energy_optimization(self, action: ControlAction) -> Dict[str, Any]:
        """Execute energy optimization action."""
        house_id = action.context.get("house_id")
        results = []

        if "devices_to_optimize" in action.parameters:
            for device_config in action.parameters["devices_to_optimize"]:
                device_id = device_config["device_id"]
                state_update = device_config["state_update"]

                await self.twin_manager.update_device_state(house_id, device_id, state_update)
                results.append({"device_id": device_id, "state_update": state_update})

        return {"optimized_devices": results}

    async def _execute_comfort_adjustment(self, action: ControlAction) -> Dict[str, Any]:
        """Execute comfort adjustment action."""
        # Similar to climate control but may affect multiple devices
        return await self._execute_climate_control(action)

    async def _execute_emergency_response(self, action: ControlAction) -> Dict[str, Any]:
        """Execute emergency response action."""
        house_id = action.context.get("house_id")
        response_type = action.parameters.get("response_type")

        results = []

        if response_type == "smoke_alarm":
            # Turn on all lights, unlock doors, alert authorities
            house = await self.twin_manager.get_house_twin(house_id)
            if house:
                for device in house.all_devices.values():
                    if device.device_class == "light":
                        await self.twin_manager.update_device_state(
                            house_id, device.id, {"power": True, "brightness": 100}
                        )
                        results.append(f"Activated light: {device.id}")
                    elif device.device_class == "lock":
                        await self.twin_manager.update_device_state(
                            house_id, device.id, {"locked": False}
                        )
                        results.append(f"Unlocked door: {device.id}")

        return {"emergency_type": response_type, "actions_taken": results}


class SafetyController:
    """STPA-based safety controller."""

    def __init__(self, constraints: List[SafetyConstraint]):
        self.constraints = constraints
        self.violation_history: deque = deque(maxlen=1000)

    async def validate(self, action: ControlAction) -> Dict[str, Any]:
        """Validate action against safety constraints."""
        violations = []
        total_risk = 0.0

        for constraint in self.constraints:
            try:
                if not constraint.evaluate(action):
                    violation = {
                        "constraint": constraint.name,
                        "severity": constraint.severity,
                        "description": constraint.description,
                        "mitigation": constraint.get_mitigation(),
                        "timestamp": datetime.now().isoformat()
                    }
                    violations.append(violation)

                    # Add to history
                    self.violation_history.append(violation)

                    # Calculate risk contribution
                    severity_weights = {"critical": 1.0, "high": 0.7, "medium": 0.4, "low": 0.2}
                    total_risk += severity_weights.get(constraint.severity, 0.5)

            except Exception as e:
                print(f"Error evaluating constraint {constraint.name}: {e}")

        return {
            "safe": len(violations) == 0,
            "violations": violations,
            "risk_score": min(1.0, total_risk),
            "validation_timestamp": datetime.now().isoformat()
        }


class TwinActionValidator:
    """Validates actions using digital twin simulation."""

    def __init__(self, twin_manager: DigitalTwinManager):
        self.twin_manager = twin_manager

    async def validate_action(self, action: ControlAction) -> Dict[str, Any]:
        """Test action on digital twin before physical execution."""
        house_id = action.context.get("house_id")
        if not house_id:
            return {
                "safe": False,
                "reason": "No house_id provided for twin validation",
                "confidence": 0.0
            }

        try:
            # Get current twin state
            house = await self.twin_manager.get_house_twin(house_id)
            if not house:
                return {
                    "safe": False,
                    "reason": f"No twin found for house {house_id}",
                    "confidence": 0.0
                }

            # Create state backup for rollback
            original_state = self._capture_state(house, action.target)

            # Simulate action execution
            simulation_result = await self._simulate_action(action)

            # Analyze safety of predicted outcome
            safety_analysis = await self._analyze_twin_safety(simulation_result, action)

            # Restore original state
            await self._restore_state(house_id, action.target, original_state)

            return {
                "safe": safety_analysis["safe"],
                "confidence": safety_analysis["confidence"],
                "predicted_outcome": simulation_result,
                "risk_factors": safety_analysis.get("risks", []),
                "validation_timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            print(f"Error in twin validation: {e}")
            return {
                "safe": False,
                "reason": f"Twin validation error: {str(e)}",
                "confidence": 0.0
            }

    def _capture_state(self, house, device_id: str) -> Dict[str, Any]:
        """Capture current device state for rollback."""
        device = house.all_devices.get(device_id)
        if device:
            return device.current_values.copy()
        return {}

    async def _simulate_action(self, action: ControlAction) -> Dict[str, Any]:
        """Simulate action execution on twin."""
        house_id = action.context.get("house_id")

        # Execute action on twin
        executor = ActionExecutor(self.twin_manager)
        result = await executor.execute(action)

        # Get final state
        house = await self.twin_manager.get_house_twin(house_id)
        device = house.all_devices.get(action.target) if house else None

        return {
            "execution_result": result.result_data,
            "final_state": device.current_values if device else {},
            "success": result.success,
            "execution_time": result.execution_time
        }

    async def _analyze_twin_safety(
        self,
        simulation_result: Dict[str, Any],
        action: ControlAction
    ) -> Dict[str, Any]:
        """Analyze safety of simulated outcome."""
        risks = []
        confidence = 1.0

        # Check for constraint violations in final state
        final_state = simulation_result.get("final_state", {})

        # Temperature safety checks
        if action.action_type == ActionType.CLIMATE_CONTROL:
            target_temp = final_state.get("temperature")
            if target_temp is not None:
                if target_temp < 10 or target_temp > 35:
                    risks.append({
                        "type": "temperature_extreme",
                        "severity": 0.9,
                        "description": f"Temperature {target_temp}°C is outside safe range"
                    })

        # Power consumption checks
        power_consumption = final_state.get("power_consumption", 0)
        if power_consumption > 5000:  # 5kW
            risks.append({
                "type": "power_excessive",
                "severity": 0.7,
                "description": f"Power consumption {power_consumption}W exceeds limits"
            })

        # Security checks
        if action.action_type == ActionType.SECURITY_CONTROL:
            if final_state.get("locked") is False:
                # Check time of day - unlocking at night might be risky
                hour = datetime.now().hour
                if 22 <= hour or hour <= 6:
                    risks.append({
                        "type": "nighttime_unlock",
                        "severity": 0.6,
                        "description": "Unlocking doors during nighttime hours"
                    })

        # Adjust confidence based on risks
        if risks:
            max_severity = max(r["severity"] for r in risks)
            confidence = max(0.0, 1.0 - max_severity)

        return {
            "safe": len(risks) == 0 or max([r["severity"] for r in risks] + [0]) < 0.5,
            "confidence": confidence,
            "risks": risks
        }

    async def _restore_state(self, house_id: str, device_id: str, original_state: Dict[str, Any]):
        """Restore device to original state."""
        if original_state:
            await self.twin_manager.update_device_state(house_id, device_id, original_state)


class RollbackManager:
    """Manages rollback checkpoints for actions."""

    def __init__(self, twin_manager: DigitalTwinManager):
        self.twin_manager = twin_manager
        self.checkpoints: Dict[str, Dict[str, Any]] = {}

    async def create_checkpoint(self, action: ControlAction) -> str:
        """Create rollback checkpoint before action execution."""
        checkpoint_id = f"checkpoint_{action.action_id}_{uuid.uuid4().hex[:8]}"

        house_id = action.context.get("house_id")
        if house_id:
            house = await self.twin_manager.get_house_twin(house_id)
            if house:
                device = house.all_devices.get(action.target)
                if device:
                    self.checkpoints[checkpoint_id] = {
                        "house_id": house_id,
                        "device_id": action.target,
                        "original_state": device.current_values.copy(),
                        "timestamp": datetime.now().isoformat(),
                        "action_id": action.action_id
                    }

        return checkpoint_id

    async def rollback(self, checkpoint_id: str) -> bool:
        """Rollback to checkpoint state."""
        if checkpoint_id not in self.checkpoints:
            return False

        checkpoint = self.checkpoints[checkpoint_id]

        try:
            await self.twin_manager.update_device_state(
                checkpoint["house_id"],
                checkpoint["device_id"],
                checkpoint["original_state"]
            )

            # Remove checkpoint after successful rollback
            del self.checkpoints[checkpoint_id]
            return True

        except Exception as e:
            print(f"Rollback failed for checkpoint {checkpoint_id}: {e}")
            return False


class FeedbackModule:
    """SAFLA Feedback Module - Control actions and responses with safety validation."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.action_queue = PriorityQueue()
        self.twin_manager: Optional[DigitalTwinManager] = None
        self.executor: Optional[ActionExecutor] = None
        self.safety_controller: Optional[SafetyController] = None
        self.twin_validator: Optional[TwinActionValidator] = None
        self.rollback_manager: Optional[RollbackManager] = None

        # Metrics
        self.metrics = {
            "actions_generated": 0,
            "actions_executed": 0,
            "actions_failed": 0,
            "safety_violations": 0,
            "twin_validations": 0,
            "rollbacks_performed": 0
        }

    async def initialize(self):
        """Initialize the feedback module."""
        # Initialize twin manager
        self.twin_manager = DigitalTwinManager()
        await self.twin_manager.initialize()

        # Initialize components
        self.executor = ActionExecutor(self.twin_manager)

        # Initialize safety constraints
        safety_constraints = [
            TemperatureSafetyConstraint(10, 35),
            RateLimitConstraint(10, 60),
            PowerLimitConstraint(5000)
        ]
        self.safety_controller = SafetyController(safety_constraints)

        # Initialize validators
        self.twin_validator = TwinActionValidator(self.twin_manager)
        self.rollback_manager = RollbackManager(self.twin_manager)

        print("= Feedback Module initialized")

    async def process_analysis(self, analysis: AnalysisResult) -> List[ExecutionResult]:
        """Process analysis results and generate control actions."""
        # Generate actions from analysis
        actions = self._generate_actions(analysis)
        self.metrics["actions_generated"] += len(actions)

        # Validate and queue actions
        validated_actions = []
        for action in actions:
            if await self._validate_action(action):
                self.action_queue.enqueue(action)
                validated_actions.append(action)
            else:
                self.metrics["safety_violations"] += 1

        # Execute actions
        results = await self._execute_actions(validated_actions)

        return results

    def _generate_actions(self, analysis: AnalysisResult) -> List[ControlAction]:
        """Generate control actions based on analysis."""
        actions = []

        # Handle critical anomalies first
        for anomaly in analysis.anomalies:
            if anomaly.severity > 0.8:
                action = self._create_mitigation_action(anomaly)
                if action:
                    actions.append(action)

        # Handle predictions
        for prediction in analysis.predictions:
            if prediction.confidence > 0.7:
                action = self._create_preventive_action(prediction)
                if action:
                    actions.append(action)

        # Handle optimization patterns
        for pattern in analysis.patterns:
            if pattern.confidence > 0.6:
                action = self._create_optimization_action(pattern)
                if action:
                    actions.append(action)

        return actions

    def _create_mitigation_action(self, anomaly: Anomaly) -> Optional[ControlAction]:
        """Create action to mitigate anomaly."""
        action_id = f"mitigation_{uuid.uuid4().hex[:8]}"

        # Determine action based on anomaly type and sensor
        if "temperature" in anomaly.sensor_id.lower():
            if anomaly.value > anomaly.expected_range[1]:
                # Temperature too high
                return ControlAction(
                    action_id=action_id,
                    action_type=ActionType.CLIMATE_CONTROL,
                    target=f"thermostat_{anomaly.sensor_id.split('_')[0]}",
                    parameters={
                        "hvac_mode": "cool",
                        "target_temperature": anomaly.expected_range[1] - 1
                    },
                    priority=Priority.HIGH,
                    context={"anomaly_id": anomaly.sensor_id},
                    generated_from=f"anomaly_mitigation_{anomaly.anomaly_type.value}"
                )
            elif anomaly.value < anomaly.expected_range[0]:
                # Temperature too low
                return ControlAction(
                    action_id=action_id,
                    action_type=ActionType.CLIMATE_CONTROL,
                    target=f"thermostat_{anomaly.sensor_id.split('_')[0]}",
                    parameters={
                        "hvac_mode": "heat",
                        "target_temperature": anomaly.expected_range[0] + 1
                    },
                    priority=Priority.HIGH,
                    context={"anomaly_id": anomaly.sensor_id},
                    generated_from=f"anomaly_mitigation_{anomaly.anomaly_type.value}"
                )

        elif "power" in anomaly.sensor_id.lower():
            if anomaly.severity > 0.9:
                # Excessive power consumption
                return ControlAction(
                    action_id=action_id,
                    action_type=ActionType.ENERGY_OPTIMIZATION,
                    target=anomaly.sensor_id.split('_')[0],
                    parameters={
                        "action": "reduce_consumption",
                        "target_reduction": 0.2
                    },
                    priority=Priority.CRITICAL,
                    context={"anomaly_id": anomaly.sensor_id},
                    generated_from=f"anomaly_mitigation_{anomaly.anomaly_type.value}"
                )

        return None

    def _create_preventive_action(self, prediction: Prediction) -> Optional[ControlAction]:
        """Create preventive action based on prediction."""
        if prediction.prediction_type == "next_value":
            pred_data = prediction.prediction
            sensor_id = pred_data.get("sensor_id")
            predicted_value = pred_data.get("predicted_value")
            trend = pred_data.get("trend")

            if abs(trend) > 0.1:  # Significant trend
                action_id = f"preventive_{uuid.uuid4().hex[:8]}"

                if "temperature" in sensor_id.lower():
                    # Predict temperature changes
                    if trend > 0 and predicted_value > 0.8:  # Getting hot
                        return ControlAction(
                            action_id=action_id,
                            action_type=ActionType.CLIMATE_CONTROL,
                            target=f"thermostat_{sensor_id.split('_')[0]}",
                            parameters={
                                "hvac_mode": "cool",
                                "target_temperature": 22
                            },
                            priority=Priority.MEDIUM,
                            context={"prediction_id": prediction.model_name},
                            generated_from=f"prediction_{prediction.model_name}"
                        )
                    elif trend < 0 and predicted_value < 0.3:  # Getting cold
                        return ControlAction(
                            action_id=action_id,
                            action_type=ActionType.CLIMATE_CONTROL,
                            target=f"thermostat_{sensor_id.split('_')[0]}",
                            parameters={
                                "hvac_mode": "heat",
                                "target_temperature": 20
                            },
                            priority=Priority.MEDIUM,
                            context={"prediction_id": prediction.model_name},
                            generated_from=f"prediction_{prediction.model_name}"
                        )

        return None

    def _create_optimization_action(self, pattern: Pattern) -> Optional[ControlAction]:
        """Create optimization action based on detected pattern."""
        action_id = f"optimization_{uuid.uuid4().hex[:8]}"

        if pattern.pattern_type.value == "periodic":
            # Use periodic patterns for scheduling
            period = pattern.metadata.get("period", 0)

            if 3600 <= period <= 86400:  # 1-24 hour periods
                # Daily pattern detected - optimize based on time
                return ControlAction(
                    action_id=action_id,
                    action_type=ActionType.ENERGY_OPTIMIZATION,
                    target="house_schedule",
                    parameters={
                        "action": "schedule_optimization",
                        "period": period,
                        "pattern_confidence": pattern.confidence
                    },
                    priority=Priority.LOW,
                    context={"pattern_id": pattern.sensor_ids[0] if pattern.sensor_ids else "unknown"},
                    generated_from=f"pattern_{pattern.pattern_type.value}"
                )

        elif pattern.pattern_type.value == "trend":
            # Use trends for proactive adjustments
            trend_data = pattern.metadata
            if trend_data.get("trend_type") == "linear":
                slope = trend_data.get("slope", 0)

                if abs(slope) > 0.05:  # Significant trend
                    return ControlAction(
                        action_id=action_id,
                        action_type=ActionType.COMFORT_ADJUSTMENT,
                        target=pattern.sensor_ids[0] if pattern.sensor_ids else "default",
                        parameters={
                            "action": "trend_adjustment",
                            "slope": slope,
                            "direction": trend_data.get("direction", "stable")
                        },
                        priority=Priority.LOW,
                        context={"pattern_id": pattern.sensor_ids[0] if pattern.sensor_ids else "unknown"},
                        generated_from=f"pattern_{pattern.pattern_type.value}"
                    )

        return None

    async def _validate_action(self, action: ControlAction) -> bool:
        """Validate action against safety constraints and twin testing."""
        action.status = ActionStatus.VALIDATING

        # Safety constraint validation
        safety_result = await self.safety_controller.validate(action)
        action.safety_validations.append(safety_result)

        if not safety_result["safe"]:
            action.status = ActionStatus.FAILED
            action.error = f"Safety constraint violations: {safety_result['violations']}"
            return False

        # Twin-based validation
        action.status = ActionStatus.TWIN_TESTING
        self.metrics["twin_validations"] += 1

        twin_result = await self.twin_validator.validate_action(action)
        action.twin_test_result = twin_result

        if not twin_result["safe"]:
            action.status = ActionStatus.FAILED
            action.error = f"Twin validation failed: {twin_result.get('reason', 'Unknown')}"
            return False

        return True

    async def _execute_actions(self, actions: List[ControlAction]) -> List[ExecutionResult]:
        """Execute validated actions with rollback capability."""
        results = []

        for action in actions:
            try:
                # Create rollback checkpoint
                checkpoint_id = await self.rollback_manager.create_checkpoint(action)
                action.rollback_data = {"checkpoint_id": checkpoint_id}

                # Execute action
                result = await self.executor.execute(action)

                if result.success:
                    self.metrics["actions_executed"] += 1
                else:
                    self.metrics["actions_failed"] += 1

                    # Rollback on failure
                    if checkpoint_id:
                        rollback_success = await self.rollback_manager.rollback(checkpoint_id)
                        if rollback_success:
                            self.metrics["rollbacks_performed"] += 1

                results.append(result)

            except Exception as e:
                # Create error result
                error_result = ExecutionResult(
                    action_id=action.action_id,
                    success=False,
                    timestamp=datetime.now(),
                    execution_time=0.0,
                    error=str(e)
                )
                results.append(error_result)
                self.metrics["actions_failed"] += 1

        return results

    def get_metrics(self) -> Dict[str, Any]:
        """Get feedback module metrics."""
        return {
            **self.metrics,
            "queue_size": len(self.action_queue.items),
            "success_rate": (
                self.metrics["actions_executed"] /
                max(1, self.metrics["actions_executed"] + self.metrics["actions_failed"])
            ),
            "safety_violation_rate": (
                self.metrics["safety_violations"] /
                max(1, self.metrics["actions_generated"])
            )
        }

    async def get_action_status(self, action_id: str) -> Optional[Dict[str, Any]]:
        """Get status of specific action."""
        # Check queue
        for action in self.action_queue.items:
            if action.action_id == action_id:
                return {
                    "action_id": action_id,
                    "status": action.status.value,
                    "created_at": action.created_at.isoformat(),
                    "priority": action.priority.value,
                    "action_type": action.action_type.value,
                    "safety_validations": action.safety_validations,
                    "twin_test_result": action.twin_test_result
                }

        return None
