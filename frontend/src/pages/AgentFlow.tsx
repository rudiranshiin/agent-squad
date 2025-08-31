import React, { useCallback, useEffect, useState } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  CircularProgress,
} from '@mui/material'
import {
  PlayArrow,
  Stop,
  Refresh,
  ZoomIn,
  ZoomOut,
  FitScreen,
  Share,
} from '@mui/icons-material'
import ReactFlow, {
  Node,
  Edge,
  Connection,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  BackgroundVariant,
  MiniMap,
  ReactFlowProvider,
  useReactFlow,
  Handle,
  Position,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import toast from 'react-hot-toast'
import { agentApi } from '../services/api'


// Custom Node Component
const AgentNodeComponent = ({ data, selected }: { data: any; selected: boolean }) => {
  const { status, agentType, tools, label } = data

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
    <>
      {/* Connection Handles - Much More Visible */}
      <Handle
        type="target"
        position={Position.Left}
        style={{
          background: 'linear-gradient(45deg, #667eea, #764ba2)',
          width: 20,
          height: 20,
          border: '3px solid #fff',
          boxShadow: '0 0 15px rgba(102, 126, 234, 1), 0 0 30px rgba(102, 126, 234, 0.5)',
          transition: 'all 0.3s ease',
          cursor: 'crosshair',
          zIndex: 1000,
          animation: 'handlePulse 2s infinite',
        }}
        onMouseEnter={(e) => {
          const target = e.target as HTMLElement
          target.style.transform = 'scale(1.5)'
          target.style.boxShadow = '0 0 20px rgba(102, 126, 234, 1), 0 0 40px rgba(102, 126, 234, 0.8)'
          target.style.background = 'linear-gradient(45deg, #764ba2, #667eea)'
        }}
        onMouseLeave={(e) => {
          const target = e.target as HTMLElement
          target.style.transform = 'scale(1)'
          target.style.boxShadow = '0 0 15px rgba(102, 126, 234, 1), 0 0 30px rgba(102, 126, 234, 0.5)'
          target.style.background = 'linear-gradient(45deg, #667eea, #764ba2)'
        }}
      />
      <Handle
        type="source"
        position={Position.Right}
        style={{
          background: 'linear-gradient(45deg, #667eea, #764ba2)',
          width: 20,
          height: 20,
          border: '3px solid #fff',
          boxShadow: '0 0 15px rgba(102, 126, 234, 1), 0 0 30px rgba(102, 126, 234, 0.5)',
          transition: 'all 0.3s ease',
          cursor: 'crosshair',
          zIndex: 1000,
          animation: 'handlePulse 2s infinite',
        }}
        onMouseEnter={(e) => {
          const target = e.target as HTMLElement
          target.style.transform = 'scale(1.5)'
          target.style.boxShadow = '0 0 20px rgba(102, 126, 234, 1), 0 0 40px rgba(102, 126, 234, 0.8)'
          target.style.background = 'linear-gradient(45deg, #764ba2, #667eea)'
        }}
        onMouseLeave={(e) => {
          const target = e.target as HTMLElement
          target.style.transform = 'scale(1)'
          target.style.boxShadow = '0 0 15px rgba(102, 126, 234, 1), 0 0 30px rgba(102, 126, 234, 0.5)'
          target.style.background = 'linear-gradient(45deg, #667eea, #764ba2)'
        }}
      />

      <Card
        sx={{
          minWidth: 200,
          border: selected ? '2px solid #667eea' : '1px solid rgba(255, 255, 255, 0.1)',
          backgroundColor: 'rgba(255, 255, 255, 0.05)',
          backdropFilter: 'blur(10px)',
          transition: 'all 0.3s ease',
          position: 'relative',
          '&:hover': {
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
            transform: 'scale(1.02)',
            '&::before': {
              content: '"← CONNECT"',
              position: 'absolute',
              left: -60,
              top: '50%',
              transform: 'translateY(-50%)',
              fontSize: '10px',
              color: '#667eea',
              fontWeight: 'bold',
              animation: 'pulse 1.5s infinite',
            },
            '&::after': {
              content: '"CONNECT →"',
              position: 'absolute',
              right: -60,
              top: '50%',
              transform: 'translateY(-50%)',
              fontSize: '10px',
              color: '#667eea',
              fontWeight: 'bold',
              animation: 'pulse 1.5s infinite',
            },
          },
          '@keyframes pulse': {
            '0%': { opacity: 0.5 },
            '50%': { opacity: 1 },
            '100%': { opacity: 0.5 },
          },
        }}
      >
        <CardContent sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <Typography variant="h6" sx={{ fontSize: '24px' }}>
              {getTypeIcon(agentType)}
            </Typography>
            <Box sx={{ flexGrow: 1 }}>
              <Typography variant="h6" sx={{ fontSize: '14px', fontWeight: 600 }}>
                {label}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ fontSize: '12px' }}>
                {agentType}
              </Typography>
            </Box>
            <Box
              sx={{
                width: 12,
                height: 12,
                borderRadius: '50%',
                backgroundColor: getStatusColor(status),
                boxShadow: `0 0 8px ${getStatusColor(status)}`,
              }}
            />
          </Box>

          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
            {tools.slice(0, 3).map((tool: string) => (
              <Chip
                key={tool}
                label={tool}
                size="small"
                sx={{
                  fontSize: '10px',
                  height: '20px',
                  backgroundColor: 'rgba(102, 126, 234, 0.2)',
                  color: 'white',
                }}
              />
            ))}
            {tools.length > 3 && (
              <Chip
                label={`+${tools.length - 3}`}
                size="small"
                sx={{
                  fontSize: '10px',
                  height: '20px',
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                  color: 'white',
                }}
              />
            )}
          </Box>
        </CardContent>
      </Card>
    </>
  )
}

