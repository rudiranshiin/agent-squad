import React from 'react'
import { Routes, Route } from 'react-router-dom'
import { Box } from '@mui/material'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import AgentFlow from './pages/AgentFlow'
import AgentChat from './pages/AgentChat'
import ModuleManager from './pages/ModuleManager'

const App: React.FC = () => {
  return (
    <Box sx={{ minHeight: '100vh' }}>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/flow" element={<AgentFlow />} />
          <Route path="/chat" element={<AgentChat />} />
          <Route path="/modules" element={<ModuleManager />} />
        </Routes>
      </Layout>
    </Box>
  )
}

export default App
