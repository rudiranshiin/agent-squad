export interface Agent {
  name: string
  type: string
  status: 'running' | 'stopped'
  module?: string
  personality?: Record<string, any>
  context_summary?: ContextSummary
  memory_stats?: Record<string, any>
  tools?: string[]
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
  version: string
  description: string
  author: string
  dependencies: string[]
  agent_types: string[]
  tools: string[]
  config_schema: Record<string, any>
  module_path: string
  is_active: boolean
}

export interface ModuleStatus {
  module_info: Module
  agents: Record<string, AgentStatus>
  tools: string[]
  hooks: number
  initialized: boolean
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
}

export interface MessageResponse {
  response: string
  suggestions?: string[]
  tool_results?: any[]
  processing_time?: number
  agent_name?: string
  agent_type?: string
  context_summary?: ContextSummary
}

export interface CollaborationGraph {
  [agentName: string]: {
    type: string
    can_collaborate_with: string[]
    collaboration_style: string
  }
}

export interface PerformanceMetrics {
  resource_limits: Record<string, number>
  connection_pools: Record<string, number>
  performance_metrics: Record<string, {
    avg: number
    min: number
    max: number
    count: number
  }>
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy'
  version: string
  modules: Record<string, ModuleStatus>
  performance: PerformanceMetrics
  timestamp: number
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

export interface CollaborationEdge {
  id: string
  source: string
  target: string
  type: 'collaboration'
  animated?: boolean
  style?: Record<string, any>
}
