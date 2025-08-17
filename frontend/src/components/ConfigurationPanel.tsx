import React, { useState, useEffect } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Slider,
  Switch,
  FormControlLabel,
  Chip,
  Divider,
  Grid,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  IconButton,
  Tooltip,
  Alert,
  Stack,
  ButtonGroup,
} from '@mui/material'
import {
  ExpandMore,
  Settings,
  Psychology,
  Speed,
  Analytics,
  Save,
  RestoreFromTrash,
  Info,
  Tune,
  Science,
  CompareArrows,
} from '@mui/icons-material'

export interface LLMConfig {
  provider: 'openai' | 'anthropic'
  model: string
  temperature: number
  max_tokens: number
  top_p: number
  frequency_penalty: number
  presence_penalty: number
  system_prompt: string
  response_format: 'text' | 'json'
  stream: boolean
}

export interface TestingConfig {
  enable_performance_tracking: boolean
  enable_token_usage_tracking: boolean
  enable_response_time_tracking: boolean
  enable_conversation_history: boolean
  max_conversation_history: number
  enable_model_comparison: boolean
  enable_batch_testing: boolean
  auto_save_conversations: boolean
  performance_threshold_ms: number
  token_budget_limit: number
}

interface ConfigurationPanelProps {
  onConfigChange: (config: { llm: LLMConfig; testing: TestingConfig }) => void
  currentConfig?: { llm: LLMConfig; testing: TestingConfig }
  disabled?: boolean
}

const defaultLLMConfig: LLMConfig = {
  provider: 'openai',
  model: 'gpt-4o',
  temperature: 0.7,
  max_tokens: 1000,
  top_p: 1.0,
  frequency_penalty: 0,
  presence_penalty: 0,
  system_prompt: 'You are a helpful AI assistant.',
  response_format: 'text',
  stream: false,
}

const defaultTestingConfig: TestingConfig = {
  enable_performance_tracking: true,
  enable_token_usage_tracking: true,
  enable_response_time_tracking: true,
  enable_conversation_history: true,
  max_conversation_history: 50,
  enable_model_comparison: false,
  enable_batch_testing: false,
  auto_save_conversations: true,
  performance_threshold_ms: 5000,
  token_budget_limit: 10000,
}

