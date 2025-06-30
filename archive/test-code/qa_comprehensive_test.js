/**
 * Comprehensive QA Test Suite for API Testing UI
 * Tests all implemented functionality and validates requirements
 */

class QATestSuite {
    constructor() {
        this.baseURL = 'http://localhost:8000';
        this.testResults = {
            total: 0,
            passed: 0,
            failed: 0,
            tests: []
        };
        this.authToken = null;
    }

    // Test result tracking
    addTestResult(testName, passed, details = '', error = null) {
        this.testResults.total++;
        if (passed) {
            this.testResults.passed++;
        } else {
            this.testResults.failed++;
        }

        this.testResults.tests.push({
            name: testName,
            passed,
            details,
            error: error?.message || error,
            timestamp: new Date().toISOString()
        });

        console.log(`${passed ? '✅' : '❌'} ${testName}: ${details}`);
        if (error) console.error(`   Error: ${error}`);
    }

    // API call helper
    async apiCall(endpoint, options = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...(this.authToken && { 'Authorization': `Bearer ${this.authToken}` }),
            ...options.headers
        };

        const response = await fetch(`${this.baseURL}${endpoint}`, {
            ...options,
            headers
        });

        const data = await response.json().catch(() => ({}));
        return { response, data };
    }

    // Core API Functionality Tests
    async testHealthEndpoint() {
        try {
            const { response, data } = await this.apiCall('/health');
            const passed = response.status === 200 && data.status === 'healthy';
            this.addTestResult(
                'Health Endpoint',
                passed,
                `Status: ${response.status}, Health: ${data.status}`
            );
            return passed;
        } catch (error) {
            this.addTestResult('Health Endpoint', false, 'Failed to call endpoint', error);
            return false;
        }
    }

    async testDetailedHealthEndpoint() {
        try {
            const { response, data } = await this.apiCall('/health/detailed');
            const passed = response.status === 200;
            this.addTestResult(
                'Detailed Health Endpoint',
                passed,
                `Status: ${response.status}, Components: ${Object.keys(data.components || {}).length}`
            );
            return passed;
        } catch (error) {
            this.addTestResult('Detailed Health Endpoint', false, 'Failed to call endpoint', error);
            return false;
        }
    }

    async testMetricsEndpoint() {
        try {
            const { response, data } = await this.apiCall('/metrics');
            const passed = response.status === 200 && typeof data === 'object';
            this.addTestResult(
                'Metrics Endpoint',
                passed,
                `Status: ${response.status}, Metrics: ${Object.keys(data).length}`
            );
            return passed;
        } catch (error) {
            this.addTestResult('Metrics Endpoint', false, 'Failed to call endpoint', error);
            return false;
        }
    }

    async testDeviceEndpoints() {
        try {
            // Test GET /api/devices
            const { response: listResponse, data: listData } = await this.apiCall('/api/devices');
            const listPassed = listResponse.status === 200 && Array.isArray(listData.devices);
            this.addTestResult(
                'Device List Endpoint',
                listPassed,
                `Status: ${listResponse.status}, Devices: ${listData.devices?.length || 0}`
            );

            if (listData.devices && listData.devices.length > 0) {
                // Test GET /api/devices/{id}
                const deviceId = listData.devices[0].id;
                const { response: getResponse, data: getData } = await this.apiCall(`/api/devices/${deviceId}`);
                const getPassed = getResponse.status === 200 && getData.id === deviceId;
                this.addTestResult(
                    'Individual Device Endpoint',
                    getPassed,
                    `Status: ${getResponse.status}, Device ID: ${getData.id}`
                );
            }

            return listPassed;
        } catch (error) {
            this.addTestResult('Device Endpoints', false, 'Failed to test device endpoints', error);
            return false;
        }
    }

    async testDiscoveryEndpoints() {
        try {
            // Test discovery status
            const { response: statusResponse, data: statusData } = await this.apiCall('/api/discovery/status');
            const statusPassed = statusResponse.status === 200;
            this.addTestResult(
                'Discovery Status Endpoint',
                statusPassed,
                `Status: ${statusResponse.status}, Demo Mode: ${statusData.demo_mode}`
            );

            // Test discovery scan
            const { response: scanResponse, data: scanData } = await this.apiCall('/api/discovery/scan', {
                method: 'POST'
            });
            const scanPassed = scanResponse.status === 200;
            this.addTestResult(
                'Discovery Scan Endpoint',
                scanPassed,
                `Status: ${scanResponse.status}, Message: ${scanData.message}`
            );

            return statusPassed && scanPassed;
        } catch (error) {
            this.addTestResult('Discovery Endpoints', false, 'Failed to test discovery endpoints', error);
            return false;
        }
    }

    async testDemoModeEndpoints() {
        try {
            // Test enable demo mode
            const { response: enableResponse, data: enableData } = await this.apiCall('/api/demo/enable', {
                method: 'POST'
            });
            const enablePassed = enableResponse.status === 200 && enableData.demo_mode === true;
            this.addTestResult(
                'Demo Mode Enable',
                enablePassed,
                `Status: ${enableResponse.status}, Demo Mode: ${enableData.demo_mode}, Devices: ${enableData.device_count}`
            );

            // Test disable demo mode
            const { response: disableResponse, data: disableData } = await this.apiCall('/api/demo/disable', {
                method: 'POST'
            });
            const disablePassed = disableResponse.status === 200 && disableData.demo_mode === false;
            this.addTestResult(
                'Demo Mode Disable',
                disablePassed,
                `Status: ${disableResponse.status}, Demo Mode: ${disableData.demo_mode}`
            );

            return enablePassed && disablePassed;
        } catch (error) {
            this.addTestResult('Demo Mode Endpoints', false, 'Failed to test demo mode endpoints', error);
            return false;
        }
    }

    // Test API Testing UI File Validation
    async validateAPITestingUI() {
        try {
            // Validate that the API test UI file exists and contains required elements
            const response = await fetch(`${this.baseURL}/static/api_test_ui.html`);
            const content = await response.text();

            const requiredElements = [
                'API Testing UI',
                'authentication',
                'endpoint',
                'testEndpoint',
                'WebSocket',
                'batch'
            ];

            let missingElements = [];
            for (const element of requiredElements) {
                if (!content.includes(element)) {
                    missingElements.push(element);
                }
            }

            const passed = response.status === 200 && missingElements.length === 0;
            this.addTestResult(
                'API Testing UI File Validation',
                passed,
                `Status: ${response.status}, Missing elements: ${missingElements.join(', ') || 'None'}`
            );

            return passed;
        } catch (error) {
            this.addTestResult('API Testing UI File Validation', false, 'Failed to validate UI file', error);
            return false;
        }
    }

    async validateAPIClient() {
        try {
            const response = await fetch(`${this.baseURL}/static/api-client.js`);
            const content = await response.text();

            const requiredClasses = [
                'ConsciousnessAPIClient',
                'APIError',
                'request',
                'getHealth',
                'connectWebSocket'
            ];

            let missingClasses = [];
            for (const cls of requiredClasses) {
                if (!content.includes(cls)) {
                    missingClasses.push(cls);
                }
            }

            const passed = response.status === 200 && missingClasses.length === 0;
            this.addTestResult(
                'API Client Validation',
                passed,
                `Status: ${response.status}, Missing classes: ${missingClasses.join(', ') || 'None'}`
            );

            return passed;
        } catch (error) {
            this.addTestResult('API Client Validation', false, 'Failed to validate API client', error);
            return false;
        }
    }

    async validateTestChecklist() {
        try {
            const response = await fetch(`${this.baseURL}/static/api_test_checklist.md`);
            const content = await response.text();

            const requiredSections = [
                'Authentication Tests',
                'Core System Tests',
                'Device Management Tests',
                'Error Handling Tests',
                'Test Completion Checklist'
            ];

            let missingSections = [];
            for (const section of requiredSections) {
                if (!content.includes(section)) {
                    missingSections.push(section);
                }
            }

            const passed = response.status === 200 && missingSections.length === 0;
            this.addTestResult(
                'Test Checklist Validation',
                passed,
                `Status: ${response.status}, Missing sections: ${missingSections.join(', ') || 'None'}`
            );

            return passed;
        } catch (error) {
            this.addTestResult('Test Checklist Validation', false, 'Failed to validate test checklist', error);
            return false;
        }
    }

    async validateDashboard() {
        try {
            const response = await fetch(`${this.baseURL}/static/dashboard.html`);
            const content = await response.text();

            const requiredFeatures = [
                'React',
                'Dashboard',
                'Device',
                'Consciousness',
                'WebSocket',
                'Authentication'
            ];

            let missingFeatures = [];
            for (const feature of requiredFeatures) {
                if (!content.includes(feature)) {
                    missingFeatures.push(feature);
                }
            }

            const passed = response.status === 200 && missingFeatures.length === 0;
            this.addTestResult(
                'Dashboard Validation',
                passed,
                `Status: ${response.status}, Missing features: ${missingFeatures.join(', ') || 'None'}`
            );

            return passed;
        } catch (error) {
            this.addTestResult('Dashboard Validation', false, 'Failed to validate dashboard', error);
            return false;
        }
    }

    // Performance Tests
    async testResponseTimes() {
        const endpoints = [
            '/health',
            '/api',
            '/api/devices',
            '/metrics'
        ];

        let allPassed = true;

        for (const endpoint of endpoints) {
            try {
                const startTime = Date.now();
                const { response } = await this.apiCall(endpoint);
                const responseTime = Date.now() - startTime;

                const passed = response.status === 200 && responseTime < 5000; // 5 second threshold
                allPassed = allPassed && passed;

                this.addTestResult(
                    `Response Time - ${endpoint}`,
                    passed,
                    `${responseTime}ms (threshold: 5000ms)`
                );
            } catch (error) {
                allPassed = false;
                this.addTestResult(`Response Time - ${endpoint}`, false, 'Failed to measure response time', error);
            }
        }

        return allPassed;
    }

    // Error Handling Tests
    async testErrorHandling() {
        try {
            // Test 404 endpoint
            const { response: notFoundResponse } = await this.apiCall('/nonexistent-endpoint');
            const notFoundPassed = notFoundResponse.status === 404;
            this.addTestResult(
                'Error Handling - 404',
                notFoundPassed,
                `Status: ${notFoundResponse.status}`
            );

            // Test invalid device ID
            const { response: invalidDeviceResponse } = await this.apiCall('/api/devices/invalid-id-12345');
            const invalidDevicePassed = invalidDeviceResponse.status === 404;
            this.addTestResult(
                'Error Handling - Invalid Device ID',
                invalidDevicePassed,
                `Status: ${invalidDeviceResponse.status}`
            );

            return notFoundPassed && invalidDevicePassed;
        } catch (error) {
            this.addTestResult('Error Handling Tests', false, 'Failed to test error handling', error);
            return false;
        }
    }

    // Run all tests
    async runAllTests() {
        console.log('🚀 Starting Comprehensive QA Test Suite');
        console.log('=========================================');

        const testStartTime = Date.now();

        // Core API Tests
        await this.testHealthEndpoint();
        await this.testDetailedHealthEndpoint();
        await this.testMetricsEndpoint();
        await this.testDeviceEndpoints();
        await this.testDiscoveryEndpoints();
        await this.testDemoModeEndpoints();

        // UI Component Validation
        await this.validateAPITestingUI();
        await this.validateAPIClient();
        await this.validateTestChecklist();
        await this.validateDashboard();

        // Performance and Error Handling
        await this.testResponseTimes();
        await this.testErrorHandling();

        const testDuration = Date.now() - testStartTime;

        // Generate final report
        const report = this.generateFinalReport(testDuration);
        console.log('\n📊 Final Test Report');
        console.log('====================');
        console.log(report);

        return this.testResults;
    }

    generateFinalReport(duration) {
        const passRate = ((this.testResults.passed / this.testResults.total) * 100).toFixed(1);

        return `
Total Tests: ${this.testResults.total}
Passed: ${this.testResults.passed}
Failed: ${this.testResults.failed}
Pass Rate: ${passRate}%
Duration: ${duration}ms

Test Categories:
- Core API Functionality: ✓
- UI Component Validation: ✓
- Performance Testing: ✓
- Error Handling: ✓

Overall Assessment: ${passRate >= 90 ? 'EXCELLENT' : passRate >= 75 ? 'GOOD' : passRate >= 50 ? 'FAIR' : 'NEEDS IMPROVEMENT'}

Failed Tests:
${this.testResults.tests.filter(t => !t.passed).map(t => `- ${t.name}: ${t.error || 'Unknown error'}`).join('\n')}
        `;
    }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = QATestSuite;
}
