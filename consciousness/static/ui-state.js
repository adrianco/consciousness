/**
 * UI State Management for House Consciousness System
 * Manages application state, loading states, and UI updates
 */

class UIStateManager {
    constructor() {
        this.state = new Proxy({}, {
            set: (target, property, value) => {
                target[property] = value;
                this.notifySubscribers(property, value);
                return true;
            }
        });

        this.subscribers = new Map();
        this.loadingStates = new Map();
        this.errorStates = new Map();

        // Initialize default state
        this.initializeState();
    }

    initializeState() {
        this.setState({
            // System state
            consciousness: {
                status: null,
                emotions: null,
                lastQuery: null,
                isActive: false
            },

            // Device state
            devices: {
                list: [],
                currentDevice: null,
                discoveryResults: null,
                lastScanId: null
            },

            // Memory state
            memory: {
                entries: [],
                recentMemories: []
            },

            // Interview state
            interview: {
                currentSession: null,
                messages: [],
                status: null,
                candidates: []
            },

            // SAFLA state
            safla: {
                status: null,
                activeLoops: [],
                lastTrigger: null
            },

            // Digital Twin state
            twins: {
                list: [],
                currentTwin: null,
                scenarios: []
            },

            // Integration state
            integration: {
                templates: [],
                classifications: []
            },

            // WebSocket state
            realtime: {
                connected: false,
                lastMessage: null,
                subscriptions: []
            },

            // UI state
            ui: {
                activeTab: 'dashboard',
                showModal: false,
                modalData: null,
                notifications: []
            }
        });
    }

    // State management
    setState(updates) {
        Object.assign(this.state, updates);
    }

    getState(path = null) {
        if (path) {
            return this.getNestedValue(this.state, path);
        }
        return { ...this.state };
    }

    getNestedValue(obj, path) {
        return path.split('.').reduce((current, key) => current?.[key], obj);
    }

    setNestedValue(obj, path, value) {
        const keys = path.split('.');
        const lastKey = keys.pop();
        const target = keys.reduce((current, key) => {
            if (!current[key]) current[key] = {};
            return current[key];
        }, obj);
        target[lastKey] = value;
    }

    // Subscription management
    subscribe(statePath, callback) {
        if (!this.subscribers.has(statePath)) {
            this.subscribers.set(statePath, []);
        }
        this.subscribers.get(statePath).push(callback);

        // Return unsubscribe function
        return () => {
            const callbacks = this.subscribers.get(statePath);
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        };
    }

    notifySubscribers(property, value) {
        // Notify exact path subscribers
        const subscribers = this.subscribers.get(property) || [];
        subscribers.forEach(callback => {
            try {
                callback(value, property);
            } catch (error) {
                console.error(`Error in state subscriber for ${property}:`, error);
            }
        });

        // Notify wildcard subscribers
        const wildcardSubscribers = this.subscribers.get('*') || [];
        wildcardSubscribers.forEach(callback => {
            try {
                callback(value, property);
            } catch (error) {
                console.error(`Error in wildcard state subscriber:`, error);
            }
        });
    }

    // Loading state management
    setLoading(operation, isLoading) {
        this.loadingStates.set(operation, isLoading);
        this.notifySubscribers('loading', { operation, isLoading });
        this.updateLoadingUI(operation, isLoading);
    }

    isLoading(operation) {
        return this.loadingStates.get(operation) || false;
    }

    // Error state management
    setError(operation, error) {
        this.errorStates.set(operation, error);
        this.notifySubscribers('error', { operation, error });
        if (error) {
            this.showNotification(`Error in ${operation}: ${error.message}`, 'error');
        }
    }

    getError(operation) {
        return this.errorStates.get(operation);
    }

    clearError(operation) {
        this.errorStates.delete(operation);
        this.notifySubscribers('error', { operation, error: null });
    }

    // UI helpers
    updateLoadingUI(operation, isLoading) {
        // Update loading indicators in UI
        const loadingElement = document.getElementById(`loading-${operation}`);
        if (loadingElement) {
            loadingElement.style.display = isLoading ? 'block' : 'none';
        }

        // Disable/enable related buttons
        const buttons = document.querySelectorAll(`[data-operation="${operation}"]`);
        buttons.forEach(button => {
            button.disabled = isLoading;
            if (isLoading) {
                button.classList.add('loading');
            } else {
                button.classList.remove('loading');
            }
        });
    }

    // Notification system
    showNotification(message, type = 'info', duration = 5000) {
        const notification = {
            id: Date.now(),
            message,
            type,
            timestamp: new Date().toISOString()
        };

        const notifications = [...this.state.ui.notifications, notification];
        this.setNestedValue(this.state, 'ui.notifications', notifications);

        this.renderNotification(notification);

        if (duration > 0) {
            setTimeout(() => {
                this.removeNotification(notification.id);
            }, duration);
        }

        return notification.id;
    }

    removeNotification(id) {
        const notifications = this.state.ui.notifications.filter(n => n.id !== id);
        this.setNestedValue(this.state, 'ui.notifications', notifications);

        const element = document.getElementById(`notification-${id}`);
        if (element) {
            element.remove();
        }
    }

