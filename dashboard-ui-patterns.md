# House Consciousness Dashboard UI Patterns & Code Examples

## Component Interaction Patterns

### 1. Tab Navigation Pattern

```javascript
// Tab switching with lazy loading and state preservation
const TabContent = React.memo(({ activeTab }) => {
  return (
    <>
      {/* Render all tabs but only display active one */}
      <div style={{display: activeTab === 'consciousness' ? 'block' : 'none'}}>
        <ConsciousnessTab />
      </div>
      <div style={{display: activeTab === 'devices' ? 'block' : 'none'}}>
        <DeviceManager />
      </div>
      {/* ... other tabs */}
    </>
  );
});

// Navigation handler with analytics
const handleTabChange = (tabId) => {
  // Track tab change
  analytics.track('tab_changed', { from: activeTab, to: tabId });
  
  // Update UI state
  setActiveTab(tabId);
  
  // Persist preference
  localStorage.setItem('lastActiveTab', tabId);
};
```

### 2. Real-time Chat Pattern

```javascript
// Chat component with auto-scroll and loading states
const ConsciousnessChat = () => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  
  // Auto-scroll to latest message
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  const sendMessage = async (e) => {
    e.preventDefault();
    const input = e.target.elements.message;
    const message = input.value.trim();
    
    if (!message || loading) return;
    
    // Optimistic UI update
    const userMessage = { 
      id: Date.now(), 
      type: 'user', 
      content: message,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    input.value = '';
    setLoading(true);
    
    try {
      const response = await apiCall('/api/consciousness/query', {
        method: 'POST',
        body: JSON.stringify({ query: message })
      });
      
      setMessages(prev => [...prev, {
        id: Date.now(),
        type: 'system',
        content: response.answer,
        timestamp: new Date()
      }]);
    } catch (error) {
      setMessages(prev => [...prev, {
        id: Date.now(),
        type: 'error',
        content: 'Failed to get response. Please try again.',
        timestamp: new Date()
      }]);
    } finally {
      setLoading(false);
      input.focus();
    }
  };
  
  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.map(msg => (
          <ChatMessage key={msg.id} {...msg} />
        ))}
        {loading && <TypingIndicator />}
        <div ref={messagesEndRef} />
      </div>
      <ChatInput onSubmit={sendMessage} disabled={loading} />
    </div>
  );
};
```

### 3. Device Control Pattern

```javascript
// Device card with optimistic updates
const DeviceCard = ({ device, onUpdate }) => {
  const [localState, setLocalState] = useState(device.state);
  const [updating, setUpdating] = useState(false);
  
  const handleControl = async (action, value) => {
    // Optimistic update
    const previousState = localState;
    setLocalState({ ...localState, [action]: value });
    setUpdating(true);
    
    try {
      const result = await apiCall(`/api/devices/${device.id}`, {
        method: 'PUT',
        body: JSON.stringify({ action, value })
      });
      
      // Update parent component
      onUpdate(device.id, result);
    } catch (error) {
      // Rollback on error
      setLocalState(previousState);
      showNotification('Failed to control device', 'error');
    } finally {
      setUpdating(false);
    }
  };
  
  return (
    <div className={`device-card ${updating ? 'updating' : ''}`}>
      <DeviceHeader device={device} state={localState} />
      <DeviceControls 
        onControl={handleControl}
        disabled={updating}
        state={localState}
      />
    </div>
  );
};
```

### 4. Batch Operations Pattern

