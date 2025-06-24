"""Integration test for complete SAFLA system."""

import asyncio
import os
import sys
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from consciousness.components.safla_loop import SAFLALoop, SAFLAState
from consciousness.components.sense_module import (
    DataQuality,
    NormalizedData,
    SensorType,
)
from consciousness.simulators.manager import SimulatorConfig, SimulatorManager


async def test_safla_integration():
    """Test complete SAFLA system integration."""
    print("🧪 Starting SAFLA Integration Test")
    print("=" * 50)

    # Configuration for SAFLA system
    safla_config = {
        "loop_interval": 0.2,  # 200ms for testing
        "sense": {"buffer_size": 1000, "use_digital_twins": True},
        "analyze": {"cache_size": 100, "models": {}},
        "feedback": {"queue_size": 50, "safety": {"riskThreshold": 0.1}},
        "learn": {
            "buffer_size": 5000,
            "batch_size": 16,
            "accuracy_threshold": 0.7,
            "update_interval": 30,  # 30 seconds for testing
        },
        "sense_timeout": 0.1,
        "analyze_timeout": 0.3,
        "feedback_timeout": 0.2,
        "learn_timeout": 1.0,
    }

    # Initialize simulator for data generation
    print("🏠 Initializing device simulator...")
    simulator_config = SimulatorConfig(
        auto_start=True, enable_random_events=True, environmental_updates=True
    )
    simulator = SimulatorManager(simulator_config)

    # Create test environment
    await simulator.start()
    await simulator.create_test_environment("default")

    devices = simulator.list_devices()
    print(f"✅ Created {len(devices)} simulated devices")

    # Initialize SAFLA system
    print("\n🔄 Initializing SAFLA Loop...")
    safla_loop = SAFLALoop(safla_config)

    try:
        await safla_loop.initialize()
        print("✅ SAFLA Loop initialized successfully")

        # Get initial status
        status = await safla_loop.get_status()
        print(f"📊 Initial state: {status['state']}")
        print(f"🔧 Component status: {len(status['component_status'])} components ready")

        # Test manual cycle execution
        print("\n🔄 Testing manual cycle execution...")
        for i in range(3):
            print(f"\n--- Cycle {i+1} ---")

            # Generate some sensor data by updating devices
            if i == 0:
                # Test temperature change
                thermostats = simulator.get_devices_by_type("thermostat")
                if thermostats:
                    await simulator.send_command(
                        thermostats[0].device_id, "set_temperature", {"temperature": 25}
                    )
                    print("🌡️ Set thermostat to 25°C")

            elif i == 1:
                # Test lighting change
                lights = simulator.get_devices_by_type("light")
                if lights:
                    await simulator.send_command(
                        lights[0].device_id, "turn_on", {"brightness": 80}
                    )
                    print("💡 Turned on light at 80% brightness")

            elif i == 2:
                # Test security device
                locks = simulator.get_devices_by_type("lock")
                if locks:
                    await simulator.send_command(locks[0].device_id, "lock", {})
                    print("🔒 Locked door")

            # Wait a moment for data to propagate
            await asyncio.sleep(0.1)

            # Run SAFLA cycle
            cycle_result = await safla_loop.run_single_cycle()

            if cycle_result.get("success"):
                print(
                    f"✅ Cycle completed in {cycle_result.get('total_duration', 0):.3f}s"
                )
                print(
                    f"   📊 Sensor data: {cycle_result.get('sensor_data_count', 0)} readings"
                )
                print(
                    f"   🔍 Analysis: {'✓' if cycle_result.get('analysis_result') else '✗'}"
                )
                print(
                    f"   🎯 Actions: {cycle_result.get('execution_results_count', 0)} executed"
                )
                print(
                    f"   🧠 Learning: {'✓' if cycle_result.get('learning_result') else '✗'}"
                )

                phases = cycle_result.get("phases_completed", [])
                timings = cycle_result.get("phase_timings", {})
                for phase in phases:
                    timing = timings.get(phase, 0)
                    print(f"      {phase}: {timing:.3f}s")
            else:
                print(f"❌ Cycle failed: {cycle_result.get('error', 'Unknown error')}")

        # Test continuous operation
        print("\n🚀 Testing continuous operation...")

        # Start SAFLA loop in background
        safla_task = asyncio.create_task(safla_loop.start())

        # Wait a few seconds to let it run
        await asyncio.sleep(5.0)

        # Check status during operation
        status = await safla_loop.get_status()
        print(f"📊 Running status: {status['state']}")
        print(f"🔄 Cycles completed: {status['cycle_count']}")
        print(f"⏱️ Uptime: {status['uptime_seconds']:.1f}s")

        if "performance_metrics" in status:
            perf = status["performance_metrics"]
            print(f"📈 Success rate: {perf.get('success_rate', 0):.1%}")
            print(f"📈 Avg cycle time: {perf.get('average_cycle_time', 0):.3f}s")
            print(f"📈 Throughput: {perf.get('throughput', 0):.1f} cycles/sec")

        # Test some scenarios during operation
        print("\n🎭 Testing scenarios during operation...")

        # Scenario 1: Environmental change
        simulator.set_environmental_condition("temperature", 35)  # Hot day
        print("🌡️ Set external temperature to 35°C")
        await asyncio.sleep(2.0)

        # Scenario 2: Security event
        sensors = simulator.get_devices_by_type("sensor")
        motion_sensors = [s for s in sensors if "motion" in s.name.lower()]
        if motion_sensors:
            await simulator.send_command(
                motion_sensors[0].device_id, "trigger", {"detected": True}
            )
            print("👥 Triggered motion sensor")
            await asyncio.sleep(2.0)

        # Scenario 3: Power optimization opportunity
        lights = simulator.get_devices_by_type("light")
        for light in lights[:2]:  # Turn on multiple lights
            await simulator.send_command(
                light.device_id, "turn_on", {"brightness": 100}
            )
        simulator.set_environmental_condition("occupancy", False)  # No one home
        print("💡 Created energy optimization opportunity")
        await asyncio.sleep(3.0)

        # Stop SAFLA loop
        await safla_loop.stop()
        safla_task.cancel()

        try:
            await safla_task
        except asyncio.CancelledError:
            pass

        # Final status
        final_status = await safla_loop.get_status()
        print(f"\n📊 Final status: {final_status['state']}")
        print(f"🔄 Total cycles: {final_status['cycle_count']}")
        print(f"⏱️ Total uptime: {final_status['uptime_seconds']:.1f}s")

        # Component metrics
        print("\n📈 Component Performance:")
        comp_metrics = final_status.get("component_metrics", {})
        for component, metrics in comp_metrics.items():
            if isinstance(metrics, dict):
                print(f"   {component}:")
                for metric, value in list(metrics.items())[:3]:  # Show first 3 metrics
                    if isinstance(value, (int, float)):
                        print(f"     {metric}: {value}")

        # Safety metrics
        safety = final_status.get("safety_status", {})
        print(f"\n🛡️ Safety Status:")
        print(
            f"   Safe mode activations: {final_status['system_metrics'].get('safe_mode_activations', 0)}"
        )
        print(
            f"   Safety violations: {final_status['system_metrics'].get('safety_violations', 0)}"
        )
        print(f"   Recent violations: {safety.get('recent_violations', 0)}")

        # Test performance optimization
        print("\n⚡ Testing performance optimization...")
        optimization_result = await safla_loop.optimize_performance()
        print(f"🔧 Applied {optimization_result['optimizations_applied']} optimizations")

        for opt in optimization_result.get("optimizations", []):
            print(f"   {opt['type']}: {opt.get('reason', 'No reason given')}")

        # Test diagnostic info
        print("\n🔍 Diagnostic Information:")
        diagnostics = safla_loop.get_diagnostic_info()

        cycle_stats = diagnostics["cycle_statistics"]
        print(f"   Success rate: {cycle_stats['success_rate']:.1%}")
        print(
            f"   Component health: {len([c for c in diagnostics['component_health'].values() if c['available']])} / {len(diagnostics['component_health'])} available"
        )

        recent_failures = diagnostics.get("recent_failures", [])
        if recent_failures:
            print(f"   Recent failures: {len(recent_failures)}")
            for failure in recent_failures[-3:]:  # Show last 3 failures
                print(f"     {failure['component']}: {failure['error'][:50]}...")
        else:
            print("   Recent failures: None")

        print("\n✅ SAFLA Integration Test Completed Successfully!")

    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        # Cleanup
        await simulator.stop()

    return True


async def main():
    """Main test function."""
    try:
        success = await test_safla_integration()
        if success:
            print("\n🎉 All tests passed!")
            return 0
        else:
            print("\n💥 Some tests failed!")
            return 1
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    # Run the test
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