const modelOptions = {
  openai: [
    { value: 'gpt-4o', label: 'GPT-4o (Latest)' },
    { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
    { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
    { value: 'gpt-4', label: 'GPT-4' },
    { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
  ],
  anthropic: [
    { value: 'claude-3-5-sonnet-latest', label: 'Claude 3.5 Sonnet (Latest)' },
    { value: 'claude-3-5-haiku-latest', label: 'Claude 3.5 Haiku' },
    { value: 'claude-3-opus-latest', label: 'Claude 3 Opus' },
    { value: 'claude-3-sonnet-latest', label: 'Claude 3 Sonnet' },
    { value: 'claude-3-haiku-latest', label: 'Claude 3 Haiku' },
  ],
}

const ConfigurationPanel: React.FC<ConfigurationPanelProps> = ({
  onConfigChange,
  currentConfig,
  disabled = false,
}) => {
  const [llmConfig, setLLMConfig] = useState<LLMConfig>(
    currentConfig?.llm || defaultLLMConfig
  )
  const [testingConfig, setTestingConfig] = useState<TestingConfig>(
    currentConfig?.testing || defaultTestingConfig
  )
  const [isDirty, setIsDirty] = useState(false)

  useEffect(() => {
    if (currentConfig) {
      setLLMConfig(currentConfig.llm)
      setTestingConfig(currentConfig.testing)
    }
  }, [currentConfig])

  const handleLLMConfigChange = (field: keyof LLMConfig, value: any) => {
    const newConfig = { ...llmConfig, [field]: value }
    setLLMConfig(newConfig)
    setIsDirty(true)
  }

  const handleTestingConfigChange = (field: keyof TestingConfig, value: any) => {
    const newConfig = { ...testingConfig, [field]: value }
    setTestingConfig(newConfig)
    setIsDirty(true)
  }

  const handleSave = () => {
    onConfigChange({ llm: llmConfig, testing: testingConfig })
    setIsDirty(false)
  }

  const handleReset = () => {
    setLLMConfig(currentConfig?.llm || defaultLLMConfig)
    setTestingConfig(currentConfig?.testing || defaultTestingConfig)
    setIsDirty(false)
  }

  const getTemperatureLabel = (value: number) => {
    if (value <= 0.3) return 'Focused'
    if (value <= 0.7) return 'Balanced'
    return 'Creative'
  }

  const getPerformanceColor = (threshold: number) => {
    if (threshold <= 2000) return 'success'
    if (threshold <= 5000) return 'warning'
    return 'error'
  }

  return (
    <Box sx={{ width: '100%', maxWidth: '100%' }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Settings color="primary" />
          <Typography variant="h5" fontWeight={600}>
            Configuration Panel
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<RestoreFromTrash />}
            onClick={handleReset}
            disabled={!isDirty || disabled}
            size="small"
          >
            Reset
          </Button>
          <Button
            variant="contained"
            startIcon={<Save />}
            onClick={handleSave}
            disabled={!isDirty || disabled}
            size="small"
          >
            Apply Changes
          </Button>
        </Box>
      </Box>

      {isDirty && (
        <Alert severity="info" sx={{ mb: 2 }}>
          You have unsaved changes. Click "Apply Changes" to save your configuration.
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* LLM Configuration */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <Psychology color="primary" />
                <Typography variant="h6" fontWeight={600}>
                  LLM Configuration
                </Typography>
              </Box>

              <Stack spacing={3}>
                {/* Provider Selection */}
                <FormControl fullWidth>
                  <InputLabel>Provider</InputLabel>
                  <Select
                    value={llmConfig.provider}
                    onChange={(e) => handleLLMConfigChange('provider', e.target.value)}
                    disabled={disabled}
                  >
                    <MenuItem value="openai">
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        🤖 OpenAI
                      </Box>
                    </MenuItem>
                    <MenuItem value="anthropic">
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        🧠 Anthropic
                      </Box>
                    </MenuItem>
                  </Select>
                </FormControl>

                {/* Model Selection */}
                <FormControl fullWidth>
                  <InputLabel>Model</InputLabel>
                  <Select
                    value={llmConfig.model}
                    onChange={(e) => handleLLMConfigChange('model', e.target.value)}
                    disabled={disabled}
                  >
                    {modelOptions[llmConfig.provider].map((option) => (
                      <MenuItem key={option.value} value={option.value}>
                        {option.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>

                {/* Temperature */}
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2" fontWeight={500}>
                      Temperature
                    </Typography>
                    <Chip
                      label={`${llmConfig.temperature} - ${getTemperatureLabel(llmConfig.temperature)}`}
                      size="small"
                      color={llmConfig.temperature <= 0.3 ? 'info' : llmConfig.temperature <= 0.7 ? 'warning' : 'secondary'}
                    />
                  </Box>
                  <Slider
                    value={llmConfig.temperature}
                    onChange={(_, value) => handleLLMConfigChange('temperature', value)}
                    min={0}
                    max={2}
                    step={0.1}
                    marks={[
                      { value: 0, label: '0' },
                      { value: 0.5, label: '0.5' },
                      { value: 1, label: '1' },
                      { value: 1.5, label: '1.5' },
                      { value: 2, label: '2' },
                    ]}
                    disabled={disabled}
                  />
                </Box>

                {/* Max Tokens */}
                <TextField
                  label="Max Tokens"
                  type="number"
                  value={llmConfig.max_tokens}
                  onChange={(e) => handleLLMConfigChange('max_tokens', parseInt(e.target.value))}
                  inputProps={{ min: 1, max: 8192 }}
                  disabled={disabled}
                  helperText="Maximum number of tokens to generate"
                />

                {/* Advanced Settings Accordion */}
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Typography variant="body2" fontWeight={500}>
                      Advanced Parameters
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Stack spacing={2}>
                      {/* Top P */}
                      <Box>
                        <Typography variant="body2" fontWeight={500} gutterBottom>
                          Top P: {llmConfig.top_p}
                        </Typography>
                        <Slider
                          value={llmConfig.top_p}
                          onChange={(_, value) => handleLLMConfigChange('top_p', value)}
                          min={0}
                          max={1}
                          step={0.1}
                          disabled={disabled}
                        />
                      </Box>

                      {/* Frequency Penalty */}
                      <Box>
                        <Typography variant="body2" fontWeight={500} gutterBottom>
                          Frequency Penalty: {llmConfig.frequency_penalty}
                        </Typography>
                        <Slider
                          value={llmConfig.frequency_penalty}
                          onChange={(_, value) => handleLLMConfigChange('frequency_penalty', value)}
                          min={-2}
                          max={2}
                          step={0.1}
                          disabled={disabled}
                        />
                      </Box>

                      {/* Presence Penalty */}
                      <Box>
                        <Typography variant="body2" fontWeight={500} gutterBottom>
                          Presence Penalty: {llmConfig.presence_penalty}
                        </Typography>
                        <Slider
                          value={llmConfig.presence_penalty}
                          onChange={(_, value) => handleLLMConfigChange('presence_penalty', value)}
                          min={-2}
                          max={2}
                          step={0.1}
                          disabled={disabled}
                        />
                      </Box>

                      {/* Response Format */}
                      <FormControl fullWidth>
                        <InputLabel>Response Format</InputLabel>
                        <Select
                          value={llmConfig.response_format}
                          onChange={(e) => handleLLMConfigChange('response_format', e.target.value)}
                          disabled={disabled}
                        >
                          <MenuItem value="text">Text</MenuItem>
                          <MenuItem value="json">JSON</MenuItem>
                        </Select>
                      </FormControl>

                      {/* Stream */}
                      <FormControlLabel
                        control={
                          <Switch
                            checked={llmConfig.stream}
                            onChange={(e) => handleLLMConfigChange('stream', e.target.checked)}
                            disabled={disabled}
                          />
                        }
                        label="Enable Streaming"
                      />
                    </Stack>
                  </AccordionDetails>
                </Accordion>

                {/* System Prompt */}
                <TextField
                  label="System Prompt"
                  multiline
                  rows={3}
                  value={llmConfig.system_prompt}
                  onChange={(e) => handleLLMConfigChange('system_prompt', e.target.value)}
                  disabled={disabled}
                  helperText="Instructions for the AI assistant's behavior"
                />
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        {/* Testing Configuration */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <Science color="primary" />
                <Typography variant="h6" fontWeight={600}>
                  Testing & Analytics
                </Typography>
              </Box>

              <Stack spacing={3}>
                {/* Performance Tracking */}
                <Box>
                  <Typography variant="body1" fontWeight={500} gutterBottom>
                    Performance Monitoring
                  </Typography>
                  <Stack spacing={1}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={testingConfig.enable_performance_tracking}
                          onChange={(e) => handleTestingConfigChange('enable_performance_tracking', e.target.checked)}
                          disabled={disabled}
                        />
                      }
                      label="Track Performance Metrics"
                    />
                    <FormControlLabel
                      control={
                        <Switch
                          checked={testingConfig.enable_response_time_tracking}
                          onChange={(e) => handleTestingConfigChange('enable_response_time_tracking', e.target.checked)}
                          disabled={disabled}
                        />
                      }
                      label="Track Response Times"
                    />
                    <FormControlLabel
                      control={
                        <Switch
                          checked={testingConfig.enable_token_usage_tracking}
                          onChange={(e) => handleTestingConfigChange('enable_token_usage_tracking', e.target.checked)}
                          disabled={disabled}
                        />
                      }
                      label="Track Token Usage"
                    />
                  </Stack>
                </Box>

                <Divider />

                {/* Performance Threshold */}
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2" fontWeight={500}>
                      Performance Threshold (ms)
                    </Typography>
                    <Chip
                      label={`${testingConfig.performance_threshold_ms}ms`}
                      size="small"
                      color={getPerformanceColor(testingConfig.performance_threshold_ms)}
                    />
                  </Box>
                  <Slider
                    value={testingConfig.performance_threshold_ms}
                    onChange={(_, value) => handleTestingConfigChange('performance_threshold_ms', value)}
                    min={1000}
                    max={30000}
                    step={500}
                    marks={[
                      { value: 1000, label: '1s' },
                      { value: 5000, label: '5s' },
                      { value: 10000, label: '10s' },
                      { value: 30000, label: '30s' },
                    ]}
                    disabled={disabled}
                  />
                </Box>

                {/* Token Budget */}
                <TextField
                  label="Token Budget Limit"
                  type="number"
                  value={testingConfig.token_budget_limit}
                  onChange={(e) => handleTestingConfigChange('token_budget_limit', parseInt(e.target.value))}
                  inputProps={{ min: 1000, max: 1000000 }}
                  disabled={disabled}
                  helperText="Daily token usage limit"
                />

                <Divider />

                {/* Conversation Settings */}
                <Box>
                  <Typography variant="body1" fontWeight={500} gutterBottom>
                    Conversation Management
                  </Typography>
                  <Stack spacing={1}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={testingConfig.enable_conversation_history}
                          onChange={(e) => handleTestingConfigChange('enable_conversation_history', e.target.checked)}
                          disabled={disabled}
                        />
                      }
                      label="Enable Conversation History"
                    />
                    <FormControlLabel
                      control={
                        <Switch
                          checked={testingConfig.auto_save_conversations}
                          onChange={(e) => handleTestingConfigChange('auto_save_conversations', e.target.checked)}
                          disabled={disabled}
                        />
                      }
                      label="Auto-save Conversations"
                    />
                  </Stack>
                </Box>

                {/* Max History */}
                <TextField
                  label="Max Conversation History"
                  type="number"
                  value={testingConfig.max_conversation_history}
                  onChange={(e) => handleTestingConfigChange('max_conversation_history', parseInt(e.target.value))}
                  inputProps={{ min: 10, max: 1000 }}
                  disabled={disabled || !testingConfig.enable_conversation_history}
                  helperText="Number of messages to keep in history"
                />

                <Divider />

                {/* Advanced Testing */}
                <Box>
                  <Typography variant="body1" fontWeight={500} gutterBottom>
                    Advanced Testing Features
                  </Typography>
                  <Stack spacing={1}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={testingConfig.enable_model_comparison}
                          onChange={(e) => handleTestingConfigChange('enable_model_comparison', e.target.checked)}
                          disabled={disabled}
                        />
                      }
                      label="Enable Model Comparison"
                    />
                    <FormControlLabel
                      control={
                        <Switch
                          checked={testingConfig.enable_batch_testing}
                          onChange={(e) => handleTestingConfigChange('enable_batch_testing', e.target.checked)}
                          disabled={disabled}
                        />
                      }
                      label="Enable Batch Testing"
                    />
                  </Stack>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Quick Actions */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Quick Presets
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <Button
              variant="outlined"
              size="small"
              startIcon={<Speed />}
              onClick={() => {
                handleLLMConfigChange('temperature', 0.1)
                handleLLMConfigChange('max_tokens', 500)
                setIsDirty(true)
              }}
              disabled={disabled}
            >
              Fast & Focused
            </Button>
            <Button
              variant="outlined"
              size="small"
              startIcon={<Tune />}
              onClick={() => {
                handleLLMConfigChange('temperature', 0.7)
                handleLLMConfigChange('max_tokens', 1000)
                setIsDirty(true)
              }}
              disabled={disabled}
            >
              Balanced
            </Button>
            <Button
              variant="outlined"
              size="small"
              startIcon={<Psychology />}
              onClick={() => {
                handleLLMConfigChange('temperature', 1.2)
                handleLLMConfigChange('max_tokens', 1500)
                setIsDirty(true)
              }}
              disabled={disabled}
            >
              Creative
            </Button>
            <Button
              variant="outlined"
              size="small"
              startIcon={<Analytics />}
              onClick={() => {
                handleTestingConfigChange('enable_performance_tracking', true)
                handleTestingConfigChange('enable_token_usage_tracking', true)
                handleTestingConfigChange('enable_response_time_tracking', true)
                handleTestingConfigChange('enable_model_comparison', true)
                setIsDirty(true)
              }}
              disabled={disabled}
            >
              Full Analytics
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  )
}

export default ConfigurationPanel
