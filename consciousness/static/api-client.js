/**
 * Comprehensive API Client for House Consciousness System
 * Provides functions for all available API endpoints with proper error handling
 */

class ConsciousnessAPIClient {
    constructor(baseURL = '', authToken = null) {
        this.baseURL = baseURL;
        this.authToken = authToken;
        this.wsConnection = null;
        this.wsSubscriptions = new Map();
        this.requestInterceptors = [];
        this.responseInterceptors = [];
    }

    // Request configuration
    getHeaders() {
        const headers = {
            'Content-Type': 'application/json',
        };
        if (this.authToken) {
            headers['Authorization'] = `Bearer ${this.authToken}`;
        }
        return headers;
    }

    // Base request method with interceptors
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: this.getHeaders(),
            ...options,
        };

        // Apply request interceptors
        for (const interceptor of this.requestInterceptors) {
            await interceptor(config);
        }

        try {
            const response = await fetch(url, config);

            // Apply response interceptors
            for (const interceptor of this.responseInterceptors) {
                await interceptor(response);
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new APIError(
                    response.status,
                    errorData.error?.message || response.statusText,
                    errorData.error
                );
            }

            return await response.json();
        } catch (error) {
            if (error instanceof APIError) throw error;
            throw new APIError(0, error.message, { networkError: true });
        }
    }

    // Authentication endpoints
    async login(username, password) {
        const response = await this.request('/api/v1/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password }),
        });
        this.authToken = response.access_token;
        return response;
    }

    async logout() {
        this.authToken = null;
        if (this.wsConnection) {
            this.wsConnection.close();
        }
    }

    // Consciousness endpoints
    async getConsciousnessStatus() {
        return this.request('/api/v1/consciousness/status');
    }

    async getEmotions(timeRange = '1h', includeHistory = true) {
        const params = new URLSearchParams({
            time_range: timeRange,
            include_history: includeHistory,
        });
        return this.request(`/api/v1/consciousness/emotions?${params}`);
    }

    async queryConsciousness(query, context = {}, includeDevices = true) {
        return this.request('/api/v1/consciousness/query', {
            method: 'POST',
            body: JSON.stringify({
                query,
                context,
                include_devices: includeDevices,
            }),
        });
    }

    // Device endpoints
    async getDevices(filters = {}) {
        const params = new URLSearchParams();
        if (filters.status) params.append('status', filters.status);
        if (filters.location) params.append('location', filters.location);
        if (filters.device_type) params.append('device_type', filters.device_type);

        return this.request(`/api/v1/devices?${params}`);
    }

    async getDevice(deviceId) {
        return this.request(`/api/v1/devices/${deviceId}`);
    }

    async controlDevice(deviceId, action, value = null, transitionTime = null) {
        return this.request(`/api/v1/devices/${deviceId}/control`, {
            method: 'PUT',
            body: JSON.stringify({
                action,
                value,
                transition_time: transitionTime,
            }),
        });
    }

    async batchControlDevices(devices) {
        return this.request('/api/v1/devices/batch-control', {
            method: 'POST',
            body: JSON.stringify({ devices }),
        });
    }

    // Memory endpoints
    async getMemory(memoryType = null, timeRange = '7d', limit = 10) {
        const params = new URLSearchParams({
            time_range: timeRange,
            limit: limit,
        });
        if (memoryType) params.append('memory_type', memoryType);

        return this.request(`/api/v1/memory?${params}`);
    }

    async storeMemory(type, content, context = {}) {
        return this.request('/api/v1/memory', {
            method: 'POST',
            body: JSON.stringify({ type, content, context }),
        });
    }

    // Interview endpoints
    async startInterview(houseId) {
        return this.request('/api/v1/interview/start', {
            method: 'POST',
            body: JSON.stringify({ house_id: houseId }),
        });
    }

    async sendInterviewMessage(interviewId, message) {
        return this.request(`/api/v1/interview/${interviewId}/message`, {
            method: 'POST',
            body: JSON.stringify({ message }),
        });
    }

    async getInterviewStatus(interviewId) {
        return this.request(`/api/v1/interview/${interviewId}/status`);
    }

    async confirmInterviewCandidates(interviewId, confirmedCandidates) {
        return this.request(`/api/v1/interview/${interviewId}/confirm`, {
            method: 'POST',
            body: JSON.stringify({ confirmed_candidates: confirmedCandidates }),
        });
    }

    // Discovery endpoints
    async startDiscoveryScan(protocols = ['mdns', 'upnp', 'bluetooth'], timeoutSeconds = 30) {
        return this.request('/api/v1/discovery/scan', {
            method: 'POST',
            body: JSON.stringify({
                protocols,
                timeout_seconds: timeoutSeconds,
            }),
        });
    }

    async getDiscoveryResults(scanId) {
        return this.request(`/api/v1/discovery/scan/${scanId}`);
    }

    // Integration endpoints
    async getIntegrationTemplates(brand = null, deviceClass = null) {
        const params = new URLSearchParams();
        if (brand) params.append('brand', brand);
        if (deviceClass) params.append('device_class', deviceClass);

        return this.request(`/api/v1/integrations/templates?${params}`);
    }

    async classifyDevice(description, context = {}) {
        return this.request('/api/v1/integrations/classify', {
            method: 'POST',
            body: JSON.stringify({ description, context }),
        });
    }

    // SAFLA Loop endpoints
    async getSAFLAStatus() {
        return this.request('/api/v1/safla/status');
    }

    async triggerSAFLALoop(loopId, parameters = {}) {
        return this.request('/api/v1/safla/trigger', {
            method: 'POST',
            body: JSON.stringify({
                loop_id: loopId,
                parameters,
            }),
        });
    }

    // Digital Twin endpoints
    async getDigitalTwins(filters = {}) {
        const params = new URLSearchParams();
        if (filters.device_id) params.append('device_id', filters.device_id);
        if (filters.sync_status) params.append('sync_status', filters.sync_status);
        if (filters.fidelity_level) params.append('fidelity_level', filters.fidelity_level);

        return this.request(`/api/v1/twins?${params}`);
    }

    async createDigitalTwin(deviceId, fidelityLevel = 'advanced', config = {}) {
        return this.request('/api/v1/twins', {
            method: 'POST',
            body: JSON.stringify({
                device_id: deviceId,
                fidelity_level: fidelityLevel,
                config,
            }),
        });
    }

    async getDigitalTwin(twinId) {
        return this.request(`/api/v1/twins/${twinId}`);
    }

    async updateDigitalTwin(twinId, updates) {
        return this.request(`/api/v1/twins/${twinId}`, {
            method: 'PUT',
            body: JSON.stringify(updates),
        });
    }

    async syncDigitalTwin(twinId) {
        return this.request(`/api/v1/twins/${twinId}/sync`, {
            method: 'POST',
        });
    }

    // Scenario endpoints
    async createScenario(name, description, duration, events, twinIds) {
        return this.request('/api/v1/scenarios', {
            method: 'POST',
            body: JSON.stringify({
                name,
                description,
                duration,
                events,
                twin_ids: twinIds,
            }),
        });
    }

    async getScenarios() {
        return this.request('/api/v1/scenarios');
    }

    async getScenario(scenarioId) {
        return this.request(`/api/v1/scenarios/${scenarioId}`);
    }

    async runScenario(scenarioId) {
        return this.request(`/api/v1/scenarios/${scenarioId}/run`, {
            method: 'POST',
        });
    }

    // Prediction endpoints
    async runWhatIfAnalysis(scenario, changes, duration, metrics) {
        return this.request('/api/v1/predictions/what-if', {
            method: 'POST',
            body: JSON.stringify({
                scenario,
                changes,
                duration,
                metrics,
            }),
        });
    }

    async getPredictions(deviceId = null, predictionType = null) {
        const params = new URLSearchParams();
        if (deviceId) params.append('device_id', deviceId);
        if (predictionType) params.append('type', predictionType);

        return this.request(`/api/v1/predictions?${params}`);
    }

    // Health and metrics endpoints
    async getHealth() {
        return this.request('/health');
    }

    async getDetailedHealth() {
        return this.request('/health/detailed');
    }

    async getMetrics() {
        return this.request('/metrics');
    }

    // WebSocket connection management
    connectWebSocket(subscriptions = ['status', 'devices', 'consciousness']) {
        if (this.wsConnection?.readyState === WebSocket.OPEN) {
            return Promise.resolve();
        }

        return new Promise((resolve, reject) => {
            const wsUrl = `${this.baseURL.replace('http', 'ws')}/api/v1/realtime`;
            this.wsConnection = new WebSocket(wsUrl);

            this.wsConnection.onopen = () => {
                // Send initialization message
                this.wsConnection.send(JSON.stringify({
                    type: 'init',
                    data: { subscriptions },
                }));
                resolve();
            };

            this.wsConnection.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    this.handleWebSocketMessage(message);
                } catch (error) {
                    console.error('Failed to parse WebSocket message:', error);
                }
            };

            this.wsConnection.onerror = (error) => {
                console.error('WebSocket error:', error);
                reject(error);
            };

            this.wsConnection.onclose = () => {
                console.log('WebSocket connection closed');
                this.wsConnection = null;
                // Attempt reconnection after 5 seconds
                setTimeout(() => this.connectWebSocket(subscriptions), 5000);
            };
        });
    }

    handleWebSocketMessage(message) {
        const { type, data } = message;

        // Notify all subscribers for this message type
        const subscribers = this.wsSubscriptions.get(type) || [];
        subscribers.forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error(`Error in WebSocket subscriber for ${type}:`, error);
            }
        });
    }

    subscribeToWebSocket(messageType, callback) {
        if (!this.wsSubscriptions.has(messageType)) {
            this.wsSubscriptions.set(messageType, []);
        }
        this.wsSubscriptions.get(messageType).push(callback);

        // Return unsubscribe function
        return () => {
            const subscribers = this.wsSubscriptions.get(messageType);
            const index = subscribers.indexOf(callback);
            if (index > -1) {
                subscribers.splice(index, 1);
            }
        };
    }

    // Utility methods
    addRequestInterceptor(interceptor) {
        this.requestInterceptors.push(interceptor);
    }

    addResponseInterceptor(interceptor) {
        this.responseInterceptors.push(interceptor);
    }

    // Batch operations utility
    async batchRequests(requests) {
        return Promise.all(
            requests.map(req =>
                this.request(req.endpoint, req.options)
                    .catch(error => ({ error, request: req }))
            )
        );
    }
}

// Custom error class for API errors
class APIError extends Error {
    constructor(status, message, details = {}) {
        super(message);
        this.status = status;
        this.details = details;
        this.name = 'APIError';
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ConsciousnessAPIClient, APIError };
}
