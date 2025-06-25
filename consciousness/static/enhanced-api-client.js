/**
 * Enhanced API Client for House Consciousness System
 * Extends the basic API client with enhanced testing, GitHub integration, and comprehensive endpoint coverage
 */

class EnhancedConsciousnessAPIClient extends ConsciousnessAPIClient {
    constructor(baseURL = '', authToken = null) {
        super(baseURL, authToken);
        this.testResults = {
            total: 0,
            tested: 0,
            successful: 0,
            failed: 0,
            results: []
        };
        this.githubConfig = {
            token: localStorage.getItem('github-token') || '',
            repo: localStorage.getItem('github-repo') || '',
            branch: localStorage.getItem('github-branch') || 'main'
        };
        this.testSuite = new APITestSuite(this);
    }

    // Enhanced testing methods
    async runTestSuite(endpoints = null) {
        const defaultEndpoints = [
            'health',
            'consciousness/status',
            'consciousness/emotions',
            'devices',
            'memory',
            'interview/start',
            'discovery/scan',
            'integrations/templates',
            'safla/status',
            'twins'
        ];

        const endpointsToTest = endpoints || defaultEndpoints;
        this.testResults = { total: endpointsToTest.length, tested: 0, successful: 0, failed: 0, results: [] };

        for (const endpoint of endpointsToTest) {
            await this.testEndpoint(endpoint);
            await new Promise(resolve => setTimeout(resolve, 500)); // Rate limiting
        }

        return this.testResults;
    }

    async testEndpoint(endpoint) {
        const startTime = Date.now();
        let result = null;
        let error = null;

        try {
            switch (endpoint) {
                case 'health':
                    result = await this.getHealth();
                    break;
                case 'consciousness/status':
                    result = await this.getConsciousnessStatus();
                    break;
                case 'consciousness/emotions':
                    result = await this.getEmotions('1h', true);
                    break;
                case 'devices':
                    result = await this.getDevices();
                    break;
                case 'memory':
                    result = await this.getMemory(null, '7d', 10);
                    break;
                case 'interview/start':
                    result = await this.startInterview('test_house_' + Date.now());
                    break;
                case 'discovery/scan':
                    result = await this.startDiscoveryScan(['mdns'], 5);
                    break;
                case 'integrations/templates':
                    result = await this.getIntegrationTemplates();
                    break;
                case 'safla/status':
                    result = await this.getSAFLAStatus();
                    break;
                case 'twins':
                    result = await this.getDigitalTwins();
                    break;
                default:
                    throw new Error(`Unknown endpoint: ${endpoint}`);
            }

            this.testResults.successful++;
            this.testResults.results.push({
                endpoint,
                status: 'success',
                timestamp: new Date().toISOString(),
                duration: Date.now() - startTime,
                response: result
            });
        } catch (err) {
            error = err;
            this.testResults.failed++;
            this.testResults.results.push({
                endpoint,
                status: 'failed',
                timestamp: new Date().toISOString(),
                duration: Date.now() - startTime,
                error: err.message
            });
        }

        this.testResults.tested++;
        return { endpoint, status: error ? 'failed' : 'success', result, error };
    }

