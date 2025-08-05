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
} from '@mui/material'
import {
  Send,
  Clear,
  SmartToy,
  Person,
  Refresh,
} from '@mui/icons-material'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import toast from 'react-hot-toast'
import { agentApi } from '../services/api'

interface ChatMessage {
  id: string
  sender: 'user' | 'agent'
  content: string
  timestamp: Date
  agentName?: string
  processingTime?: number
  suggestions?: string[]
}

const AgentChat: React.FC = () => {
  const [selectedAgent, setSelectedAgent] = useState<string>('')
  const [message, setMessage] = useState<string>('')
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([])
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
        // Add agent response to chat
        const agentMessage: ChatMessage = {
          id: `agent-${Date.now()}`,
          sender: 'agent',
          content: response.response,
          timestamp: new Date(),
          agentName: variables.agentName,
          processingTime: response.processing_time,
          suggestions: response.suggestions,
        }
        setChatHistory(prev => [...prev, agentMessage])

        // Show success toast with processing time
        if (response.processing_time) {
          toast.success(`Response received in ${response.processing_time.toFixed(2)}s`)
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

    // Send to agent
    await sendMessageMutation.mutateAsync({
      agentName: selectedAgent,
      messageData: {
        text: message,
        context: {},
        user_id: 'ui-user',
      },
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
  }

  const handleSuggestionClick = (suggestion: string) => {
    setMessage(suggestion)
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

  const agents = agentsData?.agents || {}
  const runningAgents = Object.entries(agents).filter(([, agent]: [string, any]) => agent.status === 'running')

  return (
    <Box sx={{ height: '80vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Agent Chat Interface
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Chat directly with your AI agents and test their capabilities
        </Typography>
      </Box>

      {/* Agent Selection */}
      <Card sx={{ mb: 2 }}>
        <CardContent sx={{ py: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <FormControl sx={{ minWidth: 200 }}>
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
                        <Typography variant="body2">{agentName}</Typography>
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
                sx={{ backgroundColor: 'rgba(76, 175, 80, 0.2)' }}
              />
            )}

            <IconButton onClick={clearChat} disabled={chatHistory.length === 0}>
              <Clear />
            </IconButton>

            <IconButton onClick={() => queryClient.invalidateQueries('agents')}>
              <Refresh />
            </IconButton>
          </Box>
        </CardContent>
      </Card>

      {/* Chat Area */}
      <Card sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
        <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', p: 0 }}>
          {/* Messages */}
          <Box
            sx={{
              flexGrow: 1,
              overflowY: 'auto',
              p: 2,
              maxHeight: '50vh',
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
                }}
              >
                <SmartToy sx={{ fontSize: 64, mb: 2, opacity: 0.5 }} />
                <Typography variant="h6" gutterBottom>
                  No conversation yet
                </Typography>
                <Typography variant="body2">
                  Select an agent and start chatting to test the framework
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
                        bgcolor: msg.sender === 'user' ? '#667eea' : '#4caf50',
                        mx: 1,
                      }}
                    >
                      {msg.sender === 'user' ? <Person /> : <SmartToy />}
                    </Avatar>

                    <Paper
                      sx={{
                        p: 2,
                        maxWidth: '70%',
                        backgroundColor: msg.sender === 'user'
                          ? 'rgba(102, 126, 234, 0.1)'
                          : 'rgba(255, 255, 255, 0.05)',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                      }}
                    >
                      <Typography variant="body1" sx={{ mb: 1 }}>
                        {msg.content}
                      </Typography>

                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="caption" color="text.secondary">
                          {msg.timestamp.toLocaleTimeString()}
                        </Typography>
                        {msg.agentName && (
                          <Chip
                            label={msg.agentName}
                            size="small"
                            sx={{ fontSize: '10px', height: '18px' }}
                          />
                        )}
                        {msg.processingTime && (
                          <Chip
                            label={`${msg.processingTime.toFixed(2)}s`}
                            size="small"
                            color="info"
                            sx={{ fontSize: '10px', height: '18px' }}
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
                                  backgroundColor: 'rgba(102, 126, 234, 0.2)',
                                  '&:hover': {
                                    backgroundColor: 'rgba(102, 126, 234, 0.3)',
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
              p: 2,
              borderTop: '1px solid rgba(255, 255, 255, 0.1)',
              backgroundColor: 'rgba(255, 255, 255, 0.02)',
            }}
          >
            <Box sx={{ display: 'flex', gap: 1 }}>
              <TextField
                fullWidth
                multiline
                maxRows={3}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={
                  selectedAgent
                    ? `Type a message to ${selectedAgent}...`
                    : 'Select an agent first...'
                }
                disabled={!selectedAgent || sendMessageMutation.isLoading}
                variant="outlined"
                sx={{
                  '& .MuiOutlinedInput-root': {
                    backgroundColor: 'rgba(255, 255, 255, 0.05)',
                  },
                }}
              />
              <Button
                variant="contained"
                onClick={handleSendMessage}
                disabled={!message.trim() || !selectedAgent || sendMessageMutation.isLoading}
                sx={{ minWidth: 'auto', px: 2 }}
              >
                {sendMessageMutation.isLoading ? (
                  <CircularProgress size={20} color="inherit" />
                ) : (
                  <Send />
                )}
              </Button>
            </Box>

            {runningAgents.length === 0 && (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                No running agents available. Please start an agent first.
              </Typography>
            )}
          </Box>
        </CardContent>
      </Card>
    </Box>
  )
}

export default AgentChat
