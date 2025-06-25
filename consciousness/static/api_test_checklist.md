# Consciousness API Manual Test Checklist

## Overview
This checklist provides comprehensive manual testing procedures for all API endpoints in the Consciousness System. Each test includes preconditions, test steps, and expected results.

## Test Environment Setup

### Prerequisites
- [ ] Consciousness API server running on port 8000
- [ ] Web UI accessible at http://localhost:8000/static/api_test_ui.html
- [ ] Valid authentication credentials (admin/consciousness123)

### Initial Setup
- [ ] Open API Test UI in browser
- [ ] Authenticate with valid credentials
- [ ] Verify authentication status shows "Authenticated"

---

## 1. Authentication Tests

### Test 1.1: Valid Login
**Endpoint:** `POST /api/v1/auth/login`
**Steps:**
1. Enter username: "admin"
2. Enter password: "consciousness123"
3. Click "Login" button
**Expected Result:**
- Status: 200 OK
- Response contains `access_token`, `token_type`, `expires_in`
- Auth status changes to "Authenticated"

### Test 1.2: Invalid Login
**Endpoint:** `POST /api/v1/auth/login`
**Steps:**
1. Enter username: "invalid"
2. Enter password: "wrong"
3. Click "Login" button
**Expected Result:**
- Status: 401 Unauthorized
- Error message about invalid credentials

---

## 2. Core System Tests

### Test 2.1: Health Check
**Endpoint:** `GET /health`
**Steps:**
1. Click "Test" button for health endpoint
**Expected Result:**
- Status: 200 OK
- Response contains `status`, `version`, `timestamp`, `components`
- Status should be "healthy"

### Test 2.2: Consciousness Status
**Endpoint:** `GET /api/v1/consciousness/status`
**Prerequisites:** Must be authenticated
**Steps:**
1. Click "Test" button for consciousness status
**Expected Result:**
- Status: 200 OK
- Response contains `status`, `awareness_level`, `emotional_state`, `active_devices`, `safla_loops`

### Test 2.3: Get Emotions
**Endpoint:** `GET /api/v1/consciousness/emotions`
**Prerequisites:** Must be authenticated
**Steps:**
1. Select time range: "1h"
2. Check "Include History"
3. Click "Test" button
**Expected Result:**
- Status: 200 OK
- Response contains `current` emotion data
- If history enabled, includes `history` array

### Test 2.4: Natural Language Query
**Endpoint:** `POST /api/v1/consciousness/query`
**Prerequisites:** Must be authenticated
**Steps:**
1. Enter query: "How are you feeling today?"
2. Check "Include Devices"
3. Click "Test" button
**Expected Result:**
- Status: 200 OK
- Response contains natural language response
- Query processing confirmation

---

## 3. Device Management Tests

### Test 3.1: Get All Devices
**Endpoint:** `GET /api/v1/devices`
**Prerequisites:** Must be authenticated
**Steps:**
1. Leave filters empty
2. Click "Test" button
**Expected Result:**
- Status: 200 OK
- Response contains `devices` array and `total` count
- Filter information included

### Test 3.2: Get Devices with Filters
**Endpoint:** `GET /api/v1/devices`
**Prerequisites:** Must be authenticated
**Steps:**
1. Set Status Filter: "active"
2. Set Location Filter: "living_room"
3. Set Device Type Filter: "light"
4. Click "Test" button
**Expected Result:**
- Status: 200 OK
- Response shows filtered results
- Filters applied correctly in response

### Test 3.3: Get Specific Device
**Endpoint:** `GET /api/v1/devices/{device_id}`
**Prerequisites:** Must be authenticated
**Steps:**
1. Enter Device ID: "test_device_001"
2. Click "Test" button
**Expected Result:**
- Status: 200 OK if device exists
- Status: 404 Not Found if device doesn't exist
- Device details in response

### Test 3.4: Control Device
**Endpoint:** `PUT /api/v1/devices/{device_id}/control`
**Prerequisites:** Must be authenticated
**Steps:**
1. Enter Device ID: "test_device_001"
2. Enter Action: "turn_on"
3. Enter Value: "true"
4. Enter Transition Time: "1000"
5. Click "Test" button
**Expected Result:**
- Status: 200 OK if device exists and action is valid
- Response contains control result

### Test 3.5: Batch Device Control
**Endpoint:** `POST /api/v1/devices/batch-control`
**Prerequisites:** Must be authenticated
**Steps:**
1. Enter JSON: `{"devices": [{"device_id": "1", "action": "turn_on"}, {"device_id": "2", "action": "turn_off"}]}`
2. Click "Test" button
**Expected Result:**
- Status: 200 OK
- Response contains results for each device command

