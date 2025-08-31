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

const drawerWidth = 260

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
          height: '100vh',
          display: 'flex',
          flexDirection: 'column',
          background: 'linear-gradient(180deg, #0A0A0A 0%, #111111 100%)',
          borderRight: '1px solid rgba(255, 255, 255, 0.06)',
        }}
      >
        {/* Logo & Brand */}
        <Box sx={{ p: 3, pb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2.5 }}>
            <Avatar
              sx={{
                width: 40,
                height: 40,
                background: 'linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%)',
                fontWeight: 700,
                fontSize: '1.1rem',
                boxShadow: '0 4px 16px rgba(59, 130, 246, 0.3)',
              }}
            >
              A
            </Avatar>
            <Box>
              <Typography
                variant="h6"
                sx={{
                  fontWeight: 700,
                  lineHeight: 1.2,
                  color: 'white',
                  fontSize: '1.1rem',
                }}
              >
                Agentic
              </Typography>
              <Typography
                variant="caption"
                sx={{
                  color: 'text.secondary',
                  fontWeight: 500,
                  fontSize: '0.7rem',
                  letterSpacing: '0.05em',
                  textTransform: 'uppercase',
                  opacity: 0.7,
                }}
              >
                AI Framework
              </Typography>
            </Box>
          </Box>
        </Box>

        <Divider sx={{ mx: 2, opacity: 0.08 }} />

              {/* Navigation */}
        <Box sx={{ px: 1, py: 2, flexGrow: 1 }}>
          <List sx={{ px: 1 }}>
            {menuItems.map((item) => (
              <ListItem key={item.text} disablePadding sx={{ mb: 0.5 }}>
                <ListItemButton
                  selected={location.pathname === item.path}
                  onClick={() => navigate(item.path)}
                  sx={{
                    borderRadius: 2,
                    py: 1.5,
                    px: 2,
                    transition: 'all 0.15s ease',
                    position: 'relative',
                    '&.Mui-selected': {
                      background: `linear-gradient(135deg, ${item.color}12 0%, ${item.color}06 100%)`,
                      color: item.color,
                      '&::before': {
                        content: '""',
                        position: 'absolute',
                        left: 0,
                        top: '50%',
                        transform: 'translateY(-50%)',
                        width: 3,
                        height: 16,
                        background: item.color,
                        borderRadius: '0 2px 2px 0',
                      },
                      '&:hover': {
                        background: `linear-gradient(135deg, ${item.color}18 0%, ${item.color}08 100%)`,
                      },
                    },
                    '&:hover': {
                      background: 'rgba(255, 255, 255, 0.03)',
                    },
                  }}
                >
                  <ListItemIcon
                    sx={{
                      color: location.pathname === item.path ? item.color : 'rgba(255, 255, 255, 0.6)',
                      minWidth: 36,
                      transition: 'color 0.15s ease',
                    }}
                  >
                    {item.icon}
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Typography
                        variant="body2"
                        fontWeight={location.pathname === item.path ? 600 : 500}
                        sx={{
                          fontSize: '0.875rem',
                          color: location.pathname === item.path ? item.color : 'white',
                        }}
                      >
                        {item.text}
                      </Typography>
                    }
                    secondary={
                      <Typography
                        variant="caption"
                        sx={{
                          color: 'rgba(255, 255, 255, 0.5)',
                          fontSize: '0.7rem',
                          mt: 0.25,
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
      <Box sx={{ p: 2, mt: 'auto' }}>
        <Divider sx={{ mb: 2, opacity: 0.08 }} />
        {healthData && (
          <Box
            sx={{
              p: 2,
              background: 'rgba(255, 255, 255, 0.02)',
              border: '1px solid rgba(255, 255, 255, 0.04)',
              borderRadius: 2,
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
              <Typography
                variant="caption"
                sx={{
                  fontWeight: 500,
                  fontSize: '0.7rem',
                  color: 'rgba(255, 255, 255, 0.6)',
                }}
              >
                System Status
              </Typography>
              <Chip
                label={healthData.status === 'healthy' ? 'Healthy' : 'Warning'}
                size="small"
                color={healthData.status === 'healthy' ? 'success' : 'warning'}
                sx={{
                  height: 20,
                  fontSize: '0.65rem',
                  fontWeight: 500,
                }}
              />
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography
                variant="caption"
                sx={{
                  color: 'rgba(255, 255, 255, 0.5)',
                  fontSize: '0.7rem',
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
                    height: 14,
                    minWidth: 14,
                  },
                }}
              >
                <ModuleIcon sx={{ fontSize: 16, color: 'rgba(255, 255, 255, 0.5)' }} />
              </Badge>
            </Box>
          </Box>
        )}
      </Box>
    </Box>
  )

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', background: '#0A0A0A' }}>
      {/* App Bar */}
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
          background: 'rgba(10, 10, 10, 0.9)',
          backdropFilter: 'blur(20px)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
          zIndex: (theme) => theme.zIndex.drawer + 1,
        }}
      >
        <Toolbar sx={{ minHeight: 48, px: 3 }}>
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
              variant="h6"
              sx={{
                fontWeight: 600,
                fontSize: '1.1rem',
                color: 'white',
                mb: 0.25,
              }}
            >
              {menuItems.find(item => item.path === location.pathname)?.text || 'Agentic Framework'}
            </Typography>
            <Typography
              variant="body2"
              sx={{
                color: 'rgba(255, 255, 255, 0.6)',
                fontSize: '0.8rem',
              }}
            >
              {menuItems.find(item => item.path === location.pathname)?.description || 'Enhanced AI Agent Framework 2.0'}
            </Typography>
          </Box>

          {/* Header Status */}
          {healthData && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
              <Chip
                label={`v${healthData.version}`}
                variant="outlined"
                size="small"
                sx={{
                  color: 'rgba(255, 255, 255, 0.8)',
                  borderColor: 'rgba(255, 255, 255, 0.15)',
                  fontSize: '0.7rem',
                  height: 24,
                }}
              />
              <Chip
                label={healthData.status === 'healthy' ? 'Healthy' : 'Warning'}
                color={healthData.status === 'healthy' ? 'success' : 'warning'}
                size="small"
                sx={{
                  fontSize: '0.7rem',
                  height: 24,
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
              background: 'linear-gradient(180deg, #0A0A0A 0%, #111111 100%)',
              border: 'none',
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
              background: 'linear-gradient(180deg, #0A0A0A 0%, #111111 100%)',
              border: 'none',
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
            p: 2,
            width: { sm: `calc(100% - ${drawerWidth}px)` },
            minHeight: '100vh',
            background: '#0A0A0A',
          }}
        >
          <Toolbar sx={{ minHeight: 48 }} />
          {children}
        </Box>
    </Box>
  )
}

export default Layout
