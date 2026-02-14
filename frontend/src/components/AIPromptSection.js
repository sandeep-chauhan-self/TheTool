import { useEffect, useRef, useState } from 'react';
import { AI_AGENTS } from '../constants/aiAgents';
import { buildCombinedPrompt, buildSinglePrompt, buildUniversalPrompt, getPromptTitles } from '../utils/promptBuilder';
import './AIPromptSection.css';

/**
 * Single Prompt Card Component
 */
function PromptCard({ title, subtitle, content, index, isExpanded, onToggle, onCopy }) {
  const [showAiDropdown, setShowAiDropdown] = useState(false);
  const dropdownRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowAiDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleAiClick = (agent) => {
    onCopy(content, agent); // Pass agent to parent handler
    setShowAiDropdown(false);
  };

  return (
    <div className={`prompt-card ${isExpanded ? 'expanded' : ''}`}>
      {/* Card Header (Click to Expand) */}
      <div className="card-header" onClick={onToggle}>
        <div className="card-title-group">
          <div className={`status-icon ${index === -2 ? 'status-universal' : 'status-completed'}`}>
             {index === -2 ? '🚀' : (index + 1)}
          </div>
          <div>
            <div className="card-title">{title}</div>
            {subtitle && <div className="card-subtitle">{subtitle}</div>}
          </div>
        </div>
        <div className="expand-icon">▼</div>
      </div>

      {/* Card Content (Visible when Expanded) */}
      {isExpanded && (
        <div className="card-content">
          <pre className="prompt-preview">{content}</pre>
          
          <div className="card-actions">
            <button 
              className="action-btn btn-secondary"
              onClick={(e) => { e.stopPropagation(); onCopy(content); }}
            >
              <span>📋 Copy Text</span>
            </button>

            <div className="ai-dropdown-wrapper" ref={dropdownRef}>
              <button 
                className="action-btn btn-primary"
                onClick={(e) => { e.stopPropagation(); setShowAiDropdown(!showAiDropdown); }}
              >
                <span>🤖 Ask AI</span>
                <span>▼</span>
              </button>

              {showAiDropdown && (
                <div className="ai-agent-dropdown">
                  {AI_AGENTS.map((agent) => (
                    <button
                      key={agent.id}
                      className={`ai-agent-option`}
                      onClick={() => handleAiClick(agent)}
                    >
                      <span className="ai-agent-icon">{agent.icon}</span>
                      <div className="ai-agent-info">
                        <span className="ai-agent-name">{agent.name}</span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Main AI Prompt Section Component
 */
function AIPromptSection({ stockName, ticker, strategyId, strategyName, verdict, score, entry, stopLoss, target }) {
  const [mode, setMode] = useState('universal'); // 'universal' or 'breakdown'
  const [expandedIndex, setExpandedIndex] = useState(0); // For breakdown mode
  const [toastMessage, setToastMessage] = useState('');

  const params = { stockName, ticker, verdict, score, entry, stopLoss, target, strategyName };
  const promptTitles = getPromptTitles(strategyId);
  
  // Strategy-specific subtitles map (simplified for layout)
  const subtitles = [
    "Volume, spreads, and circuit limits",
    "Recent news, earnings, and sentiment",
    "Valuation, growth, and health",
    "Sector trends and market mood",
    "FII/DII activity and ownership",
    "Comprehensive risk assessment"
  ];

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(''), 3000);
  };

  const handleCopy = async (text, agent = null) => {
    try {
      await navigator.clipboard.writeText(text);
      if (agent) {
        showToast(`✅ Copied! Opening ${agent.name}...`);
        window.open(agent.url, '_blank');
      } else {
        showToast('✅ Prompt copied to clipboard!');
      }
    } catch (err) {
      showToast('❌ Failed to copy');
    }
  };

  return (
    <div className="bg-white rounded shadow p-6 mb-6 ai-prompt-section">
      {/* 1. Header & Signal Summary */}
      <div className="ai-section-header">
        <div className="ai-title-row">
          <span className="text-2xl">🤖</span>
          <div>
            <h2 className="ai-title-text">AI Deep Dive Analysis</h2>
            <div className="text-sm text-gray-500">Validate signals with comprehensive AI research</div>
          </div>
        </div>
      </div>

      <div className="signal-summary-card mb-6">
        <div className="signal-tag">Signal</div>
        <div className="signal-value">{stockName} ({ticker})</div>
        <div className="text-gray-300">|</div>
        <div className="signal-tag" style={{ color: verdict === 'Buy' ? 'green' : 'red' }}>{verdict}</div>
        <div className="signal-value">Score: {score}</div>
        <div className="text-gray-300">|</div>
        <div className="text-sm">
          Entry: <span className="font-mono">{entry}</span> • Target: <span className="font-mono">{target}</span>
        </div>
      </div>

      {/* 2. Mode Switcher */}
      <div className="mode-switcher">
        <button 
          className={`mode-btn ${mode === 'universal' ? 'active' : ''}`}
          onClick={() => setMode('universal')}
        >
          🚀 Universal Framework (One-Shot)
        </button>
        <button 
          className={`mode-btn ${mode === 'breakdown' ? 'active' : ''}`}
          onClick={() => setMode('breakdown')}
        >
          📋 Strategy Breakdown (5 Steps)
        </button>
      </div>

      {/* 3. Card List */}
      <div className="prompt-card-list">
        
        {/* Universal Mode */}
        {mode === 'universal' && (
          <PromptCard
            title="Universal Analysis Framework"
            subtitle="Complete 6-factor analysis in one single prompt"
            content={buildUniversalPrompt(params)}
            index={-2} // Special index for universal
            isExpanded={true} // Always expanded in this mode
            onToggle={() => {}} 
            onCopy={handleCopy}
          />
        )}

        {/* Breakdown Mode */}
        {mode === 'breakdown' && promptTitles.map((title, idx) => (
          <PromptCard
            key={idx}
            title={`${idx + 1}. ${title}`}
            subtitle={subtitles[idx] || "Strategy specific analysis"}
            content={buildSinglePrompt(strategyId, idx, params)}
            index={idx}
            isExpanded={expandedIndex === idx}
            onToggle={() => setExpandedIndex(expandedIndex === idx ? -1 : idx)}
            onCopy={handleCopy}
          />
        ))}

        {mode === 'breakdown' && (
             <div className="text-center mt-2">
                 <button 
                    className="text-sm text-purple-600 font-semibold hover:underline"
                    onClick={() => handleCopy(buildCombinedPrompt(strategyId, params))}
                 >
                     📋 Copy All 5 Prompts at Once
                 </button>
             </div>
        )}
      </div>

      {/* Toast */}
      {toastMessage && (
        <div className="copy-toast fixed bottom-8 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white px-4 py-2 rounded-lg shadow-lg z-50">
          {toastMessage}
        </div>
      )}
    </div>
  );
}

export default AIPromptSection;