const nodeTypes = {
  agent: AgentNodeComponent,
}

const FlowContent: React.FC = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null)
  const [collaborationDialog, setCollaborationDialog] = useState(false)
  const [collaborationMessage, setCollaborationMessage] = useState('')
  const [collaborationTarget, setCollaborationTarget] = useState('')
  const queryClient = useQueryClient()
  const { fitView, zoomIn, zoomOut } = useReactFlow()

  // Fetch agents
  const { data: agentsData, isLoading: agentsLoading } = useQuery(
    'agents',
    agentApi.listAgents,
    {
      refetchInterval: 10000,
    }
  )

  // Fetch collaboration graph
  const { data: collaborationData } = useQuery(
    'collaboration-graph',
    agentApi.getCollaborationGraph,
    {
      refetchInterval: 15000,
    }
  )

  // Fetch active collaborations
  const { data: activeCollaborationsData } = useQuery(
    'active-collaborations',
    agentApi.getActiveCollaborations,
    {
      refetchInterval: 5000,
    }
  )

  // Mutations
  const startAgentMutation = useMutation(agentApi.startAgent, {
    onSuccess: () => {
      queryClient.invalidateQueries('agents')
      toast.success('Agent started successfully!')
    },
    onError: () => {
      toast.error('Failed to start agent')
    },
  })

  const stopAgentMutation = useMutation(agentApi.stopAgent, {
    onSuccess: () => {
      queryClient.invalidateQueries('agents')
      toast.success('Agent stopped successfully!')
    },
    onError: () => {
      toast.error('Failed to stop agent')
    },
  })

  const collaborationMutation = useMutation(
    ({ agent1, agent2, message }: { agent1: string; agent2: string; message?: string }) =>
      agentApi.collaborateAgents(agent1, agent2, message || ''),
    {
      onSuccess: (data) => {
        toast.success('Collaboration thread established successfully!')
        setCollaborationDialog(false)
        setCollaborationMessage('')
        // Refresh the collaboration data to show new connections
        queryClient.invalidateQueries('collaboration-graph')
        queryClient.invalidateQueries('active-collaborations')
        console.log('Collaboration result:', data)
      },
      onError: (error: any) => {
        toast.error(`Failed to establish collaboration: ${error?.response?.data?.detail || error.message}`)
      },
    }
  )

  const removeCollaborationMutation = useMutation(
    ({ agent1, agent2 }: { agent1: string; agent2: string }) =>
      agentApi.removeCollaboration(agent1, agent2),
    {
      onSuccess: (data) => {
        toast.success('Collaboration thread removed successfully!')
        queryClient.invalidateQueries('active-collaborations')
        console.log('Collaboration removed:', data)
      },
      onError: (error: any) => {
        toast.error(`Failed to remove collaboration: ${error?.response?.data?.detail || error.message}`)
      },
    }
  )

  // Generate nodes and edges from data
  useEffect(() => {
    if (!agentsData?.agents) return

    const agentEntries = Object.entries(agentsData.agents)
    const newNodes: Node[] = agentEntries.map(([name, agent], index) => ({
      id: name,
      type: 'agent',
      position: {
        x: (index % 3) * 300 + 50,
        y: Math.floor(index / 3) * 200 + 50,
      },
      data: {
        label: name,
        agentType: agent.type,
        status: agent.status,
        module: (agent as any).module || 'unknown',
        tools: (agent as any).tools || [],
      },
    }))

    setNodes(newNodes)

        // Generate edges from active collaborations only (no default/potential threads)
    const newEdges: Edge[] = []

    // Add active collaboration edges (solid, prominent)
    if (activeCollaborationsData?.active_collaborations) {
      Object.values(activeCollaborationsData.active_collaborations).forEach((collab: any) => {
        if (agentsData.agents[collab.agent1] && agentsData.agents[collab.agent2]) {
          newEdges.push({
            id: `active-${collab.agent1}-${collab.agent2}`,
            source: collab.agent1,
            target: collab.agent2,
            type: 'smoothstep',
            animated: true,
            style: {
              stroke: '#4caf50',
              strokeWidth: 3,
            },
            label: 'Active Thread',
            labelStyle: {
              fill: '#ffffff',
              fontSize: '12px',
              fontWeight: 600,
            },
            labelBgStyle: {
              fill: 'rgba(76, 175, 80, 0.8)',
              fillOpacity: 0.8,
            },
          })
        }
      })
    }

    setEdges(newEdges)
  }, [agentsData, collaborationData, activeCollaborationsData, setNodes, setEdges])

  const onConnect = useCallback(
    async (params: Connection) => {
      if (!params.source || !params.target) return

      // Check if both agents are running
      const sourceAgent = agentsData?.agents[params.source]
      const targetAgent = agentsData?.agents[params.target]

      if (!sourceAgent || !targetAgent) {
        toast.error('One or both agents not found')
        return
      }

      if (sourceAgent.status !== 'running' || targetAgent.status !== 'running') {
        toast.error('Both agents must be running to establish collaboration')
        return
      }

      // Check if connection already exists
      const existingEdge = edges.find(edge =>
        (edge.source === params.source && edge.target === params.target) ||
        (edge.source === params.target && edge.target === params.source)
      )

      if (existingEdge) {
        toast('Collaboration already exists between these agents', { icon: 'ℹ️' })
        return
      }

      // Establish collaboration
      try {
        await collaborationMutation.mutateAsync({
          agent1: params.source,
          agent2: params.target,
          message: `Thread connection established between ${params.source} and ${params.target}`
        })

        // The edge will be automatically added when active collaborations are refreshed

      } catch (error) {
        console.error('Failed to establish collaboration:', error)
      }
    },
    [setEdges, agentsData, edges, collaborationMutation]
  )

  const onNodeClick = useCallback((_event: React.MouseEvent, node: Node) => {
    setSelectedAgent(node.id)
  }, [])

  const onEdgeClick = useCallback((_event: React.MouseEvent, edge: Edge) => {
    if (edge.id.startsWith('active-')) {
      const confirmed = window.confirm('Remove this collaboration thread?')
      if (confirmed) {
        removeCollaborationMutation.mutate({
          agent1: edge.source,
          agent2: edge.target
        })
      }
    }
  }, [removeCollaborationMutation])

  const handleStartAgent = async (agentName: string) => {
    await startAgentMutation.mutateAsync(agentName)
  }

  const handleStopAgent = async (agentName: string) => {
    await stopAgentMutation.mutateAsync(agentName)
  }

  const handleCollaboration = () => {
    if (!selectedAgent || !collaborationTarget) {
      toast.error('Please select a target agent')
      return
    }

    collaborationMutation.mutate({
      agent1: selectedAgent,
      agent2: collaborationTarget,
      message: collaborationMessage || `Thread connection established between ${selectedAgent} and ${collaborationTarget}`,
    })
  }

  const handleQuickConnect = () => {
    if (!selectedAgent || !collaborationTarget) {
      toast.error('Please select a target agent')
      return
    }

    collaborationMutation.mutate({
      agent1: selectedAgent,
      agent2: collaborationTarget,
      message: `Quick thread connection established between ${selectedAgent} and ${collaborationTarget}`,
    })
  }

  const selectedAgentData = selectedAgent ? agentsData?.agents[selectedAgent] : null

  if (agentsLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <CircularProgress size={60} />
      </Box>
    )
  }

  const availableAgents = Object.keys(agentsData?.agents || {}).filter(name => name !== selectedAgent)

  return (
    <Box sx={{
      height: '100vh',
      width: '100%',
      display: 'flex',
      '@keyframes handlePulse': {
        '0%': {
          boxShadow: '0 0 15px rgba(102, 126, 234, 1), 0 0 30px rgba(102, 126, 234, 0.5)',
          transform: 'scale(1)'
        },
        '50%': {
          boxShadow: '0 0 25px rgba(102, 126, 234, 1), 0 0 50px rgba(102, 126, 234, 0.8)',
          transform: 'scale(1.1)'
        },
        '100%': {
          boxShadow: '0 0 15px rgba(102, 126, 234, 1), 0 0 30px rgba(102, 126, 234, 0.5)',
          transform: 'scale(1)'
        },
      }
    }}>
      {/* Sidebar Control Panel */}
      <Box
        sx={{
          width: 350,
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          backdropFilter: 'blur(10px)',
          borderRight: '1px solid rgba(255, 255, 255, 0.1)',
          overflowY: 'auto',
          p: 2,
        }}
      >
        <Card
          sx={{
            backgroundColor: 'rgba(255, 255, 255, 0.05)',
            backdropFilter: 'blur(10px)',
          }}
        >
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Agent Network
          </Typography>

          <Alert severity="info" sx={{ mb: 2, fontSize: '12px' }}>
            💡 <strong>Connect:</strong> Look for the bright blue glowing circles on agent sides - drag from RIGHT circle to LEFT circle of another agent<br/>
            🗑️ <strong>Remove:</strong> Click on a green collaboration thread to remove it<br/>
            ✨ <strong>Tip:</strong> Hover over agents to see connection hints!
          </Alert>

          {selectedAgent && selectedAgentData && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Selected: {selectedAgent}
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                <Button
                  size="small"
                  variant="contained"
                  color={selectedAgentData.status === 'running' ? 'error' : 'success'}
                  startIcon={selectedAgentData.status === 'running' ? <Stop /> : <PlayArrow />}
                  onClick={() =>
                    selectedAgentData.status === 'running'
                      ? handleStopAgent(selectedAgent)
                      : handleStartAgent(selectedAgent)
                  }
                  disabled={startAgentMutation.isLoading || stopAgentMutation.isLoading}
                >
                  {selectedAgentData.status === 'running' ? 'Stop' : 'Start'}
                </Button>
                <Button
                  size="small"
                  variant="outlined"
                  startIcon={<Share />}
                  onClick={() => setCollaborationDialog(true)}
                  disabled={selectedAgentData.status !== 'running'}
                >
                  Collaborate
                </Button>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Status: {selectedAgentData.status} | Type: {selectedAgentData.type}
              </Typography>
            </Box>
          )}

          <Box sx={{ display: 'flex', gap: 1 }}>
            <IconButton size="small" onClick={() => zoomIn()}>
              <ZoomIn />
            </IconButton>
            <IconButton size="small" onClick={() => zoomOut()}>
              <ZoomOut />
            </IconButton>
            <IconButton size="small" onClick={() => fitView()}>
              <FitScreen />
            </IconButton>
            <IconButton size="small" onClick={() => queryClient.invalidateQueries(['agents', 'collaboration-graph'])}>
              <Refresh />
            </IconButton>
          </Box>
        </CardContent>
        </Card>
      </Box>

      {/* React Flow Container */}
      <Box sx={{ flex: 1, position: 'relative' }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onEdgeClick={onEdgeClick}
          nodeTypes={nodeTypes}
          fitView
          connectOnClick={false}
          nodesDraggable={true}
          nodesConnectable={true}
          elementsSelectable={true}
          connectionLineStyle={{
            stroke: '#667eea',
            strokeWidth: 3,
            strokeDasharray: '5,5',
          }}
          connectionLineType={'smoothstep' as any}
          style={{
            backgroundColor: 'transparent',
          }}
        >
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="rgba(255, 255, 255, 0.1)" />
        <Controls />
        <MiniMap
          style={{
            backgroundColor: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
          }}
          nodeColor="#667eea"
          maskColor="rgba(0, 0, 0, 0.8)"
        />
        </ReactFlow>
      </Box>

      {/* Collaboration Dialog */}
      <Dialog
        open={collaborationDialog}
        onClose={() => setCollaborationDialog(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            backgroundColor: 'rgba(255, 255, 255, 0.05)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
          }
        }}
      >
        <DialogTitle>Agent Collaboration</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <Alert severity="info">
              Establish collaboration thread between {selectedAgent} and another agent
            </Alert>

            <TextField
              select
              label="Target Agent"
              value={collaborationTarget}
              onChange={(e) => setCollaborationTarget(e.target.value)}
              SelectProps={{ native: true }}
              fullWidth
            >
              <option value="">Select an agent...</option>
              {availableAgents.map((agentName) => (
                <option key={agentName} value={agentName}>
                  {agentName} ({agentsData?.agents[agentName]?.type})
                </option>
              ))}
            </TextField>

            <TextField
              label="Collaboration Message (Optional)"
              multiline
              rows={3}
              value={collaborationMessage}
              onChange={(e) => setCollaborationMessage(e.target.value)}
              placeholder="Enter a message for collaboration (optional)..."
              fullWidth
              helperText="Leave empty for a simple thread connection"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCollaborationDialog(false)}>Cancel</Button>
          <Button
            onClick={handleQuickConnect}
            variant="outlined"
            disabled={collaborationMutation.isLoading || !collaborationTarget}
            sx={{ mr: 1 }}
          >
            {collaborationMutation.isLoading ? 'Connecting...' : 'Quick Connect'}
          </Button>
          <Button
            onClick={handleCollaboration}
            variant="contained"
            disabled={collaborationMutation.isLoading || !collaborationTarget}
          >
            {collaborationMutation.isLoading ? 'Establishing...' : 'Establish Thread'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

const AgentFlow: React.FC = () => {
  return (
    <ReactFlowProvider>
      <FlowContent />
    </ReactFlowProvider>
  )
}

export default AgentFlow