    // GitHub integration
    async uploadTestResultsToGitHub(commitMessage = 'Update API test results', filePath = 'api-test-results.json') {
        if (!this.githubConfig.token || !this.githubConfig.repo) {
            throw new Error('GitHub configuration not set. Please configure token and repository.');
        }

        const data = {
            summary: this.testResults,
            timestamp: new Date().toISOString(),
            environment: {
                url: window.location.origin,
                userAgent: navigator.userAgent
            },
            version: '1.0.0',
            testSuite: 'enhanced-consciousness-api'
        };

        const response = await fetch(`https://api.github.com/repos/${this.githubConfig.repo}/contents/${filePath}`, {
            method: 'PUT',
            headers: {
                'Authorization': `token ${this.githubConfig.token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: commitMessage,
                content: btoa(JSON.stringify(data, null, 2)),
                branch: this.githubConfig.branch
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(`GitHub upload failed: ${error.message}`);
        }

        return await response.json();
    }

    // Advanced endpoint testing
    async testAllEndpointsWithParameters() {
        const testCases = [
            {
                name: 'Health Check - Basic',
                test: () => this.getHealth()
            },
            {
                name: 'Health Check - Detailed',
                test: () => this.getDetailedHealth()
            },
            {
                name: 'Consciousness Status',
                test: () => this.getConsciousnessStatus()
            },
            {
                name: 'Emotions - 1 hour',
                test: () => this.getEmotions('1h', true)
            },
            {
                name: 'Emotions - 1 day',
                test: () => this.getEmotions('1d', false)
            },
            {
                name: 'Query Consciousness',
                test: () => this.queryConsciousness('How are you feeling?', {}, true)
            },
            {
                name: 'Get All Devices',
                test: () => this.getDevices()
            },
            {
                name: 'Get Active Devices',
                test: () => this.getDevices({ status: 'active' })
            },
            {
                name: 'Get Memory - Recent',
                test: () => this.getMemory(null, '1d', 5)
            },
            {
                name: 'Store Test Memory',
                test: () => this.storeMemory('test', 'API test memory entry', { source: 'enhanced_api_test' })
            },
            {
                name: 'Start Interview',
                test: () => this.startInterview(`test_house_${Date.now()}`)
            },
            {
                name: 'Discovery Scan - mDNS',
                test: () => this.startDiscoveryScan(['mdns'], 10)
            },
            {
                name: 'Integration Templates',
                test: () => this.getIntegrationTemplates()
            },
            {
                name: 'Device Classification',
                test: () => this.classifyDevice('Smart LED bulb with color changing capabilities')
            },
            {
                name: 'SAFLA Status',
                test: () => this.getSAFLAStatus()
            },
            {
                name: 'Digital Twins List',
                test: () => this.getDigitalTwins()
            }
        ];

        const results = [];
        for (const testCase of testCases) {
            const startTime = Date.now();
            try {
                const result = await testCase.test();
                results.push({
                    name: testCase.name,
                    status: 'success',
                    duration: Date.now() - startTime,
                    timestamp: new Date().toISOString(),
                    response: result
                });
            } catch (error) {
                results.push({
                    name: testCase.name,
                    status: 'failed',
                    duration: Date.now() - startTime,
                    timestamp: new Date().toISOString(),
                    error: error.message
                });
            }

            // Rate limiting
            await new Promise(resolve => setTimeout(resolve, 300));
        }

        return {
            total: testCases.length,
            successful: results.filter(r => r.status === 'success').length,
            failed: results.filter(r => r.status === 'failed').length,
            results: results
        };
    }

    // Configuration management
    setGitHubConfig(token, repo, branch = 'main') {
        this.githubConfig = { token, repo, branch };
        localStorage.setItem('github-token', token);
        localStorage.setItem('github-repo', repo);
        localStorage.setItem('github-branch', branch);
    }

    getGitHubConfig() {
        return { ...this.githubConfig };
    }

    // Report generation
    generateTestReport(format = 'markdown') {
        const report = {
            title: 'Enhanced Consciousness API Test Report',
            date: new Date().toISOString(),
            summary: {
                totalTests: this.testResults.tested,
                passed: this.testResults.successful,
                failed: this.testResults.failed,
                passRate: this.testResults.tested > 0 ? ((this.testResults.successful / this.testResults.tested) * 100).toFixed(1) : 0
            },
            environment: {
                url: window.location.origin,
                userAgent: navigator.userAgent,
                timestamp: new Date().toISOString()
            },
            results: this.testResults.results
        };

        switch (format) {
            case 'markdown':
                return this.generateMarkdownReport(report);
            case 'json':
                return JSON.stringify(report, null, 2);
            case 'csv':
                return this.generateCSVReport(report);
            default:
                return report;
        }
    }

    generateMarkdownReport(report) {
        return `# ${report.title}

**Date:** ${new Date(report.date).toLocaleString()}

## Summary

- **Total Tests:** ${report.summary.totalTests}
- **Passed:** ${report.summary.passed}
- **Failed:** ${report.summary.failed}
- **Pass Rate:** ${report.summary.passRate}%

## Environment

- **URL:** ${report.environment.url}
- **User Agent:** ${report.environment.userAgent}
- **Timestamp:** ${report.environment.timestamp}

## Test Results

${report.results.map(result => `
### ${result.endpoint}

- **Status:** ${result.status}
- **Timestamp:** ${result.timestamp}
- **Duration:** ${result.duration}ms
${result.error ? `- **Error:** ${result.error}` : '- **Result:** Success'}
`).join('')}

## Performance Metrics

- **Average Response Time:** ${(report.results.reduce((sum, r) => sum + (r.duration || 0), 0) / report.results.length).toFixed(2)}ms
- **Fastest Response:** ${Math.min(...report.results.map(r => r.duration || 0))}ms
- **Slowest Response:** ${Math.max(...report.results.map(r => r.duration || 0))}ms

---

*Generated by Enhanced Consciousness API Testing Suite*
*Version: 1.0.0*`;
    }

    generateCSVReport(report) {
        const headers = ['Endpoint', 'Status', 'Timestamp', 'Duration (ms)', 'Error'];
        const rows = report.results.map(result => [
            result.endpoint,
            result.status,
            result.timestamp,
            result.duration || 0,
            result.error || ''
        ]);

        return [headers, ...rows].map(row => row.map(field => `"${field}"`).join(',')).join('\n');
    }

    // Download report functionality
    downloadReport(format = 'markdown') {
        const report = this.generateTestReport(format);
        const extensions = { markdown: 'md', json: 'json', csv: 'csv' };
        const mimeTypes = {
            markdown: 'text/markdown',
            json: 'application/json',
            csv: 'text/csv'
        };

        const blob = new Blob([report], { type: mimeTypes[format] });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `consciousness-api-test-report-${new Date().toISOString().split('T')[0]}.${extensions[format]}`;
        a.click();
        URL.revokeObjectURL(url);
    }

    // Real-time testing with WebSocket monitoring
    async runRealTimeTest(duration = 30000) {
        const results = [];
        const startTime = Date.now();

        // Connect to WebSocket for real-time updates
        await this.connectWebSocket();

        const testInterval = setInterval(async () => {
            try {
                const status = await this.getConsciousnessStatus();
                results.push({
                    timestamp: new Date().toISOString(),
                    status: 'success',
                    response: status
                });
            } catch (error) {
                results.push({
                    timestamp: new Date().toISOString(),
                    status: 'failed',
                    error: error.message
                });
            }
        }, 5000);

        // Run for specified duration
        setTimeout(() => {
            clearInterval(testInterval);
        }, duration);

        return {
            duration: duration,
            results: results,
            summary: {
                total: results.length,
                successful: results.filter(r => r.status === 'success').length,
                failed: results.filter(r => r.status === 'failed').length
            }
        };
    }
}

/**
 * API Test Suite for automated testing
 */
class APITestSuite {
    constructor(apiClient) {
        this.client = apiClient;
        this.testCategories = {
            core: ['health', 'consciousness/status'],
            devices: ['devices', 'device-control'],
            memory: ['memory', 'memory-store'],
            interview: ['interview/start', 'interview/message'],
            discovery: ['discovery/scan'],
            integration: ['integrations/templates', 'integrations/classify'],
            safla: ['safla/status'],
            twins: ['twins', 'twin-create'],
            scenarios: ['scenarios', 'predictions/what-if']
        };
    }

    async runCategoryTests(category) {
        if (!this.testCategories[category]) {
            throw new Error(`Unknown test category: ${category}`);
        }

        const endpoints = this.testCategories[category];
        const results = [];

        for (const endpoint of endpoints) {
            const result = await this.client.testEndpoint(endpoint);
            results.push(result);
        }

        return {
            category,
            total: endpoints.length,
            successful: results.filter(r => r.status === 'success').length,
            failed: results.filter(r => r.status === 'failed').length,
            results
        };
    }

    async runAllTests() {
        const categoryResults = {};

        for (const category of Object.keys(this.testCategories)) {
            categoryResults[category] = await this.runCategoryTests(category);
        }

        return categoryResults;
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { EnhancedConsciousnessAPIClient, APITestSuite };
}
