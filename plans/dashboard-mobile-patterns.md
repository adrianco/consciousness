# House Consciousness Dashboard Mobile UI Patterns

## Mobile-First Design Principles

### 1. Touch Target Guidelines

```css
/* Minimum touch target sizes */
.touch-target {
  min-width: 44px;
  min-height: 44px;
  padding: 12px;
  margin: 4px; /* Spacing between targets */
}

/* Expanded hit areas for small elements */
.small-control {
  position: relative;
  padding: 8px;
}

.small-control::before {
  content: '';
  position: absolute;
  top: -10px;
  left: -10px;
  right: -10px;
  bottom: -10px;
  /* Invisible expanded touch area */
}
```

### 2. Responsive Breakpoints

```scss
// Mobile-first breakpoint system
$breakpoints: (
  'phone': 375px,      // iPhone SE/8
  'phablet': 414px,    // iPhone Plus/Pro Max
  'tablet': 768px,     // iPad Portrait
  'desktop': 1024px,   // iPad Landscape+
  'wide': 1400px       // Desktop
);

// Usage
@media (min-width: map-get($breakpoints, 'tablet')) {
  .device-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
```

## Mobile Navigation Patterns

### 1. Bottom Tab Navigation

```javascript
const MobileNavigation = () => {
  const [activeTab, setActiveTab] = useState('consciousness');
  
  // Core tabs for mobile (limit to 5)
  const mobileTabs = [
    { id: 'consciousness', icon: '🏠', label: 'Home' },
    { id: 'devices', icon: '💡', label: 'Devices' },
    { id: 'chat', icon: '💬', label: 'Chat' },
    { id: 'memory', icon: '🧠', label: 'Memory' },
    { id: 'more', icon: '⋯', label: 'More' }
  ];
  
  return (
    <nav className="mobile-nav">
      {mobileTabs.map(tab => (
        <button
          key={tab.id}
          className={`nav-item ${activeTab === tab.id ? 'active' : ''}`}
          onClick={() => setActiveTab(tab.id)}
        >
          <span className="nav-icon">{tab.icon}</span>
          <span className="nav-label">{tab.label}</span>
        </button>
      ))}
    </nav>
  );
};
```

```css
/* Bottom navigation styles */
.mobile-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 56px;
  background: white;
  border-top: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-around;
  align-items: center;
  padding-bottom: env(safe-area-inset-bottom); /* iPhone X+ */
  z-index: 1000;
}

.nav-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px;
  border: none;
  background: none;
  color: #666;
}

.nav-item.active {
  color: #667eea;
}

.nav-icon {
  font-size: 20px;
  margin-bottom: 2px;
}

.nav-label {
  font-size: 10px;
}
```

### 2. Gesture-Based Navigation

```javascript
const SwipeableViews = ({ children, onSwipe }) => {
  const [startX, setStartX] = useState(0);
  const [currentX, setCurrentX] = useState(0);
  const [activeIndex, setActiveIndex] = useState(0);
  
  const handleTouchStart = (e) => {
    setStartX(e.touches[0].clientX);
  };
  
  const handleTouchMove = (e) => {
    setCurrentX(e.touches[0].clientX);
  };
  
  const handleTouchEnd = () => {
    const diff = startX - currentX;
    const threshold = window.innerWidth / 3;
    
    if (Math.abs(diff) > threshold) {
      if (diff > 0 && activeIndex < children.length - 1) {
        // Swipe left - next
        setActiveIndex(activeIndex + 1);
        onSwipe('next');
      } else if (diff < 0 && activeIndex > 0) {
        // Swipe right - previous
        setActiveIndex(activeIndex - 1);
        onSwipe('previous');
      }
    }
    
    setStartX(0);
    setCurrentX(0);
  };
  
  return (
    <div 
      className="swipeable-container"
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      <div 
        className="swipeable-content"
        style={{
          transform: `translateX(${-activeIndex * 100}%)`,
          transition: currentX ? 'none' : 'transform 0.3s'
        }}
      >
        {children}
      </div>
      <div className="swipe-indicators">
        {children.map((_, index) => (
          <span 
            key={index}
            className={`indicator ${index === activeIndex ? 'active' : ''}`}
          />
        ))}
      </div>
    </div>
  );
};
```

## Mobile-Specific Components

### 1. Collapsible Device Cards

