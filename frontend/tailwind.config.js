/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#F8FAFC', // Slate 50
        surface: '#FFFFFF',
        primary: {
          50: '#F5F3FF',
          100: '#EDE9FE',
          500: '#8B5CF6', // Violet 500
          600: '#7C3AED',
          700: '#6D28D9',
        },
        accent: {
          50: '#EFF6FF',
          500: '#3B82F6', // Blue 500
          600: '#2563EB',
        },
        success: {
          50: '#ECFDF5',
          500: '#10B981', // Emerald 500
          600: '#059669',
        },
        danger: {
          50: '#FEF2F2',
          500: '#EF4444', // Red 500
          600: '#E11D48',
        },
        warning: {
          50: '#FFFBEB',
          500: '#F59E0B', // Amber 500
        }
      },
      boxShadow: {
        'glass': '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)',
        'glass-hover': '0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04)',
        'glow-success': '0 0 15px rgba(16, 185, 129, 0.3)',
        'glow-danger': '0 0 15px rgba(239, 68, 68, 0.3)',
        'glow-warning': '0 0 15px rgba(245, 158, 11, 0.3)',
      },
      animation: {
        'shimmer': 'shimmer 2s linear infinite',
        'fade-in': 'fadeIn 0.3s ease-out forwards',
        'slide-up': 'slideUp 0.4s ease-out forwards',
      },
      keyframes: {
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        }
      }
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
