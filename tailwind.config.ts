import type { Config } from 'tailwindcss'

export default {
  content: [
    './index.html',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#eff6ff',
          100: '#dbeafe',
          500: '#2563eb',
          700: '#1d4ed8',
          900: '#1e3a8a',
        },
        price: {
          up:   '#dc2626',
          down: '#2563eb',
          flat: '#6b7280',
        },
      },
      fontFamily: {
        sans: ['"Noto Sans JP"', '"Hiragino Sans"', '"Yu Gothic UI"', 'Meiryo', 'sans-serif'],
      },
    },
  },
  plugins: [],
} satisfies Config