```javascript
const MobileDeviceCard = ({ device }) => {
  const [expanded, setExpanded] = useState(false);
  
  return (
    <div className={`mobile-device-card ${expanded ? 'expanded' : ''}`}>
      <div 
        className="device-header"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="device-info">
          <h3>{device.name}</h3>
          <span className="device-location">{device.location}</span>
        </div>
        <div className="device-quick-toggle">
          <Switch
            checked={device.state.on}
            onChange={(checked) => handleQuickToggle(device.id, checked)}
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      </div>
      
      {expanded && (
        <div className="device-controls">
          <DeviceSliders device={device} />
          <DeviceSchedule device={device} />
          <DeviceSettings device={device} />
        </div>
      )}
    </div>
  );
};
```

### 2. Pull-to-Refresh Pattern

```javascript
const PullToRefresh = ({ onRefresh, children }) => {
  const [pullDistance, setPullDistance] = useState(0);
  const [refreshing, setRefreshing] = useState(false);
  const threshold = 80;
  
  const handleTouchStart = (e) => {
    if (window.scrollY === 0) {
      setPullDistance(0);
    }
  };
  
  const handleTouchMove = (e) => {
    if (window.scrollY === 0 && !refreshing) {
      const touch = e.touches[0];
      const distance = Math.max(0, touch.clientY - 50);
      setPullDistance(Math.min(distance, threshold * 1.5));
    }
  };
  
  const handleTouchEnd = async () => {
    if (pullDistance > threshold && !refreshing) {
      setRefreshing(true);
      setPullDistance(threshold);
      
      await onRefresh();
      
      setRefreshing(false);
      setPullDistance(0);
    } else {
      setPullDistance(0);
    }
  };
  
  return (
    <div
      className="pull-to-refresh"
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      <div 
        className="pull-indicator"
        style={{
          transform: `translateY(${pullDistance}px)`,
          opacity: pullDistance / threshold
        }}
      >
        {refreshing ? (
          <Spinner />
        ) : (
          <PullIcon rotation={pullDistance * 3} />
        )}
      </div>
      <div
        className="content"
        style={{
          transform: `translateY(${pullDistance}px)`,
          transition: refreshing ? 'none' : 'transform 0.3s'
        }}
      >
        {children}
      </div>
    </div>
  );
};
```

### 3. Mobile Chat Interface

```javascript
const MobileChatInterface = () => {
  const [keyboardHeight, setKeyboardHeight] = useState(0);
  const [messages, setMessages] = useState([]);
  const inputRef = useRef(null);
  
  useEffect(() => {
    // Handle virtual keyboard on mobile
    const handleResize = () => {
      const visualViewport = window.visualViewport;
      if (visualViewport) {
        const keyboardHeight = window.innerHeight - visualViewport.height;
        setKeyboardHeight(keyboardHeight);
      }
    };
    
    window.visualViewport?.addEventListener('resize', handleResize);
    return () => {
      window.visualViewport?.removeEventListener('resize', handleResize);
    };
  }, []);
  
  return (
    <div 
      className="mobile-chat"
      style={{ paddingBottom: keyboardHeight }}
    >
      <div className="chat-messages">
        {messages.map(msg => (
          <MessageBubble key={msg.id} {...msg} />
        ))}
      </div>
      
      <div className="chat-input-bar">
        <button className="attach-btn">
          <AttachIcon />
        </button>
        <input
          ref={inputRef}
          type="text"
          placeholder="Message..."
          className="chat-input"
          enterKeyHint="send"
        />
        <button className="voice-btn">
          <MicIcon />
        </button>
        <button className="send-btn">
          <SendIcon />
        </button>
      </div>
    </div>
  );
};
```

### 4. Bottom Sheet Pattern

