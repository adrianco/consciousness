"""SAFLA Analyze Module - Pattern recognition and AI processing component."""

import asyncio
import pickle
from collections import defaultdict, deque
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.ensemble import IsolationForest

from ..database import get_async_session
from ..models.events import AnalysisResult as AnalysisResultModel
from .sense_module import NormalizedData, TemporalPattern


class PatternType(Enum):
    """Types of detected patterns."""
    PERIODIC = "periodic"
    TREND = "trend"
    ANOMALY = "anomaly"
    CORRELATION = "correlation"
    SEQUENCE = "sequence"
    CLUSTER = "cluster"


class AnomalyType(Enum):
    """Types of anomalies."""
    STATISTICAL = "statistical"
    CONTEXTUAL = "contextual"
    COLLECTIVE = "collective"
    RULE_BASED = "rule_based"


class Pattern:
    """Detected pattern in sensor data."""

    def __init__(
        self,
        pattern_type: PatternType,
        sensor_ids: List[str],
        confidence: float,
        start_time: float,
        end_time: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.pattern_type = pattern_type
        self.sensor_ids = sensor_ids
        self.confidence = confidence
        self.start_time = start_time
        self.end_time = end_time
        self.metadata = metadata or {}


class Anomaly:
    """Detected anomaly in sensor data."""

    def __init__(
        self,
        anomaly_type: AnomalyType,
        sensor_id: str,
        timestamp: float,
        severity: float,
        value: Any,
        expected_range: Tuple[float, float],
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.anomaly_type = anomaly_type
        self.sensor_id = sensor_id
        self.timestamp = timestamp
        self.severity = severity
        self.value = value
        self.expected_range = expected_range
        self.description = description
        self.metadata = metadata or {}


class Prediction:
    """AI model prediction."""

    def __init__(
        self,
        model_name: str,
        prediction_type: str,
        timestamp: float,
        prediction: Any,
        confidence: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.model_name = model_name
        self.prediction_type = prediction_type
        self.timestamp = timestamp
        self.prediction = prediction
        self.confidence = confidence
        self.metadata = metadata or {}


class AnalysisResult:
    """Complete analysis result."""

    def __init__(
        self,
        patterns: List[Pattern],
        anomalies: List[Anomaly],
        predictions: List[Prediction],
        confidence: float,
        processing_time: float
    ):
        self.patterns = patterns
        self.anomalies = anomalies
        self.predictions = predictions
        self.confidence = confidence
        self.processing_time = processing_time


class AnalysisCache:
    """Cache for analysis results."""

    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, Tuple[AnalysisResult, float]] = {}
        self.max_size = max_size
        self.ttl = 300  # 5 minutes

    def get(self, data: List[NormalizedData]) -> Optional[AnalysisResult]:
        """Get cached result if available."""
        cache_key = self._generate_key(data)

        if cache_key in self.cache:
            result, timestamp = self.cache[cache_key]
            if datetime.now().timestamp() - timestamp < self.ttl:
                return result
            else:
                del self.cache[cache_key]

        return None

    def set(self, data: List[NormalizedData], result: AnalysisResult):
        """Cache analysis result."""
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]

        cache_key = self._generate_key(data)
        self.cache[cache_key] = (result, datetime.now().timestamp())

    def _generate_key(self, data: List[NormalizedData]) -> str:
        """Generate cache key from data."""
        if not data:
            return "empty"

        # Use first and last timestamps, sensor count, and data hash
        key_parts = [
            str(data[0].timestamp),
            str(data[-1].timestamp),
            str(len(data)),
            str(len(set(d.sensor_id for d in data)))
        ]
        return "_".join(key_parts)


class PatternDetector:
    """Base pattern detector interface."""

    async def detect(self, data: List[NormalizedData]) -> List[Pattern]:
        """Detect patterns in data."""
        raise NotImplementedError


class PeriodicPatternDetector(PatternDetector):
    """Detects periodic patterns using FFT."""

    def __init__(self, min_period: float = 60, max_period: float = 86400):
        self.min_period = min_period  # 1 minute
        self.max_period = max_period  # 24 hours

    async def detect(self, data: List[NormalizedData]) -> List[Pattern]:
        """Detect periodic patterns."""
        patterns = []

        # Group by sensor
        sensor_groups = defaultdict(list)
        for d in data:
            sensor_groups[d.sensor_id].append(d)

        for sensor_id, sensor_data in sensor_groups.items():
            if len(sensor_data) < 10:
                continue

            # Extract time series
            timestamps = np.array([d.timestamp for d in sensor_data])
            values = np.array([d.normalized_value for d in sensor_data])

            # Perform FFT analysis
            pattern = self._analyze_periodicity(sensor_id, timestamps, values)
            if pattern:
                patterns.append(pattern)

        return patterns

    def _analyze_periodicity(
        self,
        sensor_id: str,
        timestamps: np.ndarray,
        values: np.ndarray
    ) -> Optional[Pattern]:
        """Analyze periodicity using FFT."""
        try:
            # Ensure uniform sampling
            time_diffs = np.diff(timestamps)
            avg_interval = np.mean(time_diffs)

            # Resample if needed
            if np.std(time_diffs) > avg_interval * 0.1:
                # Non-uniform sampling, need to interpolate
                uniform_timestamps = np.linspace(
                    timestamps[0],
                    timestamps[-1],
                    len(timestamps)
                )
                values = np.interp(uniform_timestamps, timestamps, values)
                timestamps = uniform_timestamps

            # Remove trend
            detrended = values - np.polyval(np.polyfit(range(len(values)), values, 1), range(len(values)))

            # Apply window to reduce edge effects
            window = np.hanning(len(detrended))
            windowed = detrended * window

            # FFT
            fft_result = np.fft.fft(windowed)
            frequencies = np.fft.fftfreq(len(windowed), d=avg_interval)

            # Get positive frequencies only
            positive_freq_idx = frequencies > 0
            frequencies = frequencies[positive_freq_idx]
            magnitudes = np.abs(fft_result[positive_freq_idx])

            # Find peaks
            peak_idx = np.argmax(magnitudes)
            peak_freq = frequencies[peak_idx]
            peak_magnitude = magnitudes[peak_idx]

            # Check if significant
            if peak_magnitude < np.mean(magnitudes) * 2:
                return None

            period = 1 / peak_freq

            # Check if within valid range
            if self.min_period <= period <= self.max_period:
                return Pattern(
                    pattern_type=PatternType.PERIODIC,
                    sensor_ids=[sensor_id],
                    confidence=min(1.0, peak_magnitude / (np.sum(magnitudes) + 1e-10)),
                    start_time=timestamps[0],
                    end_time=timestamps[-1],
                    metadata={
                        "period": period,
                        "frequency": peak_freq,
                        "amplitude": peak_magnitude,
                        "phase": np.angle(fft_result[peak_idx])
                    }
                )

        except Exception as e:
            print(f"Error in periodicity analysis: {e}")

        return None


class TrendPatternDetector(PatternDetector):
    """Detects trend patterns using regression analysis."""

    def __init__(self, min_r_squared: float = 0.7):
        self.min_r_squared = min_r_squared

    async def detect(self, data: List[NormalizedData]) -> List[Pattern]:
        """Detect trend patterns."""
        patterns = []

        # Group by sensor
        sensor_groups = defaultdict(list)
        for d in data:
            sensor_groups[d.sensor_id].append(d)

        for sensor_id, sensor_data in sensor_groups.items():
            if len(sensor_data) < 5:
                continue

            # Extract time series
            timestamps = np.array([d.timestamp for d in sensor_data])
            values = np.array([d.normalized_value for d in sensor_data])

            # Detect trend
            pattern = self._analyze_trend(sensor_id, timestamps, values)
            if pattern:
                patterns.append(pattern)

        return patterns

    def _analyze_trend(
        self,
        sensor_id: str,
        timestamps: np.ndarray,
        values: np.ndarray
    ) -> Optional[Pattern]:
        """Analyze trend using linear regression."""
        try:
            # Normalize timestamps
            t_normalized = timestamps - timestamps[0]

            # Fit polynomial (degree 1 for linear, 2 for quadratic)
            coeffs_linear = np.polyfit(t_normalized, values, 1)
            coeffs_quad = np.polyfit(t_normalized, values, 2)

            # Calculate R-squared for both
            y_pred_linear = np.polyval(coeffs_linear, t_normalized)
            y_pred_quad = np.polyval(coeffs_quad, t_normalized)

            ss_res_linear = np.sum((values - y_pred_linear) ** 2)
            ss_res_quad = np.sum((values - y_pred_quad) ** 2)
            ss_tot = np.sum((values - np.mean(values)) ** 2)

            r2_linear = 1 - (ss_res_linear / (ss_tot + 1e-10))
            r2_quad = 1 - (ss_res_quad / (ss_tot + 1e-10))

            # Choose best fit
            if r2_quad > r2_linear * 1.1 and r2_quad > self.min_r_squared:
                # Quadratic trend
                return Pattern(
                    pattern_type=PatternType.TREND,
                    sensor_ids=[sensor_id],
                    confidence=r2_quad,
                    start_time=timestamps[0],
                    end_time=timestamps[-1],
                    metadata={
                        "trend_type": "quadratic",
                        "coefficients": coeffs_quad.tolist(),
                        "r_squared": r2_quad,
                        "acceleration": coeffs_quad[0] * 2
                    }
                )
            elif r2_linear > self.min_r_squared:
                # Linear trend
                slope = coeffs_linear[0]
                return Pattern(
                    pattern_type=PatternType.TREND,
                    sensor_ids=[sensor_id],
                    confidence=r2_linear,
                    start_time=timestamps[0],
                    end_time=timestamps[-1],
                    metadata={
                        "trend_type": "linear",
                        "slope": slope,
                        "direction": "increasing" if slope > 0 else "decreasing",
                        "r_squared": r2_linear,
                        "rate_per_hour": slope * 3600
                    }
                )

        except Exception as e:
            print(f"Error in trend analysis: {e}")

        return None


class AnomalyDetector:
    """Base anomaly detector interface."""

    async def detect(self, data: List[NormalizedData]) -> List[Anomaly]:
        """Detect anomalies in data."""
        raise NotImplementedError


class StatisticalAnomalyDetector(AnomalyDetector):
    """Statistical anomaly detection using z-scores and IQR."""

    def __init__(self, z_threshold: float = 3.0):
        self.z_threshold = z_threshold

    async def detect(self, data: List[NormalizedData]) -> List[Anomaly]:
        """Detect statistical anomalies."""
        anomalies = []

        # Group by sensor
        sensor_groups = defaultdict(list)
        for d in data:
            sensor_groups[d.sensor_id].append(d)

        for sensor_id, sensor_data in sensor_groups.items():
            if len(sensor_data) < 5:
                continue

            values = np.array([d.normalized_value for d in sensor_data])

            # Z-score method
            mean = np.mean(values)
            std = np.std(values)

            if std > 0:
                for i, d in enumerate(sensor_data):
                    z_score = abs((d.normalized_value - mean) / std)
                    if z_score > self.z_threshold:
                        anomalies.append(Anomaly(
                            anomaly_type=AnomalyType.STATISTICAL,
                            sensor_id=sensor_id,
                            timestamp=d.timestamp,
                            severity=min(1.0, z_score / (self.z_threshold * 2)),
                            value=d.value,
                            expected_range=(mean - 2*std, mean + 2*std),
                            description=f"Value {d.value} is {z_score:.1f} standard deviations from mean",
                            metadata={
                                "z_score": z_score,
                                "mean": mean,
                                "std": std
                            }
                        ))

        return anomalies


class MLAnomalyDetector(AnomalyDetector):
    """Machine learning based anomaly detection."""

    def __init__(self, contamination: float = 0.1):
        self.contamination = contamination
        self.model = IsolationForest(contamination=contamination, random_state=42)

    async def detect(self, data: List[NormalizedData]) -> List[Anomaly]:
        """Detect anomalies using Isolation Forest."""
        anomalies = []

        # Group by sensor type for better detection
        sensor_type_groups = defaultdict(list)
        for d in data:
            sensor_type_groups[d.sensor_type].append(d)

        for sensor_type, type_data in sensor_type_groups.items():
            if len(type_data) < 20:  # Need enough data for ML
                continue

            # Prepare features
            features = []
            data_points = []

            for d in type_data:
                # Feature vector: [normalized_value, hour_of_day, day_of_week]
                dt = datetime.fromtimestamp(d.timestamp)
                features.append([
                    d.normalized_value,
                    dt.hour / 24.0,
                    dt.weekday() / 7.0
                ])
                data_points.append(d)

            features_array = np.array(features)

            try:
                # Fit and predict
                predictions = self.model.fit_predict(features_array)

                # Extract anomalies (labeled as -1)
                for i, pred in enumerate(predictions):
                    if pred == -1:
                        d = data_points[i]
                        anomalies.append(Anomaly(
                            anomaly_type=AnomalyType.STATISTICAL,
                            sensor_id=d.sensor_id,
                            timestamp=d.timestamp,
                            severity=0.8,
                            value=d.value,
                            expected_range=(0, 1),  # Normalized range
                            description="ML model detected unusual pattern",
                            metadata={
                                "model": "IsolationForest",
                                "sensor_type": sensor_type.value
                            }
                        ))

            except Exception as e:
                print(f"Error in ML anomaly detection: {e}")

        return anomalies


class AnalyzeModule:
    """SAFLA Analyze Module - Pattern recognition and AI processing."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cache = AnalysisCache(config.get("cache_size", 1000))

        # Initialize pattern detectors
        self.pattern_detectors = [
            PeriodicPatternDetector(),
            TrendPatternDetector()
        ]

        # Initialize anomaly detectors
        self.anomaly_detectors = [
            StatisticalAnomalyDetector(),
            MLAnomalyDetector()
        ]

        # Model storage
        self.models: Dict[str, Any] = {}

        # Metrics
        self.metrics = {
            "analyses_performed": 0,
            "patterns_detected": 0,
            "anomalies_detected": 0,
            "predictions_made": 0,
            "cache_hits": 0,
            "average_processing_time": 0
        }

    async def initialize(self):
        """Initialize the analyze module."""
        print(">à Analyze Module initialized")

    async def analyze(self, data: List[NormalizedData]) -> AnalysisResult:
        """Analyze sensor data for patterns, anomalies, and predictions."""
        start_time = datetime.now()

        # Check cache
        cached_result = self.cache.get(data)
        if cached_result:
            self.metrics["cache_hits"] += 1
            return cached_result

        try:
            # Run parallel analysis pipelines
            patterns_task = self._detect_patterns(data)
            anomalies_task = self._detect_anomalies(data)
            predictions_task = self._generate_predictions(data)

            patterns, anomalies, predictions = await asyncio.gather(
                patterns_task,
                anomalies_task,
                predictions_task
            )

            # Calculate overall confidence
            confidence = self._calculate_overall_confidence(patterns, anomalies, predictions)

            # Create result
            processing_time = (datetime.now() - start_time).total_seconds()
            result = AnalysisResult(
                patterns=patterns,
                anomalies=anomalies,
                predictions=predictions,
                confidence=confidence,
                processing_time=processing_time
            )

            # Cache result
            self.cache.set(data, result)

            # Update metrics
            self.metrics["analyses_performed"] += 1
            self.metrics["patterns_detected"] += len(patterns)
            self.metrics["anomalies_detected"] += len(anomalies)
            self.metrics["predictions_made"] += len(predictions)

            # Update average processing time
            avg_time = self.metrics["average_processing_time"]
            count = self.metrics["analyses_performed"]
            self.metrics["average_processing_time"] = (avg_time * (count - 1) + processing_time) / count

            return result

        except Exception as e:
            print(f"L Error in analysis: {e}")
            # Return empty result on error
            return AnalysisResult([], [], [], 0.0, 0.0)

    async def _detect_patterns(self, data: List[NormalizedData]) -> List[Pattern]:
        """Detect patterns using all pattern detectors."""
        all_patterns = []

        # Run detectors in parallel
        detector_tasks = [detector.detect(data) for detector in self.pattern_detectors]
        detector_results = await asyncio.gather(*detector_tasks)

        # Merge results
        for patterns in detector_results:
            all_patterns.extend(patterns)

        return all_patterns

    async def _detect_anomalies(self, data: List[NormalizedData]) -> List[Anomaly]:
        """Detect anomalies using all anomaly detectors."""
        all_anomalies = []

        # Run detectors in parallel
        detector_tasks = [detector.detect(data) for detector in self.anomaly_detectors]
        detector_results = await asyncio.gather(*detector_tasks)

        # Merge results
        for anomalies in detector_results:
            all_anomalies.extend(anomalies)

        return all_anomalies

    async def _generate_predictions(self, data: List[NormalizedData]) -> List[Prediction]:
        """Generate predictions using AI models."""
        predictions = []

        # Simple prediction based on trends
        sensor_groups = defaultdict(list)
        for d in data:
            sensor_groups[d.sensor_id].append(d)

        for sensor_id, sensor_data in sensor_groups.items():
            if len(sensor_data) >= 5:
                values = [d.normalized_value for d in sensor_data[-10:]]

                # Simple moving average prediction
                if len(values) >= 3:
                    trend = (values[-1] - values[0]) / len(values)
                    next_value = values[-1] + trend

                    predictions.append(Prediction(
                        model_name="simple_trend",
                        prediction_type="next_value",
                        timestamp=datetime.now().timestamp(),
                        prediction={
                            "sensor_id": sensor_id,
                            "predicted_value": max(0, min(1, next_value)),
                            "trend": trend
                        },
                        confidence=0.6,
                        metadata={"method": "linear_extrapolation"}
                    ))

        return predictions

    def _calculate_overall_confidence(
        self,
        patterns: List[Pattern],
        anomalies: List[Anomaly],
        predictions: List[Prediction]
    ) -> float:
        """Calculate overall analysis confidence."""
        confidences = []

        # Pattern confidences
        if patterns:
            pattern_conf = np.mean([p.confidence for p in patterns])
            confidences.append(pattern_conf)

        # Anomaly confidence (inverse of severity average)
        if anomalies:
            anomaly_conf = 1 - np.mean([a.severity for a in anomalies])
            confidences.append(anomaly_conf)

        # Prediction confidences
        if predictions:
            pred_conf = np.mean([p.confidence for p in predictions])
            confidences.append(pred_conf)

        # If no results, low confidence
        if not confidences:
            return 0.3

        return np.mean(confidences)

    def get_metrics(self) -> Dict[str, Any]:
        """Get analyze module metrics."""
        return {
            **self.metrics,
            "cache_hit_rate": self.metrics["cache_hits"] / max(1, self.metrics["analyses_performed"]),
            "detectors": {
                "pattern_detectors": len(self.pattern_detectors),
                "anomaly_detectors": len(self.anomaly_detectors)
            }
        }
