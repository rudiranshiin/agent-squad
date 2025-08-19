import React, { useState } from 'react'
import {
  AppBar,
  Box,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  Badge,
  Chip,

  Avatar,
  Divider,
} from '@mui/material'
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  AccountTree as FlowIcon,
  Chat as ChatIcon,
  Extension as ModuleIcon,
} from '@mui/icons-material'
import { useNavigate, useLocation } from 'react-router-dom'
import { useQuery } from 'react-query'
import { systemApi } from '../services/api'

const drawerWidth = 280

interface LayoutProps {
  children: React.ReactNode
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [mobileOpen, setMobileOpen] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()

  const { data: healthData } = useQuery(
    'health',
    systemApi.getHealth,
    {
      refetchInterval: 30000,
      retry: 1,
    }
  )

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen)
  }

  const menuItems = [
    {
      text: 'Dashboard',
      icon: <DashboardIcon />,
      path: '/',
      description: 'System overview & metrics',
      color: '#3B82F6',
    },
    {
      text: 'Agent Flow',
      icon: <FlowIcon />,
      path: '/flow',
      description: 'Visual workflow builder',
      color: '#8B5CF6',
    },
    {
      text: 'Testing Studio',
      icon: <ChatIcon />,
      path: '/chat',
      description: 'Test & analyze agents',
      color: '#10B981',
    },
    {
      text: 'Module Manager',
      icon: <ModuleIcon />,
      path: '/modules',
      description: 'Install & manage modules',
      color: '#F59E0B',
    },
  ]

  const drawer = (
    <Box
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        background: 'linear-gradient(180deg, rgba(10, 10, 10, 0.98) 0%, rgba(15, 15, 15, 0.98) 100%)',
      }}
    >
      {/* Logo & Brand */}
      <Box sx={{ p: 3, pb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
          <Avatar
            sx={{
              width: 48,
              height: 48,
              background: 'linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%)',
              fontWeight: 700,
              fontSize: '1.25rem',
              boxShadow: '0 8px 24px rgba(59, 130, 246, 0.4)',
            }}
          >
            A
          </Avatar>
          <Box>
            <Typography
              variant="h5"
              sx={{
                fontWeight: 800,
                lineHeight: 1.2,
                background: 'linear-gradient(135deg, #FFFFFF 0%, #A1A1AA 100%)',
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                color: 'transparent',
              }}
            >
              Agentic
            </Typography>
            <Typography
              variant="caption"
              sx={{
                color: 'text.secondary',
                fontWeight: 500,
                fontSize: '0.75rem',
                letterSpacing: '0.05em',
                textTransform: 'uppercase',
              }}
            >
              AI Framework
            </Typography>
          </Box>
        </Box>
      </Box>

      <Divider sx={{ mx: 3, opacity: 0.1 }} />

      {/* Navigation */}
      <Box sx={{ px: 2, py: 2, flexGrow: 1 }}>
        <Typography
          variant="caption"
          sx={{
            px: 2,
            py: 1,
            color: 'text.secondary',
            fontWeight: 600,
            fontSize: '0.7rem',
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
          }}
        >
          Navigation
        </Typography>
        <List sx={{ mt: 1 }}>
          {menuItems.map((item) => (
            <ListItem key={item.text} disablePadding sx={{ mb: 1 }}>
              <ListItemButton
                selected={location.pathname === item.path}
                onClick={() => navigate(item.path)}
                sx={{
                  borderRadius: 3,
                  mx: 1,
                  py: 2,
                  px: 3,
                  transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                  '&.Mui-selected': {
                    background: `linear-gradient(135deg, ${item.color}15 0%, ${item.color}08 100%)`,
                    border: `1px solid ${item.color}30`,
                    color: item.color,
                    '&:hover': {
                      background: `linear-gradient(135deg, ${item.color}20 0%, ${item.color}10 100%)`,
                    },
                    '&::before': {
                      content: '""',
                      position: 'absolute',
                      left: 0,
                      top: '50%',
                      transform: 'translateY(-50%)',
                      width: 3,
                      height: 20,
                      background: item.color,
                      borderRadius: '0 2px 2px 0',
                    },
                  },
                  '&:hover': {
                    background: 'rgba(255, 255, 255, 0.04)',
                    transform: 'translateX(2px)',
                  },
                  position: 'relative',
                }}
              >
                <ListItemIcon
                  sx={{
                    color: location.pathname === item.path ? item.color : 'text.secondary',
                    minWidth: 40,
                    transition: 'color 0.2s ease',
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Typography
                      variant="body2"
                      fontWeight={location.pathname === item.path ? 600 : 500}
                      sx={{ fontSize: '0.875rem' }}
                    >
                      {item.text}
                    </Typography>
                  }
                  secondary={
                    <Typography
                      variant="caption"
                      sx={{
                        color: 'text.secondary',
                        opacity: 0.7,
                        fontSize: '0.7rem',
                        mt: 0.5,
                      }}
                    >
                      {item.description}
                    </Typography>
                  }
                />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Box>

      {/* System Status */}
      <Box sx={{ p: 3, mt: 'auto' }}>
        <Divider sx={{ mb: 3, opacity: 0.1 }} />
        {healthData && (
          <Box
            sx={{
              p: 3,
              background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.01) 100%)',
              border: '1px solid rgba(255, 255, 255, 0.05)',
              borderRadius: 3,
              backdropFilter: 'blur(10px)',
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
              <Typography
                variant="caption"
                sx={{
                  fontWeight: 600,
                  fontSize: '0.7rem',
                  letterSpacing: '0.05em',
                  textTransform: 'uppercase',
                  color: 'text.secondary',
                }}
              >
                System Status
              </Typography>
              <Chip
                label={healthData.status === 'healthy' ? 'Healthy' : 'Warning'}
                size="small"
                color={healthData.status === 'healthy' ? 'success' : 'warning'}
                sx={{
                  height: 22,
                  fontSize: '0.65rem',
                  fontWeight: 600,
                }}
              />
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography
                variant="caption"
                sx={{
                  color: 'text.secondary',
                  fontSize: '0.75rem',
                }}
              >
                v{healthData.version}
              </Typography>
              <Badge
                badgeContent={Object.keys(healthData.modules || {}).length}
                color="primary"
                max={99}
                sx={{
                  '& .MuiBadge-badge': {
                    fontSize: '0.6rem',
                    height: 16,
                    minWidth: 16,
                  },
                }}
              >
                <ModuleIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
              </Badge>
            </Box>
          </Box>
        )}
      </Box>
    </Box>
  )

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {/* App Bar */}
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
          background: 'rgba(10, 10, 10, 0.85)',
          backdropFilter: 'blur(20px) saturate(180%)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          boxShadow: '0 1px 0 rgba(255, 255, 255, 0.05) inset, 0 1px 20px rgba(0, 0, 0, 0.1)',
        }}
      >
        <Toolbar sx={{ minHeight: { xs: 56, sm: 70 }, py: 1 }}>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>

          <Box sx={{ flexGrow: 1 }}>
            <Typography
              variant="h5"
              sx={{
                fontWeight: 700,
                fontSize: '1.25rem',
                background: 'linear-gradient(135deg, #FFFFFF 0%, #A1A1AA 100%)',
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                color: 'transparent',
              }}
            >
              {menuItems.find(item => item.path === location.pathname)?.text || 'Agentic Framework'}
            </Typography>
            <Typography
              variant="body2"
              sx={{
                color: 'text.secondary',
                opacity: 0.8,
                fontSize: '0.875rem',
                fontWeight: 400,
              }}
            >
              {menuItems.find(item => item.path === location.pathname)?.description || 'Enhanced AI Agent Framework 2.0'}
            </Typography>
          </Box>

          {/* Header Status */}
          {healthData && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Chip
                label={`v${healthData.version}`}
                size="small"
                variant="outlined"
                sx={{
                  color: 'white',
                  borderColor: 'rgba(255, 255, 255, 0.2)',
                  fontSize: '0.75rem',
                  height: 28,
                  fontWeight: 500,
                }}
              />
              <Chip
                label={healthData.status}
                size="small"
                color={healthData.status === 'healthy' ? 'success' : 'warning'}
                sx={{
                  fontWeight: 600,
                  fontSize: '0.75rem',
                  height: 28,
                }}
              />
            </Box>
          )}
        </Toolbar>
      </AppBar>

      {/* Navigation Drawer */}
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
        aria-label="navigation"
      >
        {/* Mobile drawer */}
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true,
          }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
              background: 'linear-gradient(180deg, rgba(10, 10, 10, 0.98) 0%, rgba(15, 15, 15, 0.98) 100%)',
              backdropFilter: 'blur(20px) saturate(180%)',
              border: 'none',
              borderRight: '1px solid rgba(255, 255, 255, 0.08)',
              boxShadow: '1px 0 0 rgba(255, 255, 255, 0.05) inset',
            },
          }}
        >
          {drawer}
        </Drawer>

        {/* Desktop drawer */}
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
              background: 'linear-gradient(180deg, rgba(10, 10, 10, 0.98) 0%, rgba(15, 15, 15, 0.98) 100%)',
              backdropFilter: 'blur(20px) saturate(180%)',
              border: 'none',
              borderRight: '1px solid rgba(255, 255, 255, 0.08)',
              boxShadow: '1px 0 0 rgba(255, 255, 255, 0.05) inset',
            },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: { xs: 2, sm: 4 },
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          minHeight: '100vh',
          background: 'radial-gradient(ellipse at top left, rgba(59, 130, 246, 0.05) 0%, transparent 50%), radial-gradient(ellipse at bottom right, rgba(139, 92, 246, 0.05) 0%, transparent 50%), linear-gradient(180deg, rgba(10, 10, 10, 1) 0%, rgba(15, 15, 15, 1) 100%)',
        }}
      >
        <Toolbar sx={{ minHeight: { xs: 56, sm: 70 } }} />
        {children}
      </Box>
    </Box>
  )
}

export default Layout
