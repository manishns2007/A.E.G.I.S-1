/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0B1329',
        surface: '#162032',
        surfaceHover: '#1f2937',
        primary: '#00d2ff',
        secondary: '#94a3b8',
        accent: '#ffb703',
        success: '#00e676',
        danger: '#ff4b4b',
        border: '#2a364f',
        textMain: '#e2e8f0',
        textMuted: '#94a3b8'
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      }
    },
  },
  plugins: [],
}
