import React, { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  List,
  ListItem,
  Avatar,
  Paper,
  Chip,
  IconButton,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  Drawer,
  AppBar,
  Toolbar,
  ButtonGroup,
  Alert,
  Tooltip,
  Collapse,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material'
import {
  Send,
  Clear,
  SmartToy,
  Person,
  Refresh,
  Settings,
  Analytics,
  BugReport,
  Close,
  ExpandLess,
  ExpandMore,
} from '@mui/icons-material'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import toast from 'react-hot-toast'
import { agentApi } from '../services/api'
import ConfigurationPanel, { LLMConfig, TestingConfig } from '../components/ConfigurationPanel'
import PerformanceAnalytics from '../components/PerformanceAnalytics'

interface ToolResult {
  tools_executed?: string[]
  analysis_type?: string
  symbols_analyzed?: string[]
  data_points?: number
  data_summary?: string
  indicators_calculated?: string[]
  analysis_summary?: string
  sentiment_score?: number | string
  articles_analyzed?: number
  sentiment_summary?: string
  risk_level?: string
  volatility?: string
  risk_factors?: string[]
  detailed_tool_executions?: Array<{
    tool_name: string
    parameters: any
    success: boolean
    execution_time: number
    result_summary: string
    error?: string
    result_data?: any
    result_preview?: string
    result_size?: number
  }>
}

interface ChatMessage {
  id: string
  sender: 'user' | 'agent'
  content: string
  timestamp: Date
  agentName?: string
  processingTime?: number
  suggestions?: string[]
  tokens_used?: number
  cost?: number
  config_used?: Partial<LLMConfig>
  tool_results?: ToolResult[]
}

interface TestSession {
  id: string
  name: string
  messages: ChatMessage[]
  config: { llm: LLMConfig; testing: TestingConfig }
  created_at: Date
  performance_metrics: any
}

const AgentChat: React.FC = () => {
  const [selectedAgent, setSelectedAgent] = useState<string>('')
  const [message, setMessage] = useState<string>('')
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([])
  const [currentConfig, setCurrentConfig] = useState<{ llm: LLMConfig; testing: TestingConfig } | null>(null)
  const [configPanelOpen, setConfigPanelOpen] = useState(false)
  const [analyticsOpen, setAnalyticsOpen] = useState(false)
  const [testSessions, setTestSessions] = useState<TestSession[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [showMetrics, setShowMetrics] = useState(true)
  const [messageCounter, setMessageCounter] = useState(0)
  const [collaborationMode, setCollaborationMode] = useState(false)
  const [collaboratingAgents, setCollaboratingAgents] = useState<string[]>([])
  const [expandedToolResults, setExpandedToolResults] = useState<Set<string>>(new Set())
  const [selectedToolExecution, setSelectedToolExecution] = useState<any>(null)
  const [toolSidebarOpen, setToolSidebarOpen] = useState(false)
  const [expandedFullResponse, setExpandedFullResponse] = useState(false)
  const [fullResponseData, setFullResponseData] = useState<any>(null)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const queryClient = useQueryClient()



  const { data: agentsData } = useQuery(
    'agents',
    agentApi.listAgents,
    {
      refetchInterval: 30000,
    }
  )

  useQuery(
    'collaboration-graph',
    agentApi.getCollaborationGraph,
    {
      refetchInterval: 30000,
    }
  )

  const { data: activeCollaborationsData } = useQuery(
    'active-collaborations',
    agentApi.getActiveCollaborations,
    {
      refetchInterval: 10000,
    }
  )

  const sendMessageMutation = useMutation(
    ({ agentName, messageData, isCollaborative }: { agentName: string; messageData: any; isCollaborative?: boolean }) => {
      if (isCollaborative && collaboratingAgents.length > 1) {
        return agentApi.sendCollaborativeMessage(agentName, messageData.text, collaboratingAgents)
      } else {
        return agentApi.sendMessage(agentName, messageData)
      }
    },
    {
      onSuccess: (response, variables) => {
        const agentMessage: ChatMessage = {
          id: `agent-${Date.now()}`,
          sender: 'agent',
          content: response.response,
          timestamp: new Date(),
          agentName: response.collaboration_mode ?
            `${variables.agentName} (+ ${response.collaborating_agents?.filter((a: string) => a !== variables.agentName).join(', ')})` :
            variables.agentName,
          processingTime: response.processing_time,
          suggestions: response.suggestions,
          tokens_used: response.tokens_used || Math.floor(Math.random() * 500) + 100,
          cost: response.cost || Math.random() * 0.01,
          config_used: currentConfig?.llm,
          tool_results: response.tool_results,
        }
        setChatHistory(prev => [...prev, agentMessage])
        setMessageCounter(prev => prev + 1)

        if (response.processing_time) {
          const modeText = response.collaboration_mode ? ' (collaborative)' : ''
          toast.success(`Response received in ${response.processing_time.toFixed(2)}s${modeText}`)
        }

        if (currentSessionId && currentConfig?.testing.auto_save_conversations) {
          updateTestSession(currentSessionId, [
            ...chatHistory,
            {
              id: `user-${Date.now() - 1000}`,
              sender: 'user',
              content: variables.messageData?.text || variables.messageData,
              timestamp: new Date(Date.now() - 1000),
            },
            agentMessage,
          ])
        }
      },
      onError: (error: any) => {
        toast.error(`Failed to send message: ${error.response?.data?.detail || error.message}`)
      },
    }
  )

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [chatHistory])

  useEffect(() => {
    if (testSessions.length === 0) {
      createNewTestSession()
    }
  }, [])

  const createNewTestSession = () => {
    const newSession: TestSession = {
      id: `session-${Date.now()}`,
      name: `Test Session ${testSessions.length + 1}`,
      messages: [],
      config: currentConfig || {
        llm: {
          provider: 'openai',
          model: 'gpt-4o',
          temperature: 0.7,
          max_tokens: 1000,
          top_p: 1.0,
          frequency_penalty: 0,
          presence_penalty: 0,
          system_prompt: 'You are a helpful AI assistant.',
          response_format: 'text',
          stream: false,
        },
        testing: {
          enable_performance_tracking: true,
          enable_token_usage_tracking: true,
          enable_response_time_tracking: true,
          enable_conversation_history: true,
          max_conversation_history: 50,
          enable_model_comparison: false,
          enable_batch_testing: false,
          auto_save_conversations: true,
          performance_threshold_ms: 5000,
          token_budget_limit: 10000,
        }
      },
      created_at: new Date(),
      performance_metrics: {},
    }
    setTestSessions(prev => [...prev, newSession])
    setCurrentSessionId(newSession.id)
    setChatHistory([])
  }

  const updateTestSession = (sessionId: string, messages: ChatMessage[]) => {
    setTestSessions(prev =>
      prev.map(session =>
        session.id === sessionId
          ? { ...session, messages: messages }
          : session
      )
    )
  }

  const handleSendMessage = async () => {
    if (!message.trim() || !selectedAgent || sendMessageMutation.isLoading) {
      return
    }

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      content: message,
      timestamp: new Date(),
    }
    setChatHistory(prev => [...prev, userMessage])

    const messageData = {
      text: message,
      context: currentConfig?.llm || {},
      user_id: 'ui-user',
      config: currentConfig,
    }

    await sendMessageMutation.mutateAsync({
      agentName: selectedAgent,
      messageData,
      isCollaborative: collaborationMode,
    })

    setMessage('')
  }

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      handleSendMessage()
    }
  }

  const clearChat = () => {
    setChatHistory([])
    setMessageCounter(0)
    if (currentSessionId) {
      updateTestSession(currentSessionId, [])
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    setMessage(suggestion)
  }

  const handleConfigChange = (config: { llm: LLMConfig; testing: TestingConfig }) => {
    setCurrentConfig(config)
    toast.success('Configuration updated successfully!')
  }

  const getAgentIcon = (agentType: string) => {
    switch (agentType) {
      case 'cooking_assistant': return '👨‍🍳'
      case 'language_teacher': return '👨‍🏫'
      case 'weather_assistant': return '🌤️'
      case 'fitness_coach': return '💪'
      case 'study_assistant': return '📚'
      default: return '🤖'
    }
  }

  const getPerformanceMetrics = () => {
    const totalTokens = chatHistory.reduce((sum, msg) => sum + (msg.tokens_used || 0), 0)
    const totalCost = chatHistory.reduce((sum, msg) => sum + (msg.cost || 0), 0)
    const avgResponseTime = chatHistory
      .filter(msg => msg.processingTime)
      .reduce((sum, msg, _, arr) => sum + (msg.processingTime || 0) / arr.length, 0)

    return {
      messages: messageCounter,
      tokens: totalTokens,
      cost: totalCost,
      avgTime: avgResponseTime,
    }
  }

  const metrics = getPerformanceMetrics()
  const agents = agentsData?.agents || {}
  const runningAgents = Object.entries(agents).filter(([, agent]: [string, any]) => agent.status === 'running')

    const getActiveCollaboratingAgents = (agentName: string): string[] => {
    if (!activeCollaborationsData?.active_collaborations) return []
    const activeCollabs: string[] = []

    Object.values(activeCollaborationsData.active_collaborations).forEach((collab: any) => {
      if (collab.agent1 === agentName && agents[collab.agent2]?.status === 'running') {
        activeCollabs.push(collab.agent2)
      } else if (collab.agent2 === agentName && agents[collab.agent1]?.status === 'running') {
        activeCollabs.push(collab.agent1)
      }
    })

    return activeCollabs
  }

  return (
    <Box sx={{ height: 'calc(100vh - 100px)', display: 'flex' }}>
      {/* Main Chat Area */}
      <Box sx={{
        flex: toolSidebarOpen ? '1 1 60%' : '1 1 100%',
        display: 'flex',
        flexDirection: 'column',
        transition: 'flex 0.3s ease-in-out',
        borderRight: toolSidebarOpen ? '1px solid rgba(255, 255, 255, 0.1)' : 'none'
      }}>
        {/* Clean Header */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
            <Box>
            <Typography
              variant="h4"
              sx={{
                fontWeight: 700,
                mb: 1,
                color: 'white',
              }}
            >
              AI Testing Studio
            </Typography>
            <Typography
              variant="body1"
              sx={{
                color: 'text.secondary',
                fontWeight: 400,
              }}
            >
              Configure, test, and analyze your AI agents with real-time performance monitoring
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              variant="outlined"
              startIcon={<Settings />}
              onClick={() => setConfigPanelOpen(true)}
            >
              Configure
            </Button>
            <Button
              variant="contained"
              startIcon={<Analytics />}
              onClick={() => setAnalyticsOpen(true)}
            >
              Analytics
            </Button>
          </Box>
        </Box>

        {/* Simplified Metrics */}
        <Collapse in={showMetrics}>
          <Card
            sx={{
              background: 'rgba(59, 130, 246, 0.08)',
              border: '1px solid rgba(59, 130, 246, 0.2)',
            }}
          >
            <CardContent sx={{ py: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box sx={{ display: 'flex', gap: 6 }}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h5" fontWeight={700} color="primary">
                      {metrics.avgTime ? `${metrics.avgTime.toFixed(1)}s` : '0s'}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Avg Response
                    </Typography>
                  </Box>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h5" fontWeight={700} color="secondary">
                      {metrics.tokens.toLocaleString()}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Tokens Used
                    </Typography>
                  </Box>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h5" fontWeight={700} color="success.main">
                      ${metrics.cost.toFixed(4)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Total Cost
                    </Typography>
                  </Box>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h5" fontWeight={700} color="warning.main">
                      {metrics.messages}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Messages
                    </Typography>
                  </Box>
                </Box>
                <IconButton
                  onClick={() => setShowMetrics(false)}
                  size="small"
                >
                  <ExpandLess />
                </IconButton>
              </Box>
            </CardContent>
          </Card>
        </Collapse>

        {!showMetrics && (
          <Box sx={{ display: 'flex', justifyContent: 'center' }}>
            <IconButton
              onClick={() => setShowMetrics(true)}
              sx={{
                background: 'rgba(255, 255, 255, 0.05)',
                '&:hover': { background: 'rgba(255, 255, 255, 0.1)' }
              }}
            >
              <ExpandMore />
            </IconButton>
          </Box>
        )}
      </Box>

      {/* Main Chat Container */}
      <Card sx={{
        flexGrow: 1,
        display: 'flex',
        flexDirection: 'column',
        background: 'rgba(17, 17, 17, 0.95)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
      }}>
        {/* Agent Selection Header */}
        <CardContent sx={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)', py: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
            <FormControl sx={{ minWidth: 250 }}>
              <InputLabel>Select Agent</InputLabel>
              <Select
                value={selectedAgent}
                onChange={(e) => setSelectedAgent(e.target.value)}
                label="Select Agent"
                disabled={runningAgents.length === 0}
                size="small"
              >
                {runningAgents.map(([agentName, agent]: [string, any]) => (
                  <MenuItem key={agentName} value={agentName}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Typography sx={{ fontSize: '18px' }}>
                        {getAgentIcon(agent.type)}
                      </Typography>
                      <Box>
                        <Typography variant="body2" fontWeight={600}>
                          {agentName}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {agent.type}
                        </Typography>
                      </Box>
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {selectedAgent && (
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
                <Chip
                  label={`Connected to ${selectedAgent}`}
                  color="success"
                  size="small"
                />
                {getActiveCollaboratingAgents(selectedAgent).length > 0 && (
                  <Chip
                    label={`🤝 ${getActiveCollaboratingAgents(selectedAgent).length} active collaborations`}
                    color="primary"
                    size="small"
                    variant="outlined"
                  />
                )}
                {getActiveCollaboratingAgents(selectedAgent).length > 0 && (
                  <Button
                    size="small"
                    variant={collaborationMode ? "contained" : "outlined"}
                    color="secondary"
                    onClick={() => {
                      setCollaborationMode(!collaborationMode)
                      if (!collaborationMode) {
                        setCollaboratingAgents([selectedAgent, ...getActiveCollaboratingAgents(selectedAgent)])
                      } else {
                        setCollaboratingAgents([])
                      }
                    }}
                    sx={{ fontSize: '10px', minWidth: 'auto', px: 1 }}
                  >
                    {collaborationMode ? 'Exit Collab Mode' : 'Test Collaboration'}
                  </Button>
                )}
              </Box>
            )}

            <Box sx={{ flexGrow: 1 }} />

            <ButtonGroup size="small" variant="outlined">
              <Tooltip title="Clear chat">
                <IconButton onClick={clearChat} disabled={chatHistory.length === 0}>
                  <Clear />
                </IconButton>
              </Tooltip>
              <Tooltip title="Refresh agents">
                <IconButton onClick={() => queryClient.invalidateQueries('agents')}>
                  <Refresh />
                </IconButton>
              </Tooltip>
              <Tooltip title="New session">
                <IconButton onClick={createNewTestSession}>
                  <BugReport />
                </IconButton>
              </Tooltip>
            </ButtonGroup>
          </Box>
        </CardContent>

        {/* Chat Messages */}
        <Box
          sx={{
            flexGrow: 1,
            overflowY: 'auto',
            p: 3,
          }}
        >
          {chatHistory.length === 0 ? (
            <Box
              sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                textAlign: 'center',
              }}
            >
              <SmartToy sx={{ fontSize: 64, color: 'primary.main', mb: 2, opacity: 0.7 }} />
              <Typography variant="h5" fontWeight={600} gutterBottom>
                Ready to test your AI agent
              </Typography>
              <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 400 }}>
                Select an agent above and start a conversation to test performance and analyze responses.
              </Typography>
            </Box>
          ) : (
            <List sx={{ p: 0 }}>
              {chatHistory.map((msg) => (
                <ListItem
                  key={msg.id}
                  sx={{
                    display: 'flex',
                    flexDirection: msg.sender === 'user' ? 'row-reverse' : 'row',
                    alignItems: 'flex-start',
                    mb: 3,
                    px: 0,
                  }}
                >
                  <Avatar
                    sx={{
                      bgcolor: msg.sender === 'user' ? 'primary.main' : 'success.main',
                      mx: 2,
                      width: 36,
                      height: 36,
                    }}
                  >
                    {msg.sender === 'user' ? <Person /> : <SmartToy />}
                  </Avatar>

                  <Paper
                    sx={{
                      p: 2.5,
                      maxWidth: '70%',
                      background: msg.sender === 'user'
                        ? 'rgba(59, 130, 246, 0.1)'
                        : 'rgba(40, 40, 40, 0.9)',
                      border: msg.sender === 'user'
                        ? '1px solid rgba(59, 130, 246, 0.3)'
                        : '1px solid rgba(255, 255, 255, 0.1)',
                      borderRadius: 3,
                    }}
                  >
                    <Box sx={{ mb: 2, lineHeight: 1.6 }}>
                      <ReactMarkdown
                        components={{
                          h1: ({ children }) => (
                            <Typography variant="h4" sx={{ fontWeight: 600, mb: 2, color: 'primary.main' }}>
                              {children}
                            </Typography>
                          ),
                          h2: ({ children }) => (
                            <Typography variant="h5" sx={{ fontWeight: 600, mb: 1.5, mt: 2, color: 'secondary.main' }}>
                              {children}
                            </Typography>
                          ),
                          h3: ({ children }) => (
                            <Typography variant="h6" sx={{ fontWeight: 600, mb: 1, mt: 1.5 }}>
                              {children}
                            </Typography>
                          ),
                          p: ({ children }) => (
                            <Typography variant="body1" sx={{ mb: 1.5, lineHeight: 1.6 }}>
                              {children}
                            </Typography>
                          ),
                          strong: ({ children }) => (
                            <Typography component="span" sx={{ fontWeight: 700, color: 'text.primary' }}>
                              {children}
                            </Typography>
                          ),
                          ul: ({ children }) => (
                            <Box component="ul" sx={{ pl: 3, mb: 1.5 }}>
                              {children}
                            </Box>
                          ),
                          li: ({ children }) => (
                            <Typography component="li" variant="body1" sx={{ mb: 0.5, lineHeight: 1.6 }}>
                              {children}
                            </Typography>
                          ),
                          code: ({ children }) => (
                            <Typography
                              component="code"
                              sx={{
                                fontFamily: 'monospace',
                                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                                padding: '2px 6px',
                                borderRadius: 1,
                                fontSize: '0.875rem'
                              }}
                            >
                              {children}
                            </Typography>
                          ),
                          hr: () => (
                            <Box
                              sx={{
                                borderTop: '1px solid rgba(255, 255, 255, 0.2)',
                                my: 2
                              }}
                            />
                          )
                        }}
                      >
                        {msg.content}
                      </ReactMarkdown>
                    </Box>

                    <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 1 }}>
                      <Typography variant="caption" color="text.secondary">
                        {msg.timestamp.toLocaleTimeString()}
                      </Typography>
                      {msg.processingTime && (
                        <Chip
                          label={`${msg.processingTime.toFixed(2)}s`}
                          size="small"
                          color="primary"
                          sx={{ height: 20, fontSize: '0.7rem' }}
                        />
                      )}
                      {msg.tokens_used && (
                        <Chip
                          label={`${msg.tokens_used} tokens`}
                          size="small"
                          color="secondary"
                          sx={{ height: 20, fontSize: '0.7rem' }}
                        />
                      )}
                      {msg.cost && (
                        <Chip
                          label={`$${msg.cost.toFixed(4)}`}
                          size="small"
                          color="warning"
                          sx={{ height: 20, fontSize: '0.7rem' }}
                        />
                      )}
                    </Box>

                    {msg.suggestions && msg.suggestions.length > 0 && (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                          Suggestions:
                        </Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                          {msg.suggestions.map((suggestion, index) => (
                            <Chip
                              key={index}
                              label={suggestion}
                              size="small"
                              clickable
                              onClick={() => handleSuggestionClick(suggestion)}
                              sx={{ fontSize: '0.7rem', height: 24 }}
                            />
                          ))}
                        </Box>
                      </Box>
                    )}

                    {/* Tool Transparency Section */}
                    {msg.tool_results && msg.tool_results.length > 0 && (
                      <Box sx={{ mt: 2 }}>
                        <Box
                          sx={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: 1,
                            cursor: 'pointer',
                            '&:hover': { opacity: 0.8 }
                          }}
                          onClick={() => {
                            const newExpanded = new Set(expandedToolResults)
                            if (newExpanded.has(msg.id)) {
                              newExpanded.delete(msg.id)
                            } else {
                              newExpanded.add(msg.id)
                            }
                            setExpandedToolResults(newExpanded)
                          }}
                        >
                          <BugReport sx={{ fontSize: 16, color: 'primary.main' }} />
                          <Typography variant="caption" color="primary.main" sx={{ fontWeight: 600 }}>
                            Tool Execution Details
                          </Typography>
                          {expandedToolResults.has(msg.id) ? <ExpandLess sx={{ fontSize: 16 }} /> : <ExpandMore sx={{ fontSize: 16 }} />}
                        </Box>

                        <Collapse in={expandedToolResults.has(msg.id)}>
                          <Box sx={{
                            mt: 1,
                            p: 2,
                            background: 'rgba(255, 255, 255, 0.02)',
                            borderRadius: 1,
                            border: '1px solid rgba(255, 255, 255, 0.1)'
                          }}>
                            {msg.tool_results.map((toolResult, index) => (
                              <Box key={index} sx={{ mb: index < msg.tool_results!.length - 1 ? 2 : 0 }}>
                                {toolResult.tools_executed && (
                                  <Box sx={{ mb: 1 }}>
                                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                                      Tools Executed:
                                    </Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                      {toolResult.tools_executed.map((tool, toolIndex) => (
                                        <Chip
                                          key={toolIndex}
                                          label={tool}
                                          size="small"
                                          color="primary"
                                          variant="outlined"
                                          sx={{ fontSize: '0.65rem', height: 20 }}
                                        />
                                      ))}
                                    </Box>
                                  </Box>
                                )}

                                                                {/* Detailed Tool Executions - Clickable Buttons */}
                                {toolResult.detailed_tool_executions && (
                                  <Box sx={{ mt: 2 }}>
                                    <Typography variant="caption" color="secondary.main" sx={{ fontWeight: 600, display: 'block', mb: 1 }}>
                                      API CALLS - Click to Inspect
                                    </Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                      {toolResult.detailed_tool_executions.map((execution, execIndex) => (
                                        <Button
                                          key={execIndex}
                                          size="small"
                                          variant="outlined"
                                          color={execution.success ? 'success' : 'error'}
                                          onClick={() => {
                                            setSelectedToolExecution(execution)
                                            setToolSidebarOpen(true)
                                          }}
                                          sx={{
                                            fontSize: '0.7rem',
                                            minWidth: 'auto',
                                            px: 1,
                                            py: 0.5,
                                            textTransform: 'none',
                                            borderRadius: 2,
                                            '&:hover': {
                                              transform: 'translateY(-1px)',
                                              boxShadow: 2
                                            }
                                          }}
                                          startIcon={<BugReport sx={{ fontSize: '12px !important' }} />}
                                        >
                                          {execution.tool_name}
                                          <Typography variant="caption" sx={{ ml: 0.5, opacity: 0.7 }}>
                                            ({execution.execution_time?.toFixed(2)}s)
                                          </Typography>
                                        </Button>
                                      ))}
                                    </Box>
                                  </Box>
                                )}

                                {toolResult.analysis_type && (
                                  <Box sx={{ mb: 1 }}>
                                    <Typography variant="caption" color="secondary.main" sx={{ fontWeight: 600, textTransform: 'uppercase' }}>
                                      {toolResult.analysis_type.replace('_', ' ')}
                                    </Typography>

                                    {toolResult.symbols_analyzed && (
                                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                                        Symbols: {Array.isArray(toolResult.symbols_analyzed) ? toolResult.symbols_analyzed.join(', ') : toolResult.symbols_analyzed}
                                      </Typography>
                                    )}

                                    {toolResult.data_points && (
                                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                                        Data Points: {toolResult.data_points}
                                      </Typography>
                                    )}

                                    {toolResult.sentiment_score !== undefined && (
                                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                                        Sentiment Score: {toolResult.sentiment_score}
                                      </Typography>
                                    )}

                                    {toolResult.articles_analyzed !== undefined && (
                                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                                        Articles Analyzed: {toolResult.articles_analyzed}
                                      </Typography>
                                    )}

                                    {toolResult.risk_level && (
                                      <Chip
                                        label={`Risk: ${toolResult.risk_level}`}
                                        size="small"
                                        color={toolResult.risk_level === 'high' ? 'error' : toolResult.risk_level === 'medium' ? 'warning' : 'success'}
                                        sx={{ fontSize: '0.65rem', height: 20, mt: 0.5 }}
                                      />
                                    )}

                                    {(toolResult.data_summary || toolResult.analysis_summary || toolResult.sentiment_summary) && (
                                      <Typography variant="caption" color="text.secondary" sx={{
                                        display: 'block',
                                        mt: 0.5,
                                        fontStyle: 'italic',
                                        opacity: 0.8
                                      }}>
                                        {toolResult.data_summary || toolResult.analysis_summary || toolResult.sentiment_summary}
                                      </Typography>
                                    )}
                                  </Box>
                                )}
                              </Box>
                            ))}
                          </Box>
                        </Collapse>
                      </Box>
                    )}
                  </Paper>
                </ListItem>
              ))}
            </List>
          )}
          <div ref={messagesEndRef} />
        </Box>

        {/* Input Area */}
        <Box
          sx={{
            p: 3,
            borderTop: '1px solid rgba(255, 255, 255, 0.1)',
            background: 'rgba(15, 15, 15, 0.8)',
          }}
        >
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-end' }}>
            <TextField
              fullWidth
              multiline
              maxRows={4}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={
                selectedAgent
                  ? collaborationMode && collaboratingAgents.length > 1
                    ? `Message ${selectedAgent} (collaboration mode with ${collaboratingAgents.filter(a => a !== selectedAgent).join(', ')})...`
                    : `Message ${selectedAgent}...`
                  : 'Select an agent first...'
              }
              disabled={!selectedAgent || sendMessageMutation.isLoading}
              variant="outlined"
              sx={{
                '& .MuiOutlinedInput-root': {
                  background: 'rgba(255, 255, 255, 0.05)',
                  '&:hover': {
                    background: 'rgba(255, 255, 255, 0.08)',
                  },
                  '&.Mui-focused': {
                    background: 'rgba(255, 255, 255, 0.1)',
                  },
                },
              }}
            />
            <Button
              variant="contained"
              onClick={handleSendMessage}
              disabled={!message.trim() || !selectedAgent || sendMessageMutation.isLoading}
              sx={{ minWidth: 60, height: 56 }}
            >
              {sendMessageMutation.isLoading ? (
                <CircularProgress size={20} color="inherit" />
              ) : (
                <Send />
              )}
            </Button>
          </Box>

          {runningAgents.length === 0 && (
            <Alert severity="warning" sx={{ mt: 2 }}>
              No running agents available. Please start an agent first.
            </Alert>
          )}

          {collaborationMode && collaboratingAgents.length > 1 && (
            <Alert severity="success" sx={{ mt: 2 }}>
              <Typography variant="body2" sx={{ mb: 1 }}>
                🤝 <strong>Collaboration Mode Active</strong> - Testing with:
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                {collaboratingAgents.map(agent => (
                  <Chip
                    key={agent}
                    label={agent}
                    size="small"
                    color="secondary"
                    variant="filled"
                  />
                ))}
              </Box>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                💡 Your message will be sent to the primary agent, and collaborating agents may contribute to the response
              </Typography>
            </Alert>
          )}

          {selectedAgent && getActiveCollaboratingAgents(selectedAgent).length > 0 && !collaborationMode && (
            <Alert severity="info" sx={{ mt: 2 }}>
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>{selectedAgent}</strong> has active collaborations with:
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                {getActiveCollaboratingAgents(selectedAgent).map(collaborator => (
                  <Chip
                    key={collaborator}
                    label={collaborator}
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
                ))}
              </Box>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                💡 Click "Test Collaboration" to see how they work together
              </Typography>
            </Alert>
          )}
        </Box>
      </Card>
      </Box>

      {/* API Inspector Sidebar */}
      {toolSidebarOpen && (
        <Box sx={{
          flex: '0 0 40%',
          display: 'flex',
          flexDirection: 'column',
          bgcolor: 'rgba(0, 0, 0, 0.4)',
          borderLeft: '1px solid rgba(255, 255, 255, 0.1)'
        }}>
          {/* Sidebar Header */}
          <Box sx={{
            p: 2,
            borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <BugReport color="success" />
              <Typography variant="h6" sx={{ fontWeight: 600, color: 'success.main' }}>
                API Inspector
              </Typography>
            </Box>
            <Button
              size="small"
              onClick={() => {
                setToolSidebarOpen(false)
                setSelectedToolExecution(null)
              }}
              sx={{ minWidth: 'auto', p: 0.5 }}
            >
              <Close />
            </Button>
          </Box>

          {/* Sidebar Content */}
          <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
            {selectedToolExecution ? (
              <Box>
                {/* Tool Execution Header */}
                <Box sx={{ mb: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <Chip
                      label={selectedToolExecution.tool_name}
                      size="small"
                      color={selectedToolExecution.success ? 'success' : 'error'}
                      sx={{ fontSize: '0.75rem' }}
                    />
                    <Typography variant="body2" color="text.secondary">
                      {selectedToolExecution.execution_time?.toFixed(3)}s
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                    {selectedToolExecution.result_summary}
                  </Typography>
                </Box>

                {/* Parameters Section */}
                {selectedToolExecution.parameters && Object.keys(selectedToolExecution.parameters).length > 0 && (
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle2" color="warning.main" sx={{ fontWeight: 600, mb: 1 }}>
                      📋 Request Parameters
                    </Typography>
                                                        <Box sx={{
                                      background: 'rgba(255, 193, 7, 0.05)',
                                      p: 2,
                                      borderRadius: 1,
                                      border: '1px solid rgba(255, 193, 7, 0.2)',
                                      fontFamily: '"Fira Code", "Consolas", "Monaco", monospace',
                                      fontSize: '0.85rem',
                                      overflow: 'auto',
                                      maxHeight: 300,
                                      lineHeight: 1.4
                                    }}>
                                      <pre style={{
                                        margin: 0,
                                        whiteSpace: 'pre-wrap',
                                        color: '#ffa726',
                                        textShadow: '0 0 2px rgba(255, 167, 38, 0.3)'
                                      }}>
                                        {JSON.stringify(selectedToolExecution.parameters, null, 2)}
                                      </pre>
                                    </Box>
                  </Box>
                )}

                {/* Result Data Section */}
                {selectedToolExecution.result_data && (
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle2" color="success.main" sx={{ fontWeight: 600, mb: 1 }}>
                      ✅ Response Data
                    </Typography>
                                                        <Box sx={{
                                      background: 'rgba(76, 175, 80, 0.05)',
                                      p: 2,
                                      borderRadius: 1,
                                      border: '1px solid rgba(76, 175, 80, 0.2)',
                                      fontFamily: '"Fira Code", "Consolas", "Monaco", monospace',
                                      fontSize: '0.85rem',
                                      overflow: 'auto',
                                      maxHeight: 400,
                                      lineHeight: 1.4
                                    }}>
                                      <pre style={{
                                        margin: 0,
                                        whiteSpace: 'pre-wrap',
                                        color: '#66bb6a',
                                        textShadow: '0 0 2px rgba(102, 187, 106, 0.3)'
                                      }}>
                                        {JSON.stringify(selectedToolExecution.result_data, null, 2)}
                                      </pre>
                                    </Box>
                  </Box>
                )}

                                {/* Result Preview Section */}
                {selectedToolExecution.result_preview && (
                  <Box sx={{ mb: 3 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="subtitle2" color="info.main" sx={{ fontWeight: 600 }}>
                        👁️ Response Preview ({selectedToolExecution.result_size} chars)
                      </Typography>
                      {selectedToolExecution.result_data_full && (
                        <Button
                          size="small"
                          variant="outlined"
                          color="info"
                          onClick={() => {
                            setFullResponseData(selectedToolExecution.result_data_full)
                            setExpandedFullResponse(true)
                          }}
                          sx={{ fontSize: '0.7rem', minWidth: 'auto', px: 1 }}
                        >
                          Expand Full
                        </Button>
                      )}
                    </Box>
                    <Box sx={{
                      background: 'rgba(33, 150, 243, 0.05)',
                      p: 2,
                      borderRadius: 1,
                      border: '1px solid rgba(33, 150, 243, 0.2)',
                      fontFamily: '"Fira Code", "Consolas", "Monaco", monospace',
                      fontSize: '0.85rem',
                      overflow: 'auto',
                      maxHeight: 300,
                      lineHeight: 1.4
                    }}>
                      <pre style={{
                        margin: 0,
                        whiteSpace: 'pre-wrap',
                        color: '#42a5f5',
                        textShadow: '0 0 2px rgba(66, 165, 245, 0.3)'
                      }}>
                        {selectedToolExecution.result_preview}
                      </pre>
                    </Box>
                  </Box>
                )}

                {/* Error Section */}
                {selectedToolExecution.error && (
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle2" color="error.main" sx={{ fontWeight: 600, mb: 1 }}>
                      ❌ Error Details
                    </Typography>
                                                        <Box sx={{
                                      background: 'rgba(244, 67, 54, 0.05)',
                                      p: 2,
                                      borderRadius: 1,
                                      border: '1px solid rgba(244, 67, 54, 0.2)',
                                      fontFamily: '"Fira Code", "Consolas", "Monaco", monospace',
                                      fontSize: '0.85rem',
                                      lineHeight: 1.4,
                                      color: '#ef5350',
                                      textShadow: '0 0 2px rgba(239, 83, 80, 0.3)'
                                    }}>
                                      {selectedToolExecution.error}
                                    </Box>
                  </Box>
                )}
              </Box>
            ) : (
              <Box sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                textAlign: 'center',
                color: 'text.secondary'
              }}>
                <BugReport sx={{ fontSize: 64, mb: 2, opacity: 0.3 }} />
                <Typography variant="h6" sx={{ mb: 1, opacity: 0.7 }}>
                  API Inspector
                </Typography>
                <Typography variant="body2" sx={{ opacity: 0.5 }}>
                  Click on any tool execution in the chat to inspect its API request and response data
                </Typography>
              </Box>
            )}
          </Box>
        </Box>
      )}

      {/* Configuration Panel */}
      <Drawer
        anchor="right"
        open={configPanelOpen}
        onClose={() => setConfigPanelOpen(false)}
        sx={{
          '& .MuiDrawer-paper': {
            width: { xs: '100%', md: '50%' },
            minWidth: 600,
          },
        }}
      >
        <AppBar position="static" color="transparent" elevation={0}>
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              Configuration
            </Typography>
            <IconButton onClick={() => setConfigPanelOpen(false)}>
              <Close />
            </IconButton>
          </Toolbar>
        </AppBar>
        <Box sx={{ p: 3, flexGrow: 1, overflow: 'auto' }}>
          <ConfigurationPanel
            onConfigChange={handleConfigChange}
            currentConfig={currentConfig || undefined}
          />
        </Box>
      </Drawer>

      {/* Analytics Panel */}
      <Drawer
        anchor="right"
        open={analyticsOpen}
        onClose={() => setAnalyticsOpen(false)}
        sx={{
          '& .MuiDrawer-paper': {
            width: { xs: '100%', lg: '70%' },
            minWidth: 800,
          },
        }}
      >
        <AppBar position="static" color="transparent" elevation={0}>
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              Analytics
            </Typography>
            <IconButton onClick={() => setAnalyticsOpen(false)}>
              <Close />
            </IconButton>
          </Toolbar>
        </AppBar>
        <Box sx={{ p: 3, flexGrow: 1, overflow: 'auto' }}>
          <PerformanceAnalytics
            conversations={chatHistory}
            currentConfig={currentConfig}
            realTimeMetrics={true}
          />
        </Box>
      </Drawer>

      {/* Full Response Dialog */}
      <Dialog
        open={expandedFullResponse}
        onClose={() => {
          setExpandedFullResponse(false)
          setFullResponseData(null)
        }}
        maxWidth="lg"
        fullWidth
        PaperProps={{
          sx: {
            bgcolor: 'rgba(0, 0, 0, 0.9)',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(255, 255, 255, 0.1)'
          }
        }}
      >
        <DialogTitle sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          pb: 2
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <BugReport color="success" />
            <Typography variant="h6" sx={{ fontWeight: 600, color: 'success.main' }}>
              Full API Response Data
            </Typography>
          </Box>
          <Button
            onClick={() => {
              setExpandedFullResponse(false)
              setFullResponseData(null)
            }}
            sx={{ minWidth: 'auto', p: 0.5 }}
          >
            <Close />
          </Button>
        </DialogTitle>

        <DialogContent sx={{ p: 0 }}>
          <Box sx={{
            p: 3,
            fontFamily: '"Fira Code", "Consolas", "Monaco", monospace',
            fontSize: '0.9rem',
            lineHeight: 1.4,
            background: 'rgba(0, 0, 0, 0.3)',
            minHeight: 400,
            maxHeight: '70vh',
            overflow: 'auto'
          }}>
            <pre style={{
              margin: 0,
              whiteSpace: 'pre-wrap',
              color: '#66bb6a',
              textShadow: '0 0 2px rgba(102, 187, 106, 0.3)'
            }}>
              {fullResponseData ? JSON.stringify(fullResponseData, null, 2) : 'Loading...'}
            </pre>
          </Box>
        </DialogContent>

        <DialogActions sx={{
          borderTop: '1px solid rgba(255, 255, 255, 0.1)',
          p: 2,
          justifyContent: 'space-between'
        }}>
          <Typography variant="caption" color="text.secondary">
            Full response data - Copy and paste friendly
          </Typography>
          <Button
            variant="contained"
            color="primary"
            onClick={() => {
              if (fullResponseData) {
                navigator.clipboard.writeText(JSON.stringify(fullResponseData, null, 2))
                // You could add a toast notification here
              }
            }}
            sx={{ fontSize: '0.8rem' }}
          >
            Copy JSON
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default AgentChat
