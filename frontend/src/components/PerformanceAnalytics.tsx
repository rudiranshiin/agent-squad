import React, { useState, useEffect } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  IconButton,
  Tooltip,
  Alert,
  Stack,
  Button,
} from '@mui/material'
import {
  Timer,
  Memory,
  TrendingUp,
  TrendingDown,
  Speed,
  Analytics,
  Warning,
  CheckCircle,
  Error,
  Refresh,
  Download,
  Compare,
} from '@mui/icons-material'

interface PerformanceMetric {
  name: string
  value: number
  unit: string
  trend: 'up' | 'down' | 'stable'
  status: 'good' | 'warning' | 'error'
  threshold?: number
}

interface ConversationStats {
  total_messages: number
  avg_response_time: number
  total_tokens_used: number
  total_cost: number
  error_rate: number
  success_rate: number
}

interface ModelComparison {
  model: string
  avg_response_time: number
  token_efficiency: number
  quality_score: number
  cost_per_token: number
}

interface PerformanceAnalyticsProps {
  conversations?: any[]
  currentConfig?: any
  realTimeMetrics?: boolean
}

const PerformanceAnalytics: React.FC<PerformanceAnalyticsProps> = ({
  conversations = [],
  currentConfig,
  realTimeMetrics = true,
}) => {
  const [metrics, setMetrics] = useState<PerformanceMetric[]>([])
  const [conversationStats, setConversationStats] = useState<ConversationStats | null>(null)
  const [modelComparisons, setModelComparisons] = useState<ModelComparison[]>([])
  const [isLoading, setIsLoading] = useState(false)

  // Mock data generation for demonstration
  useEffect(() => {
    generateMockMetrics()
    generateMockStats()
    generateMockComparisons()
  }, [conversations])

  const generateMockMetrics = () => {
    const mockMetrics: PerformanceMetric[] = [
      {
        name: 'Average Response Time',
        value: 2.4,
        unit: 's',
        trend: 'down',
        status: 'good',
        threshold: 5.0,
      },
      {
        name: 'Token Usage Rate',
        value: 850,
        unit: 'tokens/min',
        trend: 'up',
        status: 'warning',
        threshold: 1000,
      },
      {
        name: 'Success Rate',
        value: 98.5,
        unit: '%',
        trend: 'stable',
        status: 'good',
        threshold: 95,
      },
      {
        name: 'Error Rate',
        value: 1.5,
        unit: '%',
        trend: 'down',
        status: 'good',
        threshold: 5,
      },
      {
        name: 'Memory Usage',
        value: 72,
        unit: '%',
        trend: 'up',
        status: 'warning',
        threshold: 80,
      },
      {
        name: 'API Latency',
        value: 320,
        unit: 'ms',
        trend: 'stable',
        status: 'good',
        threshold: 500,
      },
    ]
    setMetrics(mockMetrics)
  }

  const generateMockStats = () => {
    const stats: ConversationStats = {
      total_messages: conversations.length || 156,
      avg_response_time: 2.4,
      total_tokens_used: 45620,
      total_cost: 12.34,
      error_rate: 1.5,
      success_rate: 98.5,
    }
    setConversationStats(stats)
  }

  const generateMockComparisons = () => {
    const comparisons: ModelComparison[] = [
      {
        model: 'GPT-4o',
        avg_response_time: 2.1,
        token_efficiency: 85,
        quality_score: 92,
        cost_per_token: 0.00003,
      },
      {
        model: 'GPT-4 Turbo',
        avg_response_time: 1.8,
        token_efficiency: 78,
        quality_score: 89,
        cost_per_token: 0.00001,
      },
      {
        model: 'Claude 3.5 Sonnet',
        avg_response_time: 2.7,
        token_efficiency: 90,
        quality_score: 94,
        cost_per_token: 0.00003,
      },
    ]
    setModelComparisons(comparisons)
  }

  const refreshMetrics = () => {
    setIsLoading(true)
    setTimeout(() => {
      generateMockMetrics()
      generateMockStats()
      setIsLoading(false)
    }, 1000)
  }

  const exportData = () => {
    const data = {
      metrics,
      conversationStats,
      modelComparisons,
      timestamp: new Date().toISOString(),
    }
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `performance_analytics_${new Date().toISOString().split('T')[0]}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'good': return 'success'
      case 'warning': return 'warning'
      case 'error': return 'error'
      default: return 'default'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'good': return <CheckCircle color="success" />
      case 'warning': return <Warning color="warning" />
      case 'error': return <Error color="error" />
      default: return null
    }
  }

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return <TrendingUp color="primary" />
      case 'down': return <TrendingDown color="secondary" />
      default: return null
    }
  }

  const getProgressValue = (value: number, threshold?: number) => {
    if (!threshold) return Math.min(value, 100)
    return Math.min((value / threshold) * 100, 100)
  }

  return (
    <Box sx={{ width: '100%' }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Analytics color="primary" />
          <Typography variant="h5" fontWeight={600}>
            Performance Analytics
          </Typography>
          {realTimeMetrics && (
            <Chip label="Real-time" size="small" color="success" variant="outlined" />
          )}
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<Compare />}
            size="small"
          >
            Compare Models
          </Button>
          <Button
            variant="outlined"
            startIcon={<Download />}
            onClick={exportData}
            size="small"
          >
            Export Data
          </Button>
          <IconButton onClick={refreshMetrics} disabled={isLoading}>
            <Refresh />
          </IconButton>
        </Box>
      </Box>

      {/* Key Metrics Overview */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {metrics.map((metric, index) => (
          <Grid item xs={12} sm={6} md={4} key={index}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2" color="text.secondary" fontWeight={500}>
                    {metric.name}
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    {getTrendIcon(metric.trend)}
                    {getStatusIcon(metric.status)}
                  </Box>
                </Box>

                <Typography variant="h4" fontWeight={700} sx={{ mb: 1 }}>
                  {metric.value}
                  <Typography component="span" variant="body1" color="text.secondary" sx={{ ml: 0.5 }}>
                    {metric.unit}
                  </Typography>
                </Typography>

                {metric.threshold && (
                  <Box sx={{ mt: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="caption" color="text.secondary">
                        Usage
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {metric.threshold} {metric.unit} limit
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={getProgressValue(metric.value, metric.threshold)}
                      color={getStatusColor(metric.status) as any}
                      sx={{ height: 6, borderRadius: 3 }}
                    />
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={3}>
        {/* Conversation Statistics */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Conversation Statistics
              </Typography>

              {conversationStats && (
                <List>
                  <ListItem>
                    <ListItemIcon>
                      <Timer />
                    </ListItemIcon>
                    <ListItemText
                      primary="Total Messages"
                      secondary={conversationStats.total_messages.toLocaleString()}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <Speed />
                    </ListItemIcon>
                    <ListItemText
                      primary="Avg Response Time"
                      secondary={`${conversationStats.avg_response_time}s`}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <Memory />
                    </ListItemIcon>
                    <ListItemText
                      primary="Total Tokens Used"
                      secondary={conversationStats.total_tokens_used.toLocaleString()}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <Analytics />
                    </ListItemIcon>
                    <ListItemText
                      primary="Total Cost"
                      secondary={`$${conversationStats.total_cost.toFixed(2)}`}
                    />
                  </ListItem>
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Model Comparison */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Model Performance Comparison
              </Typography>

              <Stack spacing={2}>
                {modelComparisons.map((model, index) => (
                  <Box key={index}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Typography variant="body1" fontWeight={500}>
                        {model.model}
                      </Typography>
                      <Chip
                        label={`${model.quality_score}% quality`}
                        size="small"
                        color={model.quality_score >= 90 ? 'success' : 'warning'}
                      />
                    </Box>

                    <Grid container spacing={2}>
                      <Grid item xs={3}>
                        <Typography variant="caption" color="text.secondary">
                          Response Time
                        </Typography>
                        <Typography variant="body2" fontWeight={500}>
                          {model.avg_response_time}s
                        </Typography>
                      </Grid>
                      <Grid item xs={3}>
                        <Typography variant="caption" color="text.secondary">
                          Efficiency
                        </Typography>
                        <Typography variant="body2" fontWeight={500}>
                          {model.token_efficiency}%
                        </Typography>
                      </Grid>
                      <Grid item xs={3}>
                        <Typography variant="caption" color="text.secondary">
                          Quality
                        </Typography>
                        <Typography variant="body2" fontWeight={500}>
                          {model.quality_score}%
                        </Typography>
                      </Grid>
                      <Grid item xs={3}>
                        <Typography variant="caption" color="text.secondary">
                          Cost/Token
                        </Typography>
                        <Typography variant="body2" fontWeight={500}>
                          ${model.cost_per_token.toFixed(5)}
                        </Typography>
                      </Grid>
                    </Grid>

                    {index < modelComparisons.length - 1 && <Divider sx={{ mt: 2 }} />}
                  </Box>
                ))}
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Performance Alerts */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Performance Alerts & Recommendations
          </Typography>

          <Stack spacing={2}>
            {metrics.filter(m => m.status === 'warning' || m.status === 'error').length > 0 ? (
              metrics
                .filter(m => m.status === 'warning' || m.status === 'error')
                .map((metric, index) => (
                  <Alert
                    key={index}
                    severity={metric.status === 'error' ? 'error' : 'warning'}
                    sx={{ borderRadius: 2 }}
                  >
                    <Typography variant="body2">
                      <strong>{metric.name}</strong> is {metric.status === 'error' ? 'critical' : 'elevated'} at{' '}
                      {metric.value} {metric.unit}
                      {metric.threshold && ` (threshold: ${metric.threshold} ${metric.unit})`}
                    </Typography>
                  </Alert>
                ))
            ) : (
              <Alert severity="success" sx={{ borderRadius: 2 }}>
                <Typography variant="body2">
                  All performance metrics are within acceptable ranges. System is operating optimally.
                </Typography>
              </Alert>
            )}
          </Stack>
        </CardContent>
      </Card>
    </Box>
  )
}

export default PerformanceAnalytics
