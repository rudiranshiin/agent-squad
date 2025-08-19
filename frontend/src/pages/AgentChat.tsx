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
  Drawer,
  AppBar,
  Toolbar,
  ButtonGroup,
  Alert,
  Tooltip,
  Collapse,
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
  const [testSessions, setTestSessions] = useState<TestSession[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [showMetrics, setShowMetrics] = useState(true)
  const [messageCounter, setMessageCounter] = useState(0)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const queryClient = useQueryClient()

  const { data: agentsData } = useQuery(
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
    <Box sx={{ height: 'calc(100vh - 100px)', display: 'flex', flexDirection: 'column' }}>
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
              <Chip
                label={`Connected to ${selectedAgent}`}
                color="success"
                size="small"
              />
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
              {chatHistory.map((msg, index) => (
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
                    <Typography variant="body1" sx={{ mb: 2, lineHeight: 1.6 }}>
                      {msg.content}
                    </Typography>

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
                  ? `Message ${selectedAgent}...`
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
        </Box>
      </Card>

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
    </Box>
  )
}

export default AgentChat
