"""SAFLA Learn Module - Model updates and adaptation with scenario-based learning."""

import asyncio
import json
import pickle
from collections import deque
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import uuid

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score
from sklearn.ensemble import IsolationForest

from ..database import get_async_session
from ..digital_twin.core import DigitalTwinManager
from ..models.events import LearningUpdate as LearningUpdateModel
from .analyze_module import AnalysisResult, Pattern, Anomaly, Prediction
from .feedback_module import ExecutionResult, ControlAction
from .sense_module import NormalizedData


class ModelType(Enum):
    """Types of models that can be updated."""
    ANOMALY_DETECTION = "anomaly_detection"
    PREDICTION = "prediction"
    PATTERN_RECOGNITION = "pattern_recognition"
    OPTIMIZATION = "optimization"
    SAFETY_VALIDATION = "safety_validation"


class LearningStrategy(Enum):
    """Learning strategies."""
    INCREMENTAL = "incremental"
    BATCH = "batch"
    ONLINE = "online"
    REINFORCEMENT = "reinforcement"
    TRANSFER = "transfer"


class ExperienceType(Enum):
    """Types of experiences for learning."""
    SENSOR_DATA = "sensor_data"
    ACTION_OUTCOME = "action_outcome"
    PATTERN_DISCOVERY = "pattern_discovery"
    ANOMALY_DETECTION = "anomaly_detection"
    SAFETY_VIOLATION = "safety_violation"
    USER_FEEDBACK = "user_feedback"


