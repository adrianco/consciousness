"""Demo dashboard for visualizing the consciousness system in action."""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from consciousness.core.consciousness_engine import ConsciousnessEngine
from consciousness.simulators.device_simulator import HouseSimulator
from consciousness.simulators.demo_scenarios import register_scenarios


class DemoDashboard:
    """Web-based dashboard for demonstrating consciousness system capabilities."""
    
    def __init__(self, consciousness_engine: ConsciousnessEngine):
        self.app = FastAPI(title="Consciousness Demo Dashboard")
        self.consciousness = consciousness_engine
        self.house_simulator = HouseSimulator()
        self.connections: List[WebSocket] = []
        self.running_scenarios = {}
        
        # Register scenarios
        register_scenarios(self.house_simulator)
        
        # Setup routes
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard():
            return self._get_dashboard_html()
        
        @self.app.get("/api/status")
        async def get_status():
            """Get system status."""
            return {
                "timestamp": datetime.now().isoformat(),
                "consciousness_status": await self._get_consciousness_status(),
                "devices": await self._get_device_status(),
                "scenarios": list(self.house_simulator.scenarios.keys()),
                "running_scenario": self.house_simulator.current_scenario
            }
        
        @self.app.get("/api/devices")
        async def get_devices():
            """Get all devices and their states."""
            devices = []
            for device_id, simulator in self.house_simulator.devices.items():
                devices.append({
                    "id": device_id,
                    "name": simulator.device.user_name if hasattr(simulator.device, 'user_name') else f"Device {device_id}",
                    "type": simulator.device.device_class,
                    "location": simulator.device.location,
                    "state": simulator.state,
                    "running": simulator.running
                })
            return {"devices": devices}
        
        @self.app.post("/api/scenarios/{scenario_name}/run")
        async def run_scenario(scenario_name: str):
            """Run a demonstration scenario."""
            if scenario_name in self.house_simulator.scenarios:
                # Run scenario in background
                task = asyncio.create_task(self._run_scenario_with_updates(scenario_name))
                self.running_scenarios[scenario_name] = task
                return {"status": "started", "scenario": scenario_name}
            else:
                return {"status": "error", "message": f"Scenario '{scenario_name}' not found"}
        
        @self.app.post("/api/scenarios/stop")
        async def stop_scenarios():
            """Stop all running scenarios."""
            for task in self.running_scenarios.values():
                task.cancel()
            self.running_scenarios.clear()
            self.house_simulator.current_scenario = None
            return {"status": "stopped"}
        
        @self.app.post("/api/devices/{device_id}/control")
        async def control_device(device_id: int, command: Dict[str, Any]):
            """Control a specific device."""
            if device_id in self.house_simulator.devices:
                simulator = self.house_simulator.devices[device_id]
                await simulator.set_state(command)
                await self._broadcast_update("device_update", {
                    "device_id": device_id,
                    "state": simulator.state
                })
                return {"status": "success", "device_id": device_id, "new_state": simulator.state}
            else:
                return {"status": "error", "message": f"Device {device_id} not found"}
        
        @self.app.post("/api/consciousness/query")
        async def query_consciousness(query: Dict[str, str]):
            """Query the consciousness engine."""
            response = await self.consciousness.process_query(query.get("question", ""))
            return {"response": response}
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            await websocket.accept()
            self.connections.append(websocket)
            
            try:
                while True:
                    # Send periodic status updates
                    status = await self._get_system_status()
                    await websocket.send_json(status)
                    await asyncio.sleep(2)  # Update every 2 seconds
                    
            except WebSocketDisconnect:
                self.connections.remove(websocket)
    
    async def _run_scenario_with_updates(self, scenario_name: str):
        """Run a scenario and broadcast updates."""
        try:
            await self._broadcast_update("scenario_start", {"scenario": scenario_name})
            await self.house_simulator.run_scenario(scenario_name)
            await self._broadcast_update("scenario_complete", {"scenario": scenario_name})
        except Exception as e:
            await self._broadcast_update("scenario_error", {
                "scenario": scenario_name,
                "error": str(e)
            })
        finally:
            if scenario_name in self.running_scenarios:
                del self.running_scenarios[scenario_name]
    
    async def _broadcast_update(self, event_type: str, data: Dict[str, Any]):
        """Broadcast update to all connected WebSocket clients."""
        message = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        disconnected = []
        for connection in self.connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.connections.remove(connection)
    
    async def _get_consciousness_status(self) -> Dict[str, Any]:
        """Get consciousness engine status."""
        try:
            status = await self.consciousness.get_status()
            return {
                "active": True,
                "emotional_state": status.get("emotional_state", "content"),
                "mood": status.get("mood", "stable"),
                "active_concerns": status.get("active_concerns", []),
                "last_activity": status.get("last_activity", datetime.now().isoformat())
            }
        except Exception as e:
            return {
                "active": False,
                "error": str(e)
            }
    
    async def _get_device_status(self) -> Dict[str, Any]:
        """Get aggregated device status."""
        total_devices = len(self.house_simulator.devices)
        active_devices = sum(1 for sim in self.house_simulator.devices.values() if sim.running)
        
        device_types = {}
        for simulator in self.house_simulator.devices.values():
            device_type = simulator.device.device_class
            if device_type not in device_types:
                device_types[device_type] = 0
            device_types[device_type] += 1
        
        return {
            "total": total_devices,
            "active": active_devices,
            "types": device_types
        }
    
    async def _get_system_status(self) -> Dict[str, Any]:
        """Get complete system status for WebSocket updates."""
        return {
            "type": "status_update",
            "timestamp": datetime.now().isoformat(),
            "consciousness": await self._get_consciousness_status(),
            "devices": await self._get_device_status(),
            "running_scenario": self.house_simulator.current_scenario,
            "device_states": {
                device_id: simulator.state 
                for device_id, simulator in self.house_simulator.devices.items()
            }
        }
    
    def _get_dashboard_html(self) -> str:
        """Return the dashboard HTML."""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Consciousness Demo Dashboard</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        .dashboard {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .card h3 {
            margin-top: 0;
            color: #667eea;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .status-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        .status-value {
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }
        .scenarios {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
        }
        .scenario-card {
            background: white;
            border: 2px solid #eee;
            border-radius: 10px;
            padding: 15px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .scenario-card:hover {
            border-color: #667eea;
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .scenario-card.running {
            border-color: #4CAF50;
            background: #f1f8e9;
        }
        .device-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 15px;
        }
        .device-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            border-left: 4px solid #667eea;
        }
        .device-card.climate { border-left-color: #ff9800; }
        .device-card.light { border-left-color: #ffeb3b; }
        .device-card.sensor { border-left-color: #4caf50; }
        .device-card.security { border-left-color: #f44336; }
        .device-card.energy { border-left-color: #2196f3; }
        .device-state {
            font-family: monospace;
            background: #eee;
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
            font-size: 12px;
        }
        .controls {
            margin-top: 20px;
            text-align: center;
        }
        .btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 5px;
            font-size: 14px;
        }
        .btn:hover {
            background: #5a6fd8;
        }
        .btn.danger {
            background: #f44336;
        }
        .btn.danger:hover {
            background: #da190b;
        }
        .log {
            background: #1e1e1e;
            color: #00ff00;
            padding: 15px;
            border-radius: 8px;
            font-family: monospace;
            height: 200px;
            overflow-y: auto;
            margin-top: 20px;
        }
        .consciousness-status {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        .emotion-indicator {
            font-size: 48px;
            margin: 10px 0;
        }
        @media (max-width: 768px) {
            .dashboard {
                grid-template-columns: 1fr;
            }
            .scenarios {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🧠 Consciousness Demo Dashboard</h1>
        <p>Real-time demonstration of AI-powered home consciousness system</p>
        <div id="connectionStatus">Connecting...</div>
    </div>

    <div class="dashboard">
        <div class="card">
            <h3>🤖 Consciousness Status</h3>
            <div id="consciousnessStatus" class="consciousness-status">
                <div class="emotion-indicator" id="emotionIndicator">😊</div>
                <div id="emotionalState">Loading...</div>
                <div id="moodStatus"></div>
                <div id="activeConcerns"></div>
            </div>
        </div>

        <div class="card">
            <h3>📊 System Overview</h3>
            <div class="status-grid">
                <div class="status-item">
                    <div class="status-value" id="totalDevices">-</div>
                    <div>Total Devices</div>
                </div>
                <div class="status-item">
                    <div class="status-value" id="activeDevices">-</div>
                    <div>Active Devices</div>
                </div>
                <div class="status-item">
                    <div class="status-value" id="runningScenario">None</div>
                    <div>Current Scenario</div>
                </div>
            </div>
        </div>
    </div>

    <div class="card">
        <h3>🎭 Demo Scenarios</h3>
        <div class="scenarios" id="scenarios">
            <div class="scenario-card" data-scenario="smart_morning">
                <h4>🌅 Smart Morning Routine</h4>
                <p>Automated wake-up sequence with gradual lighting, climate control, and security disarming.</p>
            </div>
            <div class="scenario-card" data-scenario="security_alert">
                <h4>🚨 Security Alert</h4>
                <p>Intrusion detection simulation with motion sensors, lighting deterrents, and alerts.</p>
            </div>
            <div class="scenario-card" data-scenario="energy_optimization">
                <h4>⚡ Energy Optimization</h4>
                <p>Adaptive device control for peak demand management and solar utilization.</p>
            </div>
            <div class="scenario-card" data-scenario="party_mode">
                <h4>🎉 Party Mode</h4>
                <p>Entertainment scenario with dynamic lighting effects and crowd-aware climate control.</p>
            </div>
            <div class="scenario-card" data-scenario="vacation_mode">
                <h4>✈️ Vacation Mode</h4>
                <p>Security and energy saving while away with presence simulation.</p>
            </div>
        </div>
        <div class="controls">
            <button class="btn danger" onclick="stopScenarios()">Stop All Scenarios</button>
        </div>
    </div>

    <div class="card">
        <h3>🏠 Device Status</h3>
        <div id="deviceGrid" class="device-grid">
            <!-- Devices will be populated here -->
        </div>
    </div>

    <div class="card">
        <h3>📝 Event Log</h3>
        <div id="eventLog" class="log"></div>
    </div>

    <script>
        let socket;
        let isConnected = false;

        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            socket = new WebSocket(`${protocol}//${window.location.host}/ws`);
            
            socket.onopen = function(event) {
                isConnected = true;
                document.getElementById('connectionStatus').textContent = 'Connected';
                document.getElementById('connectionStatus').style.color = '#4CAF50';
                logEvent('Connected to consciousness system');
            };
            
            socket.onmessage = function(event) {
                const data = JSON.parse(event.data);
                handleUpdate(data);
            };
            
            socket.onclose = function(event) {
                isConnected = false;
                document.getElementById('connectionStatus').textContent = 'Disconnected';
                document.getElementById('connectionStatus').style.color = '#f44336';
                logEvent('Disconnected from consciousness system');
                
                // Attempt to reconnect after 3 seconds
                setTimeout(connectWebSocket, 3000);
            };
        }

        function handleUpdate(data) {
            if (data.type === 'status_update') {
                updateConsciousnessStatus(data.consciousness);
                updateSystemOverview(data.devices);
                updateDeviceGrid(data.device_states);
                document.getElementById('runningScenario').textContent = data.running_scenario || 'None';
            } else if (data.type === 'scenario_start') {
                logEvent(`🎬 Scenario started: ${data.data.scenario}`);
                markScenarioRunning(data.data.scenario, true);
            } else if (data.type === 'scenario_complete') {
                logEvent(`✅ Scenario completed: ${data.data.scenario}`);
                markScenarioRunning(data.data.scenario, false);
            } else if (data.type === 'scenario_error') {
                logEvent(`❌ Scenario error: ${data.data.scenario} - ${data.data.error}`);
                markScenarioRunning(data.data.scenario, false);
            }
        }

        function updateConsciousnessStatus(consciousness) {
            const emotions = {
                'happy': '😊',
                'excited': '😄',
                'content': '😌',
                'worried': '😟',
                'concerned': '😰',
                'focused': '🤔',
                'relaxed': '😎'
            };
            
            document.getElementById('emotionIndicator').textContent = emotions[consciousness.emotional_state] || '🤖';
            document.getElementById('emotionalState').textContent = `Feeling ${consciousness.emotional_state}`;
            document.getElementById('moodStatus').textContent = `Mood: ${consciousness.mood}`;
            
            const concerns = consciousness.active_concerns || [];
            document.getElementById('activeConcerns').textContent = 
                concerns.length > 0 ? `Concerns: ${concerns.join(', ')}` : 'No active concerns';
        }

        function updateSystemOverview(devices) {
            document.getElementById('totalDevices').textContent = devices.total;
            document.getElementById('activeDevices').textContent = devices.active;
        }

        function updateDeviceGrid(deviceStates) {
            const grid = document.getElementById('deviceGrid');
            grid.innerHTML = '';
            
            Object.entries(deviceStates).forEach(([deviceId, state]) => {
                const deviceCard = document.createElement('div');
                deviceCard.className = `device-card`;
                deviceCard.innerHTML = `
                    <h4>Device ${deviceId}</h4>
                    <div class="device-state">${JSON.stringify(state, null, 2)}</div>
                `;
                grid.appendChild(deviceCard);
            });
        }

        function markScenarioRunning(scenarioName, isRunning) {
            const scenarioCard = document.querySelector(`[data-scenario="${scenarioName}"]`);
            if (scenarioCard) {
                if (isRunning) {
                    scenarioCard.classList.add('running');
                } else {
                    scenarioCard.classList.remove('running');
                }
            }
        }

        function logEvent(message) {
            const log = document.getElementById('eventLog');
            const timestamp = new Date().toLocaleTimeString();
            log.innerHTML += `[${timestamp}] ${message}\\n`;
            log.scrollTop = log.scrollHeight;
        }

        function runScenario(scenarioName) {
            fetch(`/api/scenarios/${scenarioName}/run`, { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'started') {
                        logEvent(`Starting scenario: ${scenarioName}`);
                    } else {
                        logEvent(`Error starting scenario: ${data.message}`);
                    }
                });
        }

        function stopScenarios() {
            fetch('/api/scenarios/stop', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    logEvent('All scenarios stopped');
                    document.querySelectorAll('.scenario-card').forEach(card => {
                        card.classList.remove('running');
                    });
                });
        }

        // Event listeners
        document.addEventListener('DOMContentLoaded', function() {
            connectWebSocket();
            
            // Add click handlers to scenario cards
            document.querySelectorAll('.scenario-card').forEach(card => {
                card.addEventListener('click', function() {
                    const scenario = this.getAttribute('data-scenario');
                    runScenario(scenario);
                });
            });
        });
    </script>
</body>
</html>
        '''


def create_demo_dashboard(consciousness_engine: ConsciousnessEngine) -> DemoDashboard:
    """Create and configure the demo dashboard."""
    return DemoDashboard(consciousness_engine)