# Trading Agent Tool Transparency Guide

## Overview

The trading agent now provides complete transparency into its tool execution process. Every API response includes detailed information about which tools were called, their parameters, execution results, and any errors encountered.

## Enhanced API Response Structure

### Tool Results Section

The `tool_results` array in the API response now contains detailed information about each tool execution:

```json
{
  "response": "...",
  "agent_name": "trading_bot",
  "agent_type": "trading_assistant",
  "processing_time": 6.53,
  "suggestions": [...],
  "tool_results": [
    {
      "tools_executed": ["yahoo_finance_api", "technical_indicators", "news_sentiment_analyzer", "risk_analyzer"]
    },
    {
      "analysis_type": "stock_data",
      "symbols_analyzed": ["AAPL", "TSLA"],
      "data_points": 2,
      "data_summary": "Stock price data retrieved successfully"
    },
    {
      "analysis_type": "technical_indicators",
      "indicators_calculated": ["AAPL", "TSLA"],
      "analysis_summary": "Technical indicators calculated successfully"
    },
    {
      "analysis_type": "news_sentiment",
      "sentiment_score": "N/A",
      "articles_analyzed": 0,
      "sentiment_summary": "No sentiment data available"
    },
    {
      "analysis_type": "risk_assessment",
      "risk_level": "medium",
      "volatility": "0.25",
      "risk_factors": ["market_volatility", "sector_concentration"]
    }
  ]
}
```

## Tool Transparency Features

### 1. Tool Execution Summary
- **`tools_executed`**: List of all tools that were called
- **`processing_time`**: Total time taken for analysis
- **`success`**: Whether the overall analysis was successful

### 2. Stock Data Analysis
- **`symbols_analyzed`**: Which stock symbols were processed
- **`data_points`**: Number of data fields retrieved
- **`data_summary`**: Summary of data retrieval success

### 3. Technical Analysis Details
- **`indicators_calculated`**: Which technical indicators were computed
- **`analysis_summary`**: Summary of technical analysis results

### 4. News Sentiment Analysis
- **`sentiment_score`**: Overall sentiment score (-1 to 1)
- **`articles_analyzed`**: Number of news articles processed
- **`sentiment_summary`**: Summary of sentiment analysis

### 5. Risk Assessment
- **`risk_level`**: Calculated risk level (low/medium/high)
- **`volatility`**: Volatility metrics
- **`risk_factors`**: List of identified risk factors

## Frontend Implementation Example

### React Component for Tool Transparency

```tsx
import React from 'react';

interface ToolResult {
  tools_executed?: string[];
  analysis_type?: string;
  symbols_analyzed?: string[];
  data_points?: number;
  data_summary?: string;
  indicators_calculated?: string[];
  analysis_summary?: string;
  sentiment_score?: number | string;
  articles_analyzed?: number;
  sentiment_summary?: string;
  risk_level?: string;
  volatility?: string;
  risk_factors?: string[];
}

interface TradingResponse {
  response: string;
  agent_name: string;
  processing_time: number;
  tool_results: ToolResult[];
  suggestions: string[];
}

const ToolTransparencyPanel: React.FC<{ response: TradingResponse }> = ({ response }) => {
  const toolsExecuted = response.tool_results.find(r => r.tools_executed)?.tools_executed || [];
  const analysisResults = response.tool_results.filter(r => r.analysis_type);

  return (
    <div className="tool-transparency-panel">
      <h3>🔍 Tool Execution Transparency</h3>

      {/* Execution Summary */}
      <div className="execution-summary">
        <h4>Execution Summary</h4>
        <p><strong>Processing Time:</strong> {response.processing_time.toFixed(2)}s</p>
        <p><strong>Tools Called:</strong> {toolsExecuted.join(', ')}</p>
      </div>

      {/* Analysis Details */}
      <div className="analysis-details">
        <h4>Analysis Breakdown</h4>
        {analysisResults.map((result, index) => (
          <div key={index} className="analysis-item">
            <h5>{result.analysis_type?.replace('_', ' ').toUpperCase()}</h5>

            {result.symbols_analyzed && (
              <p><strong>Symbols:</strong> {result.symbols_analyzed.join(', ')}</p>
            )}

            {result.data_points && (
              <p><strong>Data Points:</strong> {result.data_points}</p>
            )}

            {result.sentiment_score !== undefined && (
              <p><strong>Sentiment Score:</strong> {result.sentiment_score}</p>
            )}

            {result.articles_analyzed !== undefined && (
              <p><strong>Articles Analyzed:</strong> {result.articles_analyzed}</p>
            )}

            {result.risk_level && (
              <p><strong>Risk Level:</strong> {result.risk_level}</p>
            )}

            {result.volatility && (
              <p><strong>Volatility:</strong> {result.volatility}</p>
            )}

            {result.risk_factors && result.risk_factors.length > 0 && (
              <p><strong>Risk Factors:</strong> {result.risk_factors.join(', ')}</p>
            )}

            <p className="summary">{result.data_summary || result.analysis_summary || result.sentiment_summary}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ToolTransparencyPanel;
```

### CSS Styling

```css
.tool-transparency-panel {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin: 16px 0;
}

.tool-transparency-panel h3 {
  color: #495057;
  margin-bottom: 16px;
}

.execution-summary, .analysis-details {
  margin-bottom: 16px;
}

.analysis-item {
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  padding: 12px;
  margin-bottom: 8px;
}

.analysis-item h5 {
  color: #007bff;
  margin-bottom: 8px;
}

.summary {
  font-style: italic;
  color: #6c757d;
  margin-top: 8px;
}
```

## Usage in Your Application

1. **Make API Request** to the trading agent
2. **Extract tool_results** from the response
3. **Display transparency information** using the component above
4. **Show users exactly what data** was used for the analysis

## Benefits

✅ **Complete Transparency**: Users can see exactly which tools were called
✅ **Data Validation**: Users can verify what data was used for analysis
✅ **Error Visibility**: Any tool failures are clearly shown
✅ **Performance Metrics**: Processing times for each component
✅ **Trust Building**: Users can validate the agent's reasoning process

## Example API Call

```javascript
const response = await fetch('/api/agents/trading_bot/message', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    text: "Analyze AAPL and TSLA stocks with risk assessment",
    user_id: "user123"
  })
});

const data = await response.json();
// data.tool_results contains all transparency information
```

This transparency system ensures users can trust the trading agent's analysis by seeing exactly what data sources and tools were used to generate each recommendation.