```javascript
// Batch device control with progress tracking
const BatchDeviceControl = ({ devices }) => {
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 0 });
  
  const handleBatchAction = async (action) => {
    if (selectedIds.size === 0) {
      showNotification('Please select devices first', 'warning');
      return;
    }
    
    setProcessing(true);
    setProgress({ current: 0, total: selectedIds.size });
    
    const commands = Array.from(selectedIds).map(id => ({
      device_id: id,
      action: action,
      value: action === 'turn_on'
    }));
    
    try {
      // Process in chunks for better UX
      const chunkSize = 5;
      for (let i = 0; i < commands.length; i += chunkSize) {
        const chunk = commands.slice(i, i + chunkSize);
        
        await apiCall('/api/devices/batch-control', {
          method: 'POST',
          body: JSON.stringify({ devices: chunk })
        });
        
        setProgress({ 
          current: Math.min(i + chunkSize, commands.length), 
          total: selectedIds.size 
        });
      }
      
      showNotification(`${selectedIds.size} devices updated`, 'success');
      setSelectedIds(new Set());
    } catch (error) {
      showNotification('Batch operation failed', 'error');
    } finally {
      setProcessing(false);
      setProgress({ current: 0, total: 0 });
    }
  };
  
  return (
    <div className="batch-controls">
      {processing && (
        <ProgressBar 
          value={progress.current} 
          max={progress.total}
          label={`Processing ${progress.current}/${progress.total}`}
        />
      )}
      <BatchActionButtons 
        onAction={handleBatchAction}
        disabled={processing || selectedIds.size === 0}
        selectedCount={selectedIds.size}
      />
    </div>
  );
};
```

### 5. Form Wizard Pattern

```javascript
// Multi-step interview wizard with validation
const InterviewWizard = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [responses, setResponses] = useState({});
  const [validationErrors, setValidationErrors] = useState({});
  
  const steps = [
    { id: 'intro', component: IntroStep },
    { id: 'devices', component: DeviceListStep },
    { id: 'preferences', component: PreferencesStep },
    { id: 'confirm', component: ConfirmationStep }
  ];
  
  const validateStep = (stepId, data) => {
    const validators = {
      devices: (data) => {
        if (!data.devices || data.devices.length === 0) {
          return { devices: 'Please add at least one device' };
        }
        return {};
      },
      preferences: (data) => {
        const errors = {};
        if (!data.wakeTime) errors.wakeTime = 'Wake time is required';
        if (!data.sleepTime) errors.sleepTime = 'Sleep time is required';
        return errors;
      }
    };
    
    return validators[stepId] ? validators[stepId](data) : {};
  };
  
  const handleNext = async () => {
    const currentStepId = steps[currentStep].id;
    const errors = validateStep(currentStepId, responses[currentStepId]);
    
    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors);
      return;
    }
    
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
      setValidationErrors({});
    } else {
      await submitInterview();
    }
  };
  
  const StepComponent = steps[currentStep].component;
  
  return (
    <div className="interview-wizard">
      <WizardProgress 
        steps={steps} 
        currentStep={currentStep}
      />
      <StepComponent
        data={responses[steps[currentStep].id] || {}}
        onChange={(data) => setResponses({
          ...responses,
          [steps[currentStep].id]: data
        })}
        errors={validationErrors}
      />
      <WizardNavigation
        onPrevious={() => setCurrentStep(Math.max(0, currentStep - 1))}
        onNext={handleNext}
        canGoBack={currentStep > 0}
        canGoForward={currentStep < steps.length - 1}
        isLastStep={currentStep === steps.length - 1}
      />
    </div>
  );
};
```

### 6. Discovery Scanner Pattern

