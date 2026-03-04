import type { Config } from 'tailwindcss'

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'bg-primary': '#0A0A1A',
        'bg-secondary': '#0D1117',
        'bg-card': '#111827',
        'bg-card-hover': '#1A2332',
        'border-subtle': '#1E293B',
        'border-accent': '#2E4057',
        'accent-cyan': '#00D4FF',
        'accent-violet': '#7C3AED',
        'text-primary': '#F1F5F9',
        'text-secondary': '#94A3B8',
        'text-muted': '#475569',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      backgroundImage: {
        'gradient-main': 'linear-gradient(135deg, #00D4FF 0%, #7C3AED 100%)',
      },
      boxShadow: {
        'glow-cyan': '0 0 20px rgba(0, 212, 255, 0.15)',
        'glow-violet': '0 0 20px rgba(124, 58, 237, 0.15)',
        'glow-cyan-strong': '0 0 30px rgba(0, 212, 255, 0.3)',
      },
    },
  },
  plugins: [],
} satisfies Config
