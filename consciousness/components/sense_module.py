"""SAFLA Sense Module - Data collection and normalization component."""

import asyncio
from collections import deque
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_async_session
from ..digital_twin.core import DigitalTwinManager
from ..models.events import SensorReading


class DataQuality(Enum):
    """Data quality indicators."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INVALID = "invalid"


class SensorType(Enum):
    """Types of sensors."""
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    MOTION = "motion"
    LIGHT = "light"
    PRESSURE = "pressure"
    POWER = "power"
    DOOR = "door"
    WINDOW = "window"
    CO2 = "co2"
    AIR_QUALITY = "air_quality"
    NOISE = "noise"
    VIBRATION = "vibration"


class NormalizedData:
    """Normalized sensor data structure."""

    def __init__(
        self,
        sensor_id: str,
        sensor_type: SensorType,
        timestamp: float,
        value: Union[float, bool, str],
        normalized_value: float,
        unit: str,
        quality: DataQuality,
        confidence: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.sensor_id = sensor_id
        self.sensor_type = sensor_type
        self.timestamp = timestamp
        self.value = value
        self.normalized_value = normalized_value
        self.unit = unit
        self.quality = quality
        self.confidence = confidence
        self.metadata = metadata or {}


class TemporalPattern:
    """Detected temporal pattern in sensor data."""

    def __init__(
        self,
        pattern_type: str,
        sensor_ids: List[str],
        confidence: float,
        period: Optional[float] = None,
        amplitude: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.pattern_type = pattern_type
        self.sensor_ids = sensor_ids
        self.confidence = confidence
        self.period = period
        self.amplitude = amplitude
        self.metadata = metadata or {}


class CircularBuffer:
    """Efficient circular buffer for sensor data."""

    def __init__(self, size: int):
        self.size = size
        self.buffer = deque(maxlen=size)

    def push(self, data: NormalizedData):
        """Add data to buffer."""
        self.buffer.append(data)

    def get_last_n(self, n: int) -> List[NormalizedData]:
        """Get last n items from buffer."""
        return list(self.buffer)[-n:]

    def get_by_sensor(self, sensor_id: str, limit: int = 100) -> List[NormalizedData]:
        """Get data for specific sensor."""
        return [d for d in list(self.buffer)[-limit:] if d.sensor_id == sensor_id]

    def get_time_window(self, seconds: float) -> List[NormalizedData]:
        """Get data within time window."""
        now = datetime.now().timestamp()
        cutoff = now - seconds
        return [d for d in self.buffer if d.timestamp > cutoff]


class Normalizer:
    """Base normalizer interface."""

    def __init__(self, method: str = "min-max"):
        self.method = method

    def normalize(self, value: Any) -> float:
        """Normalize value to 0-1 range."""
        raise NotImplementedError


class TemperatureNormalizer(Normalizer):
    """Temperature normalizer with unit conversion."""

    def __init__(self, min_temp: float = -10, max_temp: float = 40):
        super().__init__("min-max-scaling")
        self.min = min_temp  # Celsius
        self.max = max_temp

    def normalize(self, value: float, unit: str = "C") -> float:
        """Normalize temperature to 0-1 range."""
        # Convert to Celsius if needed
        if unit == "F":
            value = (value - 32) * 5/9
        elif unit == "K":
            value = value - 273.15

        # Clamp and normalize
        value = max(self.min, min(self.max, value))
        return (value - self.min) / (self.max - self.min)


class HumidityNormalizer(Normalizer):
    """Humidity normalizer (0-100%)."""

    def normalize(self, value: float, unit: str = "%") -> float:
        """Normalize humidity to 0-1 range."""
        return max(0, min(100, value)) / 100


class MotionNormalizer(Normalizer):
    """Motion sensor normalizer (binary)."""

    def normalize(self, value: Union[bool, int, str], unit: str = "") -> float:
        """Normalize motion to 0 or 1."""
        if isinstance(value, bool):
            return 1.0 if value else 0.0
        elif isinstance(value, (int, float)):
            return 1.0 if value > 0 else 0.0
        elif isinstance(value, str):
            return 1.0 if value.lower() in ["true", "yes", "1", "on"] else 0.0
        return 0.0


class PowerNormalizer(Normalizer):
    """Power consumption normalizer."""

    def __init__(self, max_power: float = 10000):  # 10kW max
        super().__init__("log-scaling")
        self.max_power = max_power

    def normalize(self, value: float, unit: str = "W") -> float:
        """Normalize power using log scaling."""
        # Convert to Watts if needed
        if unit == "kW":
            value = value * 1000
        elif unit == "mW":
            value = value / 1000

        # Log normalize for better range handling
        if value <= 0:
            return 0.0
        log_value = np.log10(value + 1)
        log_max = np.log10(self.max_power + 1)
        return min(1.0, log_value / log_max)


class SenseModule:
    """SAFLA Sense Module - Collects and normalizes sensor data."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.buffer_size = config.get("buffer_size", 10000)
        self.buffer = CircularBuffer(self.buffer_size)
        self.session: Optional[AsyncSession] = None
        self.twin_manager: Optional[DigitalTwinManager] = None

        # Initialize normalizers
        self.normalizers = {
            SensorType.TEMPERATURE: TemperatureNormalizer(),
            SensorType.HUMIDITY: HumidityNormalizer(),
            SensorType.MOTION: MotionNormalizer(),
            SensorType.LIGHT: PowerNormalizer(max_power=100),  # 100W for lights
            SensorType.POWER: PowerNormalizer(),
            SensorType.DOOR: MotionNormalizer(),  # Binary
            SensorType.WINDOW: MotionNormalizer(),  # Binary
            SensorType.CO2: Normalizer(),  # ppm - needs custom range
            SensorType.AIR_QUALITY: Normalizer(),  # AQI
            SensorType.NOISE: Normalizer(),  # dB
            SensorType.PRESSURE: Normalizer()  # hPa
        }

        # Sensor registry
        self.sensors: Dict[str, Dict[str, Any]] = {}

        # Metrics
        self.metrics = {
            "readings_collected": 0,
            "readings_validated": 0,
            "readings_rejected": 0,
            "patterns_detected": 0,
            "last_collection": None
        }

    async def initialize(self):
        """Initialize the sense module."""
        # Get database session
        if not self.session:
            session_gen = get_async_session()
            self.session = await session_gen.__anext__()

        # Initialize twin manager if configured
        if self.config.get("use_digital_twins", True):
            self.twin_manager = DigitalTwinManager()
            await self.twin_manager.initialize()

        print("=A Sense Module initialized")

    async def register_sensor(
        self,
        sensor_id: str,
        sensor_type: SensorType,
        metadata: Dict[str, Any]
    ):
        """Register a sensor with the module."""
        self.sensors[sensor_id] = {
            "type": sensor_type,
            "metadata": metadata,
            "last_reading": None,
            "error_count": 0,
            "quality_history": deque(maxlen=10)
        }

    async def collect_data(self) -> List[NormalizedData]:
        """Collect and normalize sensor data."""
        try:
            start_time = datetime.now()

            # Read from all registered sensors
            raw_data = await self._read_sensors()
            self.metrics["readings_collected"] += len(raw_data)

            # Validate data quality
            validated_data = self._validate_data(raw_data)
            self.metrics["readings_validated"] += len(validated_data)
            self.metrics["readings_rejected"] += len(raw_data) - len(validated_data)

            # Normalize data
            normalized_data = self._normalize_data(validated_data)

            # Store in buffer
            for data in normalized_data:
                self.buffer.push(data)

            # Update digital twins if available
            if self.twin_manager:
                await self._update_digital_twins(normalized_data)

            self.metrics["last_collection"] = datetime.now()

            # Log collection time
            collection_time = (datetime.now() - start_time).total_seconds()
            if collection_time > 0.1:  # Log if takes more than 100ms
                print(f"  Sense collection took {collection_time:.3f}s")

            return normalized_data

        except Exception as e:
            print(f"L Error in sense data collection: {e}")
            return []

    async def _read_sensors(self) -> List[Dict[str, Any]]:
        """Read data from all sensors."""
        if not self.session:
            return []

        # Query recent sensor readings from database
        from sqlalchemy import select
        from datetime import datetime, timedelta

        cutoff_time = datetime.utcnow() - timedelta(seconds=60)

        stmt = select(SensorReading).where(
            SensorReading.timestamp > cutoff_time,
            SensorReading.processed == False
        ).limit(1000)

        result = await self.session.execute(stmt)
        readings = result.scalars().all()

        # Convert to sensor data format
        sensor_data = []
        for reading in readings:
            # Determine sensor type
            sensor_type = self._get_sensor_type(reading.sensor_type)
            if sensor_type:
                sensor_data.append({
                    "sensor_id": f"{reading.device_id}_{reading.sensor_type}",
                    "device_id": reading.device_id,
                    "type": sensor_type,
                    "value": reading.value,
                    "unit": reading.unit,
                    "timestamp": reading.timestamp.timestamp(),
                    "raw_reading": reading
                })

                # Mark as processed
                reading.processed = True

        await self.session.commit()
        return sensor_data

    def _get_sensor_type(self, sensor_type_str: str) -> Optional[SensorType]:
        """Map string sensor type to enum."""
        mapping = {
            "temperature": SensorType.TEMPERATURE,
            "humidity": SensorType.HUMIDITY,
            "motion": SensorType.MOTION,
            "light": SensorType.LIGHT,
            "power": SensorType.POWER,
            "door": SensorType.DOOR,
            "window": SensorType.WINDOW,
            "co2": SensorType.CO2,
            "air_quality": SensorType.AIR_QUALITY,
            "noise": SensorType.NOISE,
            "pressure": SensorType.PRESSURE
        }
        return mapping.get(sensor_type_str.lower())

    def _validate_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate sensor data quality."""
        validated = []

        for reading in raw_data:
            # Check timestamp validity
            if not self._is_timestamp_valid(reading["timestamp"]):
                continue

            # Check value range
            if not self._is_value_valid(reading["value"], reading["type"]):
                continue

            # Calculate quality
            quality = self._calculate_quality(reading)
            reading["quality"] = quality

            # Skip invalid quality
            if quality == DataQuality.INVALID:
                continue

            validated.append(reading)

        return validated

    def _is_timestamp_valid(self, timestamp: float) -> bool:
        """Check if timestamp is reasonable."""
        now = datetime.now().timestamp()
        # Within last hour and not in future
        return (now - 3600) < timestamp <= now

    def _is_value_valid(self, value: Any, sensor_type: SensorType) -> bool:
        """Check if value is within valid range for sensor type."""
        if value is None:
            return False

        # Type-specific validation
        if sensor_type == SensorType.TEMPERATURE:
            return isinstance(value, (int, float)) and -50 <= value <= 150
        elif sensor_type == SensorType.HUMIDITY:
            return isinstance(value, (int, float)) and 0 <= value <= 100
        elif sensor_type in [SensorType.MOTION, SensorType.DOOR, SensorType.WINDOW]:
            return isinstance(value, (bool, int, str))
        elif sensor_type == SensorType.POWER:
            return isinstance(value, (int, float)) and value >= 0
        elif sensor_type == SensorType.CO2:
            return isinstance(value, (int, float)) and 0 <= value <= 10000

        return True

    def _calculate_quality(self, reading: Dict[str, Any]) -> DataQuality:
        """Calculate data quality based on various factors."""
        sensor_id = reading["sensor_id"]

        # Check sensor history
        if sensor_id in self.sensors:
            sensor_info = self.sensors[sensor_id]

            # High error rate = low quality
            if sensor_info["error_count"] > 10:
                return DataQuality.LOW

            # Check consistency with recent readings
            recent = self.buffer.get_by_sensor(sensor_id, limit=10)
            if recent and self._is_outlier(reading["value"], recent, reading["type"]):
                return DataQuality.MEDIUM

        # Fresh reading with valid range
        age = datetime.now().timestamp() - reading["timestamp"]
        if age < 5:  # Less than 5 seconds old
            return DataQuality.HIGH
        elif age < 30:  # Less than 30 seconds
            return DataQuality.MEDIUM
        else:
            return DataQuality.LOW

    def _is_outlier(
        self,
        value: float,
        recent_data: List[NormalizedData],
        sensor_type: SensorType
    ) -> bool:
        """Check if value is an outlier compared to recent data."""
        if len(recent_data) < 3:
            return False

        # Get recent values
        recent_values = [d.value for d in recent_data if isinstance(d.value, (int, float))]
        if not recent_values:
            return False

        # Calculate statistics
        mean = np.mean(recent_values)
        std = np.std(recent_values)

        # Z-score test
        if std > 0:
            z_score = abs((value - mean) / std)
            return z_score > 3  # More than 3 standard deviations

        return False

    def _normalize_data(self, validated_data: List[Dict[str, Any]]) -> List[NormalizedData]:
        """Normalize validated sensor data."""
        normalized = []

        for reading in validated_data:
            sensor_type = reading["type"]
            normalizer = self.normalizers.get(sensor_type)

            if not normalizer:
                continue

            try:
                # Normalize value
                normalized_value = normalizer.normalize(
                    reading["value"],
                    reading.get("unit", "")
                )

                # Calculate confidence
                confidence = self._calculate_confidence(reading)

                # Create normalized data
                norm_data = NormalizedData(
                    sensor_id=reading["sensor_id"],
                    sensor_type=sensor_type,
                    timestamp=reading["timestamp"],
                    value=reading["value"],
                    normalized_value=normalized_value,
                    unit=reading.get("unit", ""),
                    quality=reading["quality"],
                    confidence=confidence,
                    metadata={
                        "device_id": reading.get("device_id"),
                        "normalization_method": normalizer.method,
                        "processing_time": datetime.now().timestamp() - reading["timestamp"]
                    }
                )

                normalized.append(norm_data)

            except Exception as e:
                print(f"L Error normalizing {sensor_type} data: {e}")

        return normalized

    def _calculate_confidence(self, reading: Dict[str, Any]) -> float:
        """Calculate confidence score for reading."""
        confidence = 1.0

        # Factor in quality
        quality_scores = {
            DataQuality.HIGH: 1.0,
            DataQuality.MEDIUM: 0.8,
            DataQuality.LOW: 0.5,
            DataQuality.INVALID: 0.0
        }
        confidence *= quality_scores.get(reading["quality"], 0.5)

        # Factor in age
        age = datetime.now().timestamp() - reading["timestamp"]
        age_factor = max(0, 1 - (age / 300))  # Decay over 5 minutes
        confidence *= age_factor

        return confidence

    async def _update_digital_twins(self, data: List[NormalizedData]):
        """Update digital twins with sensor readings."""
        if not self.twin_manager:
            return

        # Group by device
        device_updates: Dict[str, List[NormalizedData]] = {}
        for reading in data:
            device_id = reading.metadata.get("device_id")
            if device_id:
                if device_id not in device_updates:
                    device_updates[device_id] = []
                device_updates[device_id].append(reading)

        # Update twins
        for device_id, readings in device_updates.items():
            try:
                # Convert to state update format
                state_update = {}
                for reading in readings:
                    if reading.sensor_type == SensorType.TEMPERATURE:
                        state_update["temperature"] = reading.value
                    elif reading.sensor_type == SensorType.HUMIDITY:
                        state_update["humidity"] = reading.value
                    elif reading.sensor_type == SensorType.MOTION:
                        state_update["motion_detected"] = bool(reading.value)
                    elif reading.sensor_type == SensorType.POWER:
                        state_update["power_consumption"] = reading.value

                # Find house and update device
                for house_id, house in self.twin_manager.houses.items():
                    device_twin_id = f"device_{device_id}"
                    if device_twin_id in house.all_devices:
                        await self.twin_manager.update_device_state(
                            house_id,
                            device_twin_id,
                            state_update
                        )
                        break

            except Exception as e:
                print(f"L Error updating twin for device {device_id}: {e}")

    def get_temporal_patterns(self, window_size: int = 100) -> List[TemporalPattern]:
        """Detect temporal patterns in buffered data."""
        patterns = []

        # Get recent data
        recent_data = self.buffer.get_last_n(window_size)
        if len(recent_data) < 10:
            return patterns

        # Group by sensor
        sensor_groups: Dict[str, List[NormalizedData]] = {}
        for data in recent_data:
            if data.sensor_id not in sensor_groups:
                sensor_groups[data.sensor_id] = []
            sensor_groups[data.sensor_id].append(data)

        # Detect patterns per sensor
        for sensor_id, sensor_data in sensor_groups.items():
            # Skip if insufficient data
            if len(sensor_data) < 5:
                continue

            # Extract time series
            timestamps = [d.timestamp for d in sensor_data]
            values = [d.normalized_value for d in sensor_data]

            # Check for periodic patterns
            periodic = self._detect_periodicity(timestamps, values)
            if periodic:
                patterns.append(periodic)

            # Check for trends
            trend = self._detect_trend(timestamps, values)
            if trend:
                patterns.append(trend)

        self.metrics["patterns_detected"] = len(patterns)
        return patterns

    def _detect_periodicity(
        self,
        timestamps: List[float],
        values: List[float]
    ) -> Optional[TemporalPattern]:
        """Detect periodic patterns using FFT."""
        if len(values) < 10:
            return None

        try:
            # Convert to numpy arrays
            values_array = np.array(values)

            # Remove DC component
            values_centered = values_array - np.mean(values_array)

            # Apply FFT
            fft_result = np.fft.fft(values_centered)
            frequencies = np.fft.fftfreq(len(values), d=1.0)

            # Find dominant frequency (excluding DC)
            magnitudes = np.abs(fft_result[1:len(values)//2])
            if len(magnitudes) == 0:
                return None

            max_idx = np.argmax(magnitudes)
            dominant_freq = frequencies[max_idx + 1]

            # Check if significant
            if magnitudes[max_idx] < 0.1 * len(values):
                return None

            # Calculate period
            if dominant_freq > 0:
                period = 1 / dominant_freq

                return TemporalPattern(
                    pattern_type="periodic",
                    sensor_ids=[timestamps[0]],  # Using first timestamp as ID placeholder
                    confidence=min(1.0, magnitudes[max_idx] / len(values)),
                    period=period,
                    amplitude=magnitudes[max_idx],
                    metadata={"frequency": dominant_freq}
                )

        except Exception as e:
            print(f"Error in periodicity detection: {e}")

        return None

    def _detect_trend(
        self,
        timestamps: List[float],
        values: List[float]
    ) -> Optional[TemporalPattern]:
        """Detect trend patterns using linear regression."""
        if len(values) < 5:
            return None

        try:
            # Normalize timestamps
            t_min = min(timestamps)
            t_normalized = [(t - t_min) for t in timestamps]

            # Linear regression
            coeffs = np.polyfit(t_normalized, values, 1)
            slope = coeffs[0]

            # Calculate R-squared
            y_pred = np.poly1d(coeffs)(t_normalized)
            ss_res = np.sum((values - y_pred) ** 2)
            ss_tot = np.sum((values - np.mean(values)) ** 2)
            r_squared = 1 - (ss_res / (ss_tot + 1e-10))

            # Check if significant trend
            if abs(slope) > 0.01 and r_squared > 0.7:
                return TemporalPattern(
                    pattern_type="trend",
                    sensor_ids=[timestamps[0]],  # Using first timestamp as ID placeholder
                    confidence=r_squared,
                    metadata={
                        "slope": slope,
                        "direction": "increasing" if slope > 0 else "decreasing",
                        "r_squared": r_squared
                    }
                )

        except Exception as e:
            print(f"Error in trend detection: {e}")

        return None

    def get_sensor_statistics(self, sensor_id: str) -> Dict[str, Any]:
        """Get statistics for a specific sensor."""
        recent_data = self.buffer.get_by_sensor(sensor_id, limit=100)

        if not recent_data:
            return {"error": "No data available"}

        values = [d.normalized_value for d in recent_data]
        timestamps = [d.timestamp for d in recent_data]

        return {
            "sensor_id": sensor_id,
            "count": len(values),
            "mean": np.mean(values),
            "std": np.std(values),
            "min": np.min(values),
            "max": np.max(values),
            "latest_value": values[-1] if values else None,
            "latest_timestamp": timestamps[-1] if timestamps else None,
            "quality_distribution": self._get_quality_distribution(recent_data)
        }

    def _get_quality_distribution(self, data: List[NormalizedData]) -> Dict[str, float]:
        """Calculate quality distribution."""
        quality_counts = {
            DataQuality.HIGH: 0,
            DataQuality.MEDIUM: 0,
            DataQuality.LOW: 0,
            DataQuality.INVALID: 0
        }

        for d in data:
            quality_counts[d.quality] += 1

        total = len(data)
        return {
            q.value: count / total if total > 0 else 0
            for q, count in quality_counts.items()
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get sense module metrics."""
        return {
            **self.metrics,
            "buffer_usage": len(self.buffer.buffer) / self.buffer_size,
            "active_sensors": len(self.sensors),
            "sensor_types": list(set(s["type"].value for s in self.sensors.values()))
        }
