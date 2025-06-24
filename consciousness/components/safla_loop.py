"""SAFLA Loop - Real-time processing pipeline orchestrating Sense, Analyze, Feedback, Learn."""

import asyncio
import time
import traceback
import uuid
from collections import deque
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ..database import get_async_session
from ..digital_twin.core import DigitalTwinManager
from .analyze_module import AnalysisResult, AnalyzeModule
from .feedback_module import ExecutionResult, FeedbackModule
from .learn_module import LearningResult, LearnModule

# from ..models.events import SAFLACycle as SAFLACycleModel  # Not needed for now
from .sense_module import NormalizedData, SenseModule


class SAFLAState(Enum):
    """SAFLA system states."""

    INACTIVE = "inactive"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    SHUTDOWN = "shutdown"
    SAFE_MODE = "safe_mode"


class CyclePhase(Enum):
    """Phases of SAFLA cycle."""

    SENSE = "sense"
    ANALYZE = "analyze"
    FEEDBACK = "feedback"
    LEARN = "learn"
    COMPLETE = "complete"


class SAFLACycle:
    """Single SAFLA processing cycle."""

    def __init__(self, cycle_id: str):
        self.cycle_id = cycle_id
        self.start_time = datetime.now()
        self.current_phase = CyclePhase.SENSE
        self.phases_completed: List[CyclePhase] = []
        self.phase_timings: Dict[CyclePhase, float] = {}
        self.phase_errors: Dict[CyclePhase, str] = {}

        # Data flow
        self.sensor_data: List[NormalizedData] = []
        self.analysis_result: Optional[AnalysisResult] = None
        self.execution_results: List[ExecutionResult] = []
        self.learning_result: Optional[LearningResult] = None

        # Metrics
        self.total_duration: Optional[float] = None
        self.success = False
        self.error_message: Optional[str] = None

    def start_phase(self, phase: CyclePhase):
        """Start a new phase."""
        self.current_phase = phase
        self.phase_start_time = time.time()

    def complete_phase(
        self, phase: CyclePhase, success: bool = True, error: Optional[str] = None
    ):
        """Complete current phase."""
        if phase == self.current_phase:
            duration = time.time() - self.phase_start_time
            self.phase_timings[phase] = duration

            if success:
                self.phases_completed.append(phase)
            else:
                self.phase_errors[phase] = error or "Unknown error"

    def complete_cycle(self, success: bool = True, error: Optional[str] = None):
        """Complete the entire cycle."""
        self.total_duration = (datetime.now() - self.start_time).total_seconds()
        self.success = success
        self.error_message = error
        self.current_phase = CyclePhase.COMPLETE


class PerformanceMonitor:
    """Monitors SAFLA system performance."""

    def __init__(self, max_history: int = 1000):
        self.cycle_history: deque = deque(maxlen=max_history)
        self.performance_metrics: Dict[str, float] = {}
        self.alert_thresholds = {
            "cycle_time": 1.0,  # 1 second
            "error_rate": 0.1,  # 10%
            "timeout_rate": 0.05,  # 5%
            "safety_violations": 0.01,  # 1%
        }

    def record_cycle(self, cycle: SAFLACycle):
        """Record completed cycle for monitoring."""
        self.cycle_history.append(cycle)
        self._update_metrics()

    def _update_metrics(self):
        """Update performance metrics."""
        if not self.cycle_history:
            return

        recent_cycles = list(self.cycle_history)[-100:]  # Last 100 cycles

        # Calculate metrics
        total_cycles = len(recent_cycles)
        successful_cycles = sum(1 for c in recent_cycles if c.success)

        self.performance_metrics = {
            "success_rate": successful_cycles / total_cycles,
            "error_rate": (total_cycles - successful_cycles) / total_cycles,
            "average_cycle_time": sum(c.total_duration or 0 for c in recent_cycles)
            / total_cycles,
            "throughput": len(recent_cycles)
            / max(1, (datetime.now() - recent_cycles[0].start_time).total_seconds()),
            "phase_performance": self._calculate_phase_performance(recent_cycles),
        }

    def _calculate_phase_performance(
        self, cycles: List[SAFLACycle]
    ) -> Dict[str, float]:
        """Calculate per-phase performance metrics."""
        phase_performance = {}

        for phase in CyclePhase:
            if phase == CyclePhase.COMPLETE:
                continue

            phase_times = []
            phase_successes = 0

            for cycle in cycles:
                if phase in cycle.phase_timings:
                    phase_times.append(cycle.phase_timings[phase])
                    if phase in cycle.phases_completed:
                        phase_successes += 1

            if phase_times:
                phase_performance[phase.value] = {
                    "average_time": sum(phase_times) / len(phase_times),
                    "success_rate": phase_successes / len(phase_times),
                    "max_time": max(phase_times),
                    "min_time": min(phase_times),
                }

        return phase_performance

    def check_alerts(self) -> List[Dict[str, Any]]:
        """Check for performance alerts."""
        alerts = []

        if "average_cycle_time" in self.performance_metrics:
            if (
                self.performance_metrics["average_cycle_time"]
                > self.alert_thresholds["cycle_time"]
            ):
                alerts.append(
                    {
                        "type": "performance",
                        "severity": "warning",
                        "message": f"Average cycle time {self.performance_metrics['average_cycle_time']:.3f}s exceeds threshold {self.alert_thresholds['cycle_time']}s",
                        "metric": "cycle_time",
                        "value": self.performance_metrics["average_cycle_time"],
                    }
                )

        if "error_rate" in self.performance_metrics:
            if (
                self.performance_metrics["error_rate"]
                > self.alert_thresholds["error_rate"]
            ):
                alerts.append(
                    {
                        "type": "reliability",
                        "severity": "warning",
                        "message": f"Error rate {self.performance_metrics['error_rate']:.1%} exceeds threshold {self.alert_thresholds['error_rate']:.1%}",
                        "metric": "error_rate",
                        "value": self.performance_metrics["error_rate"],
                    }
                )

        return alerts