```javascript
// Network discovery with real-time updates
const DiscoveryScanner = () => {
  const [scanning, setScanning] = useState(false);
  const [protocols, setProtocols] = useState(['mdns', 'upnp']);
  const [discoveries, setDiscoveries] = useState({});
  const [scanProgress, setScanProgress] = useState({});
  
  const startScan = async () => {
    setScanning(true);
    setDiscoveries({});
    setScanProgress(
      protocols.reduce((acc, p) => ({ ...acc, [p]: 'scanning' }), {})
    );
    
    try {
      const { scan_id } = await apiCall('/api/discovery/scan', {
        method: 'POST',
        body: JSON.stringify({ protocols, timeout_seconds: 30 })
      });
      
      // Poll for results
      const pollInterval = setInterval(async () => {
        const results = await apiCall(`/api/discovery/scan/${scan_id}`);
        
        // Update progress for each protocol
        Object.entries(results.protocol_status).forEach(([protocol, status]) => {
          setScanProgress(prev => ({ ...prev, [protocol]: status }));
        });
        
        // Update discoveries
        setDiscoveries(results.results);
        
        if (results.status === 'completed') {
          clearInterval(pollInterval);
          setScanning(false);
        }
      }, 2000);
      
      // Timeout after 35 seconds
      setTimeout(() => {
        clearInterval(pollInterval);
        setScanning(false);
      }, 35000);
      
    } catch (error) {
      showNotification('Discovery scan failed', 'error');
      setScanning(false);
    }
  };
  
  return (
    <div className="discovery-scanner">
      <ProtocolSelector
        protocols={protocols}
        onChange={setProtocols}
        disabled={scanning}
      />
      
      <button 
        onClick={startScan} 
        disabled={scanning || protocols.length === 0}
        className="btn btn-primary"
      >
        {scanning ? 'Scanning...' : 'Start Discovery'}
      </button>
      
      {scanning && (
        <div className="scan-progress">
          {protocols.map(protocol => (
            <ProtocolProgress
              key={protocol}
              protocol={protocol}
              status={scanProgress[protocol]}
            />
          ))}
        </div>
      )}
      
      <DiscoveryResults 
        discoveries={discoveries}
        onAddDevice={(device) => handleAddDevice(device)}
      />
    </div>
  );
};
```

### 7. Memory Management Pattern

```javascript
// Memory interface with search and filtering
const MemoryInterface = () => {
  const [memories, setMemories] = useState([]);
  const [filter, setFilter] = useState({ type: 'all', timeRange: '7d' });
  const [searchQuery, setSearchQuery] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  
  const filteredMemories = useMemo(() => {
    return memories
      .filter(m => filter.type === 'all' || m.type === filter.type)
      .filter(m => {
        if (!searchQuery) return true;
        return m.content.toLowerCase().includes(searchQuery.toLowerCase());
      })
      .filter(m => {
        const age = Date.now() - new Date(m.timestamp).getTime();
        const ranges = {
          '1d': 24 * 60 * 60 * 1000,
          '7d': 7 * 24 * 60 * 60 * 1000,
          '30d': 30 * 24 * 60 * 60 * 1000,
          'all': Infinity
        };
        return age <= ranges[filter.timeRange];
      });
  }, [memories, filter, searchQuery]);
  
  const handleAddMemory = async (memory) => {
    try {
      const result = await apiCall('/api/memory', {
        method: 'POST',
        body: JSON.stringify(memory)
      });
      
      setMemories([result, ...memories]);
      setShowAddForm(false);
      showNotification('Memory stored successfully', 'success');
    } catch (error) {
      showNotification('Failed to store memory', 'error');
    }
  };
  
  return (
    <div className="memory-interface">
      <MemoryToolbar
        onAdd={() => setShowAddForm(true)}
        onSearch={setSearchQuery}
        filter={filter}
        onFilterChange={setFilter}
      />
      
      {showAddForm && (
        <MemoryForm
          onSubmit={handleAddMemory}
          onCancel={() => setShowAddForm(false)}
        />
      )}
      
      <MemoryList
        memories={filteredMemories}
        onDelete={(id) => handleDeleteMemory(id)}
        emptyMessage="No memories match your filters"
      />
    </div>
  );
};
```

### 8. WebSocket Integration Pattern