---

## 4. Memory System Tests

### Test 4.1: Get Memory Entries
**Endpoint:** `GET /api/v1/memory`
**Prerequisites:** Must be authenticated
**Steps:**
1. Enter Memory Type: "experience"
2. Select Time Range: "7d"
3. Set Limit: "10"
4. Click "Test" button
**Expected Result:**
- Status: 200 OK
- Response contains `memories` array

### Test 4.2: Store Memory Entry
**Endpoint:** `POST /api/v1/memory`
**Prerequisites:** Must be authenticated
**Steps:**
1. Enter Memory Type: "test_memory"
2. Enter Content: "Test memory entry from API testing UI"
3. Enter Context JSON: `{"source": "api_test", "timestamp": "2024-01-01T00:00:00Z"}`
4. Click "Test" button
**Expected Result:**
- Status: 200 OK
- Response contains `memory_id`, `status`, `timestamp`

---

## 5. Interview System Tests

### Test 5.1: Start Interview
**Endpoint:** `POST /api/v1/interview/start`
**Prerequisites:** Must be authenticated
**Steps:**
1. Enter House ID: "test_house_001"
2. Click "Test" button
**Expected Result:**
- Status: 200 OK
- Response contains `interview_id`, `status`, `current_phase`, `ai_message`
- **Note:** Save interview_id for subsequent tests

### Test 5.2: Send Interview Message
**Endpoint:** `POST /api/v1/interview/{interview_id}/message`
**Prerequisites:** Must be authenticated, valid interview_id from Test 5.1
**Steps:**
1. Enter Interview ID from Test 5.1
2. Enter Message: "I have smart lights in my living room and bedroom, plus a smart thermostat in the hallway."
3. Click "Test" button
**Expected Result:**
- Status: 200 OK
- Response contains `ai_response`, `current_phase`, `discovered_candidates`

### Test 5.3: Get Interview Status
**Endpoint:** `GET /api/v1/interview/{interview_id}/status`
**Prerequisites:** Must be authenticated, valid interview_id
**Steps:**
1. Enter Interview ID from Test 5.1
2. Click "Test" button
**Expected Result:**
- Status: 200 OK
- Response contains `interview_id`, `status`, `current_phase`, `progress`

---

## 6. Discovery System Tests

### Test 6.1: Start Discovery Scan
**Endpoint:** `POST /api/v1/discovery/scan`
**Prerequisites:** Must be authenticated
**Steps:**
1. Check protocols: mDNS, UPnP
2. Set Timeout: 30 seconds
3. Click "Test" button
**Expected Result:**
- Status: 200 OK
- Response contains `scan_id`, `status`, `started_at`, `estimated_completion`
- **Note:** Save scan_id for Test 6.2

### Test 6.2: Get Discovery Results
**Endpoint:** `GET /api/v1/discovery/scan/{scan_id}`
**Prerequisites:** Must be authenticated, valid scan_id from Test 6.1
**Steps:**
1. Enter Scan ID from Test 6.1
2. Click "Test" button
**Expected Result:**
- Status: 200 OK
- Response contains `scan_id`, `status`, `results`, `total_devices_found`

---

## 7. Integration Templates Tests

### Test 7.1: Get Integration Templates
**Endpoint:** `GET /api/v1/integrations/templates`
**Prerequisites:** Must be authenticated
**Steps:**
1. Enter Brand Filter: "philips"
2. Enter Device Class Filter: "light"
3. Click "Test" button
**Expected Result:**
- Status: 200 OK
- Response contains `templates` array

### Test 7.2: Classify Device
**Endpoint:** `POST /api/v1/integrations/classify`
**Prerequisites:** Must be authenticated
**Steps:**
1. Enter Description: "Smart bulb that changes colors and can be dimmed, made by Philips Hue"
2. Enter Context JSON: `{"location": "living_room", "discovered_by": "user_input"}`
3. Click "Test" button
**Expected Result:**
- Status: 200 OK
- Response contains `classifications` array

---

## 8. SAFLA Loops Tests

### Test 8.1: Get SAFLA Status
**Endpoint:** `GET /api/v1/safla/status`
**Prerequisites:** Must be authenticated
**Steps:**
1. Click "Test" button
**Expected Result:**
- Status: 200 OK
- Response contains `active_loops`, `loops` array

### Test 8.2: Trigger SAFLA Loop
**Endpoint:** `POST /api/v1/safla/trigger`
**Prerequisites:** Must be authenticated
**Steps:**
1. Enter Loop ID: "main_loop"
2. Enter Parameters JSON: `{"priority": "high", "context": "manual_trigger"}`
3. Click "Test" button
**Expected Result:**
- Status: 200 OK
- Response contains `loop_id`, `trigger_id`, `status`, `estimated_completion`