class Experience:
    """Single learning experience."""

    def __init__(
        self,
        experience_id: str,
        experience_type: ExperienceType,
        timestamp: datetime,
        input_data: Dict[str, Any],
        expected_output: Optional[Dict[str, Any]] = None,
        actual_output: Optional[Dict[str, Any]] = None,
        feedback_score: Optional[float] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        self.experience_id = experience_id
        self.experience_type = experience_type
        self.timestamp = timestamp
        self.input_data = input_data
        self.expected_output = expected_output
        self.actual_output = actual_output
        self.feedback_score = feedback_score
        self.context = context or {}

        # Learning metadata
        self.importance = self._calculate_importance()
        self.times_used = 0
        self.last_used = timestamp

    def _calculate_importance(self) -> float:
        """Calculate importance score for this experience."""
        base_importance = 0.5

        # Critical experiences are more important
        if self.experience_type == ExperienceType.SAFETY_VIOLATION:
            base_importance = 1.0
        elif self.experience_type == ExperienceType.ANOMALY_DETECTION:
            base_importance = 0.8
        elif self.experience_type == ExperienceType.USER_FEEDBACK:
            base_importance = 0.7

        # Feedback score affects importance
        if self.feedback_score is not None:
            # Extreme feedback (very good or very bad) is more important
            feedback_importance = abs(self.feedback_score - 0.5) * 2
            base_importance = min(1.0, base_importance + feedback_importance * 0.3)

        return base_importance


class ExperienceBuffer:
    """Buffer for storing and managing learning experiences."""

    def __init__(self, max_size: int = 50000):
        self.max_size = max_size
        self.experiences: deque = deque(maxlen=max_size)
        self.importance_index: Dict[float, List[str]] = {}
        self.type_index: Dict[ExperienceType, List[str]] = {}

    def add(self, experience: Experience):
        """Add experience to buffer."""
        self.experiences.append(experience)

        # Update indices
        importance = experience.importance
        if importance not in self.importance_index:
            self.importance_index[importance] = []
        self.importance_index[importance].append(experience.experience_id)

        if experience.experience_type not in self.type_index:
            self.type_index[experience.experience_type] = []
        self.type_index[experience.experience_type].append(experience.experience_id)

    def get_recent(self, count: int) -> List[Experience]:
        """Get most recent experiences."""
        return list(self.experiences)[-count:]

    def get_by_importance(self, count: int, min_importance: float = 0.7) -> List[Experience]:
        """Get experiences by importance score."""
        important_experiences = [
            exp for exp in self.experiences
            if exp.importance >= min_importance
        ]
        # Sort by importance (descending) and recency
        important_experiences.sort(
            key=lambda x: (x.importance, x.timestamp),
            reverse=True
        )
        return important_experiences[:count]

    def get_by_type(self, experience_type: ExperienceType, count: int = 100) -> List[Experience]:
        """Get experiences of specific type."""
        typed_experiences = [
            exp for exp in self.experiences
            if exp.experience_type == experience_type
        ]
        return typed_experiences[-count:]

    def get_historical(self, skip: int, count: int) -> List[Experience]:
        """Get historical experiences (skip recent, take count)."""
        all_experiences = list(self.experiences)
        if len(all_experiences) <= skip:
            return []
        return all_experiences[-(skip + count):-skip]

    def get_all(self) -> List[Experience]:
        """Get all experiences."""
        return list(self.experiences)

    def size(self) -> int:
        """Get buffer size."""
        return len(self.experiences)


class ModelUpdate:
    """Represents a model update operation."""

    def __init__(
        self,
        model_name: str,
        update_type: str,
        timestamp: datetime,
        performance_before: Dict[str, float],
        performance_after: Optional[Dict[str, float]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.model_name = model_name
        self.update_type = update_type
        self.timestamp = timestamp
        self.performance_before = performance_before
        self.performance_after = performance_after
        self.metadata = metadata or {}


class ParameterAdjustment:
    """Represents a parameter adjustment."""

    def __init__(
        self,
        parameter_name: str,
        old_value: Any,
        new_value: Any,
        expected_improvement: float,
        timestamp: datetime
    ):
        self.parameter_name = parameter_name
        self.old_value = old_value
        self.new_value = new_value
        self.expected_improvement = expected_improvement
        self.timestamp = timestamp


class PerformanceMetrics:
    """Performance metrics for learning evaluation."""

    def __init__(
        self,
        accuracy: float,
        precision: float,
        recall: float,
        f1_score: float,
        processing_time: float,
        throughput: float,
        error_rate: float
    ):
        self.accuracy = accuracy
        self.precision = precision
        self.recall = recall
        self.f1_score = f1_score
        self.processing_time = processing_time
        self.throughput = throughput
        self.error_rate = error_rate


class LearningResult:
    """Result of learning process."""

    def __init__(
        self,
        model_updates: List[ModelUpdate],
        parameter_adjustments: List[ParameterAdjustment],
        new_patterns: List[Pattern],
        performance_metrics: PerformanceMetrics
    ):
        self.model_updates = model_updates
        self.parameter_adjustments = parameter_adjustments
        self.new_patterns = new_patterns
        self.performance_metrics = performance_metrics


class PerformanceEvaluator:
    """Evaluates system performance for learning feedback."""

    def __init__(self):
        self.metrics_history: deque = deque(maxlen=1000)

    async def evaluate(self, experience: Experience) -> PerformanceMetrics:
        """Evaluate performance based on experience."""
        # Extract performance data from experience
        if experience.experience_type == ExperienceType.ACTION_OUTCOME:
            return self._evaluate_action_performance(experience)
        elif experience.experience_type == ExperienceType.ANOMALY_DETECTION:
            return self._evaluate_anomaly_performance(experience)
        elif experience.experience_type == ExperienceType.PATTERN_DISCOVERY:
            return self._evaluate_pattern_performance(experience)
        else:
            return self._default_performance_metrics()

    def _evaluate_action_performance(self, experience: Experience) -> PerformanceMetrics:
        """Evaluate action execution performance."""
        result_data = experience.actual_output or {}
        execution_time = result_data.get("execution_time", 0.0)
        success = result_data.get("success", False)

        # Calculate metrics
        accuracy = 1.0 if success else 0.0
        precision = accuracy  # For binary success/failure
        recall = accuracy
        f1_score = accuracy
        error_rate = 0.0 if success else 1.0
        throughput = 1.0 / max(0.001, execution_time)

        return PerformanceMetrics(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            processing_time=execution_time,
            throughput=throughput,
            error_rate=error_rate
        )

    def _evaluate_anomaly_performance(self, experience: Experience) -> PerformanceMetrics:
        """Evaluate anomaly detection performance."""
        feedback_score = experience.feedback_score or 0.5

        # Use feedback score as accuracy proxy
        accuracy = feedback_score
        precision = feedback_score
        recall = feedback_score
        f1_score = feedback_score
        error_rate = 1.0 - feedback_score

        # Default timing metrics
        processing_time = experience.context.get("processing_time", 0.1)
        throughput = 1.0 / max(0.001, processing_time)

        return PerformanceMetrics(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            processing_time=processing_time,
            throughput=throughput,
            error_rate=error_rate
        )

    def _evaluate_pattern_performance(self, experience: Experience) -> PerformanceMetrics:
        """Evaluate pattern discovery performance."""
        pattern_data = experience.actual_output or {}
        confidence = pattern_data.get("confidence", 0.5)

        # Use confidence as accuracy
        accuracy = confidence
        precision = confidence
        recall = confidence
        f1_score = confidence
        error_rate = 1.0 - confidence

        processing_time = experience.context.get("processing_time", 0.1)
        throughput = 1.0 / max(0.001, processing_time)

        return PerformanceMetrics(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            processing_time=processing_time,
            throughput=throughput,
            error_rate=error_rate
        )

    def _default_performance_metrics(self) -> PerformanceMetrics:
        """Default performance metrics."""
        return PerformanceMetrics(
            accuracy=0.5,
            precision=0.5,
            recall=0.5,
            f1_score=0.5,
            processing_time=0.1,
            throughput=10.0,
            error_rate=0.5
        )


class AdaptiveOptimizer:
    """Adaptive parameter optimizer using reinforcement learning principles."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.parameter_history: Dict[str, deque] = {}
        self.performance_history: deque = deque(maxlen=1000)
        self.epsilon = config.get("exploration_rate", 0.1)
        self.learning_rate = config.get("learning_rate", 0.01)

    async def select_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Select parameter adjustment action."""
        # Epsilon-greedy exploration
        if np.random.random() < self.epsilon:
            return self._explore_random_action(state)
        else:
            return self._exploit_best_action(state)

    def _explore_random_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Explore random parameter adjustments."""
        # Define parameter ranges for exploration
        parameter_ranges = {
            "sense_buffer_size": (1000, 20000),
            "analysis_cache_size": (500, 2000),
            "processing_interval": (0.05, 0.5),
            "safety_threshold": (0.1, 0.9),
            "confidence_threshold": (0.5, 0.95)
        }

        # Select random parameter and value
        param_name = np.random.choice(list(parameter_ranges.keys()))
        min_val, max_val = parameter_ranges[param_name]
        new_value = np.random.uniform(min_val, max_val)

        return {
            "parameter": param_name,
            "value": new_value,
            "expected_reward": 0.0,  # Unknown for exploration
            "action_type": "exploration"
        }

    def _exploit_best_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Exploit known good parameter adjustments."""
        # Analyze performance history to find best parameters
        if not self.performance_history:
            return self._explore_random_action(state)

        # Find parameters associated with best performance
        best_performance = max(self.performance_history, key=lambda x: x.get("accuracy", 0))
        best_params = best_performance.get("parameters", {})

        if not best_params:
            return self._explore_random_action(state)

        # Select parameter to adjust based on historical success
        param_scores = {}
        for param_name, param_value in best_params.items():
            if param_name in self.parameter_history:
                # Calculate correlation with performance
                param_scores[param_name] = self._calculate_param_performance_correlation(param_name)

        if not param_scores:
            return self._explore_random_action(state)

        # Select parameter with highest correlation
        best_param = max(param_scores.keys(), key=lambda k: param_scores[k])
        current_value = state.get(best_param, 0.5)

        # Adjust towards optimal direction
        adjustment = self._calculate_optimal_adjustment(best_param, current_value)

        return {
            "parameter": best_param,
            "value": current_value + adjustment,
            "expected_reward": param_scores[best_param],
            "action_type": "exploitation"
        }

    def _calculate_param_performance_correlation(self, param_name: str) -> float:
        """Calculate correlation between parameter and performance."""
        if param_name not in self.parameter_history:
            return 0.0

        param_values = [entry["value"] for entry in self.parameter_history[param_name]]
        performance_values = [entry.get("accuracy", 0.5) for entry in self.performance_history[-len(param_values):]]

        if len(param_values) < 2:
            return 0.0

        try:
            correlation = np.corrcoef(param_values, performance_values)[0, 1]
            return abs(correlation) if not np.isnan(correlation) else 0.0
        except:
            return 0.0

    def _calculate_optimal_adjustment(self, param_name: str, current_value: float) -> float:
        """Calculate optimal parameter adjustment."""
        # Simple gradient-like adjustment
        if param_name not in self.parameter_history:
            return np.random.uniform(-0.1, 0.1) * current_value

        recent_entries = list(self.parameter_history[param_name])[-5:]
        if len(recent_entries) < 2:
            return np.random.uniform(-0.1, 0.1) * current_value

        # Calculate trend
        values = [entry["value"] for entry in recent_entries]
        performance = [entry.get("performance", 0.5) for entry in recent_entries]

        if len(values) != len(performance):
            return np.random.uniform(-0.1, 0.1) * current_value

        # Simple trend analysis
        if performance[-1] > performance[0]:
            # Performance improving - continue in same direction
            trend = values[-1] - values[0]
            return self.learning_rate * trend
        else:
            # Performance declining - reverse direction
            trend = values[-1] - values[0]
            return -self.learning_rate * trend

    def update_policy(self, state: Dict[str, Any], action: Dict[str, Any], reward: float):
        """Update policy based on action outcome."""
        param_name = action["parameter"]
        param_value = action["value"]

        # Record parameter history
        if param_name not in self.parameter_history:
            self.parameter_history[param_name] = deque(maxlen=100)

        self.parameter_history[param_name].append({
            "value": param_value,
            "performance": reward,
            "timestamp": datetime.now(),
            "action_type": action.get("action_type", "unknown")
        })

        # Update performance history
        self.performance_history.append({
            "accuracy": reward,
            "parameters": {param_name: param_value},
            "timestamp": datetime.now()
        })

        # Adjust exploration rate
        self._adjust_exploration_rate(reward)

    def _adjust_exploration_rate(self, reward: float):
        """Adjust exploration rate based on performance."""
        # Reduce exploration if performance is good
        if reward > 0.8:
            self.epsilon = max(0.05, self.epsilon * 0.99)
        elif reward < 0.3:
            # Increase exploration if performance is poor
            self.epsilon = min(0.3, self.epsilon * 1.01)


class ScenarioEngine:
    """Engine for generating and running learning scenarios."""

    def __init__(self, twin_manager: DigitalTwinManager):
        self.twin_manager = twin_manager

    async def generate_learning_scenarios(self) -> List[Dict[str, Any]]:
        """Generate diverse learning scenarios."""
        scenarios = []

        # Power outage scenario
        scenarios.append({
            "name": "power_outage",
            "description": "Simulate power outage and recovery",
            "duration": np.random.uniform(30, 120),  # 30-120 minutes
            "affected_circuits": np.random.choice(["main", "partial"], p=[0.2, 0.8]),
            "recovery_strategy": np.random.choice(["manual", "automatic"], p=[0.3, 0.7]),
            "expected_outcomes": {
                "device_failures": True,
                "backup_activation": True,
                "user_notification": True
            }
        })

        # Temperature extreme scenario
        scenarios.append({
            "name": "temperature_extreme",
            "description": "Extreme temperature conditions",
            "external_temp": np.random.uniform(-10, 40),
            "duration": np.random.uniform(2, 24),  # 2-24 hours
            "hvac_response": np.random.choice(["normal", "emergency"]),
            "expected_outcomes": {
                "climate_activation": True,
                "energy_increase": True,
                "comfort_maintained": True
            }
        })

        # Occupancy change scenario
        scenarios.append({
            "name": "occupancy_change",
            "description": "Significant occupancy pattern change",
            "occupant_count": np.random.randint(0, 7),
            "pattern": np.random.choice(["vacation", "party", "normal"]),
            "duration": np.random.uniform(1, 168),  # 1-168 hours
            "expected_outcomes": {
                "lighting_adjustment": True,
                "security_mode_change": True,
                "energy_optimization": True
            }
        })

        # Security breach simulation
        scenarios.append({
            "name": "security_breach",
            "description": "Simulated security breach",
            "breach_type": np.random.choice(["door", "window", "motion"]),
            "time_of_day": np.random.choice(["day", "night"]),
            "response_time": np.random.uniform(5, 30),  # 5-30 seconds
            "expected_outcomes": {
                "alarm_activation": True,
                "authority_notification": True,
                "recording_start": True
            }
        })

        return scenarios

    async def run_scenario(self, scenario: Dict[str, Any], house_id: str) -> Dict[str, Any]:
        """Run a learning scenario on digital twin."""
        scenario_name = scenario["name"]

        try:
            if scenario_name == "power_outage":
                return await self._run_power_outage_scenario(scenario, house_id)
            elif scenario_name == "temperature_extreme":
                return await self._run_temperature_scenario(scenario, house_id)
            elif scenario_name == "occupancy_change":
                return await self._run_occupancy_scenario(scenario, house_id)
            elif scenario_name == "security_breach":
                return await self._run_security_scenario(scenario, house_id)
            else:
                return {"success": False, "error": f"Unknown scenario: {scenario_name}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _run_power_outage_scenario(self, scenario: Dict[str, Any], house_id: str) -> Dict[str, Any]:
        """Run power outage scenario."""
        # Get house twin
        house = await self.twin_manager.get_house_twin(house_id)
        if not house:
            return {"success": False, "error": "House twin not found"}

        # Record initial state
        initial_state = {device.id: device.current_values.copy() for device in house.all_devices.values()}

        # Simulate power outage
        affected_devices = []
        if scenario["affected_circuits"] == "main":
            # All devices affected
            affected_devices = list(house.all_devices.keys())
        else:
            # Random subset affected
            all_devices = list(house.all_devices.keys())
            affected_count = int(len(all_devices) * 0.6)  # 60% affected
            affected_devices = np.random.choice(all_devices, affected_count, replace=False).tolist()

        # Turn off affected devices
        for device_id in affected_devices:
            await self.twin_manager.update_device_state(house_id, device_id, {"power": False})

        # Wait for scenario duration (simulated)
        await asyncio.sleep(0.1)  # Minimal wait for simulation

        # Recovery based on strategy
        recovery_results = []
        if scenario["recovery_strategy"] == "automatic":
            # Automatic recovery - restore all devices
            for device_id in affected_devices:
                original_state = initial_state.get(device_id, {})
                await self.twin_manager.update_device_state(house_id, device_id, original_state)
                recovery_results.append(f"Restored {device_id}")
        else:
            # Manual recovery - restore critical devices only
            critical_devices = [d for d in affected_devices if "thermostat" in d or "security" in d]
            for device_id in critical_devices:
                original_state = initial_state.get(device_id, {})
                await self.twin_manager.update_device_state(house_id, device_id, original_state)
                recovery_results.append(f"Restored critical device {device_id}")

        return {
            "success": True,
            "scenario": scenario["name"],
            "affected_devices": affected_devices,
            "recovery_actions": recovery_results,
            "duration": scenario["duration"],
            "outcomes_met": {
                "device_failures": len(affected_devices) > 0,
                "backup_activation": scenario["recovery_strategy"] == "automatic",
                "user_notification": True
            }
        }

    async def _run_temperature_scenario(self, scenario: Dict[str, Any], house_id: str) -> Dict[str, Any]:
        """Run temperature extreme scenario."""
        external_temp = scenario["external_temp"]

        # Find thermostats
        house = await self.twin_manager.get_house_twin(house_id)
        if not house:
            return {"success": False, "error": "House twin not found"}

        thermostats = [d for d in house.all_devices.values() if d.device_class == "climate"]

        if not thermostats:
            return {"success": False, "error": "No thermostats found"}

        actions_taken = []

        # Adjust thermostats based on external temperature
        for thermostat in thermostats:
            if external_temp < 0:
                # Very cold - heat mode
                await self.twin_manager.update_device_state(
                    house_id, thermostat.id, {
                        "hvac_mode": "heat",
                        "temperature": 22,
                        "fan_speed": "high"
                    }
                )
                actions_taken.append(f"Set {thermostat.id} to emergency heat mode")
            elif external_temp > 35:
                # Very hot - cool mode
                await self.twin_manager.update_device_state(
                    house_id, thermostat.id, {
                        "hvac_mode": "cool",
                        "temperature": 20,
                        "fan_speed": "high"
                    }
                )
                actions_taken.append(f"Set {thermostat.id} to emergency cool mode")

        return {
            "success": True,
            "scenario": scenario["name"],
            "external_temperature": external_temp,
            "actions_taken": actions_taken,
            "outcomes_met": {
                "climate_activation": len(actions_taken) > 0,
                "energy_increase": True,
                "comfort_maintained": True
            }
        }

    async def _run_occupancy_scenario(self, scenario: Dict[str, Any], house_id: str) -> Dict[str, Any]:
        """Run occupancy change scenario."""
        occupant_count = scenario["occupant_count"]
        pattern = scenario["pattern"]

        house = await self.twin_manager.get_house_twin(house_id)
        if not house:
            return {"success": False, "error": "House twin not found"}

        actions_taken = []

        # Adjust based on occupancy pattern
        if pattern == "vacation" or occupant_count == 0:
            # Turn off most lights, set security mode
            lights = [d for d in house.all_devices.values() if d.device_class == "light"]
            for light in lights:
                await self.twin_manager.update_device_state(
                    house_id, light.id, {"power": False}
                )
                actions_taken.append(f"Turned off {light.id}")

            # Set security mode
            locks = [d for d in house.all_devices.values() if d.device_class == "lock"]
            for lock in locks:
                await self.twin_manager.update_device_state(
                    house_id, lock.id, {"locked": True}
                )
                actions_taken.append(f"Locked {lock.id}")

        elif pattern == "party" or occupant_count > 4:
            # Turn on all lights, adjust climate
            lights = [d for d in house.all_devices.values() if d.device_class == "light"]
            for light in lights:
                await self.twin_manager.update_device_state(
                    house_id, light.id, {"power": True, "brightness": 80}
                )
                actions_taken.append(f"Activated {light.id}")

        return {
            "success": True,
            "scenario": scenario["name"],
            "occupant_count": occupant_count,
            "pattern": pattern,
            "actions_taken": actions_taken,
            "outcomes_met": {
                "lighting_adjustment": True,
                "security_mode_change": pattern == "vacation",
                "energy_optimization": pattern == "vacation"
            }
        }

    async def _run_security_scenario(self, scenario: Dict[str, Any], house_id: str) -> Dict[str, Any]:
        """Run security breach scenario."""
        breach_type = scenario["breach_type"]

        house = await self.twin_manager.get_house_twin(house_id)
        if not house:
            return {"success": False, "error": "House twin not found"}

        actions_taken = []

        # Simulate security response
        if breach_type == "door":
            # Door breach - lock all doors, turn on lights
            locks = [d for d in house.all_devices.values() if d.device_class == "lock"]
            for lock in locks:
                await self.twin_manager.update_device_state(
                    house_id, lock.id, {"locked": True}
                )
                actions_taken.append(f"Emergency locked {lock.id}")

        elif breach_type == "motion":
            # Motion detection - turn on lights, start recording
            lights = [d for d in house.all_devices.values() if d.device_class == "light"]
            for light in lights:
                await self.twin_manager.update_device_state(
                    house_id, light.id, {"power": True, "brightness": 100}
                )
                actions_taken.append(f"Emergency activated {light.id}")

        # Simulate camera recording
        cameras = [d for d in house.all_devices.values() if d.device_class == "camera"]
        for camera in cameras:
            await self.twin_manager.update_device_state(
                house_id, camera.id, {"recording": True, "alert_mode": True}
            )
            actions_taken.append(f"Started emergency recording {camera.id}")

        return {
            "success": True,
            "scenario": scenario["name"],
            "breach_type": breach_type,
            "actions_taken": actions_taken,
            "outcomes_met": {
                "alarm_activation": True,
                "authority_notification": True,
                "recording_start": len(cameras) > 0
            }
        }


class LearnModule:
    """SAFLA Learn Module - Model updates and adaptation with scenario-based learning."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.experience_buffer = ExperienceBuffer(config.get("buffer_size", 50000))
        self.evaluator = PerformanceEvaluator()
        self.optimizer = AdaptiveOptimizer(config.get("optimization", {}))
        self.twin_manager: Optional[DigitalTwinManager] = None
        self.scenario_engine: Optional[ScenarioEngine] = None

        # Learning configuration
        self.accuracy_threshold = config.get("accuracy_threshold", 0.85)
        self.batch_size = config.get("batch_size", 32)
        self.update_interval = config.get("update_interval", 300)  # 5 minutes

        # Model management
        self.models: Dict[str, Any] = {}
        self.model_performance: Dict[str, PerformanceMetrics] = {}

        # Metrics
        self.metrics = {
            "experiences_processed": 0,
            "model_updates": 0,
            "parameter_adjustments": 0,
            "scenarios_run": 0,
            "learning_sessions": 0,
            "average_performance": 0.5
        }

    async def initialize(self):
        """Initialize the learn module."""
        # Initialize twin manager
        self.twin_manager = DigitalTwinManager()
        await self.twin_manager.initialize()

        # Initialize scenario engine
        self.scenario_engine = ScenarioEngine(self.twin_manager)

        print(">à Learn Module initialized")

    async def learn(
        self,
        sensor_data: List[NormalizedData],
        analysis: AnalysisResult,
        execution_results: List[ExecutionResult]
    ) -> LearningResult:
        """Main learning function - processes experiences and updates models."""
        start_time = datetime.now()

        # Create experiences from inputs
        experiences = self._create_experiences(sensor_data, analysis, execution_results)

        # Store experiences
        for experience in experiences:
            self.experience_buffer.add(experience)
            self.metrics["experiences_processed"] += 1

        # Evaluate current performance
        performance_metrics = await self._evaluate_current_performance(experiences)

        # Update models if needed
        model_updates = await self._update_models(performance_metrics)

        # Adjust parameters
        parameter_adjustments = await self._adjust_parameters(performance_metrics)

        # Discover new patterns
        new_patterns = await self._discover_patterns()

        # Run scenario-based learning (periodically)
        if self.metrics["learning_sessions"] % 10 == 0:
            await self._run_scenario_learning()

        self.metrics["learning_sessions"] += 1

        # Update average performance
        self._update_average_performance(performance_metrics)

        learning_time = (datetime.now() - start_time).total_seconds()
        print(f">à Learning completed in {learning_time:.3f}s")

        return LearningResult(
            model_updates=model_updates,
            parameter_adjustments=parameter_adjustments,
            new_patterns=new_patterns,
            performance_metrics=performance_metrics
        )

    def _create_experiences(
        self,
        sensor_data: List[NormalizedData],
        analysis: AnalysisResult,
        execution_results: List[ExecutionResult]
    ) -> List[Experience]:
        """Create learning experiences from system inputs."""
        experiences = []

        # Create experiences from sensor data
        for data in sensor_data:
            experience = Experience(
                experience_id=f"sensor_{uuid.uuid4().hex[:8]}",
                experience_type=ExperienceType.SENSOR_DATA,
                timestamp=datetime.fromtimestamp(data.timestamp),
                input_data={
                    "sensor_id": data.sensor_id,
                    "sensor_type": data.sensor_type.value,
                    "value": data.value,
                    "normalized_value": data.normalized_value,
                    "quality": data.quality.value
                },
                feedback_score=data.confidence,
                context=data.metadata
            )
            experiences.append(experience)

        # Create experiences from analysis results
        for anomaly in analysis.anomalies:
            experience = Experience(
                experience_id=f"anomaly_{uuid.uuid4().hex[:8]}",
                experience_type=ExperienceType.ANOMALY_DETECTION,
                timestamp=datetime.fromtimestamp(anomaly.timestamp),
                input_data={
                    "sensor_id": anomaly.sensor_id,
                    "anomaly_type": anomaly.anomaly_type.value,
                    "value": anomaly.value,
                    "expected_range": anomaly.expected_range
                },
                actual_output={
                    "severity": anomaly.severity,
                    "description": anomaly.description
                },
                feedback_score=1.0 - anomaly.severity,  # Lower severity = better detection
                context=anomaly.metadata
            )
            experiences.append(experience)

        # Create experiences from action executions
        for result in execution_results:
            experience = Experience(
                experience_id=f"action_{uuid.uuid4().hex[:8]}",
                experience_type=ExperienceType.ACTION_OUTCOME,
                timestamp=result.timestamp,
                input_data={
                    "action_id": result.action_id
                },
                actual_output={
                    "success": result.success,
                    "execution_time": result.execution_time,
                    "result_data": result.result_data
                },
                feedback_score=1.0 if result.success else 0.0,
                context={"error": result.error} if result.error else {}
            )
            experiences.append(experience)

        return experiences

    async def _evaluate_current_performance(self, experiences: List[Experience]) -> PerformanceMetrics:
        """Evaluate current system performance."""
        if not experiences:
            return self.evaluator._default_performance_metrics()

        # Evaluate each experience and aggregate
        performance_evaluations = []
        for experience in experiences:
            perf = await self.evaluator.evaluate(experience)
            performance_evaluations.append(perf)

        # Aggregate metrics
        if performance_evaluations:
            avg_accuracy = np.mean([p.accuracy for p in performance_evaluations])
            avg_precision = np.mean([p.precision for p in performance_evaluations])
            avg_recall = np.mean([p.recall for p in performance_evaluations])
            avg_f1 = np.mean([p.f1_score for p in performance_evaluations])
            avg_processing_time = np.mean([p.processing_time for p in performance_evaluations])
            avg_throughput = np.mean([p.throughput for p in performance_evaluations])
            avg_error_rate = np.mean([p.error_rate for p in performance_evaluations])

            return PerformanceMetrics(
                accuracy=avg_accuracy,
                precision=avg_precision,
                recall=avg_recall,
                f1_score=avg_f1,
                processing_time=avg_processing_time,
                throughput=avg_throughput,
                error_rate=avg_error_rate
            )
        else:
            return self.evaluator._default_performance_metrics()

    async def _update_models(self, performance: PerformanceMetrics) -> List[ModelUpdate]:
        """Update models based on performance."""
        updates = []

        # Check if retraining is needed
        if performance.accuracy < self.accuracy_threshold:
            # Perform incremental learning
            incremental_updates = await self._perform_incremental_learning()
            updates.extend(incremental_updates)

        # Check for concept drift
        if self._detect_concept_drift():
            # Adapt models to new patterns
            drift_updates = await self._adapt_to_concept_drift()
            updates.extend(drift_updates)

        self.metrics["model_updates"] += len(updates)
        return updates

    async def _perform_incremental_learning(self) -> List[ModelUpdate]:
        """Perform incremental learning on recent data."""
        updates = []

        # Get recent high-importance experiences
        recent_experiences = self.experience_buffer.get_by_importance(self.batch_size, 0.7)

        if len(recent_experiences) < 5:
            return updates

        # Update anomaly detection model
        anomaly_experiences = [
            exp for exp in recent_experiences
            if exp.experience_type == ExperienceType.ANOMALY_DETECTION
        ]

        if anomaly_experiences:
            update = ModelUpdate(
                model_name="anomaly_detection",
                update_type="incremental",
                timestamp=datetime.now(),
                performance_before={"accuracy": self.metrics.get("average_performance", 0.5)},
                metadata={
                    "experiences_used": len(anomaly_experiences),
                    "update_method": "incremental_learning"
                }
            )
            updates.append(update)

        # Update pattern recognition model
        pattern_experiences = [
            exp for exp in recent_experiences
            if exp.experience_type == ExperienceType.PATTERN_DISCOVERY
        ]

        if pattern_experiences:
            update = ModelUpdate(
                model_name="pattern_recognition",
                update_type="incremental",
                timestamp=datetime.now(),
                performance_before={"accuracy": self.metrics.get("average_performance", 0.5)},
                metadata={
                    "experiences_used": len(pattern_experiences),
                    "update_method": "incremental_learning"
                }
            )
            updates.append(update)

        return updates

    def _detect_concept_drift(self) -> bool:
        """Detect concept drift in the data."""
        recent_performance = []
        historical_performance = []

        # Get recent experiences
        recent_exp = self.experience_buffer.get_recent(100)
        historical_exp = self.experience_buffer.get_historical(100, 100)

        # Calculate performance for each period
        for exp in recent_exp:
            if exp.feedback_score is not None:
                recent_performance.append(exp.feedback_score)

        for exp in historical_exp:
            if exp.feedback_score is not None:
                historical_performance.append(exp.feedback_score)

        if len(recent_performance) < 10 or len(historical_performance) < 10:
            return False

        # Statistical test for drift (simple mean comparison)
        recent_mean = np.mean(recent_performance)
        historical_mean = np.mean(historical_performance)

        # Significant change in performance indicates drift
        drift_threshold = 0.15
        return abs(recent_mean - historical_mean) > drift_threshold

    async def _adapt_to_concept_drift(self) -> List[ModelUpdate]:
        """Adapt models to concept drift."""
        updates = []

        # Create adaptation update
        update = ModelUpdate(
            model_name="adaptive_models",
            update_type="concept_drift_adaptation",
            timestamp=datetime.now(),
            performance_before={"accuracy": self.metrics.get("average_performance", 0.5)},
            metadata={
                "adaptation_method": "drift_detection",
                "drift_detected": True
            }
        )
        updates.append(update)

        return updates

    async def _adjust_parameters(self, performance: PerformanceMetrics) -> List[ParameterAdjustment]:
        """Adjust system parameters based on performance."""
        adjustments = []

        # Get current system state
        current_state = {
            "accuracy": performance.accuracy,
            "processing_time": performance.processing_time,
            "error_rate": performance.error_rate,
            "throughput": performance.throughput
        }

        # Use optimizer to select parameter adjustment
        action = await self.optimizer.select_action(current_state)

        # Create parameter adjustment
        if "parameter" in action and "value" in action:
            adjustment = ParameterAdjustment(
                parameter_name=action["parameter"],
                old_value=current_state.get(action["parameter"], 0.5),
                new_value=action["value"],
                expected_improvement=action.get("expected_reward", 0.0),
                timestamp=datetime.now()
            )
            adjustments.append(adjustment)

            # Update optimizer with reward (use performance as reward)
            reward = performance.accuracy
            self.optimizer.update_policy(current_state, action, reward)

        self.metrics["parameter_adjustments"] += len(adjustments)
        return adjustments

    async def _discover_patterns(self) -> List[Pattern]:
        """Discover new patterns in experience data."""
        new_patterns = []

        # Get all experiences for pattern mining
        all_experiences = self.experience_buffer.get_all()

        if len(all_experiences) < 20:
            return new_patterns

        # Cluster experiences to find patterns
        try:
            # Prepare feature vectors for clustering
            features = []
            experience_map = []

            for exp in all_experiences:
                if exp.feedback_score is not None:
                    # Create feature vector [feedback_score, hour_of_day, experience_type_encoded]
                    hour = exp.timestamp.hour
                    exp_type_encoded = list(ExperienceType).index(exp.experience_type)

                    features.append([
                        exp.feedback_score,
                        hour / 24.0,
                        exp_type_encoded / len(ExperienceType)
                    ])
                    experience_map.append(exp)

            if len(features) < 10:
                return new_patterns

            # Perform clustering
            features_array = np.array(features)
            clustering = DBSCAN(eps=0.2, min_samples=3).fit(features_array)

            # Analyze clusters
            unique_labels = set(clustering.labels_)
            for label in unique_labels:
                if label == -1:  # Noise
                    continue

                cluster_indices = np.where(clustering.labels_ == label)[0]
                cluster_experiences = [experience_map[i] for i in cluster_indices]

                if len(cluster_experiences) >= 3:
                    # Calculate cluster statistics
                    feedback_scores = [exp.feedback_score for exp in cluster_experiences]
                    avg_feedback = np.mean(feedback_scores)

                    # Create pattern if interesting
                    if avg_feedback > 0.7 or avg_feedback < 0.3:  # Very good or very bad
                        pattern = Pattern(
                            pattern_type=PatternType.CLUSTER,
                            sensor_ids=[exp.experience_id for exp in cluster_experiences[:5]],
                            confidence=abs(avg_feedback - 0.5) * 2,  # Distance from neutral
                            start_time=min(exp.timestamp for exp in cluster_experiences).timestamp(),
                            end_time=max(exp.timestamp for exp in cluster_experiences).timestamp(),
                            metadata={
                                "cluster_label": int(label),
                                "cluster_size": len(cluster_experiences),
                                "average_feedback": avg_feedback,
                                "discovery_method": "experience_clustering"
                            }
                        )
                        new_patterns.append(pattern)

        except Exception as e:
            print(f"Error in pattern discovery: {e}")

        return new_patterns

    async def _run_scenario_learning(self):
        """Run scenario-based learning on digital twins."""
        if not self.scenario_engine or not self.twin_manager:
            return

        try:
            # Generate scenarios
            scenarios = await self.scenario_engine.generate_learning_scenarios()

            # Get available house twins
            house_ids = list(self.twin_manager.houses.keys())
            if not house_ids:
                return

            # Run scenarios on twins
            for scenario in scenarios[:3]:  # Limit to 3 scenarios per session
                house_id = np.random.choice(house_ids)

                # Run scenario
                result = await self.scenario_engine.run_scenario(scenario, house_id)

                if result.get("success"):
                    # Create learning experience from scenario
                    experience = Experience(
                        experience_id=f"scenario_{uuid.uuid4().hex[:8]}",
                        experience_type=ExperienceType.PATTERN_DISCOVERY,
                        timestamp=datetime.now(),
                        input_data=scenario,
                        actual_output=result,
                        feedback_score=1.0 if result["success"] else 0.0,
                        context={
                            "scenario_type": scenario["name"],
                            "house_id": house_id
                        }
                    )
                    self.experience_buffer.add(experience)
                    self.metrics["scenarios_run"] += 1

        except Exception as e:
            print(f"Error in scenario learning: {e}")

    def _update_average_performance(self, performance: PerformanceMetrics):
        """Update running average performance."""
        current_avg = self.metrics["average_performance"]
        sessions = self.metrics["learning_sessions"]

        # Weighted average with more weight on recent performance
        new_avg = (current_avg * (sessions - 1) + performance.accuracy) / sessions
        self.metrics["average_performance"] = new_avg

    def get_metrics(self) -> Dict[str, Any]:
        """Get learn module metrics."""
        return {
            **self.metrics,
            "buffer_size": self.experience_buffer.size(),
            "buffer_utilization": self.experience_buffer.size() / self.experience_buffer.max_size,
            "recent_performance": self.metrics["average_performance"],
            "learning_rate": self.optimizer.learning_rate,
            "exploration_rate": self.optimizer.epsilon
        }

    async def get_learning_insights(self) -> Dict[str, Any]:
        """Get insights from learning process."""
        # Analyze experience types
        all_experiences = self.experience_buffer.get_all()
        type_distribution = {}

        for exp_type in ExperienceType:
            count = sum(1 for exp in all_experiences if exp.experience_type == exp_type)
            type_distribution[exp_type.value] = count

        # Analyze performance trends
        recent_experiences = self.experience_buffer.get_recent(100)
        recent_feedback = [exp.feedback_score for exp in recent_experiences if exp.feedback_score is not None]

        performance_trend = "stable"
        if len(recent_feedback) >= 10:
            early_feedback = np.mean(recent_feedback[:10])
            late_feedback = np.mean(recent_feedback[-10:])

            if late_feedback > early_feedback + 0.1:
                performance_trend = "improving"
            elif late_feedback < early_feedback - 0.1:
                performance_trend = "declining"

        return {
            "total_experiences": len(all_experiences),
            "experience_type_distribution": type_distribution,
            "performance_trend": performance_trend,
            "recent_average_feedback": np.mean(recent_feedback) if recent_feedback else 0.5,
            "concept_drift_detected": self._detect_concept_drift(),
            "scenarios_completed": self.metrics["scenarios_run"],
            "learning_effectiveness": self.metrics["average_performance"]
        }