    renderNotification(notification) {
        const container = document.getElementById('notifications-container') || this.createNotificationsContainer();

        const element = document.createElement('div');
        element.id = `notification-${notification.id}`;
        element.className = `notification notification-${notification.type}`;
        element.innerHTML = `
            <div class="notification-content">
                <span class="notification-message">${notification.message}</span>
                <button class="notification-close" onclick="uiState.removeNotification(${notification.id})">×</button>
            </div>
        `;

        container.appendChild(element);

        // Animate in
        setTimeout(() => element.classList.add('notification-show'), 10);
    }

    createNotificationsContainer() {
        const container = document.createElement('div');
        container.id = 'notifications-container';
        container.className = 'notifications-container';
        document.body.appendChild(container);
        return container;
    }

    // Modal management
    showModal(title, content, actions = []) {
        this.setNestedValue(this.state, 'ui.showModal', true);
        this.setNestedValue(this.state, 'ui.modalData', { title, content, actions });
        this.renderModal();
    }

    hideModal() {
        this.setNestedValue(this.state, 'ui.showModal', false);
        this.setNestedValue(this.state, 'ui.modalData', null);
        const modal = document.getElementById('modal-overlay');
        if (modal) {
            modal.remove();
        }
    }

    renderModal() {
        const { title, content, actions } = this.state.ui.modalData;

        const overlay = document.createElement('div');
        overlay.id = 'modal-overlay';
        overlay.className = 'modal-overlay';
        overlay.innerHTML = `
            <div class="modal">
                <div class="modal-header">
                    <h3>${title}</h3>
                    <button class="modal-close" onclick="uiState.hideModal()">×</button>
                </div>
                <div class="modal-body">
                    ${content}
                </div>
                <div class="modal-footer">
                    ${actions.map(action =>
                        `<button class="btn ${action.class || 'btn-secondary'}" onclick="${action.onclick}">${action.text}</button>`
                    ).join('')}
                </div>
            </div>
        `;

        document.body.appendChild(overlay);
    }

    // Tab navigation
    setActiveTab(tabId) {
        this.setNestedValue(this.state, 'ui.activeTab', tabId);
        this.updateTabUI(tabId);
    }

    updateTabUI(activeTabId) {
        // Update tab buttons
        document.querySelectorAll('.tab-button').forEach(button => {
            button.classList.remove('active');
        });

        const activeButton = document.querySelector(`[data-tab="${activeTabId}"]`);
        if (activeButton) {
            activeButton.classList.add('active');
        }

        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.style.display = 'none';
        });

        const activeContent = document.getElementById(`${activeTabId}-tab`);
        if (activeContent) {
            activeContent.style.display = 'block';
        }
    }

    // Data update helpers
    updateConsciousnessStatus(status) {
        this.setNestedValue(this.state, 'consciousness.status', status);
        this.setNestedValue(this.state, 'consciousness.isActive', status?.status === 'active');
    }

    updateDevices(devices) {
        this.setNestedValue(this.state, 'devices.list', devices);
    }

    addDevice(device) {
        const devices = [...this.state.devices.list, device];
        this.setNestedValue(this.state, 'devices.list', devices);
    }

    updateDevice(deviceId, updates) {
        const devices = this.state.devices.list.map(device =>
            device.id === deviceId ? { ...device, ...updates } : device
        );
        this.setNestedValue(this.state, 'devices.list', devices);
    }

    addMemory(memory) {
        const memories = [memory, ...this.state.memory.entries];
        this.setNestedValue(this.state, 'memory.entries', memories);
    }

    updateInterview(sessionId, updates) {
        if (this.state.interview.currentSession?.interview_id === sessionId) {
            const currentSession = { ...this.state.interview.currentSession, ...updates };
            this.setNestedValue(this.state, 'interview.currentSession', currentSession);
        }
    }

    addInterviewMessage(message) {
        const messages = [...this.state.interview.messages, message];
        this.setNestedValue(this.state, 'interview.messages', messages);
    }

    updateTwins(twins) {
        this.setNestedValue(this.state, 'twins.list', twins);
    }

    addTwin(twin) {
        const twins = [...this.state.twins.list, twin];
        this.setNestedValue(this.state, 'twins.list', twins);
    }

    // Real-time update handlers
    handleRealtimeUpdate(type, data) {
        this.setNestedValue(this.state, 'realtime.lastMessage', { type, data, timestamp: new Date() });

        switch (type) {
            case 'consciousness_query':
                this.setNestedValue(this.state, 'consciousness.lastQuery', data);
                break;

            case 'device_update':
                this.updateDevice(data.device_id, { last_action: data });
                break;

            case 'batch_device_update':
                data.results?.forEach((result, index) => {
                    const command = data.commands[index];
                    if (command?.device_id) {
                        this.updateDevice(command.device_id, { last_batch_action: result });
                    }
                });
                break;

            case 'interview_update':
                this.updateInterview(data.interview_id, { last_event: data });
                break;

            case 'status_update':
                if (data.consciousness) {
                    this.updateConsciousnessStatus(data.consciousness);
                }
                if (data.devices) {
                    this.setNestedValue(this.state, 'devices.stats', data.devices);
                }
                break;
        }

        this.showNotification(`Real-time update: ${type}`, 'info', 3000);
    }

    // Utility methods
    formatDateTime(timestamp) {
        return new Date(timestamp).toLocaleString();
    }

    formatDuration(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;

        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }

    formatFileSize(bytes) {
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        if (bytes === 0) return '0 Bytes';
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UIStateManager;
}
