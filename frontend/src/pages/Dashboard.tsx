import React from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  LinearProgress,
  IconButton,
  Alert,
  Tooltip,
  CircularProgress,
} from '@mui/material'
import {
  Refresh,
  TrendingUp,
  Speed,
  Memory,
  Psychology,
} from '@mui/icons-material'
import { useQuery, useQueryClient } from 'react-query'
import { agentApi, systemApi, moduleApi } from '../services/api'

const StatCard: React.FC<{
  title: string
  value: string | number
  subtitle?: string
  icon?: React.ReactNode
  color?: string
  progress?: number
}> = ({ title, value, subtitle, icon, color = '#667eea', progress }) => {
  return (
    <Card
      sx={{
        height: '100%',
        background: `linear-gradient(135deg, ${color}20 0%, ${color}10 100%)`,
        border: `1px solid ${color}30`,
      }}
    >
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="h6" sx={{ fontSize: '14px', fontWeight: 600, color: 'text.secondary' }}>
            {title}
          </Typography>
          {icon && (
            <Box sx={{ color: color }}>
              {icon}
            </Box>
          )}
        </Box>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          {value}
        </Typography>
        {subtitle && (
          <Typography variant="body2" color="text.secondary" sx={{ fontSize: '12px' }}>
            {subtitle}
          </Typography>
        )}
        {progress !== undefined && (
          <Box sx={{ mt: 2 }}>
            <LinearProgress
              variant="determinate"
              value={progress}
              sx={{
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                '& .MuiLinearProgress-bar': {
                  backgroundColor: color,
                },
              }}
            />
            <Typography variant="body2" color="text.secondary" sx={{ fontSize: '11px', mt: 0.5 }}>
              {progress.toFixed(1)}% utilization
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  )
}

const AgentStatusCard: React.FC<{ agentName: string; agent: any }> = ({ agentName, agent }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return '#4caf50'
      case 'stopped': return '#f44336'
      default: return '#ff9800'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'cooking_assistant': return '👨‍🍳'
      case 'language_teacher': return '👨‍🏫'
      case 'weather_assistant': return '🌤️'
      case 'fitness_coach': return '💪'
      case 'study_assistant': return '📚'
      default: return '🤖'
    }
  }

  return (
    <Card
      sx={{
        background: 'rgba(255, 255, 255, 0.02)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        transition: 'all 0.3s ease',
        '&:hover': {
          backgroundColor: 'rgba(255, 255, 255, 0.05)',
          transform: 'translateY(-2px)',
        },
      }}
    >
      <CardContent sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <Typography sx={{ fontSize: '20px' }}>
            {getTypeIcon(agent.type)}
          </Typography>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: '14px' }}>
              {agentName}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ fontSize: '12px' }}>
              {agent.type}
            </Typography>
          </Box>
          <Chip
            label={agent.status}
            size="small"
            sx={{
              backgroundColor: getStatusColor(agent.status),
              color: 'white',
              fontSize: '10px',
              height: '20px',
            }}
          />
        </Box>

        {agent.module && (
          <Chip
            label={agent.module}
            size="small"
            variant="outlined"
            sx={{
              fontSize: '10px',
              height: '18px',
              borderColor: 'rgba(255, 255, 255, 0.3)',
            }}
          />
        )}
      </CardContent>
    </Card>
  )
}

