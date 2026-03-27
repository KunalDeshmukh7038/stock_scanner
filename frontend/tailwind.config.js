/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        positive: '#22C55E',
        negative: '#EF4444',
        neutral: '#F0A500',
        ink: '#E5E7EB',
        muted: '#9CA3AF',
        line: '#243041',
        surface: '#111827',
        canvas: '#0B0F19',
        panel: '#0F172A',
        brand: '#E5E7EB',
        highlight: '#3B82F6',
      },
      boxShadow: {
        panel: '0 22px 50px rgba(2, 6, 23, 0.45)',
        soft: '0 10px 30px rgba(2, 6, 23, 0.28)',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        display: ['Poppins', 'sans-serif'],
        mono: ['Inter', 'monospace'],
      },
      backgroundImage: {
        'hero-grid':
          'radial-gradient(circle at top left, rgba(59, 130, 246, 0.20), transparent 26%), radial-gradient(circle at top right, rgba(34, 197, 94, 0.14), transparent 24%)',
      },
    },
  },
  plugins: [],
};
