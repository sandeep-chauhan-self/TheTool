import { useCallback, useEffect, useRef, useState } from 'react';
import { AI_AGENTS } from '../constants/aiAgents';
import { buildCombinedPrompt, buildSinglePrompt, getPromptTitles } from '../utils/promptBuilder';
import './AIPromptSection.css';

/**
 * AI Prompt Section Component
 * 
 * Displays strategy-specific AI prompts on the analysis results page.
 * Users can view individual or combined prompts, copy them,
 * and open AI chat agents in a new tab.
 */
function AIPromptSection({ stockName, ticker, strategyId, strategyName, verdict, score, entry, stopLoss, target }) {
  const [selectedPromptIndex, setSelectedPromptIndex] = useState(-1); // -1 = all combined
  const [showDropdown, setShowDropdown] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [toastExiting, setToastExiting] = useState(false);
  const dropdownRef = useRef(null);
  const buttonRef = useRef(null);
  const toastTimerRef = useRef(null);

  const params = { stockName, ticker, verdict, score, entry, stopLoss, target, strategyName };

  // Get prompt titles for the tab bar
  const promptTitles = getPromptTitles(strategyId);

  // Generate the current prompt text
  const currentPrompt = selectedPromptIndex === -1
    ? buildCombinedPrompt(strategyId, params)
    : buildSinglePrompt(strategyId, selectedPromptIndex, params);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        dropdownRef.current && !dropdownRef.current.contains(event.target) &&
        buttonRef.current && !buttonRef.current.contains(event.target)
      ) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Show toast notification
  const showToast = useCallback((message) => {
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    setToastExiting(false);
    setToastMessage(message);
    toastTimerRef.current = setTimeout(() => {
      setToastExiting(true);
      setTimeout(() => setToastMessage(''), 300);
    }, 3000);
  }, []);

  // Copy prompt to clipboard
  const copyToClipboard = useCallback(async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (err) {
      // Fallback for older browsers
      const textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();
      try {
        document.execCommand('copy');
        document.body.removeChild(textarea);
        return true;
      } catch (e) {
        document.body.removeChild(textarea);
        return false;
      }
    }
  }, []);

  // Handle AI agent selection
  const handleAgentClick = async (agent) => {
    const copied = await copyToClipboard(currentPrompt);
    if (copied) {
      showToast(`✅ Prompt copied! Paste it in ${agent.name}`);
    } else {
      showToast('⚠️ Could not copy. Please select and copy manually.');
    }
    
    // Open agent URL in new tab
    window.open(agent.url, '_blank', 'noopener,noreferrer');
    setShowDropdown(false);
  };

  // Toggle dropdown
  const toggleDropdown = () => {
    setShowDropdown(prev => !prev);
  };

  return (
    <div className="bg-white rounded shadow p-6 mb-6 ai-prompt-section">
      {/* Section Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🤖</span>
          <h2 className="text-xl font-bold text-gray-800">AI Deep Dive Prompt</h2>
        </div>
        <span className="prompt-mode-badge">
          {selectedPromptIndex === -1 ? '📋 All 5 Prompts' : `#${selectedPromptIndex + 1} of 5`}
        </span>
      </div>

      <p className="text-sm text-gray-500 mb-4">
        These prompts cover what technical analysis <strong>cannot</strong> analyze — news, sentiment, fundamentals, institutional activity, and risk validation.
        Copy and paste into your preferred AI assistant for a comprehensive view.
      </p>

      {/* Prompt Selector Tabs */}
      <div className="prompt-tabs">
        <button
          className={`prompt-tab ${selectedPromptIndex === -1 ? 'active' : ''}`}
          onClick={() => setSelectedPromptIndex(-1)}
        >
          📋 All Prompts
        </button>
        {promptTitles.map((title, index) => (
          <button
            key={index}
            className={`prompt-tab ${selectedPromptIndex === index ? 'active' : ''}`}
            onClick={() => setSelectedPromptIndex(index)}
          >
            #{index + 1} {title}
          </button>
        ))}
      </div>

      {/* Prompt Display (Read-Only) */}
      <textarea
        className="ai-prompt-textarea"
        value={currentPrompt}
        readOnly
        onClick={(e) => e.target.select()}
        aria-label="AI analysis prompt"
      />

      {/* Action Bar */}
      <div className="flex items-center gap-3 mt-4 relative">
        <button
          ref={buttonRef}
          className="copy-ask-btn"
          onClick={toggleDropdown}
          aria-expanded={showDropdown}
          aria-haspopup="true"
        >
          <span>📋</span>
          <span>Copy & Ask AI</span>
          <span className={`chevron ${showDropdown ? 'open' : ''}`}>▼</span>
        </button>

        <span className="text-xs text-gray-400">
          Click to copy prompt & open AI chat
        </span>

        {/* AI Agent Dropdown */}
        {showDropdown && (
          <div ref={dropdownRef} className="ai-agent-dropdown">
            <div className="px-3 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Choose AI Assistant
            </div>
            {AI_AGENTS.map((agent) => (
              <button
                key={agent.id}
                className={`ai-agent-option ${agent.bgColor} ${agent.hoverColor} ${agent.borderColor}`}
                onClick={() => handleAgentClick(agent)}
                style={{ borderColor: 'transparent' }}
                onMouseEnter={(e) => e.currentTarget.style.borderColor = agent.color}
                onMouseLeave={(e) => e.currentTarget.style.borderColor = 'transparent'}
              >
                <span className="ai-agent-icon">{agent.icon}</span>
                <div className="ai-agent-info">
                  <span className="ai-agent-name">{agent.name}</span>
                  <span className="ai-agent-hint">Copy & open in new tab</span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Toast Notification */}
      {toastMessage && (
        <div className={`copy-toast ${toastExiting ? 'copy-toast-exit' : ''}`}>
          {toastMessage}
        </div>
      )}
    </div>
  );
}

export default AIPromptSection;