```javascript
// WebSocket manager with reconnection logic
const useWebSocket = (url) => {
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttempts = useRef(0);
  
  const connect = useCallback(() => {
    try {
      wsRef.current = new WebSocket(url);
      
      wsRef.current.onopen = () => {
        setConnected(true);
        reconnectAttempts.current = 0;
        
        // Subscribe to updates
        wsRef.current.send(JSON.stringify({
          type: 'subscribe',
          channels: ['consciousness', 'devices', 'safla']
        }));
      };
      
      wsRef.current.onmessage = (event) => {
        const message = JSON.parse(event.data);
        setLastMessage(message);
        
        // Handle different message types
        switch (message.type) {
          case 'device_update':
            updateDeviceState(message.data);
            break;
          case 'consciousness_event':
            updateConsciousnessState(message.data);
            break;
          case 'notification':
            showNotification(message.data.message, message.data.level);
            break;
        }
      };
      
      wsRef.current.onclose = () => {
        setConnected(false);
        
        // Exponential backoff reconnection
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
        reconnectAttempts.current++;
        
        reconnectTimeoutRef.current = setTimeout(connect, delay);
      };
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }
  }, [url]);
  
  useEffect(() => {
    connect();
    
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);
  
  const sendMessage = useCallback((message) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);
  
  return { connected, lastMessage, sendMessage };
};
```

### 9. Digital Twin Management Pattern

```javascript
// Digital twin interface with real-time sync
const DigitalTwinManager = () => {
  const [twins, setTwins] = useState([]);
  const [syncStatus, setSyncStatus] = useState({});
  const { lastMessage } = useWebSocket(WS_URL);
  
  // Handle real-time twin updates
  useEffect(() => {
    if (lastMessage?.type === 'twin_sync') {
      const { twin_id, status, data } = lastMessage.data;
      
      setSyncStatus(prev => ({
        ...prev,
        [twin_id]: status
      }));
      
      if (status === 'completed') {
        setTwins(prev => prev.map(twin => 
          twin.id === twin_id 
            ? { ...twin, ...data, last_sync: new Date() }
            : twin
        ));
      }
    }
  }, [lastMessage]);
  
  const createTwin = async (deviceId, config) => {
    try {
      const twin = await apiCall('/api/twins', {
        method: 'POST',
        body: JSON.stringify({
          device_id: deviceId,
          fidelity_level: config.fidelity,
          config: config.parameters
        })
      });
      
      setTwins([...twins, twin]);
      showNotification('Digital twin created', 'success');
      
      // Trigger initial sync
      syncTwin(twin.id);
    } catch (error) {
      showNotification('Failed to create twin', 'error');
    }
  };
  
  const syncTwin = async (twinId) => {
    setSyncStatus(prev => ({ ...prev, [twinId]: 'syncing' }));
    
    try {
      await apiCall(`/api/twins/${twinId}/sync`, {
        method: 'POST'
      });
    } catch (error) {
      setSyncStatus(prev => ({ ...prev, [twinId]: 'error' }));
      showNotification('Sync failed', 'error');
    }
  };
  
  return (
    <div className="twin-manager">
      <TwinOverview 
        totalTwins={twins.length}
        syncedCount={twins.filter(t => t.sync_status === 'synchronized').length}
      />
      
      <TwinGrid>
        {twins.map(twin => (
          <TwinCard
            key={twin.id}
            twin={twin}
            syncStatus={syncStatus[twin.id]}
            onSync={() => syncTwin(twin.id)}
            onConfigure={(config) => configureTwin(twin.id, config)}
          />
        ))}
      </TwinGrid>
      
      <CreateTwinButton onClick={() => showTwinWizard()} />
    </div>
  );
};
```

### 10. Scenario Builder Pattern

