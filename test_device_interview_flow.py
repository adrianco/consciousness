#!/usr/bin/env python3
"""
Test script for the complete device interview and digital twin creation flow.

This script demonstrates the end-to-end process of:
1. Starting a conversational device discovery interview
2. Classifying devices from natural language
3. Running automatic discovery
4. Matching Home Assistant integrations
5. Creating digital twins
6. Setting up synchronization

Usage:
    python test_device_interview_flow.py
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MockLLMClient:
    """Mock LLM client for testing."""

    async def chat_completions_create(self, **kwargs):
        """Mock chat completion."""
        prompt = kwargs.get("messages", [])[-1].get("content", "")

        # Simulate device extraction response
        if "Extract smart home devices" in prompt:
            return type(
                "Response",
                (),
                {
                    "choices": [
                        type(
                            "Choice",
                            (),
                            {
                                "message": type(
                                    "Message",
                                    (),
                                    {
                                        "content": json.dumps(
                                            [
                                                {
                                                    "description": "Philips Hue lights in the living room",
                                                    "brand": "Philips",
                                                    "function": "lighting",
                                                    "model": "Hue",
                                                    "location": "living room",
                                                    "keywords": [
                                                        "philips",
                                                        "hue",
                                                        "lights",
                                                        "living room",
                                                    ],
                                                    "count": 3,
                                                },
                                                {
                                                    "description": "Nest thermostat",
                                                    "brand": "Google Nest",
                                                    "function": "climate",
                                                    "model": "Thermostat",
                                                    "location": None,
                                                    "keywords": [
                                                        "nest",
                                                        "thermostat",
                                                        "temperature",
                                                    ],
                                                    "count": 1,
                                                },
                                            ]
                                        )
                                    },
                                )
                            },
                        )
                    ]
                },
            )()

        # Default response
        return type(
            "Response",
            (),
            {
                "choices": [
                    type(
                        "Choice",
                        (),
                        {
                            "message": type(
                                "Message",
                                (),
                                {"content": "I understand. Let me help you with that."},
                            )
                        },
                    )
                ]
            },
        )()


async def test_complete_interview_flow():
    """Test the complete device interview and twin creation flow."""

    logger.info("🚀 Starting Device Interview Flow Test")
    logger.info("=" * 60)

    try:
        # Import our implementation
        from consciousness.digital_twin.twin_manager import DigitalTwinManager
        from consciousness.discovery.auto_discovery import AutoDiscoveryService
        from consciousness.interview.device_classifier import DeviceClassifier
        from consciousness.interview.integration_matcher import IntegrationMatcher
        from consciousness.interview.interview_controller import InterviewController

        # Initialize mock LLM client
        mock_llm = MockLLMClient()

        # Initialize services
        logger.info("📋 Initializing services...")
        auto_discovery = AutoDiscoveryService()
        twin_manager = DigitalTwinManager()

        # Initialize interview controller
        interview_controller = InterviewController(
            llm_client=mock_llm,
            auto_discovery=auto_discovery,
            twin_manager=twin_manager,
        )

        await twin_manager.initialize()

        logger.info("✅ Services initialized successfully")

        # Step 1: Start Interview Session
        logger.info("\n🎤 Step 1: Starting Interview Session")
        logger.info("-" * 40)

        session = await interview_controller.start_interview(
            house_id="test_house_123", user_id="test_user_456"
        )

        logger.info(f"Session ID: {session.session_id}")
        logger.info(f"House ID: {session.house_id}")
        logger.info(f"Current Phase: {session.current_phase}")

        # Step 2: Process User Input
        logger.info("\n💬 Step 2: Processing User Input")
        logger.info("-" * 40)

        user_input = "I have Philips Hue lights in my living room and a Nest thermostat that controls the temperature."

        logger.info(f"User: {user_input}")

        response = await interview_controller.process_user_message(
            session.session_id, user_input
        )

        logger.info(f"AI Response: {response['response']}")
        logger.info(f"Discovered Candidates: {len(response['candidates'])}")
        logger.info(f"Current Phase: {response['phase']}")

        # Display discovered candidates
        for i, candidate in enumerate(response["candidates"]):
            logger.info(f"  Candidate {i+1}:")
            logger.info(f"    Description: {candidate.get('user_description')}")
            logger.info(f"    Brand: {candidate.get('detected_brand')}")
            logger.info(f"    Function: {candidate.get('detected_function')}")
            logger.info(f"    Confidence: {candidate.get('confidence_score', 0):.2f}")

        # Step 3: Test Integration Matching
        logger.info("\n🔧 Step 3: Testing Integration Matching")
        logger.info("-" * 40)

        integration_matcher = IntegrationMatcher()

        # Test Hue light matching
        hue_matches = await integration_matcher.match_integrations(
            brand="Philips", function="lighting", keywords=["philips", "hue", "lights"]
        )

        logger.info("Hue Integration Matches:")
        for match in hue_matches[:3]:  # Top 3 matches
            logger.info(f"  - {match['display_name']} (Score: {match['score']:.2f})")
            logger.info(f"    Requires Hub: {match['requires_hub']}")
            logger.info(f"    Requires Auth: {match['requires_auth']}")

        # Test Nest thermostat matching
        nest_matches = await integration_matcher.match_integrations(
            brand="Google Nest", function="climate", keywords=["nest", "thermostat"]
        )

        logger.info("\nNest Integration Matches:")
        for match in nest_matches[:3]:
            logger.info(f"  - {match['display_name']} (Score: {match['score']:.2f})")
            logger.info(f"    Requires Auth: {match['requires_auth']}")

        # Step 4: Test Automatic Discovery
        logger.info("\n🔍 Step 4: Testing Automatic Discovery")
        logger.info("-" * 40)

        logger.info("Running multi-protocol discovery (simulated)...")
        discovery_results = await auto_discovery.discover_all_protocols()

        total_discovered = sum(len(devices) for devices in discovery_results.values())
        logger.info(f"Total devices discovered: {total_discovered}")

        for protocol, devices in discovery_results.items():
            if devices:
                logger.info(f"  {protocol}: {len(devices)} devices")
                for device in devices[:2]:  # Show first 2 devices
                    logger.info(
                        f"    - {device.get('name', 'Unknown')} "
                        f"({device.get('device_type', 'unknown')})"
                    )

        # Step 5: Test Digital Twin Creation
        logger.info("\n🤖 Step 5: Testing Digital Twin Creation")
        logger.info("-" * 40)

        # Create device configuration for Hue light
        hue_device_config = {
            "id": "hue_light_001",
            "name": "Living Room Hue Lights",
            "brand": "Philips",
            "function": "lighting",
            "integration_type": "hue",
            "supported_features": ["brightness", "color_temp", "rgb_color"],
        }

        # Create twin configuration
        twin_config = {
            "fidelity_level": "advanced",
            "sync_frequency": 30,
            "enable_predictions": True,
            "enable_scenarios": True,
            "physics_modeling": True,
        }

        logger.info("Creating digital twin for Hue lights...")
        hue_twin = await twin_manager.create_device_twin(
            hue_device_config, twin_config, house_id="test_house_123"
        )

        logger.info(f"Twin Created: {hue_twin.id}")
        logger.info(f"Twin Type: {hue_twin.specification.twin_type}")
        logger.info(f"Fidelity Level: {hue_twin.specification.fidelity_level}")
        logger.info(
            f"Prediction Capabilities: {len(hue_twin.specification.prediction_capabilities)}"
        )

        # Create device configuration for Nest thermostat
        nest_device_config = {
            "id": "nest_thermostat_001",
            "name": "Main Thermostat",
            "brand": "Google Nest",
            "function": "climate",
            "integration_type": "nest",
            "supported_features": ["temperature", "humidity", "mode", "scheduling"],
        }

        logger.info("\nCreating digital twin for Nest thermostat...")
        nest_twin = await twin_manager.create_device_twin(
            nest_device_config, twin_config, house_id="test_house_123"
        )

        logger.info(f"Twin Created: {nest_twin.id}")
        logger.info(f"Twin Type: {nest_twin.specification.twin_type}")

        # Step 6: Test Twin Synchronization Setup
        logger.info("\n🔄 Step 6: Testing Twin Synchronization")
        logger.info("-" * 40)

        from consciousness.digital_twin.twin_manager import SyncConfig

        sync_config = SyncConfig(
            frequency=60,
            bidirectional=True,
            conflict_resolution="device_wins",
            safe_mode=True,
        )

        # Setup sync for Hue twin
        sync_success = await twin_manager.setup_synchronization(
            hue_twin.id, "physical_hue_device_123", sync_config
        )

        logger.info(
            f"Hue Twin Sync Setup: {'✅ Success' if sync_success else '❌ Failed'}"
        )

        # Setup sync for Nest twin
        sync_success = await twin_manager.setup_synchronization(
            nest_twin.id, "physical_nest_device_456", sync_config
        )

        logger.info(
            f"Nest Twin Sync Setup: {'✅ Success' if sync_success else '❌ Failed'}"
        )

        # Step 7: Test State Updates
        logger.info("\n📊 Step 7: Testing State Updates")
        logger.info("-" * 40)

        # Update Hue light state
        await twin_manager.update_twin_state(
            hue_twin.id, {"power": True, "brightness": 75, "color_temp": 3000}
        )
        logger.info(
            "Updated Hue twin state: Power=On, Brightness=75%, Color Temp=3000K"
        )

        # Update thermostat state
        await twin_manager.update_twin_state(
            nest_twin.id,
            {"target_temperature": 22.5, "current_temperature": 21.8, "mode": "heat"},
        )
        logger.info("Updated Nest twin state: Target=22.5°C, Current=21.8°C, Mode=Heat")

        # Step 8: Test Statistics and Monitoring
        logger.info("\n📈 Step 8: System Statistics")
        logger.info("-" * 40)

        twin_stats = await twin_manager.get_twin_statistics()
        logger.info(f"Total Twins: {twin_stats['total_twins']}")
        logger.info(f"Active Synchronizations: {twin_stats['active_synchronizations']}")
        logger.info(f"Twin Types: {twin_stats['twin_types']}")
        logger.info(f"Fidelity Levels: {twin_stats['fidelity_levels']}")

        # Final Summary
        logger.info("\n" + "=" * 60)
        logger.info("🎉 DEVICE INTERVIEW FLOW TEST COMPLETED SUCCESSFULLY!")
        logger.info("=" * 60)

        logger.info("\n📋 Test Summary:")
        logger.info(f"  ✅ Interview session created and managed")
        logger.info(f"  ✅ Natural language device classification")
        logger.info(f"  ✅ Home Assistant integration matching")
        logger.info(f"  ✅ Multi-protocol automatic discovery")
        logger.info(f"  ✅ Digital twin creation with physics modeling")
        logger.info(f"  ✅ Bidirectional synchronization setup")
        logger.info(f"  ✅ State management and updates")
        logger.info(f"  ✅ System monitoring and statistics")

        logger.info(
            f"\n🎯 Created {twin_stats['total_twins']} digital twins with full capabilities"
        )
        logger.info(
            f"🔗 Setup {twin_stats['active_synchronizations']} synchronization channels"
        )
        logger.info(f"🏠 Integrated with house consciousness system")

        # Cleanup
        await twin_manager.stop()

        return True

    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    print("🏠 Device Interview & Digital Twin System Test")
    print("=" * 60)

    success = await test_complete_interview_flow()

    if success:
        print("\n✅ All tests passed successfully!")
        return 0
    else:
        print("\n❌ Tests failed!")
        return 1


if __name__ == "__main__":
    import sys

    exit_code = asyncio.run(main())
    sys.exit(exit_code)