---

## 9. Digital Twins Tests

### Test 9.1: Get Digital Twins
**Endpoint:** `GET /api/v1/twins`
**Prerequisites:** Must be authenticated
**Steps:**
1. Leave filters empty
2. Click "Test" button
**Expected Result:**
- Status: 200 OK
- Response contains `twins` array, `total`, `synchronized`, `out_of_sync` counts

### Test 9.2: Create Digital Twin
**Endpoint:** `POST /api/v1/twins`
**Prerequisites:** Must be authenticated
**Steps:**
1. Enter Device ID: "test_device_001"
2. Select Fidelity Level: "advanced"
3. Enter Configuration JSON: `{"update_frequency": 60, "include_history": true}`
4. Click "Test" button
**Expected Result:**
- Status: 200 OK
- Response contains digital twin details

---

## 10. Scenarios & Predictions Tests

### Test 10.1: Create Scenario
**Endpoint:** `POST /api/v1/scenarios`
**Prerequisites:** Must be authenticated
**Steps:**
1. Enter Scenario Name: "test_scenario"
2. Enter Description: "Test scenario for API validation"
3. Set Duration: 300 seconds
4. Enter Events JSON: `[{"time": 0, "action": "turn_on", "device": "light_1"}]`
5. Enter Twin IDs: "twin_1,twin_2"
6. Click "Test" button
**Expected Result:**
- Status: 200 OK
- Response contains `scenario_id`, `status`, `estimated_completion`

### Test 10.2: What-If Analysis
**Endpoint:** `POST /api/v1/predictions/what-if`
**Prerequisites:** Must be authenticated
**Steps:**
1. Enter Scenario: "energy_optimization"
2. Enter Changes JSON: `{"temperature_setpoint": 20, "lighting_brightness": 75}`
3. Enter Duration: "1h"
4. Enter Metrics: "energy_consumption,comfort_level,cost"
5. Click "Test" button
**Expected Result:**
- Status: 200 OK
- Response contains `analysis_id`, `status`, `results`

---

## 11. WebSocket Real-time Tests

### Test 11.1: WebSocket Connection
**Endpoint:** `WebSocket /api/v1/realtime`
**Steps:**
1. Click "Connect" button in WebSocket section
2. Observe connection status
3. Monitor log for messages
**Expected Result:**
- Status changes to "Connected"
- Initialization message received
- Real-time updates appear in log

### Test 11.2: WebSocket Disconnection
**Steps:**
1. Click "Disconnect" button
2. Observe status change
**Expected Result:**
- Status changes to "Disconnected"
- No further messages received

---

## 12. Error Handling Tests

### Test 12.1: Unauthenticated Access
**Steps:**
1. Click "Logout" button
2. Try to access any protected endpoint
**Expected Result:**
- Status: 401 Unauthorized
- Error message about authentication required

### Test 12.2: Invalid JSON in POST Requests
**Steps:**
1. Enter invalid JSON in any JSON field
2. Click "Test" button
**Expected Result:**
- Status: 400 Bad Request
- JSON parsing error message

### Test 12.3: Missing Required Fields
**Steps:**
1. Leave required fields empty
2. Click "Test" button
**Expected Result:**
- Status: 400 Bad Request
- Validation error message

---

## Test Completion Checklist

### Overall Validation
- [ ] All 30+ endpoints tested
- [ ] Authentication working correctly
- [ ] All HTTP methods (GET, POST, PUT) working
- [ ] Query parameters handled correctly
- [ ] JSON request/response bodies working
- [ ] Error handling working as expected
- [ ] WebSocket connection functional

### Performance Validation
- [ ] Response times under 5 seconds for most endpoints
- [ ] No memory leaks during extended testing
- [ ] WebSocket connection stable

### Security Validation
- [ ] Authentication required for protected endpoints
- [ ] JWT tokens working correctly
- [ ] CORS headers present
- [ ] No sensitive data exposed in error messages

### Documentation
- [ ] All endpoints documented
- [ ] Test results recorded
- [ ] Issues logged and categorized

---

## Test Results Summary

**Date:** ___________
**Tester:** ___________
**Environment:** ___________

**Endpoints Tested:** _____ / 30+
**Passed:** _____
**Failed:** _____
**Blocked:** _____

**Critical Issues:** _____
**Non-Critical Issues:** _____

**Overall Assessment:** [ ] PASS [ ] FAIL [ ] PARTIAL

**Notes:**
_________________________________
_________________________________
_________________________________