```javascript
// What-if scenario analysis
const ScenarioBuilder = () => {
  const [scenario, setScenario] = useState({
    name: '',
    conditions: [],
    duration: '1h',
    metrics: ['energy_usage', 'comfort_level']
  });
  const [analysis, setAnalysis] = useState(null);
  const [running, setRunning] = useState(false);
  
  const addCondition = (condition) => {
    setScenario(prev => ({
      ...prev,
      conditions: [...prev.conditions, {
        id: Date.now(),
        ...condition
      }]
    }));
  };
  
  const runAnalysis = async () => {
    setRunning(true);
    setAnalysis(null);
    
    try {
      const result = await apiCall('/api/predictions/what-if', {
        method: 'POST',
        body: JSON.stringify(scenario)
      });
      
      setAnalysis(result);
      
      // Animate results
      animateMetrics(result.metrics);
    } catch (error) {
      showNotification('Analysis failed', 'error');
    } finally {
      setRunning(false);
    }
  };
  
  const animateMetrics = (metrics) => {
    Object.entries(metrics).forEach(([key, value], index) => {
      setTimeout(() => {
        const element = document.getElementById(`metric-${key}`);
        if (element) {
          element.classList.add('metric-animate');
          element.textContent = value;
        }
      }, index * 200);
    });
  };
  
  return (
    <div className="scenario-builder">
      <ScenarioForm
        scenario={scenario}
        onChange={setScenario}
        onAddCondition={addCondition}
      />
      
      <ConditionList
        conditions={scenario.conditions}
        onRemove={(id) => removeCondition(id)}
        onEdit={(id, updates) => updateCondition(id, updates)}
      />
      
      <AnalysisControls
        onRun={runAnalysis}
        running={running}
        canRun={scenario.conditions.length > 0}
      />
      
      {analysis && (
        <AnalysisResults
          results={analysis}
          onExport={() => exportResults(analysis)}
          onSaveScenario={() => saveScenario(scenario, analysis)}
        />
      )}
    </div>
  );
};
```

## Error Boundary Implementation

```javascript
// Global error boundary with recovery options
class DashboardErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null,
      errorCount: 0
    };
  }
  
  static getDerivedStateFromError(error) {
    return { 
      hasError: true, 
      error,
      errorCount: (state.errorCount || 0) + 1
    };
  }
  
  componentDidCatch(error, errorInfo) {
    // Log to error tracking service
    console.error('Dashboard Error:', error, errorInfo);
    
    // Send error telemetry
    if (window.analytics) {
      window.analytics.track('error_boundary_triggered', {
        error: error.toString(),
        componentStack: errorInfo.componentStack,
        errorCount: this.state.errorCount
      });
    }
  }
  
  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };
  
  handleHardReset = () => {
    localStorage.clear();
    window.location.reload();
  };
  
  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary-fallback">
          <div className="error-content">
            <h2>Something went wrong</h2>
            <p>The dashboard encountered an unexpected error.</p>
            
            {this.state.errorCount > 3 && (
              <div className="alert alert-warning">
                Multiple errors detected. Consider clearing your data.
              </div>
            )}
            
            <details className="error-details">
              <summary>Error Details</summary>
              <pre>{this.state.error?.stack}</pre>
            </details>
            
            <div className="error-actions">
              <button 
                onClick={this.handleReset}
                className="btn btn-primary"
              >
                Try Again
              </button>
              
              <button 
                onClick={this.handleHardReset}
                className="btn btn-secondary"
              >
                Reset Everything
              </button>
              
              <button 
                onClick={() => window.location.href = '/'}
                className="btn btn-secondary"
              >
                Go Home
              </button>
            </div>
          </div>
        </div>
      );
    }
    
    return this.props.children;
  }
}
```

## Performance Monitoring

```javascript
// Performance observer for UI metrics
const usePerformanceMonitoring = () => {
  useEffect(() => {
    // First Contentful Paint
    const paintObserver = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.name === 'first-contentful-paint') {
          analytics.track('performance_fcp', {
            duration: entry.startTime
          });
        }
      }
    });
    
    paintObserver.observe({ entryTypes: ['paint'] });
    
    // Long tasks
    const taskObserver = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.duration > 50) {
          console.warn('Long task detected:', entry);
        }
      }
    });
    
    taskObserver.observe({ entryTypes: ['longtask'] });
    
    // Component render times
    if (window.React && window.React.Profiler) {
      window.__REACT_DEVTOOLS_GLOBAL_HOOK__.onCommitFiberRoot = (
        id, root, priorityLevel, didTimeout
      ) => {
        // Track slow renders
        const renderTime = root.actualDuration;
        if (renderTime > 16) {
          console.warn('Slow render detected:', renderTime);
        }
      };
    }
    
    return () => {
      paintObserver.disconnect();
      taskObserver.disconnect();
    };
  }, []);
};
```