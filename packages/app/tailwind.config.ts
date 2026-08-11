import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        parchment: {
          50: '#fdfaf5',
          100: '#faf5eb',
          200: '#f0e6d3',
          300: '#e5d5b7',
          400: '#d4bd92',
          500: '#c4a572',
          600: '#b08b54',
          700: '#8b6914',
          800: '#6b5010',
          900: '#4a370c',
        },
        // 暖色强调色 — 用于笔记、交互高亮等
        accent: {
          50: '#f0f7f4',
          100: '#dceee5',
          200: '#b5dcc8',
          300: '#84c4a3',
          400: '#5aab82',
          500: '#3d8f65',
          600: '#2e7450',
          700: '#265d41',
          800: '#204b35',
          900: '#1b3d2c',
        },
      },
      fontFamily: {
        serif: ['Georgia', 'Times New Roman', 'serif'],
        sans: ['system-ui', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [],
};

export default config;
