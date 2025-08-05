# 🚀 Agentic Framework React UI

A beautiful, modern React interface for the Enhanced Agentic AI Framework 2.0. Built with React 18, TypeScript, Material-UI, and React Flow for interactive agent visualization.

## ✨ Features

### 🎛️ **Dashboard**
- Real-time framework health monitoring
- Agent status overview with performance metrics
- System resource utilization tracking
- Quick action shortcuts

### 🌐 **Agent Flow Visualization**
- Interactive agent network using React Flow
- Real-time collaboration relationship mapping
- Agent control panel (start/stop/collaborate)
- Beautiful custom node components with agent type icons
- Drag-and-drop interface for agent management

### 💬 **Chat Interface**
- Direct chat with any running agent
- Real-time message processing with typing indicators
- Agent response suggestions and quick actions
- Processing time monitoring
- Chat history with agent context

### 📦 **Module Manager**
- Visual module management interface
- One-click agent creation from templates
- Module statistics and health monitoring
- Hot-reloading and module lifecycle management

## 🛠️ Technology Stack

- **Framework**: React 18 with TypeScript
- **UI Library**: Material-UI (MUI) v5 with dark theme
- **Visualization**: React Flow for agent network diagrams
- **State Management**: React Query for server state
- **HTTP Client**: Axios with request/response interceptors
- **Notifications**: React Hot Toast
- **Icons**: Material-UI Icons & Lucide React
- **Animations**: Framer Motion
- **Build Tool**: Vite for fast development and building

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm/yarn
- Running Agentic Framework backend on port 8000

### Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Open browser to http://localhost:3000
```

### Production Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## 📱 Interface Overview

### 🏠 Dashboard Page (`/`)
The main overview page showing:
- Framework health status and version
- Agent statistics (active/total agents)
- System performance metrics
- Resource utilization graphs
- Quick action buttons

### 🌐 Agent Flow Page (`/flow`)
Interactive network visualization featuring:
- **Custom Agent Nodes**: Visual cards showing agent type, status, and tools
- **Collaboration Edges**: Animated connections showing agent relationships
- **Control Panel**: Start/stop agents and initiate collaborations
- **Zoom Controls**: Navigate large agent networks
- **Real-time Updates**: Live status changes and connections

### 💬 Chat Interface (`/chat`)
Direct agent communication with:
- **Agent Selection**: Choose from running agents
- **Message Interface**: Clean chat UI with user/agent distinction
- **Suggestions**: Agent-provided response suggestions
- **Performance Metrics**: Response time tracking
- **Chat History**: Persistent conversation within session

### 📦 Module Manager (`/modules`)
Complete module lifecycle management:
- **Module Cards**: Visual representation of loaded modules
- **Agent Creation**: One-click agent creation with templates
- **Module Controls**: Reload, unload, and manage modules
- **Statistics Dashboard**: Module and agent counts

## 🎨 Design System

### Color Palette
- **Primary**: `#667eea` (Purple-blue gradient)
- **Secondary**: `#764ba2` (Deep purple)
- **Success**: `#4caf50` (Green for running agents)
- **Error**: `#f44336` (Red for stopped/error states)
- **Warning**: `#ff9800` (Orange for warnings)

### Typography
- **Headings**: Roboto with various weights
- **Body**: System font stack for optimal readability
- **Code**: Monospace for technical information

### Components
- **Glass Morphism**: Cards with backdrop blur and transparency
- **Smooth Animations**: Hover effects and transitions
- **Consistent Spacing**: 8px grid system
- **Responsive Design**: Mobile-first approach

## 📡 API Integration

### Automatic Proxy Configuration
The frontend automatically proxies API requests to the backend:

```typescript
// vite.config.ts
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api/, '')
  }
}
```

### API Services Structure

```typescript
// src/services/api.ts
export const agentApi = {
  listAgents: () => Promise<AgentList>
  sendMessage: (agentName, message) => Promise<MessageResponse>
  startAgent: (agentName) => Promise<StatusResponse>
  // ... more agent operations
}

export const moduleApi = {
  listModules: () => Promise<ModuleList>
  createAgent: (config) => Promise<CreateResponse>
  // ... more module operations
}

export const systemApi = {
  getHealth: () => Promise<HealthStatus>
  getPerformance: () => Promise<PerformanceMetrics>
  // ... more system operations
}
```

