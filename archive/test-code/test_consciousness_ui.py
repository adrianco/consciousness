#!/usr/bin/env python3
"""
Test script for consciousness UI functionality
"""

import json
import time

import requests

BASE_URL = "http://localhost:8000"


def test_authentication():
    """Test the authentication endpoint"""
    print("🔐 Testing Authentication...")
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"username": "admin", "password": "consciousness123"},
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Authentication successful! Token received.")
        return data["access_token"]
    else:
        print(f"❌ Authentication failed: {response.status_code}")
        return None


def test_consciousness_status(token):
    """Test consciousness status endpoint"""
    print("\n🧠 Testing Consciousness Status...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/v1/consciousness/status", headers=headers)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Consciousness status: {data['status']}")
        print(f"   Awareness level: {data['awareness_level']}")
        print(f"   Emotional state: {data['emotional_state']['primary']}")
        print(f"   Active devices: {data['active_devices']}")
        return True
    else:
        print(f"❌ Failed to get consciousness status: {response.status_code}")
        return False


def test_emotions(token):
    """Test emotions endpoint"""
    print("\n❤️ Testing Emotions...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/api/v1/consciousness/emotions", headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Current emotion: {data['current']['primary_emotion']}")
        print(f"   Arousal: {data['current']['arousal']}")
        print(f"   Valence: {data['current']['valence']}")
        return True
    else:
        print(f"❌ Failed to get emotions: {response.status_code}")
        return False


def test_chat_query(token):
    """Test consciousness query/chat endpoint"""
    print("\n💬 Testing Chat Query...")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    query_data = {"query": "What is the current status of my smart home?"}
    response = requests.post(
        f"{BASE_URL}/api/v1/consciousness/query", headers=headers, json=query_data
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Query response received!")
        print(f"   Query: {query_data['query']}")
        print(f"   Response: {data['response']}")
        return True
    else:
        print(f"❌ Failed to process query: {response.status_code}")
        return False


def test_devices(token):
    """Test devices endpoint"""
    print("\n📱 Testing Devices...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/v1/devices", headers=headers)

    if response.status_code == 200:
        data = response.json()
        devices = data.get("devices", data)
        print(f"✅ Found {len(devices)} devices:")
        for device in devices[:3]:  # Show first 3 devices
            print(f"   - {device['name']} ({device['type']}) - {device['status']}")
        return True
    else:
        print(f"❌ Failed to get devices: {response.status_code}")
        return False


def test_memory(token):
    """Test memory endpoint"""
    print("\n🧠 Testing Memory...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/v1/memory", headers=headers)

    if response.status_code == 200:
        data = response.json()
        memories = data.get("memories", [])
        print(f"✅ Found {len(memories)} memory entries:")
        for memory in memories[:2]:  # Show first 2 memories
            print(f"   - {memory['type']}: {memory['content'][:50]}...")
        return True
    else:
        print(f"❌ Failed to get memory: {response.status_code}")
        return False


def main():
    """Run all tests"""
    print("🏠 House Consciousness UI Test Suite")
    print("=" * 50)

    # Test authentication
    token = test_authentication()
    if not token:
        print("\n❌ Authentication failed - stopping tests")
        return False

    # Test all consciousness features
    results = []
    results.append(test_consciousness_status(token))
    results.append(test_emotions(token))
    results.append(test_chat_query(token))
    results.append(test_devices(token))
    results.append(test_memory(token))

    # Summary
    passed = sum(results)
    total = len(results)

    print(f"\n📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All consciousness UI features are working!")
        return True
    else:
        print("⚠️ Some tests failed - check the output above")
        return False


if __name__ == "__main__":
    main()
