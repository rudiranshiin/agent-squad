export interface Agent {
  name: string
  type: string
  status: 'running' | 'stopped' | 'error'
  health: string
  config: Record<string, any>
  performance: Record<string, any>
  last_activity?: string
  error_message?: string
}

export interface ContextSummary {
  total_items: number
  total_tokens: number
  max_tokens: number
  token_utilization: number
  context_by_type: Record<string, number>
  metrics?: Record<string, any>
}

export interface Module {
  name: string
  path: string
  type: string
  dependencies: string[]
  config: Record<string, any>
  agents: string[]
}

export interface ModuleStatus {
  loaded: boolean
  error?: string
  last_update?: string
  agents_count: number
  performance: Record<string, any>
}

export interface AgentStatus {
  type: string
  running: boolean
  memory_items: number
  context_items: number
}

export interface MessageRequest {
  text: string
  context?: Record<string, any>
  user_id?: string
  config?: any
}

export interface MessageResponse {
  response: string
  agent_name: string
  processing_time?: number
  suggestions?: string[]
  tokens_used?: number
  cost?: number
  context?: Record<string, any>
  metadata?: Record<string, any>
}

export interface CollaborationNode {
  id: string
  name: string
  type: string
  status: string
  x: number
  y: number
}

export interface CollaborationEdge {
  id: string
  source: string
  target: string
  label?: string
  type: 'collaboration'
  weight?: number
  animated?: boolean
  style?: Record<string, any>
}

export interface CollaborationGraph {
  [agentName: string]: {
    type: string
    can_collaborate_with: string[]
    collaboration_style: string
  }
}

export interface PerformanceMetrics {
  agent_count: number
  total_messages: number
  avg_response_time: number
  memory_usage: number
  cpu_usage: number
  error_rate: number
  uptime: number
  throughput: number
  optimization_suggestions: string[]
}

export interface HealthStatus {
  status: 'healthy' | 'warning' | 'error'
  version: string
  modules: Record<string, ModuleStatus>
  performance: PerformanceMetrics
  timestamp: number
  issues?: string[]
}

export interface AgentNode {
  id: string
  type: 'agent'
  position: { x: number; y: number }
  data: {
    label: string
    agentType: string
    status: 'running' | 'stopped'
    module?: string
    tools: string[]
  }
}