### Real-time Updates
- **React Query**: Automatic background refetching
- **Configurable Intervals**: Different update frequencies per component
- **Error Handling**: Graceful degradation and user feedback
- **Optimistic Updates**: Immediate UI feedback

## 🔧 Development

### Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   └── Layout.tsx      # Main app layout with navigation
│   ├── pages/              # Page components
│   │   ├── Dashboard.tsx   # System overview
│   │   ├── AgentFlow.tsx   # Network visualization
│   │   ├── AgentChat.tsx   # Chat interface
│   │   └── ModuleManager.tsx # Module management
│   ├── services/           # API client and utilities
│   │   └── api.ts          # Backend API integration
│   ├── types/              # TypeScript definitions
│   │   └── index.ts        # Shared interfaces
│   ├── App.tsx             # Main app component with routing
│   └── main.tsx            # Entry point
├── public/                 # Static assets
├── package.json            # Dependencies and scripts
└── vite.config.ts         # Build configuration
```

### Key Components

#### AgentFlow Visualization
- **Custom Nodes**: Agent cards with status indicators
- **Interactive Controls**: Zoom, pan, and selection
- **Real-time Data**: Live agent status updates
- **Collaboration UI**: Initiate agent-to-agent communication

#### Chat Interface
- **Message Threading**: Chronological conversation flow
- **Agent Selection**: Dynamic agent picker
- **Response Suggestions**: Clickable suggestion chips
- **Performance Tracking**: Response time monitoring

#### Module Manager
- **Module Cards**: Visual module representation
- **Agent Creation**: Template-based agent setup
- **Lifecycle Controls**: Start, stop, reload operations

### Development Commands

```bash
# Development server with hot reload
npm run dev

# Type checking
npm run lint

# Build for production
npm run build

# Preview production build
npm run preview
```

## 🌐 Deployment

### Docker Deployment

```dockerfile
# Dockerfile for React UI
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
```

### Environment Configuration

```bash
# .env.production
VITE_API_BASE_URL=https://your-api-domain.com
VITE_APP_VERSION=1.0.0
```

### Nginx Configuration

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    # Handle React Router
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api/ {
        proxy_pass http://backend:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🚀 Getting Started with the Full Stack

1. **Start the Backend**:
   ```bash
   # In the root directory
   uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Start the Frontend**:
   ```bash
   # In the frontend directory
   npm install
   npm run dev
   ```

3. **Open your browser**: `http://localhost:3000`

4. **Create your first agent**:
   - Go to Module Manager
   - Click "Create Agent"
   - Choose a template (e.g., Cooking Assistant)
   - Give it a name (e.g., "Chef Marco")
   - Start chatting!

## 🎯 Usage Examples

### Creating a Cooking Agent
1. Navigate to **Module Manager** (`/modules`)
2. Click **"Create Agent"**
3. Select module: `cooking_assistant`
4. Enter name: `Chef Marco`
5. Select type: `Cooking Assistant`
6. Click **"Create Agent"**

### Testing Agent Communication
1. Go to **Agent Flow** (`/flow`)
2. Click on an agent node to select it
3. Click **"Collaborate"**
4. Choose another agent and send a message
5. Watch the real-time interaction

### Monitoring Performance
1. Visit **Dashboard** (`/`)
2. Monitor real-time metrics
3. Check agent status and resource usage
4. Use quick actions for common tasks

## 🛡️ Security Features

- **Input Validation**: All user inputs are validated
- **XSS Protection**: Proper content sanitization
- **CORS Configuration**: Secure cross-origin requests
- **Error Boundaries**: Graceful error handling
- **Secure Headers**: CSP and security headers

## 📈 Performance Optimizations

- **Code Splitting**: Lazy loading of route components
- **React Query**: Intelligent caching and background updates
- **Memoization**: Optimized re-renders with React.memo
- **Bundle Optimization**: Tree shaking and minification
- **Image Optimization**: Efficient asset loading

---

**Built with ❤️ for the Enhanced Agentic AI Framework 2.0**

This interface provides a complete management and interaction experience for your AI agents, making it easy to visualize, control, and communicate with your agentic framework.
