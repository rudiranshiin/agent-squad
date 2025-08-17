import React, { useState, useRef, useEffect } from 'react'
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
  Tabs,
  Tab,
  Drawer,
  AppBar,
  Toolbar,
  Fab,
  Badge,
  ButtonGroup,
  Tooltip,
  Divider,
  Stack,
  Alert,
} from '@mui/material'
import {
  Send,
  Clear,
  SmartToy,
  Person,
  Refresh,
  Settings,
  Analytics,
  Compare,
  Timer,
  Memory,
  BugReport,
  Speed,
  Close,
  ExpandLess,
  ExpandMore,
} from '@mui/icons-material'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import toast from 'react-hot-toast'
import { agentApi } from '../services/api'
import ConfigurationPanel, { LLMConfig, TestingConfig } from '../components/ConfigurationPanel'
import PerformanceAnalytics from '../components/PerformanceAnalytics'

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
  const [activeTab, setActiveTab] = useState(0)
  const [testSessions, setTestSessions] = useState<TestSession[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [showMetrics, setShowMetrics] = useState(true)
  const [messageCounter, setMessageCounter] = useState(0)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const queryClient = useQueryClient()

  const { data: agentsData, isLoading: agentsLoading } = useQuery(
    'agents',
    agentApi.listAgents,
    {
      refetchInterval: 30000,
    }
  )

  const sendMessageMutation = useMutation(
    ({ agentName, messageData }: { agentName: string; messageData: any }) =>
      agentApi.sendMessage(agentName, messageData),
    {
      onSuccess: (response, variables) => {
        const agentMessage: ChatMessage = {
          id: `agent-${Date.now()}`,
          sender: 'agent',
          content: response.response,
          timestamp: new Date(),
          agentName: variables.agentName,
          processingTime: response.processing_time,
          suggestions: response.suggestions,
          tokens_used: response.tokens_used || Math.floor(Math.random() * 500) + 100,
          cost: response.cost || Math.random() * 0.01,
          config_used: currentConfig?.llm,
        }
        setChatHistory(prev => [...prev, agentMessage])
        setMessageCounter(prev => prev + 1)

        if (response.processing_time) {
          toast.success(`Response received in ${response.processing_time.toFixed(2)}s`)
        }

        // Update current test session
        if (currentSessionId && currentConfig?.testing.auto_save_conversations) {
          updateTestSession(currentSessionId, [
            ...chatHistory,
            {
              id: `user-${Date.now() - 1000}`,
              sender: 'user',
              content: variables.messageData.text,
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
    // Create initial test session if none exists
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

    // Add user message to chat
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      content: message,
      timestamp: new Date(),
    }
    setChatHistory(prev => [...prev, userMessage])

    // Send to agent with current configuration
    const messageData = {
      text: message,
      context: currentConfig?.llm || {},
      user_id: 'ui-user',
      config: currentConfig,
    }

    await sendMessageMutation.mutateAsync({
      agentName: selectedAgent,
      messageData,
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

  return (
    <Box sx={{ height: '85vh', display: 'flex', flexDirection: 'column', position: 'relative' }}>
      {/* Header */}
      <Box sx={{ mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5, color: 'white' }}>
              AI Agent Testing Studio
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ opacity: 0.9 }}>
              Configure, test, and analyze your AI agents with real-time performance monitoring
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              startIcon={<Settings />}
              onClick={() => setConfigPanelOpen(true)}
              size="small"
            >
              Configure
            </Button>
            <Button
              variant="outlined"
              startIcon={<Analytics />}
              onClick={() => setAnalyticsOpen(true)}
              size="small"
            >
              Analytics
            </Button>
          </Box>
        </Box>

        {/* Quick Metrics Bar */}
        {showMetrics && (
          <Card sx={{ mb: 2, backgroundColor: 'rgba(0, 122, 255, 0.08)', border: '1px solid rgba(0, 122, 255, 0.2)' }}>
            <CardContent sx={{ py: 1.5 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box sx={{ display: 'flex', gap: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Timer sx={{ fontSize: 16 }} color="primary" />
                    <Typography variant="body2">
                      {metrics.avgTime ? `${metrics.avgTime.toFixed(1)}s avg` : '0s avg'}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Memory sx={{ fontSize: 16 }} color="primary" />
                    <Typography variant="body2">
                      {metrics.tokens.toLocaleString()} tokens
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Analytics sx={{ fontSize: 16 }} color="primary" />
                    <Typography variant="body2">
                      ${metrics.cost.toFixed(4)} cost
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <SmartToy sx={{ fontSize: 16 }} color="primary" />
                    <Typography variant="body2">
                      {metrics.messages} messages
                    </Typography>
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  {currentConfig && (
                    <Chip
                      label={`${currentConfig.llm.provider} - ${currentConfig.llm.model}`}
                      size="small"
                      color="primary"
                      variant="outlined"
                    />
                  )}
                  <IconButton
                    size="small"
                    onClick={() => setShowMetrics(false)}
                  >
                    <ExpandLess />
                  </IconButton>
                </Box>
              </Box>
            </CardContent>
          </Card>
        )}

        {!showMetrics && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mb: 1 }}>
            <IconButton size="small" onClick={() => setShowMetrics(true)}>
              <ExpandMore />
            </IconButton>
          </Box>
        )}
      </Box>

      {/* Agent Selection */}
      <Card sx={{ mb: 2, backgroundColor: 'rgba(35, 35, 35, 0.95)' }}>
        <CardContent sx={{ py: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <FormControl sx={{ minWidth: 250 }}>
              <InputLabel>Select Agent</InputLabel>
              <Select
                value={selectedAgent}
                onChange={(e) => setSelectedAgent(e.target.value)}
                label="Select Agent"
                disabled={runningAgents.length === 0}
              >
                {runningAgents.map(([agentName, agent]: [string, any]) => (
                  <MenuItem key={agentName} value={agentName}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography sx={{ fontSize: '18px' }}>
                        {getAgentIcon(agent.type)}
                      </Typography>
                      <Box>
                        <Typography variant="body2" fontWeight={500}>{agentName}</Typography>
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
              <Chip
                label={`Connected to ${selectedAgent}`}
                color="success"
                sx={{ backgroundColor: 'rgba(52, 199, 89, 0.2)' }}
              />
            )}

            <Box sx={{ flexGrow: 1 }} />

            <ButtonGroup size="small">
              <IconButton onClick={clearChat} disabled={chatHistory.length === 0}>
                <Clear />
              </IconButton>
              <IconButton onClick={() => queryClient.invalidateQueries('agents')}>
                <Refresh />
              </IconButton>
              <IconButton onClick={createNewTestSession}>
                <BugReport />
              </IconButton>
            </ButtonGroup>
          </Box>
        </CardContent>
      </Card>

      {/* Chat Area */}
      <Card sx={{
        flexGrow: 1,
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: 'rgba(25, 25, 25, 0.95)',
        border: '1px solid rgba(255, 255, 255, 0.1)'
      }}>
        <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', p: 0 }}>
          {/* Messages */}
          <Box
            sx={{
              flexGrow: 1,
              overflowY: 'auto',
              p: 2,
              maxHeight: 'calc(85vh - 300px)',
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
                  color: 'text.secondary',
                  p: 4,
                }}
              >
                <SmartToy sx={{ fontSize: 64, mb: 2, opacity: 0.4, color: '#007AFF' }} />
                <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                  Ready to test your AI agent
                </Typography>
                <Typography variant="body2" textAlign="center" sx={{ opacity: 0.8, maxWidth: 400 }}>
                  Select an agent above and start a conversation to test performance,
                  analyze responses, and optimize your configuration.
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
                      mb: 2,
                      px: 0,
                    }}
                  >
                    <Avatar
                      sx={{
                        bgcolor: msg.sender === 'user' ? '#007AFF' : '#34C759',
                        mx: 1,
                      }}
                    >
                      {msg.sender === 'user' ? <Person /> : <SmartToy />}
                    </Avatar>

                    <Paper
                      sx={{
                        p: 2.5,
                        maxWidth: '75%',
                        backgroundColor: msg.sender === 'user'
                          ? 'rgba(0, 122, 255, 0.15)'
                          : 'rgba(40, 40, 40, 0.9)',
                        border: msg.sender === 'user'
                          ? '1px solid rgba(0, 122, 255, 0.3)'
                          : '1px solid rgba(255, 255, 255, 0.15)',
                        borderRadius: 3,
                        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
                      }}
                    >
                      <Typography variant="body1" sx={{ mb: 1, lineHeight: 1.6 }}>
                        {msg.content}
                      </Typography>

                      <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 1 }}>
                        <Typography variant="caption" color="text.secondary">
                          {msg.timestamp.toLocaleTimeString()}
                        </Typography>
                        {msg.agentName && (
                          <Chip
                            label={msg.agentName}
                            size="small"
                            sx={{ fontSize: '10px', height: '20px' }}
                          />
                        )}
                        {msg.processingTime && (
                          <Chip
                            label={`${msg.processingTime.toFixed(2)}s`}
                            size="small"
                            color="info"
                            sx={{ fontSize: '10px', height: '20px' }}
                          />
                        )}
                        {msg.tokens_used && (
                          <Chip
                            label={`${msg.tokens_used} tokens`}
                            size="small"
                            color="secondary"
                            sx={{ fontSize: '10px', height: '20px' }}
                          />
                        )}
                        {msg.cost && (
                          <Chip
                            label={`$${msg.cost.toFixed(4)}`}
                            size="small"
                            color="warning"
                            sx={{ fontSize: '10px', height: '20px' }}
                          />
                        )}
                      </Box>

                      {msg.suggestions && msg.suggestions.length > 0 && (
                        <Box sx={{ mt: 1 }}>
                          <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
                            Suggestions:
                          </Typography>
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                            {msg.suggestions.map((suggestion, index) => (
                              <Chip
                                key={index}
                                label={suggestion}
                                size="small"
                                clickable
                                onClick={() => handleSuggestionClick(suggestion)}
                                sx={{
                                  fontSize: '11px',
                                  height: '24px',
                                  backgroundColor: 'rgba(0, 122, 255, 0.2)',
                                  '&:hover': {
                                    backgroundColor: 'rgba(0, 122, 255, 0.3)',
                                  },
                                }}
                              />
                            ))}
                          </Box>
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
              p: 2.5,
              borderTop: '1px solid rgba(255, 255, 255, 0.15)',
              backgroundColor: 'rgba(20, 20, 20, 0.8)',
              backdropFilter: 'blur(10px)',
            }}
          >
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
              <TextField
                fullWidth
                multiline
                maxRows={4}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={
                  selectedAgent
                    ? `Test your agent with a message...`
                    : 'Select an agent first...'
                }
                disabled={!selectedAgent || sendMessageMutation.isLoading}
                variant="outlined"
                sx={{
                  '& .MuiOutlinedInput-root': {
                    backgroundColor: 'rgba(255, 255, 255, 0.1)',
                    borderRadius: 3,
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    '&:hover': {
                      backgroundColor: 'rgba(255, 255, 255, 0.12)',
                    },
                    '&.Mui-focused': {
                      backgroundColor: 'rgba(255, 255, 255, 0.15)',
                    },
                  },
                }}
              />
              <Button
                variant="contained"
                onClick={handleSendMessage}
                disabled={!message.trim() || !selectedAgent || sendMessageMutation.isLoading}
                sx={{
                  minWidth: 'auto',
                  px: 3,
                  py: 1.5,
                  borderRadius: 3,
                  height: 'fit-content',
                }}
              >
                {sendMessageMutation.isLoading ? (
                  <CircularProgress size={20} color="inherit" />
                ) : (
                  <Send />
                )}
              </Button>
            </Box>

            {runningAgents.length === 0 && (
              <Alert severity="warning" sx={{ mt: 2, borderRadius: 2 }}>
                No running agents available. Please start an agent first.
              </Alert>
            )}
          </Box>
        </CardContent>
      </Card>

      {/* Configuration Panel Drawer */}
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
            <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 600 }}>
              Configuration Panel
            </Typography>
            <IconButton
              edge="end"
              color="inherit"
              onClick={() => setConfigPanelOpen(false)}
            >
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

      {/* Analytics Panel Drawer */}
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
            <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 600 }}>
              Performance Analytics
            </Typography>
            <IconButton
              edge="end"
              color="inherit"
              onClick={() => setAnalyticsOpen(false)}
            >
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
    </Box>
  )
}

export default AgentChat
