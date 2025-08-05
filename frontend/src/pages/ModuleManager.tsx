import React, { useState } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  CircularProgress,
  Tooltip,
} from '@mui/material'
import {
  Add,
  Delete,
  Refresh,
  PlayArrow,
  Stop,
  GetApp,
  Extension,
  Settings,
} from '@mui/icons-material'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import toast from 'react-hot-toast'
import { moduleApi, agentApi } from '../services/api'

const ModuleCard: React.FC<{ moduleName: string; moduleData: any }> = ({ moduleName, moduleData }) => {
  const queryClient = useQueryClient()

  const unloadMutation = useMutation(moduleApi.unloadModule, {
    onSuccess: () => {
      queryClient.invalidateQueries(['modules', 'agents'])
      toast.success(`Module ${moduleName} unloaded successfully`)
    },
    onError: () => {
      toast.error(`Failed to unload module ${moduleName}`)
    },
  })

  const reloadMutation = useMutation(moduleApi.reloadModule, {
    onSuccess: () => {
      queryClient.invalidateQueries(['modules', 'agents'])
      toast.success(`Module ${moduleName} reloaded successfully`)
    },
    onError: () => {
      toast.error(`Failed to reload module ${moduleName}`)
    },
  })

  const agentCount = Object.keys(moduleData.agents || {}).length
  const toolCount = moduleData.tools?.length || 0

  return (
    <Card
      sx={{
        height: '100%',
        background: 'rgba(255, 255, 255, 0.02)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        transition: 'all 0.3s ease',
        '&:hover': {
          backgroundColor: 'rgba(255, 255, 255, 0.05)',
          transform: 'translateY(-2px)',
        },
      }}
    >
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Extension sx={{ color: '#667eea' }} />
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 600, fontSize: '16px' }}>
                {moduleName}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ fontSize: '12px' }}>
                v{moduleData.module_info?.version || '1.0.0'}
              </Typography>
            </Box>
          </Box>
          <Chip
            label={moduleData.initialized ? 'Active' : 'Inactive'}
            size="small"
            color={moduleData.initialized ? 'success' : 'default'}
            sx={{ fontSize: '10px' }}
          />
        </Box>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 2, fontSize: '13px' }}>
          {moduleData.module_info?.description || 'No description available'}
        </Typography>

        <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
          <Chip
            label={`${agentCount} agent${agentCount !== 1 ? 's' : ''}`}
            size="small"
            sx={{ fontSize: '10px', backgroundColor: 'rgba(102, 126, 234, 0.2)' }}
          />
          <Chip
            label={`${toolCount} tool${toolCount !== 1 ? 's' : ''}`}
            size="small"
            sx={{ fontSize: '10px', backgroundColor: 'rgba(76, 175, 80, 0.2)' }}
          />
        </Box>

        {moduleData.module_info?.author && (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2, fontSize: '11px' }}>
            By {moduleData.module_info.author}
          </Typography>
        )}

        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Reload Module">
            <IconButton
              size="small"
              onClick={() => reloadMutation.mutate(moduleName)}
              disabled={reloadMutation.isLoading}
            >
              <Refresh />
            </IconButton>
          </Tooltip>
          <Tooltip title="Unload Module">
            <IconButton
              size="small"
              onClick={() => unloadMutation.mutate(moduleName)}
              disabled={unloadMutation.isLoading}
              color="error"
            >
              <Stop />
            </IconButton>
          </Tooltip>
        </Box>
      </CardContent>
    </Card>
  )
}

