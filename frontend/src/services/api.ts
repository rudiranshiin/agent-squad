import axios from 'axios'
import {
  Agent,
  Module,
  ModuleStatus,
  MessageRequest,
  MessageResponse,
  CollaborationGraph,
  PerformanceMetrics,
  HealthStatus
} from '../types'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    console.error('API Request Error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`)
    return response
  },
  (error) => {
    console.error('API Response Error:', error.response?.status, error.response?.data)
    return Promise.reject(error)
  }
)

export const agentApi = {
  // Agent management
  listAgents: async (): Promise<{ agents: Record<string, Agent> }> => {
    const response = await api.get('/agents')
    return response.data
  },

  getAgentInfo: async (agentName: string): Promise<Agent> => {
    const response = await api.get(`/agents/${encodeURIComponent(agentName)}`)
    return response.data
  },

  sendMessage: async (agentName: string, messageData: MessageRequest): Promise<MessageResponse> => {
    const response = await api.post(`/agents/${encodeURIComponent(agentName)}/message`, messageData)
    return response.data
  },

  sendCollaborativeMessage: async (primaryAgent: string, message: string, collaboratingAgents: string[]): Promise<any> => {
    const response = await api.post('/agents/collaboration/message', {
      primary_agent: primaryAgent,
      text: message,
      collaborating_agents: collaboratingAgents
    })
    return response.data
  },

  startAgent: async (agentName: string): Promise<{ message: string }> => {
    const response = await api.post(`/agents/${encodeURIComponent(agentName)}/start`)
    return response.data
  },

  stopAgent: async (agentName: string): Promise<{ message: string }> => {
    const response = await api.post(`/agents/${encodeURIComponent(agentName)}/stop`)
    return response.data
  },

  removeAgent: async (agentName: string): Promise<{ message: string }> => {
    const response = await api.delete(`/agents/${encodeURIComponent(agentName)}`)
    return response.data
  },

  createAgent: async (moduleConfig: { module_name: string; config: any }): Promise<{ message: string; agent_name: string; agent_type: string; module: string }> => {
    const response = await api.post('/agents/create', moduleConfig)
    return response.data
  },

  // Collaboration
  getCollaborationGraph: async (): Promise<{ collaboration_graph: CollaborationGraph }> => {
    const response = await api.get('/agents/collaboration/graph')
    return response.data
  },

  getActiveCollaborations: async (): Promise<{ active_collaborations: Record<string, any>; total_active: number }> => {
    const response = await api.get('/agents/collaboration/active')
    return response.data
  },

  collaborateAgents: async (agent1: string, agent2: string, message: string = ''): Promise<any> => {
    const response = await api.post(`/agents/${encodeURIComponent(agent1)}/collaborate/${encodeURIComponent(agent2)}`, {
      message,
      collaboration_type: 'thread_connection'
    })
    return response.data
  },

  removeCollaboration: async (agent1: string, agent2: string): Promise<any> => {
    const response = await api.delete(`/agents/${encodeURIComponent(agent1)}/collaborate/${encodeURIComponent(agent2)}`)
    return response.data
  },

  broadcastMessage: async (message: string, excludeAgents?: string[]): Promise<{ message: string; responses: Record<string, any>; total_agents: number }> => {
    const response = await api.post('/agents/broadcast', {
      message,
      exclude_agents: excludeAgents
    })
    return response.data
  }
}

export const moduleApi = {
  // Module management
  listModules: async (): Promise<{ modules: string[]; status: Record<string, ModuleStatus> }> => {
    const response = await api.get('/modules')
    return response.data
  },

  getModuleStatus: async (moduleName: string): Promise<ModuleStatus> => {
    const response = await api.get(`/modules/${encodeURIComponent(moduleName)}`)
    return response.data
  },

  installModule: async (templateName: string, moduleName: string, config: any): Promise<{ message: string; module_name: string; module_path: string; status: ModuleStatus }> => {
    const response = await api.post('/modules/install', {
      template_name: templateName,
      module_name: moduleName,
      config
    })
    return response.data
  },

  loadModule: async (moduleName: string, modulePath: string): Promise<{ message: string; module_info: Module }> => {
    const response = await api.post(`/modules/${encodeURIComponent(moduleName)}/load`, null, {
      params: { module_path: modulePath }
    })
    return response.data
  },

  unloadModule: async (moduleName: string): Promise<{ message: string }> => {
    const response = await api.post(`/modules/${encodeURIComponent(moduleName)}/unload`)
    return response.data
  },

  reloadModule: async (moduleName: string): Promise<{ message: string }> => {
    const response = await api.post(`/modules/${encodeURIComponent(moduleName)}/reload`)
    return response.data
  },

  uninstallModule: async (moduleName: string): Promise<{ message: string }> => {
    const response = await api.delete(`/modules/${encodeURIComponent(moduleName)}`)
    return response.data
  }
}

export const systemApi = {
  // System health and performance
  getHealth: async (): Promise<HealthStatus> => {
    const response = await api.get('/health')
    return response.data
  },

  getStatus: async (): Promise<any> => {
    const response = await api.get('/status')
    return response.data
  },

  getPerformance: async (): Promise<PerformanceMetrics> => {
    const response = await api.get('/performance')
    return response.data
  },

  optimizePerformance: async (): Promise<{ message: string; performance_report: PerformanceMetrics }> => {
    const response = await api.post('/performance/optimize')
    return response.data
  }
}

export default api
