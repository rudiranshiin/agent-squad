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
  useTheme,
  Avatar,
  Divider,
} from '@mui/material'
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  AccountTree as FlowIcon,
  Chat as ChatIcon,
  Extension as ModuleIcon,
  Settings as SettingsIcon,
  Analytics as AnalyticsIcon,
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
  const theme = useTheme()

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
      description: 'System overview',
    },
    {
      text: 'Agent Flow',
      icon: <FlowIcon />,
      path: '/flow',
      description: 'Visual workflow',
    },
    {
      text: 'Testing Studio',
      icon: <ChatIcon />,
      path: '/chat',
      description: 'Test & analyze agents',
    },
    {
      text: 'Module Manager',
      icon: <ModuleIcon />,
      path: '/modules',
      description: 'Install & manage modules',
    },
  ]

  const drawer = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Toolbar sx={{ px: 3, py: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Avatar
            sx={{
              width: 40,
              height: 40,
              background: 'linear-gradient(135deg, #007AFF 0%, #5AC8FA 100%)',
              fontWeight: 700,
              fontSize: '1.2rem',
            }}
          >
            A
          </Avatar>
          <Box>
            <Typography variant="h6" noWrap component="div" sx={{ fontWeight: 700, lineHeight: 1.2 }}>
              Agentic
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ lineHeight: 1 }}>
              AI Framework
            </Typography>
          </Box>
        </Box>
      </Toolbar>

      <Divider sx={{ mx: 2, opacity: 0.3 }} />

      <List sx={{ px: 2, py: 1, flexGrow: 1 }}>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding sx={{ mb: 0.5 }}>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => navigate(item.path)}
              sx={{
                borderRadius: 2,
                py: 1.5,
                px: 2,
                '&.Mui-selected': {
                  backgroundColor: 'rgba(0, 122, 255, 0.15)',
                  color: '#007AFF',
                  '&:hover': {
                    backgroundColor: 'rgba(0, 122, 255, 0.2)',
                  },
                },
                '&:hover': {
                  backgroundColor: 'rgba(255, 255, 255, 0.05)',
                },
              }}
            >
              <ListItemIcon
                sx={{
                  color: location.pathname === item.path ? '#007AFF' : 'inherit',
                  minWidth: 36,
                }}
              >
                {item.icon}
              </ListItemIcon>
              <ListItemText
                primary={
                  <Typography variant="body2" fontWeight={location.pathname === item.path ? 600 : 500}>
                    {item.text}
                  </Typography>
                }
                secondary={
                  <Typography variant="caption" color="text.secondary" sx={{ opacity: 0.7 }}>
                    {item.description}
                  </Typography>
                }
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      {/* Bottom Status Section */}
      <Box sx={{ p: 2, mt: 'auto' }}>
        <Divider sx={{ mb: 2, opacity: 0.3 }} />
        {healthData && (
          <Box sx={{ p: 2, backgroundColor: 'rgba(255, 255, 255, 0.03)', borderRadius: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="caption" color="text.secondary" fontWeight={500}>
                System Status
              </Typography>
              <Chip
                label={healthData.status === 'healthy' ? 'Healthy' : 'Warning'}
                size="small"
                color={healthData.status === 'healthy' ? 'success' : 'warning'}
                sx={{
                  height: 20,
                  fontSize: '0.65rem',
                  fontWeight: 600,
                }}
              />
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="caption" color="text.secondary">
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
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
          backgroundColor: 'rgba(15, 15, 15, 0.95)',
          backdropFilter: 'blur(20px) saturate(180%)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
        }}
      >
        <Toolbar sx={{ minHeight: { xs: 56, sm: 64 } }}>
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
            <Typography variant="h6" noWrap component="div" sx={{ fontWeight: 600, fontSize: '1.1rem' }}>
              {menuItems.find(item => item.path === location.pathname)?.text || 'Agentic Framework'}
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ opacity: 0.8 }}>
              {menuItems.find(item => item.path === location.pathname)?.description || 'Enhanced AI Agent Framework 2.0'}
            </Typography>
          </Box>

          {/* Header Status Indicators */}
          {healthData && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Chip
                label={`v${healthData.version}`}
                size="small"
                variant="outlined"
                sx={{
                  color: 'white',
                  borderColor: 'rgba(255, 255, 255, 0.2)',
                  fontSize: '0.7rem',
                  height: 24,
                }}
              />
              <Chip
                label={healthData.status}
                size="small"
                color={healthData.status === 'healthy' ? 'success' : 'warning'}
                sx={{
                  fontWeight: 600,
                  fontSize: '0.7rem',
                  height: 24,
                }}
              />
            </Box>
          )}
        </Toolbar>
      </AppBar>

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
              backgroundColor: 'rgba(15, 15, 15, 0.98)',
              backdropFilter: 'blur(20px) saturate(180%)',
              border: 'none',
              borderRight: '1px solid rgba(255, 255, 255, 0.1)',
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
              backgroundColor: 'rgba(15, 15, 15, 0.98)',
              backdropFilter: 'blur(20px) saturate(180%)',
              border: 'none',
              borderRight: '1px solid rgba(255, 255, 255, 0.1)',
            },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          minHeight: '100vh',
          background: 'linear-gradient(180deg, rgba(20, 20, 20, 0.8) 0%, rgba(15, 15, 15, 0.9) 100%)',
        }}
      >
        <Toolbar sx={{ minHeight: { xs: 56, sm: 64 } }} />
        {children}
      </Box>
    </Box>
  )
}

export default Layout