const CreateAgentDialog: React.FC<{
  open: boolean
  onClose: () => void
  modules: string[]
}> = ({ open, onClose, modules }) => {
  const [selectedModule, setSelectedModule] = useState('')
  const [agentName, setAgentName] = useState('')
  const [agentType, setAgentType] = useState('')
  const queryClient = useQueryClient()

  const createAgentMutation = useMutation(agentApi.createAgent, {
    onSuccess: (data) => {
      queryClient.invalidateQueries(['agents', 'modules'])
      toast.success(`Agent ${data.agent_name} created successfully!`)
      onClose()
      setAgentName('')
      setAgentType('')
      setSelectedModule('')
    },
    onError: (error: any) => {
      toast.error(`Failed to create agent: ${error.response?.data?.detail || error.message}`)
    },
  })

  const handleCreate = () => {
    if (!selectedModule || !agentName || !agentType) {
      toast.error('Please fill in all fields')
      return
    }

    createAgentMutation.mutate({
      module_name: selectedModule,
      config: {
        name: agentName,
        type: agentType,
        personality: {
          style: 'Professional and helpful',
          tone: 'Friendly',
        },
        system_prompt: `You are ${agentName}, a helpful ${agentType} assistant.`,
        memory_config: {
          remember_conversations: true,
          context_window: 5,
          importance_threshold: 0.5,
        },
        max_context_length: 4000,
      },
    })
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Create New Agent</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
          <FormControl fullWidth>
            <InputLabel>Module</InputLabel>
            <Select
              value={selectedModule}
              onChange={(e) => setSelectedModule(e.target.value)}
              label="Module"
            >
              {modules.map((module) => (
                <MenuItem key={module} value={module}>
                  {module}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <TextField
            label="Agent Name"
            value={agentName}
            onChange={(e) => setAgentName(e.target.value)}
            placeholder="e.g., Chef Marco"
            fullWidth
          />

          <FormControl fullWidth>
            <InputLabel>Agent Type</InputLabel>
            <Select
              value={agentType}
              onChange={(e) => setAgentType(e.target.value)}
              label="Agent Type"
            >
              <MenuItem value="cooking_assistant">Cooking Assistant</MenuItem>
              <MenuItem value="language_teacher">Language Teacher</MenuItem>
              <MenuItem value="weather_assistant">Weather Assistant</MenuItem>
              <MenuItem value="fitness_coach">Fitness Coach</MenuItem>
              <MenuItem value="study_assistant">Study Assistant</MenuItem>
            </Select>
          </FormControl>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          onClick={handleCreate}
          variant="contained"
          disabled={createAgentMutation.isLoading || !selectedModule || !agentName || !agentType}
        >
          {createAgentMutation.isLoading ? 'Creating...' : 'Create Agent'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}

const ModuleManager: React.FC = () => {
  const [createAgentOpen, setCreateAgentOpen] = useState(false)
  const queryClient = useQueryClient()

  const { data: modulesData, isLoading: modulesLoading } = useQuery(
    'modules',
    moduleApi.listModules,
    {
      refetchInterval: 30000,
    }
  )

  const { data: agentsData } = useQuery(
    'agents',
    agentApi.listAgents,
    {
      refetchInterval: 30000,
    }
  )

  const refreshAll = () => {
    queryClient.invalidateQueries()
    toast.success('Data refreshed!')
  }

  if (modulesLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <CircularProgress size={60} />
      </Box>
    )
  }

  const modules = modulesData?.modules || []
  const moduleStatus = modulesData?.status || {}
  const agents = agentsData?.agents || {}

  const totalAgents = Object.keys(agents).length
  const runningAgents = Object.values(agents).filter((agent: any) => agent.status === 'running').length

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
            Module Manager
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage agent modules and create new agents
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setCreateAgentOpen(true)}
            disabled={modules.length === 0}
          >
            Create Agent
          </Button>
          <IconButton onClick={refreshAll}>
            <Refresh />
          </IconButton>
        </Box>
      </Box>

      {/* Statistics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="primary" sx={{ fontWeight: 600 }}>
                {modules.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Loaded Modules
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="success.main" sx={{ fontWeight: 600 }}>
                {totalAgents}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Agents
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="info.main" sx={{ fontWeight: 600 }}>
                {runningAgents}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Running Agents
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="warning.main" sx={{ fontWeight: 600 }}>
                {Object.keys(moduleStatus).length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Active Modules
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Modules Grid */}
      {modules.length === 0 ? (
        <Alert severity="info" sx={{ mb: 3 }}>
          No modules loaded. Install modules to start creating agents.
        </Alert>
      ) : (
        <Grid container spacing={3}>
          {modules.map((moduleName) => (
            <Grid item xs={12} sm={6} md={4} key={moduleName}>
              <ModuleCard
                moduleName={moduleName}
                moduleData={moduleStatus[moduleName] || {}}
              />
            </Grid>
          ))}
        </Grid>
      )}

      {/* Create Agent Dialog */}
      <CreateAgentDialog
        open={createAgentOpen}
        onClose={() => setCreateAgentOpen(false)}
        modules={modules}
      />
    </Box>
  )
}

export default ModuleManager