```javascript
const BottomSheet = ({ isOpen, onClose, children, snapPoints = ['25%', '50%', '90%'] }) => {
  const [currentSnap, setCurrentSnap] = useState(1);
  const [dragY, setDragY] = useState(0);
  const sheetRef = useRef(null);
  
  const handleDragStart = (e) => {
    const startY = e.touches[0].clientY;
    let currentY = startY;
    
    const handleDragMove = (e) => {
      currentY = e.touches[0].clientY;
      setDragY(currentY - startY);
    };
    
    const handleDragEnd = () => {
      const threshold = 50;
      
      if (dragY > threshold) {
        // Dragged down
        if (currentSnap < snapPoints.length - 1) {
          setCurrentSnap(currentSnap + 1);
        } else {
          onClose();
        }
      } else if (dragY < -threshold) {
        // Dragged up
        if (currentSnap > 0) {
          setCurrentSnap(currentSnap - 1);
        }
      }
      
      setDragY(0);
      document.removeEventListener('touchmove', handleDragMove);
      document.removeEventListener('touchend', handleDragEnd);
    };
    
    document.addEventListener('touchmove', handleDragMove);
    document.addEventListener('touchend', handleDragEnd);
  };
  
  return (
    <div className={`bottom-sheet-overlay ${isOpen ? 'open' : ''}`} onClick={onClose}>
      <div
        ref={sheetRef}
        className="bottom-sheet"
        style={{
          transform: `translateY(${isOpen ? `calc(100% - ${snapPoints[currentSnap]})` : '100%'})`,
          transition: dragY ? 'none' : 'transform 0.3s'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div 
          className="sheet-handle"
          onTouchStart={handleDragStart}
        >
          <div className="handle-bar" />
        </div>
        <div className="sheet-content">
          {children}
        </div>
      </div>
    </div>
  );
};
```

## Touch Interaction Patterns

### 1. Long Press Actions

```javascript
const useLongPress = (callback, delay = 500) => {
  const [longPressTriggered, setLongPressTriggered] = useState(false);
  const timeout = useRef();
  const target = useRef();
  
  const start = useCallback((e) => {
    if (e.target) {
      target.current = e.target;
      timeout.current = setTimeout(() => {
        callback(e);
        setLongPressTriggered(true);
        
        // Haptic feedback
        if (window.navigator.vibrate) {
          window.navigator.vibrate(50);
        }
      }, delay);
    }
  }, [callback, delay]);
  
  const clear = useCallback((e, shouldTriggerClick = true) => {
    timeout.current && clearTimeout(timeout.current);
    
    if (shouldTriggerClick && !longPressTriggered) {
      target.current?.click();
    }
    
    setLongPressTriggered(false);
  }, [longPressTriggered]);
  
  return {
    onTouchStart: start,
    onTouchEnd: clear,
    onTouchMove: (e) => {
      // Cancel if moved too far
      if (Math.abs(e.touches[0].clientX - e.target.offsetLeft) > 10) {
        clear(e, false);
      }
    }
  };
};

// Usage
const DeviceControl = ({ device }) => {
  const longPressProps = useLongPress(() => {
    showDeviceMenu(device);
  });
  
  return (
    <div className="device-control" {...longPressProps}>
      <DeviceIcon type={device.type} />
      <span>{device.name}</span>
    </div>
  );
};
```

### 2. Swipe Actions

```javascript
const SwipeableListItem = ({ item, onDelete, onEdit }) => {
  const [swipeX, setSwipeX] = useState(0);
  const [swiping, setSwiping] = useState(false);
  const itemRef = useRef(null);
  
  const handleSwipeStart = (e) => {
    const startX = e.touches[0].clientX;
    setSwiping(true);
    
    const handleSwipeMove = (e) => {
      const currentX = e.touches[0].clientX;
      const diff = currentX - startX;
      setSwipeX(Math.max(-200, Math.min(200, diff)));
    };
    
    const handleSwipeEnd = () => {
      setSwiping(false);
      
      if (swipeX < -100) {
        // Swiped left - delete
        onDelete(item.id);
      } else if (swipeX > 100) {
        // Swiped right - edit
        onEdit(item.id);
      }
      
      setSwipeX(0);
      document.removeEventListener('touchmove', handleSwipeMove);
      document.removeEventListener('touchend', handleSwipeEnd);
    };
    
    document.addEventListener('touchmove', handleSwipeMove);
    document.addEventListener('touchend', handleSwipeEnd);
  };
  
  return (
    <div className="swipeable-item" ref={itemRef}>
      <div className="swipe-actions left">
        <button className="edit-action">Edit</button>
      </div>
      
      <div
        className="item-content"
        style={{
          transform: `translateX(${swipeX}px)`,
          transition: swiping ? 'none' : 'transform 0.3s'
        }}
        onTouchStart={handleSwipeStart}
      >
        {item.content}
      </div>
      
      <div className="swipe-actions right">
        <button className="delete-action">Delete</button>
      </div>
    </div>
  );
};
```

