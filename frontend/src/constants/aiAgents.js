/**
 * AI Chat Agent Configuration
 * 
 * Contains the list of supported AI chat agents with their
 * URLs, brand colors, and display metadata.
 */

export const AI_AGENTS = [
  {
    id: 'chatgpt',
    name: 'ChatGPT',
    url: 'https://chat.openai.com/',
    icon: '🟢',
    color: '#10a37f',
    bgColor: 'bg-green-50',
    hoverColor: 'hover:bg-green-100',
    borderColor: 'border-green-200',
    textColor: 'text-green-700',
  },
  {
    id: 'gemini',
    name: 'Gemini',
    url: 'https://gemini.google.com/app',
    icon: '🔵',
    color: '#4285f4',
    bgColor: 'bg-blue-50',
    hoverColor: 'hover:bg-blue-100',
    borderColor: 'border-blue-200',
    textColor: 'text-blue-700',
  },
  {
    id: 'claude',
    name: 'Claude',
    url: 'https://claude.ai/new',
    icon: '🟣',
    color: '#7c3aed',
    bgColor: 'bg-purple-50',
    hoverColor: 'hover:bg-purple-100',
    borderColor: 'border-purple-200',
    textColor: 'text-purple-700',
  },
];
