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
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  BackgroundVariant,
  MiniMap,
  ReactFlowProvider,
  useReactFlow,
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
    <Card
      sx={{
        minWidth: 200,
        border: selected ? '2px solid #667eea' : '1px solid rgba(255, 255, 255, 0.1)',
        backgroundColor: 'rgba(255, 255, 255, 0.05)',
        backdropFilter: 'blur(10px)',
        transition: 'all 0.3s ease',
        '&:hover': {
          backgroundColor: 'rgba(255, 255, 255, 0.1)',
          transform: 'scale(1.02)',
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
    ({ agent1, agent2, message }: { agent1: string; agent2: string; message: string }) =>
      agentApi.collaborateAgents(agent1, agent2, message),
    {
      onSuccess: (data) => {
        toast.success('Collaboration initiated successfully!')
        setCollaborationDialog(false)
        setCollaborationMessage('')
        // You could show the collaboration result in a separate dialog
        console.log('Collaboration result:', data)
      },
      onError: () => {
        toast.error('Failed to initiate collaboration')
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

    // Generate edges from collaboration graph
    if (collaborationData?.collaboration_graph) {
      const newEdges: Edge[] = []
      Object.entries(collaborationData.collaboration_graph).forEach(([agentName, agentInfo]) => {
        agentInfo.can_collaborate_with.forEach((targetAgent: string) => {
          if (agentsData.agents[targetAgent]) {
            newEdges.push({
              id: `${agentName}-${targetAgent}`,
              source: agentName,
              target: targetAgent,
              type: 'smoothstep',
              animated: true,
              style: {
                stroke: '#667eea',
                strokeWidth: 2,
                strokeDasharray: '5,5',
              },
              label: agentInfo.collaboration_style,
              labelStyle: {
                fill: '#ffffff',
                fontSize: '12px',
                fontWeight: 600,
              },
              labelBgStyle: {
                fill: 'rgba(102, 126, 234, 0.8)',
                fillOpacity: 0.8,
              },
            })
          }
        })
      })
      setEdges(newEdges)
    }
  }, [agentsData, collaborationData, setNodes, setEdges])

  const onConnect = useCallback(
    (params: Connection) => {
      if (!params.source || !params.target) return
      const edge: Edge = {
        id: `${params.source}-${params.target}`,
        source: params.source,
        target: params.target,
        type: 'smoothstep',
        animated: true,
        style: { stroke: '#667eea', strokeWidth: 2 },
      }
      setEdges((eds) => addEdge(edge, eds))
    },
    [setEdges]
  )

  const onNodeClick = useCallback((_event: React.MouseEvent, node: Node) => {
    setSelectedAgent(node.id)
  }, [])

  const handleStartAgent = async (agentName: string) => {
    await startAgentMutation.mutateAsync(agentName)
  }

  const handleStopAgent = async (agentName: string) => {
    await stopAgentMutation.mutateAsync(agentName)
  }

  const handleCollaboration = () => {
    if (!selectedAgent || !collaborationTarget || !collaborationMessage) {
      toast.error('Please fill in all fields')
      return
    }

    collaborationMutation.mutate({
      agent1: selectedAgent,
      agent2: collaborationTarget,
      message: collaborationMessage,
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
    <Box sx={{ height: '80vh', width: '100%', position: 'relative' }}>
      {/* Control Panel */}
      <Card
        sx={{
          position: 'absolute',
          top: 16,
          left: 16,
          zIndex: 1000,
          minWidth: 300,
          backgroundColor: 'rgba(255, 255, 255, 0.05)',
          backdropFilter: 'blur(10px)',
        }}
      >
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Agent Network
          </Typography>

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

      {/* React Flow */}
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        fitView
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
              Initiate collaboration between {selectedAgent} and another agent
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
              label="Collaboration Message"
              multiline
              rows={3}
              value={collaborationMessage}
              onChange={(e) => setCollaborationMessage(e.target.value)}
              placeholder="Enter the message for collaboration..."
              fullWidth
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCollaborationDialog(false)}>Cancel</Button>
          <Button
            onClick={handleCollaboration}
            variant="contained"
            disabled={collaborationMutation.isLoading || !collaborationTarget || !collaborationMessage}
          >
            {collaborationMutation.isLoading ? 'Sending...' : 'Send Collaboration'}
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