const Dashboard: React.FC = () => {
  const queryClient = useQueryClient()

  const { data: healthData, isLoading: healthLoading } = useQuery(
    'health',
    systemApi.getHealth,
    {
      refetchInterval: 30000,
    }
  )

  const { data: agentsData, isLoading: agentsLoading } = useQuery(
    'agents',
    agentApi.listAgents,
    {
      refetchInterval: 15000,
    }
  )

  const { data: modulesData, isLoading: modulesLoading } = useQuery(
    'modules',
    moduleApi.listModules,
    {
      refetchInterval: 20000,
    }
  )

  const { data: performanceData } = useQuery(
    'performance',
    systemApi.getPerformance,
    {
      refetchInterval: 10000,
    }
  )

  const refreshAll = () => {
    queryClient.invalidateQueries()
  }

  const isLoading = healthLoading || agentsLoading || modulesLoading

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <CircularProgress size={60} />
      </Box>
    )
  }

  const agents = agentsData?.agents || {}
  const agentEntries = Object.entries(agents)
  const runningAgents = agentEntries.filter(([, agent]: [string, any]) => agent.status === 'running').length
  const totalAgents = agentEntries.length

  const modules = modulesData?.modules || []
  const moduleStatus = modulesData?.status || {}

  // Calculate performance metrics
  const avgResponseTime = performanceData?.avg_response_time || 0

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
            Framework Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Monitor your agentic AI framework performance and status
          </Typography>
        </Box>
        <Tooltip title="Refresh all data">
          <IconButton onClick={refreshAll} sx={{ backgroundColor: 'rgba(255, 255, 255, 0.1)' }}>
            <Refresh />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Status Alert */}
      {healthData && (
        <Alert
          severity={healthData.status === 'healthy' ? 'success' : 'warning'}
          sx={{ mb: 3, backgroundColor: 'rgba(255, 255, 255, 0.05)', border: '1px solid rgba(255, 255, 255, 0.1)' }}
        >
          Framework Status: {healthData.status.toUpperCase()} - Version {healthData.version}
        </Alert>
      )}

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active Agents"
            value={`${runningAgents}/${totalAgents}`}
            subtitle={totalAgents > 0 ? `${((runningAgents / totalAgents) * 100).toFixed(1)}% running` : 'No agents'}
            icon={<Psychology />}
            color="#4caf50"
            progress={totalAgents > 0 ? (runningAgents / totalAgents) * 100 : 0}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Loaded Modules"
            value={modules.length}
            subtitle={`${Object.keys(moduleStatus).length} active modules`}
            icon={<Memory />}
            color="#2196f3"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Avg Response Time"
            value={`${avgResponseTime.toFixed(2)}ms`}
            subtitle="Message processing speed"
            icon={<Speed />}
            color="#ff9800"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Performance Score"
            value={healthData?.status === 'healthy' ? '98%' : '75%'}
            subtitle="Overall system health"
            icon={<TrendingUp />}
            color="#9c27b0"
            progress={healthData?.status === 'healthy' ? 98 : 75}
          />
        </Grid>
      </Grid>

      {/* Agents Overview */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                Active Agents
              </Typography>
              {totalAgents === 0 ? (
                <Alert severity="info">
                  No agents found. Create your first agent using the Module Manager.
                </Alert>
              ) : (
                <Grid container spacing={2}>
                  {agentEntries.map(([agentName, agent]: [string, any]) => (
                    <Grid item xs={12} sm={6} key={agentName}>
                      <AgentStatusCard agentName={agentName} agent={agent} />
                    </Grid>
                  ))}
                </Grid>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                System Resources
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Memory Usage
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={65}
                    sx={{
                      height: 8,
                      borderRadius: 4,
                      backgroundColor: 'rgba(255, 255, 255, 0.1)',
                    }}
                  />
                  <Typography variant="body2" color="text.secondary" sx={{ fontSize: '11px', mt: 0.5 }}>
                    65% of available memory
                  </Typography>
                </Box>

                <Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    CPU Usage
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={32}
                    sx={{
                      height: 8,
                      borderRadius: 4,
                      backgroundColor: 'rgba(255, 255, 255, 0.1)',
                    }}
                  />
                  <Typography variant="body2" color="text.secondary" sx={{ fontSize: '11px', mt: 0.5 }}>
                    32% CPU utilization
                  </Typography>
                </Box>

                <Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Token Usage
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={78}
                    sx={{
                      height: 8,
                      borderRadius: 4,
                      backgroundColor: 'rgba(255, 255, 255, 0.1)',
                    }}
                  />
                  <Typography variant="body2" color="text.secondary" sx={{ fontSize: '11px', mt: 0.5 }}>
                    78% of token limit
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                Quick Actions
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Chip
                  label="Create New Agent"
                  clickable
                  sx={{ backgroundColor: 'rgba(102, 126, 234, 0.2)', color: 'white', justifyContent: 'flex-start' }}
                />
                <Chip
                  label="Install Module"
                  clickable
                  sx={{ backgroundColor: 'rgba(118, 75, 162, 0.2)', color: 'white', justifyContent: 'flex-start' }}
                />
                <Chip
                  label="Optimize Performance"
                  clickable
                  sx={{ backgroundColor: 'rgba(76, 175, 80, 0.2)', color: 'white', justifyContent: 'flex-start' }}
                />
                <Chip
                  label="View Logs"
                  clickable
                  sx={{ backgroundColor: 'rgba(255, 152, 0, 0.2)', color: 'white', justifyContent: 'flex-start' }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}

export default Dashboard
