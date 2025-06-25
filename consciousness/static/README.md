# House Consciousness Dashboard

## Overview

This comprehensive React-based dashboard provides a complete user interface for the House Consciousness System, exercising every available API endpoint with intuitive and responsive components.

## Files

- **`index.html`** - Simple overview dashboard with basic system status
- **`dashboard.html`** - Complete React-based dashboard with full API integration

## Features

### 🔐 Authentication
- **Login/Logout System**: JWT-based authentication with token management
- **Auto-redirect**: Automatic redirection to login when token expires
- **Default Credentials**: `admin` / `consciousness123`

### 🧠 Consciousness Dashboard
- **Real-time Status**: Live consciousness system status monitoring
- **Emotional State**: Current emotion display with arousal/valence indicators
- **Awareness Level**: Visual progress bars showing system awareness
- **Active Metrics**: Device count, SAFLA loops, and system health

### 🎯 Chat Interface
- **Natural Language Queries**: Direct communication with consciousness system
- **Context-aware Responses**: Intelligent responses based on system state
- **Real-time Processing**: Instant query processing and response display

### 📱 Device Management
- **Device Listing**: Complete device inventory with filtering capabilities
- **Individual Control**: Turn devices on/off with immediate feedback
- **Batch Operations**: Multi-device selection and bulk control actions
- **Filter Options**: Filter by status, location, and device type
- **Real-time Updates**: Live device status updates via WebSocket

### 🧠 Memory Interface
- **Memory Storage**: Store different types of memories (experience, pattern, preference, interaction)
- **Memory Retrieval**: View recent memories with context and timestamps
- **Context Management**: Rich context support for memory entries

### 💬 Interview Wizard
- **Conversational Discovery**: AI-powered device discovery through natural conversation
- **Progressive Interaction**: Multi-turn conversations for device classification
- **Real-time Processing**: Instant AI responses and device candidate identification

### 🔍 Discovery Scanner
- **Multi-protocol Support**: mDNS, UPnP, Bluetooth, Zigbee, Z-wave protocol scanning
- **Real-time Results**: Live scan progress and results display
- **Protocol Selection**: Choose specific protocols for targeted discovery
- **Results Management**: Organized display of discovered devices by protocol

### 🔄 SAFLA Loop Monitor
- **Active Loop Monitoring**: Real-time status of all SAFLA loops
- **Manual Triggers**: Ability to manually trigger specific loops
- **Status Tracking**: Loop execution status and last run timestamps

### 🔄 Digital Twin Manager
- **Twin Creation**: Create digital twins for physical devices
- **Synchronization Status**: Monitor twin-to-device synchronization
- **Fidelity Levels**: Support for basic, advanced, and expert fidelity
- **Management Interface**: Complete twin lifecycle management

### 🎯 Scenario Builder
- **What-if Analysis**: Run predictive analysis on system changes
- **Custom Scenarios**: Define and execute custom scenario simulations
- **Metrics Analysis**: Monitor energy, comfort, security, and cost metrics
- **Duration Control**: Configure analysis timeframes

### 🌐 Real-time Updates
- **WebSocket Integration**: Live updates across all dashboard components
- **Connection Status**: Visual indicator of real-time connection status
- **Auto-reconnection**: Automatic reconnection on connection loss
- **Subscription Management**: Selective subscription to relevant update channels

## API Endpoints Exercised

### Authentication
- `POST /api/v1/auth/login` - User authentication

### Consciousness
- `GET /api/v1/consciousness/status` - System status
- `GET /api/v1/consciousness/emotions` - Emotional state
- `POST /api/v1/consciousness/query` - Natural language queries

### Device Management
- `GET /api/v1/devices` - List devices with filters
- `GET /api/v1/devices/{id}` - Get specific device
- `PUT /api/v1/devices/{id}/control` - Control individual device
- `POST /api/v1/devices/batch-control` - Batch device operations

### Memory
- `GET /api/v1/memory` - Retrieve memories
- `POST /api/v1/memory` - Store new memories

### Interview System
- `POST /api/v1/interview/start` - Start discovery interview
- `POST /api/v1/interview/{id}/message` - Send interview message
- `GET /api/v1/interview/{id}/status` - Get interview status

### Device Discovery
- `POST /api/v1/discovery/scan` - Start device scan
- `GET /api/v1/discovery/scan/{id}` - Get scan results

### SAFLA Loops
- `GET /api/v1/safla/status` - Get SAFLA system status
- `POST /api/v1/safla/trigger` - Trigger SAFLA loop

### Digital Twins
- `GET /api/v1/twins` - List digital twins
- `POST /api/v1/twins` - Create new digital twin

### Scenarios
- `POST /api/v1/scenarios` - Create scenario
- `POST /api/v1/predictions/what-if` - Run what-if analysis

### Real-time
- `WebSocket /api/v1/realtime` - Real-time updates

## Usage Instructions

1. **Access the Dashboard**:
   - Open `index.html` for basic overview
   - Click "🚀 Open Full Dashboard" or navigate to `dashboard.html` for complete interface

2. **Authentication**:
   - Use default credentials: `admin` / `consciousness123`
   - Token is automatically managed and stored locally

3. **Navigation**:
   - Use the top navigation tabs to switch between different sections
   - Connection status is displayed in the header

4. **Device Control**:
   - Use checkboxes to select multiple devices for batch operations
   - Individual device controls are available on each device card
   - Apply filters to find specific devices

5. **Real-time Monitoring**:
   - Dashboard automatically updates with real-time data
   - WebSocket connection status is shown in the header
   - Automatic reconnection on connection loss

## Technical Implementation

- **Framework**: React (via CDN) with Babel for JSX transformation
- **Styling**: Custom CSS with modern design patterns, CSS Grid, and Flexbox
- **State Management**: React hooks (useState, useEffect, useRef)
- **API Integration**: Fetch API with JWT authentication and comprehensive error handling
- **WebSocket**: Native WebSocket with automatic reconnection and subscription management
- **Responsive Design**: Mobile-friendly layouts with adaptive grids
- **Error Handling**: User-friendly error messages and loading states

## Architecture

The dashboard follows a component-based architecture:

- **App Component**: Main application shell with authentication and routing
- **Feature Components**: Specialized components for each API domain
- **Utility Functions**: Shared API calling and WebSocket management
- **State Management**: Local state with hooks, no external state management library needed

This implementation provides a complete, production-ready interface for the House Consciousness System with comprehensive API coverage and excellent user experience.
