/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Design tokens from §6.2
        bgApp: '#0a0a0b',
        surface: '#141416',
        surfaceRaised: '#1c1c1f',
        border: 'rgba(255,255,255,0.08)',
        text: '#ffffff',
        textMuted: '#8e8e8e',
        accent: '#ffffff',
        // Status colors
        'status-auto-commit': '#34d399',
        'status-review': '#fbbf24',
        'status-new-activity': '#f87171',
      },
      fontFamily: {
        sans: ['Inter', 'Segoe UI', 'system-ui', 'sans-serif'],
        display: ['BubbledotICG-FinePos', 'Geist Pixel Circle', 'monospace'],
      },
      fontSize: {
        'display-xl': ['4.5rem', { lineHeight: '1.1', letterSpacing: '-0.02em' }],
        'display-lg': ['3rem', { lineHeight: '1.1', letterSpacing: '-0.01em' }],
        'display-md': ['2.25rem', { lineHeight: '1.2' }],
        'display-sm': ['1.5rem', { lineHeight: '1.3' }],
        'kpi': ['3.5rem', { lineHeight: '1', letterSpacing: '-0.02em' }],
      },
      spacing: {
        'space-1': '0.25rem',
        'space-2': '0.5rem',
        'space-3': '0.75rem',
        'space-4': '1rem',
        'space-5': '1.25rem',
        'space-6': '1.5rem',
        'space-8': '2rem',
        'space-10': '2.5rem',
        'space-12': '3rem',
        'space-16': '4rem',
        'space-20': '5rem',
      },
      borderRadius: {
        'pill': '9999px',
        'card': '0.75rem',
        'card-lg': '1rem',
      },
      boxShadow: {
        'soft': '0 2px 8px rgba(0,0,0,0.3), 0 0 0 1px rgba(255,255,255,0.05)',
        'card': '0 4px 16px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.05)',
        'elevated': '0 8px 32px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.08)',
      },
      transitionDuration: {
        'motion-fast': '150ms',
        'motion-base': '250ms',
        'motion-slow': '400ms',
      },
      transitionTimingFunction: {
        'motion-ease': 'cubic-bezier(0.4, 0, 0.2, 1)',
        'motion-spring': 'cubic-bezier(0.34, 1.56, 0.64, 1)',
      },
      animation: {
        'fade-in': 'fadeIn 250ms cubic-bezier(0.4, 0, 0.2, 1) forwards',
        'slide-up': 'slideUp 300ms cubic-bezier(0.4, 0, 0.2, 1) forwards',
        'slide-down': 'slideDown 300ms cubic-bezier(0.4, 0, 0.2, 1) forwards',
        'scale-in': 'scaleIn 200ms cubic-bezier(0.34, 1.56, 0.64, 1) forwards',
        'pulse-soft': 'pulseSoft 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideDown: {
          '0%': { opacity: '0', transform: 'translateY(-16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        pulseSoft: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.6' },
        },
      },
    },
  },
  plugins: [],
}