class FailureDetector:
    """Detects and handles failures in SAFLA components."""

    def __init__(self):
        self.failure_history: deque = deque(maxlen=1000)
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}

    def record_failure(self, component: str, error: str, context: Dict[str, Any]):
        """Record a component failure."""
        failure_record = {
            "component": component,
            "error": error,
            "context": context,
            "timestamp": datetime.now(),
            "id": uuid.uuid4().hex[:8],
        }
        self.failure_history.append(failure_record)

        # Update circuit breaker
        self._update_circuit_breaker(component)

    def _update_circuit_breaker(self, component: str):
        """Update circuit breaker state for component."""
        if component not in self.circuit_breakers:
            self.circuit_breakers[component] = {
                "state": "closed",
                "failure_count": 0,
                "last_failure": None,
                "next_attempt": None,
            }

        breaker = self.circuit_breakers[component]
        breaker["failure_count"] += 1
        breaker["last_failure"] = datetime.now()

        # Open circuit breaker if too many failures
        if breaker["failure_count"] >= 5:
            breaker["state"] = "open"
            breaker["next_attempt"] = datetime.now() + timedelta(minutes=5)

    def is_component_available(self, component: str) -> bool:
        """Check if component is available (circuit breaker closed)."""
        if component not in self.circuit_breakers:
            return True

        breaker = self.circuit_breakers[component]

        if breaker["state"] == "closed":
            return True
        elif breaker["state"] == "open":
            # Check if cooldown period has passed
            if datetime.now() > breaker.get("next_attempt", datetime.now()):
                breaker["state"] = "half_open"
                return True
            return False
        elif breaker["state"] == "half_open":
            # Allow one attempt
            return True

        return False

    def record_success(self, component: str):
        """Record successful component operation."""
        if component in self.circuit_breakers:
            breaker = self.circuit_breakers[component]
            if breaker["state"] == "half_open":
                # Reset circuit breaker
                breaker["state"] = "closed"
                breaker["failure_count"] = 0


