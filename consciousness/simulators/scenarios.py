"""Scenario engine for orchestrating device simulation scenarios."""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from .demo_scenarios import DemoScenarios, register_scenarios


class ScenarioStatus(Enum):
    """Status of a scenario execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScenarioEngine:
    """Engine for managing and executing device simulation scenarios."""

    def __init__(self, simulator):
        """Initialize the scenario engine.

        Args:
            simulator: The HouseSimulator instance to run scenarios on
        """
        self.simulator = simulator
        self.scenarios: Dict[str, Callable] = {}
        self.active_scenarios: Dict[str, Dict] = {}
        self.scenario_history: List[Dict] = []
        self.logger = logging.getLogger(__name__)

        # Register built-in demo scenarios
        register_scenarios(simulator)
        if hasattr(simulator, "scenarios"):
            self.scenarios.update(simulator.scenarios)

    def register_scenario(self, name: str, scenario_func: Callable) -> None:
        """Register a new scenario.

        Args:
            name: Unique name for the scenario
            scenario_func: Async function that implements the scenario
        """
        self.scenarios[name] = scenario_func
        self.logger.info(f"Registered scenario: {name}")

    def list_scenarios(self) -> List[str]:
        """Get list of available scenario names."""
        return list(self.scenarios.keys())

    async def run_scenario(self, name: str, **kwargs) -> Dict[str, Any]:
        """Run a scenario by name.

        Args:
            name: Name of the scenario to run
            **kwargs: Additional arguments to pass to the scenario

        Returns:
            Dict containing scenario execution results
        """
        if name not in self.scenarios:
            raise ValueError(
                f"Unknown scenario: {name}. Available: {list(self.scenarios.keys())}"
            )

        scenario_id = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        scenario_info = {
            "id": scenario_id,
            "name": name,
            "status": ScenarioStatus.PENDING,
            "start_time": datetime.now(),
            "end_time": None,
            "duration": None,
            "error": None,
            "results": {},
        }

        self.active_scenarios[scenario_id] = scenario_info

        try:
            self.logger.info(f"Starting scenario: {name} (ID: {scenario_id})")
            scenario_info["status"] = ScenarioStatus.RUNNING

            # Run the scenario
            scenario_func = self.scenarios[name]
            result = await scenario_func(self.simulator, **kwargs)

            # Update scenario info
            scenario_info["status"] = ScenarioStatus.COMPLETED
            scenario_info["end_time"] = datetime.now()
            scenario_info["duration"] = (
                scenario_info["end_time"] - scenario_info["start_time"]
            ).total_seconds()
            scenario_info["results"] = result or {"success": True}

            self.logger.info(
                f"Completed scenario: {name} in {scenario_info['duration']:.2f}s"
            )

        except Exception as e:
            self.logger.error(f"Scenario {name} failed: {e}")
            scenario_info["status"] = ScenarioStatus.FAILED
            scenario_info["end_time"] = datetime.now()
            scenario_info["duration"] = (
                scenario_info["end_time"] - scenario_info["start_time"]
            ).total_seconds()
            scenario_info["error"] = str(e)
            raise

        finally:
            # Move to history and clean up active
            self.scenario_history.append(scenario_info.copy())
            if scenario_id in self.active_scenarios:
                del self.active_scenarios[scenario_id]

        return scenario_info

    async def run_multiple_scenarios(
        self, scenario_names: List[str], parallel: bool = False
    ) -> List[Dict[str, Any]]:
        """Run multiple scenarios either sequentially or in parallel.

        Args:
            scenario_names: List of scenario names to run
            parallel: Whether to run scenarios in parallel

        Returns:
            List of scenario execution results
        """
        if parallel:
            # Run scenarios concurrently
            tasks = [self.run_scenario(name) for name in scenario_names]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Convert exceptions to error dictionaries
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append(
                        {
                            "name": scenario_names[i],
                            "status": ScenarioStatus.FAILED,
                            "error": str(result),
                        }
                    )
                else:
                    processed_results.append(result)

            return processed_results
        else:
            # Run scenarios sequentially
            results = []
            for name in scenario_names:
                try:
                    result = await self.run_scenario(name)
                    results.append(result)
                except Exception as e:
                    results.append(
                        {"name": name, "status": ScenarioStatus.FAILED, "error": str(e)}
                    )
            return results

    def get_scenario_status(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a running scenario.

        Args:
            scenario_id: ID of the scenario to check

        Returns:
            Scenario status information or None if not found
        """
        return self.active_scenarios.get(scenario_id)

    def get_active_scenarios(self) -> Dict[str, Dict[str, Any]]:
        """Get all currently active scenarios."""
        return self.active_scenarios.copy()

    def get_scenario_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get scenario execution history.

        Args:
            limit: Maximum number of historical records to return

        Returns:
            List of historical scenario execution records
        """
        history = sorted(
            self.scenario_history, key=lambda x: x["start_time"], reverse=True
        )
        if limit:
            history = history[:limit]
        return history

    async def cancel_scenario(self, scenario_id: str) -> bool:
        """Cancel a running scenario.

        Args:
            scenario_id: ID of the scenario to cancel

        Returns:
            True if scenario was cancelled, False if not found or already completed
        """
        if scenario_id not in self.active_scenarios:
            return False

        scenario_info = self.active_scenarios[scenario_id]
        if scenario_info["status"] != ScenarioStatus.RUNNING:
            return False

        # Mark as cancelled
        scenario_info["status"] = ScenarioStatus.CANCELLED
        scenario_info["end_time"] = datetime.now()
        scenario_info["duration"] = (
            scenario_info["end_time"] - scenario_info["start_time"]
        ).total_seconds()

        # Move to history
        self.scenario_history.append(scenario_info.copy())
        del self.active_scenarios[scenario_id]

        self.logger.info(f"Cancelled scenario: {scenario_id}")
        return True

    def get_scenario_stats(self) -> Dict[str, Any]:
        """Get statistics about scenario executions.

        Returns:
            Dictionary containing scenario execution statistics
        """
        total_runs = len(self.scenario_history)
        if total_runs == 0:
            return {
                "total_runs": 0,
                "success_rate": 0,
                "average_duration": 0,
                "scenario_counts": {},
                "status_counts": {},
            }

        successful_runs = len(
            [
                s
                for s in self.scenario_history
                if s["status"] == ScenarioStatus.COMPLETED
            ]
        )
        durations = [
            s["duration"] for s in self.scenario_history if s["duration"] is not None
        ]

        scenario_counts = {}
        status_counts = {}

        for scenario in self.scenario_history:
            name = scenario["name"]
            status = (
                scenario["status"].value
                if isinstance(scenario["status"], ScenarioStatus)
                else scenario["status"]
            )

            scenario_counts[name] = scenario_counts.get(name, 0) + 1
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_runs": total_runs,
            "success_rate": successful_runs / total_runs if total_runs > 0 else 0,
            "average_duration": sum(durations) / len(durations) if durations else 0,
            "scenario_counts": scenario_counts,
            "status_counts": status_counts,
        }

    async def cleanup(self) -> None:
        """Clean up the scenario engine."""
        # Cancel any active scenarios
        active_ids = list(self.active_scenarios.keys())
        for scenario_id in active_ids:
            await self.cancel_scenario(scenario_id)

        self.logger.info("Scenario engine cleaned up")