## Mobile Performance Optimization

### 1. Virtual Scrolling for Large Lists

```javascript
const VirtualDeviceList = ({ devices, itemHeight = 80 }) => {
  const [scrollTop, setScrollTop] = useState(0);
  const [containerHeight, setContainerHeight] = useState(window.innerHeight);
  const containerRef = useRef(null);
  
  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        setContainerHeight(containerRef.current.clientHeight);
      }
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  
  const handleScroll = (e) => {
    setScrollTop(e.target.scrollTop);
  };
  
  // Calculate visible items
  const startIndex = Math.floor(scrollTop / itemHeight);
  const endIndex = Math.ceil((scrollTop + containerHeight) / itemHeight);
  const visibleDevices = devices.slice(startIndex, endIndex + 1);
  
  return (
    <div 
      ref={containerRef}
      className="virtual-scroll-container"
      onScroll={handleScroll}
    >
      <div 
        className="virtual-scroll-spacer"
        style={{ height: devices.length * itemHeight }}
      />
      <div 
        className="virtual-scroll-content"
        style={{ transform: `translateY(${startIndex * itemHeight}px)` }}
      >
        {visibleDevices.map((device, index) => (
          <MobileDeviceCard
            key={device.id}
            device={device}
            style={{ height: itemHeight }}
          />
        ))}
      </div>
    </div>
  );
};
```

### 2. Optimized Image Loading

```javascript
const LazyDeviceImage = ({ src, alt, placeholder }) => {
  const [imageSrc, setImageSrc] = useState(placeholder);
  const [imageRef, setImageRef] = useState(null);
  
  useEffect(() => {
    if (!imageRef) return;
    
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            // Load low-res first
            const lowResSrc = src.replace('.jpg', '-low.jpg');
            const img = new Image();
            
            img.onload = () => {
              setImageSrc(lowResSrc);
              
              // Then load high-res
              const highResImg = new Image();
              highResImg.onload = () => {
                setImageSrc(src);
              };
              highResImg.src = src;
            };
            
            img.src = lowResSrc;
            observer.unobserve(entry.target);
          }
        });
      },
      { rootMargin: '50px' }
    );
    
    observer.observe(imageRef);
    
    return () => {
      observer.disconnect();
    };
  }, [imageRef, src]);
  
  return (
    <div className="lazy-image-container">
      <img
        ref={setImageRef}
        src={imageSrc}
        alt={alt}
        className={`lazy-image ${imageSrc === placeholder ? 'loading' : ''}`}
      />
    </div>
  );
};
```

## Mobile-Specific Styles

```css
/* iOS Safe Areas */
.mobile-container {
  padding-top: env(safe-area-inset-top);
  padding-left: env(safe-area-inset-left);
  padding-right: env(safe-area-inset-right);
  padding-bottom: calc(56px + env(safe-area-inset-bottom)); /* Nav height + safe area */
}

/* Prevent bounce scrolling on iOS */
.scroll-container {
  -webkit-overflow-scrolling: touch;
  overflow-y: auto;
  overscroll-behavior-y: contain;
}

/* Disable text selection on interactive elements */
.interactive {
  -webkit-user-select: none;
  user-select: none;
  -webkit-touch-callout: none;
}

/* High contrast mode support */
@media (prefers-contrast: high) {
  .device-card {
    border: 2px solid currentColor;
  }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  :root {
    --bg-primary: #1a1a1a;
    --text-primary: #ffffff;
    --border-color: #333333;
  }
}
```

## Offline Support

```javascript
// Service Worker for offline functionality
const CacheStrategy = {
  networkFirst: async (request) => {
    try {
      const response = await fetch(request);
      const cache = await caches.open('v1');
      cache.put(request, response.clone());
      return response;
    } catch (error) {
      return caches.match(request);
    }
  },
  
  cacheFirst: async (request) => {
    const cached = await caches.match(request);
    if (cached) return cached;
    
    const response = await fetch(request);
    const cache = await caches.open('v1');
    cache.put(request, response.clone());
    return response;
  }
};

// Offline indicator component
const OfflineIndicator = () => {
  const [isOffline, setIsOffline] = useState(!navigator.onLine);
  
  useEffect(() => {
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);
  
  if (!isOffline) return null;
  
  return (
    <div className="offline-banner">
      <span>You're offline - Some features may be limited</span>
    </div>
  );
};
```