class SafetyMonitor:
    """Monitors safety constraints and triggers safe mode when needed."""

    def __init__(self):
        self.safety_violations: deque = deque(maxlen=1000)
        self.safe_mode_active = False
        self.safety_thresholds = {
            "max_violations_per_hour": 5,
            "critical_failure_threshold": 1,
            "system_response_timeout": 30.0,  # seconds
        }

    def check_safety_constraints(self, cycle: SAFLACycle) -> Tuple[bool, List[str]]:
        """Check safety constraints for cycle."""
        violations = []

        # Check cycle timing constraints
        if (
            cycle.total_duration
            and cycle.total_duration > self.safety_thresholds["system_response_timeout"]
        ):
            violations.append(
                f"Cycle duration {cycle.total_duration:.1f}s exceeds safety timeout"
            )

        # Check for critical phase failures
        for phase, error in cycle.phase_errors.items():
            if "critical" in error.lower() or "safety" in error.lower():
                violations.append(f"Critical safety error in {phase.value}: {error}")

        # Check violation rate
        recent_violations = [
            v
            for v in self.safety_violations
            if v["timestamp"] > datetime.now() - timedelta(hours=1)
        ]

        if len(recent_violations) >= self.safety_thresholds["max_violations_per_hour"]:
            violations.append("Safety violation rate exceeds threshold")

        # Record violations
        for violation in violations:
            self.safety_violations.append(
                {
                    "violation": violation,
                    "timestamp": datetime.now(),
                    "cycle_id": cycle.cycle_id,
                }
            )

        return len(violations) == 0, violations

    def should_enter_safe_mode(self, violations: List[str]) -> bool:
        """Determine if system should enter safe mode."""
        critical_violations = [v for v in violations if "critical" in v.lower()]
        return (
            len(critical_violations)
            >= self.safety_thresholds["critical_failure_threshold"]
        )


class SAFLALoop:
    """Main SAFLA Loop orchestrator."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.state = SAFLAState.INACTIVE
        self.loop_interval = config.get("loop_interval", 0.1)  # 100ms default

        # Component timeouts
        self.timeouts = {
            "sense": config.get("sense_timeout", 0.05),  # 50ms
            "analyze": config.get("analyze_timeout", 0.2),  # 200ms
            "feedback": config.get("feedback_timeout", 0.15),  # 150ms
            "learn": config.get("learn_timeout", 0.5),  # 500ms (async)
        }

        # Components
        self.sense_module: Optional[SenseModule] = None
        self.analyze_module: Optional[AnalyzeModule] = None
        self.feedback_module: Optional[FeedbackModule] = None
        self.learn_module: Optional[LearnModule] = None
        self.twin_manager: Optional[DigitalTwinManager] = None

        # Monitoring and safety
        self.performance_monitor = PerformanceMonitor()
        self.failure_detector = FailureDetector()
        self.safety_monitor = SafetyMonitor()

        # Runtime state
        self.current_cycle: Optional[SAFLACycle] = None
        self.cycle_count = 0
        self.last_learn_time = datetime.now()
        self.learn_interval = config.get("learn_interval", 60)  # 1 minute

        # Metrics
        self.metrics = {
            "cycles_completed": 0,
            "cycles_failed": 0,
            "total_uptime": 0.0,
            "safe_mode_activations": 0,
            "component_failures": 0,
            "safety_violations": 0,
        }

    async def initialize(self):
        """Initialize all SAFLA components."""
        self.state = SAFLAState.INITIALIZING

        try:
            # Initialize digital twin manager
            self.twin_manager = DigitalTwinManager()
            await self.twin_manager.initialize()

            # Initialize SAFLA components
            sense_config = self.config.get("sense", {})
            self.sense_module = SenseModule(sense_config)
            await self.sense_module.initialize()

            analyze_config = self.config.get("analyze", {})
            self.analyze_module = AnalyzeModule(analyze_config)
            await self.analyze_module.initialize()

            feedback_config = self.config.get("feedback", {})
            self.feedback_module = FeedbackModule(feedback_config)
            await self.feedback_module.initialize()

            learn_config = self.config.get("learn", {})
            self.learn_module = LearnModule(learn_config)
            await self.learn_module.initialize()

            self.state = SAFLAState.RUNNING
            print("= SAFLA Loop initialized successfully")

        except Exception as e:
            self.state = SAFLAState.ERROR
            error_msg = f"Failed to initialize SAFLA Loop: {e}"
            print(f"L {error_msg}")
            raise RuntimeError(error_msg)

    async def start(self):
        """Start the SAFLA processing loop."""
        if self.state != SAFLAState.RUNNING:
            await self.initialize()

        print("🚀 Starting SAFLA processing loop...")

        start_time = datetime.now()

        while self.state == SAFLAState.RUNNING:
            try:
                # Run single SAFLA cycle
                await self._run_cycle()

                # Update uptime
                self.metrics["total_uptime"] = (
                    datetime.now() - start_time
                ).total_seconds()

                # Check for alerts
                alerts = self.performance_monitor.check_alerts()
                if alerts:
                    await self._handle_alerts(alerts)

                # Wait for next cycle
                await asyncio.sleep(self.loop_interval)

            except Exception as e:
                print(f"L Error in SAFLA cycle: {e}")
                await self._handle_cycle_error(e)

                # Brief pause before retry
                await asyncio.sleep(min(1.0, self.loop_interval * 10))

        print(f"� SAFLA Loop stopped - Final state: {self.state.value}")

    async def stop(self):
        """Stop the SAFLA loop gracefully."""
        print("� Stopping SAFLA Loop...")
        self.state = SAFLAState.SHUTDOWN

        # Wait for current cycle to complete
        if (
            self.current_cycle
            and self.current_cycle.current_phase != CyclePhase.COMPLETE
        ):
            await asyncio.sleep(0.1)

    async def enter_safe_mode(self):
        """Enter safe mode - minimal operations only."""
        print("=� Entering SAFLA Safe Mode")
        self.state = SAFLAState.SAFE_MODE
        self.safety_monitor.safe_mode_active = True
        self.metrics["safe_mode_activations"] += 1

        # Stop non-critical operations
        # In safe mode, only basic sensing and critical safety actions are allowed

    async def exit_safe_mode(self):
        """Exit safe mode and resume normal operations."""
        if self.state == SAFLAState.SAFE_MODE:
            print(" Exiting SAFLA Safe Mode")
            self.state = SAFLAState.RUNNING
            self.safety_monitor.safe_mode_active = False

    async def _run_cycle(self):
        """Run a single SAFLA cycle."""
        cycle_id = f"safla_{self.cycle_count:06d}_{uuid.uuid4().hex[:8]}"
        cycle = SAFLACycle(cycle_id)
        self.current_cycle = cycle
        self.cycle_count += 1

        try:
            # Phase 1: Sense
            cycle.start_phase(CyclePhase.SENSE)
            sensor_data = await self._run_sense_phase(cycle)
            cycle.complete_phase(CyclePhase.SENSE, success=len(sensor_data) > 0)

            # Phase 2: Analyze
            cycle.start_phase(CyclePhase.ANALYZE)
            analysis_result = await self._run_analyze_phase(cycle, sensor_data)
            cycle.complete_phase(
                CyclePhase.ANALYZE, success=analysis_result is not None
            )

            # Phase 3: Feedback
            cycle.start_phase(CyclePhase.FEEDBACK)
            execution_results = await self._run_feedback_phase(cycle, analysis_result)
            cycle.complete_phase(
                CyclePhase.FEEDBACK, success=True
            )  # Always succeeds even if no actions

            # Phase 4: Learn (async, less frequent)
            should_learn = (
                datetime.now() - self.last_learn_time
            ).total_seconds() > self.learn_interval
            if should_learn:
                cycle.start_phase(CyclePhase.LEARN)
                learning_result = await self._run_learn_phase(
                    cycle, sensor_data, analysis_result, execution_results
                )
                cycle.complete_phase(
                    CyclePhase.LEARN, success=learning_result is not None
                )
                self.last_learn_time = datetime.now()

            # Complete cycle
            cycle.complete_cycle(success=True)
            self.metrics["cycles_completed"] += 1

            # Safety check
            is_safe, violations = self.safety_monitor.check_safety_constraints(cycle)
            if not is_safe:
                self.metrics["safety_violations"] += 1
                if self.safety_monitor.should_enter_safe_mode(violations):
                    await self.enter_safe_mode()

        except Exception as e:
            error_msg = f"Cycle {cycle_id} failed: {e}"
            cycle.complete_cycle(success=False, error=error_msg)
            self.metrics["cycles_failed"] += 1

            # Record failure
            self.failure_detector.record_failure(
                "safla_cycle",
                error_msg,
                {
                    "cycle_id": cycle_id,
                    "phase": cycle.current_phase.value,
                    "traceback": traceback.format_exc(),
                },
            )

        finally:
            # Record cycle for monitoring
            self.performance_monitor.record_cycle(cycle)
            self.current_cycle = None

    async def _run_sense_phase(self, cycle: SAFLACycle) -> List[NormalizedData]:
        """Run sense phase with timeout protection."""
        if not self.failure_detector.is_component_available("sense_module"):
            print("� Sense module circuit breaker open, skipping")
            return []

        try:
            sensor_data = await asyncio.wait_for(
                self.sense_module.collect_data(), timeout=self.timeouts["sense"]
            )

            cycle.sensor_data = sensor_data
            self.failure_detector.record_success("sense_module")
            return sensor_data

        except asyncio.TimeoutError:
            error_msg = f"Sense phase timeout ({self.timeouts['sense']}s)"
            self.failure_detector.record_failure(
                "sense_module", error_msg, {"phase": "sense"}
            )
            return []
        except Exception as e:
            error_msg = f"Sense phase error: {e}"
            self.failure_detector.record_failure(
                "sense_module", error_msg, {"phase": "sense"}
            )
            return []

    async def _run_analyze_phase(
        self, cycle: SAFLACycle, sensor_data: List[NormalizedData]
    ) -> Optional[AnalysisResult]:
        """Run analyze phase with timeout protection."""
        if not sensor_data:
            return None

        if not self.failure_detector.is_component_available("analyze_module"):
            print("� Analyze module circuit breaker open, skipping")
            return None

        try:
            analysis_result = await asyncio.wait_for(
                self.analyze_module.analyze(sensor_data),
                timeout=self.timeouts["analyze"],
            )

            cycle.analysis_result = analysis_result
            self.failure_detector.record_success("analyze_module")
            return analysis_result

        except asyncio.TimeoutError:
            error_msg = f"Analyze phase timeout ({self.timeouts['analyze']}s)"
            self.failure_detector.record_failure(
                "analyze_module", error_msg, {"phase": "analyze"}
            )
            return None
        except Exception as e:
            error_msg = f"Analyze phase error: {e}"
            self.failure_detector.record_failure(
                "analyze_module", error_msg, {"phase": "analyze"}
            )
            return None

    async def _run_feedback_phase(
        self, cycle: SAFLACycle, analysis_result: Optional[AnalysisResult]
    ) -> List[ExecutionResult]:
        """Run feedback phase with timeout protection."""
        if not analysis_result:
            return []

        if not self.failure_detector.is_component_available("feedback_module"):
            print("� Feedback module circuit breaker open, skipping")
            return []

        try:
            execution_results = await asyncio.wait_for(
                self.feedback_module.process_analysis(analysis_result),
                timeout=self.timeouts["feedback"],
            )

            cycle.execution_results = execution_results
            self.failure_detector.record_success("feedback_module")
            return execution_results

        except asyncio.TimeoutError:
            error_msg = f"Feedback phase timeout ({self.timeouts['feedback']}s)"
            self.failure_detector.record_failure(
                "feedback_module", error_msg, {"phase": "feedback"}
            )
            return []
        except Exception as e:
            error_msg = f"Feedback phase error: {e}"
            self.failure_detector.record_failure(
                "feedback_module", error_msg, {"phase": "feedback"}
            )
            return []

    async def _run_learn_phase(
        self,
        cycle: SAFLACycle,
        sensor_data: List[NormalizedData],
        analysis_result: Optional[AnalysisResult],
        execution_results: List[ExecutionResult],
    ) -> Optional[LearningResult]:
        """Run learn phase with timeout protection."""
        if not self.failure_detector.is_component_available("learn_module"):
            print("� Learn module circuit breaker open, skipping")
            return None

        try:
            # Learning can be slower, so run it async without blocking the main cycle
            learning_task = asyncio.create_task(
                self.learn_module.learn(sensor_data, analysis_result, execution_results)
            )

            learning_result = await asyncio.wait_for(
                learning_task, timeout=self.timeouts["learn"]
            )

            cycle.learning_result = learning_result
            self.failure_detector.record_success("learn_module")
            return learning_result

        except asyncio.TimeoutError:
            error_msg = f"Learn phase timeout ({self.timeouts['learn']}s)"
            self.failure_detector.record_failure(
                "learn_module", error_msg, {"phase": "learn"}
            )
            return None
        except Exception as e:
            error_msg = f"Learn phase error: {e}"
            self.failure_detector.record_failure(
                "learn_module", error_msg, {"phase": "learn"}
            )
            return None

    async def _handle_alerts(self, alerts: List[Dict[str, Any]]):
        """Handle performance alerts."""
        for alert in alerts:
            severity = alert.get("severity", "info")
            message = alert.get("message", "Unknown alert")

            print(f"=� SAFLA Alert [{severity.upper()}]: {message}")

            # Take action based on alert type
            if alert.get("type") == "performance" and severity == "warning":
                # Increase timeouts slightly
                for phase in self.timeouts:
                    self.timeouts[phase] *= 1.1

            elif alert.get("type") == "reliability" and severity == "warning":
                # Consider entering safe mode if error rate is very high
                if alert.get("value", 0) > 0.5:  # 50% error rate
                    await self.enter_safe_mode()

    async def _handle_cycle_error(self, error: Exception):
        """Handle cycle-level errors."""
        self.metrics["component_failures"] += 1

        # Log error details
        error_context = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "current_cycle": self.current_cycle.cycle_id
            if self.current_cycle
            else None,
            "system_state": self.state.value,
            "traceback": traceback.format_exc(),
        }

        self.failure_detector.record_failure("safla_loop", str(error), error_context)

        # Check if we should enter safe mode
        recent_failures = [
            f
            for f in self.failure_detector.failure_history
            if f["timestamp"] > datetime.now() - timedelta(minutes=5)
        ]

        if len(recent_failures) >= 10:  # 10 failures in 5 minutes
            await self.enter_safe_mode()

    async def get_status(self) -> Dict[str, Any]:
        """Get comprehensive SAFLA system status."""
        component_status = {}

        # Check component availability
        for component in [
            "sense_module",
            "analyze_module",
            "feedback_module",
            "learn_module",
        ]:
            component_status[component] = {
                "available": self.failure_detector.is_component_available(component),
                "circuit_breaker": self.failure_detector.circuit_breakers.get(
                    component, {}
                ),
            }

        # Get component metrics
        component_metrics = {}
        if self.sense_module:
            component_metrics["sense"] = self.sense_module.get_metrics()
        if self.analyze_module:
            component_metrics["analyze"] = self.analyze_module.get_metrics()
        if self.feedback_module:
            component_metrics["feedback"] = self.feedback_module.get_metrics()
        if self.learn_module:
            component_metrics["learn"] = self.learn_module.get_metrics()

        return {
            "state": self.state.value,
            "current_cycle": self.current_cycle.cycle_id
            if self.current_cycle
            else None,
            "current_phase": self.current_cycle.current_phase.value
            if self.current_cycle
            else None,
            "cycle_count": self.cycle_count,
            "uptime_seconds": self.metrics["total_uptime"],
            "performance_metrics": self.performance_monitor.performance_metrics,
            "component_status": component_status,
            "component_metrics": component_metrics,
            "safety_status": {
                "safe_mode_active": self.safety_monitor.safe_mode_active,
                "recent_violations": len(
                    [
                        v
                        for v in self.safety_monitor.safety_violations
                        if v["timestamp"] > datetime.now() - timedelta(hours=1)
                    ]
                ),
            },
            "system_metrics": self.metrics,
            "configuration": {
                "loop_interval": self.loop_interval,
                "timeouts": self.timeouts,
                "learn_interval": self.learn_interval,
            },
        }

    async def run_single_cycle(self) -> Dict[str, Any]:
        """Run a single SAFLA cycle manually (for testing)."""
        if self.state not in [SAFLAState.RUNNING, SAFLAState.PAUSED]:
            return {"error": "SAFLA system not in running state"}

        # Temporarily set state to running
        original_state = self.state
        self.state = SAFLAState.RUNNING

        try:
            await self._run_cycle()

            if self.current_cycle:
                return {
                    "success": True,
                    "cycle_id": self.current_cycle.cycle_id,
                    "phases_completed": [
                        p.value for p in self.current_cycle.phases_completed
                    ],
                    "phase_timings": {
                        p.value: t for p, t in self.current_cycle.phase_timings.items()
                    },
                    "total_duration": self.current_cycle.total_duration,
                    "sensor_data_count": len(self.current_cycle.sensor_data),
                    "analysis_result": bool(self.current_cycle.analysis_result),
                    "execution_results_count": len(
                        self.current_cycle.execution_results
                    ),
                    "learning_result": bool(self.current_cycle.learning_result),
                }
            else:
                return {"error": "No cycle data available"}

        finally:
            self.state = original_state

    async def optimize_performance(self) -> Dict[str, Any]:
        """Optimize SAFLA performance based on recent metrics."""
        optimization_results = []

        # Analyze recent performance
        metrics = self.performance_monitor.performance_metrics

        # Adjust timeouts based on actual performance
        if "phase_performance" in metrics:
            for phase_name, phase_metrics in metrics["phase_performance"].items():
                avg_time = phase_metrics.get("average_time", 0)
                current_timeout = self.timeouts.get(phase_name, 0.1)

                # If average time is much less than timeout, reduce timeout
                if avg_time < current_timeout * 0.5:
                    new_timeout = max(avg_time * 2, 0.01)  # At least 10ms
                    optimization_results.append(
                        {
                            "type": "timeout_optimization",
                            "phase": phase_name,
                            "old_timeout": current_timeout,
                            "new_timeout": new_timeout,
                            "reason": "Performance headroom available",
                        }
                    )
                    self.timeouts[phase_name] = new_timeout

                # If success rate is low and time is near timeout, increase timeout
                elif (
                    phase_metrics.get("success_rate", 1.0) < 0.9
                    and avg_time > current_timeout * 0.8
                ):
                    new_timeout = min(current_timeout * 1.5, 2.0)  # Max 2s
                    optimization_results.append(
                        {
                            "type": "timeout_optimization",
                            "phase": phase_name,
                            "old_timeout": current_timeout,
                            "new_timeout": new_timeout,
                            "reason": "Low success rate, increase timeout",
                        }
                    )
                    self.timeouts[phase_name] = new_timeout

        # Adjust loop interval based on system load
        if "average_cycle_time" in metrics:
            avg_cycle_time = metrics["average_cycle_time"]

            if avg_cycle_time < self.loop_interval * 0.5:
                # System has headroom, can increase frequency
                new_interval = max(avg_cycle_time * 2, 0.05)  # At least 50ms
                optimization_results.append(
                    {
                        "type": "interval_optimization",
                        "old_interval": self.loop_interval,
                        "new_interval": new_interval,
                        "reason": "System has processing headroom",
                    }
                )
                self.loop_interval = new_interval

            elif avg_cycle_time > self.loop_interval * 0.9:
                # System under load, reduce frequency
                new_interval = min(avg_cycle_time * 1.2, 1.0)  # Max 1s
                optimization_results.append(
                    {
                        "type": "interval_optimization",
                        "old_interval": self.loop_interval,
                        "new_interval": new_interval,
                        "reason": "System under load",
                    }
                )
                self.loop_interval = new_interval

        return {
            "optimizations_applied": len(optimization_results),
            "optimizations": optimization_results,
            "new_configuration": {
                "loop_interval": self.loop_interval,
                "timeouts": self.timeouts,
            },
        }

    def get_diagnostic_info(self) -> Dict[str, Any]:
        """Get detailed diagnostic information."""
        return {
            "system_state": self.state.value,
            "cycle_statistics": {
                "total_cycles": self.cycle_count,
                "successful_cycles": self.metrics["cycles_completed"],
                "failed_cycles": self.metrics["cycles_failed"],
                "success_rate": self.metrics["cycles_completed"]
                / max(1, self.cycle_count),
            },
            "component_health": {
                component: {
                    "available": self.failure_detector.is_component_available(
                        component
                    ),
                    "failure_count": self.failure_detector.circuit_breakers.get(
                        component, {}
                    ).get("failure_count", 0),
                    "last_failure": self.failure_detector.circuit_breakers.get(
                        component, {}
                    ).get("last_failure"),
                }
                for component in [
                    "sense_module",
                    "analyze_module",
                    "feedback_module",
                    "learn_module",
                ]
            },
            "recent_failures": [
                {
                    "component": f["component"],
                    "error": f["error"],
                    "timestamp": f["timestamp"].isoformat(),
                }
                for f in list(self.failure_detector.failure_history)[-10:]
            ],
            "safety_status": {
                "safe_mode_active": self.safety_monitor.safe_mode_active,
                "total_violations": len(self.safety_monitor.safety_violations),
                "recent_violations": [
                    {
                        "violation": v["violation"],
                        "timestamp": v["timestamp"].isoformat(),
                        "cycle_id": v["cycle_id"],
                    }
                    for v in list(self.safety_monitor.safety_violations)[-5:]
                ],
            },
            "performance_summary": self.performance_monitor.performance_metrics,
            "configuration": {
                "loop_interval": self.loop_interval,
                "timeouts": self.timeouts,
                "learn_interval": self.learn_interval,
            },
        }
