/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'dna-blue': '#00D4FF',
        'dna-purple': '#8B5CF6',
        'dna-cyan': '#06B6D4',
        'dna-teal': '#14B8A6',
        'dna-green': '#10B981',
        'dna-pink': '#EC4899',
        'glass': 'rgba(255, 255, 255, 0.1)',
        'glass-dark': 'rgba(0, 0, 0, 0.2)',
      },
      backgroundImage: {
        'dna-gradient': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'ai-gradient': 'linear-gradient(135deg, #00D4FF 0%, #8B5CF6 100%)',
        'genome-gradient': 'linear-gradient(135deg, #06B6D4 0%, #14B8A6 100%)',
      },
      backdropBlur: {
        'xs': '2px',
      },
      animation: {
        'dna-rotate': 'dnaRotate 20s linear infinite',
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
        'float': 'float 6s ease-in-out infinite',
        'scan': 'scan 3s linear infinite',
        'particle-float': 'particleFloat 8s ease-in-out infinite',
      },
      keyframes: {
        dnaRotate: {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
        pulseGlow: {
          '0%, 100%': { 
            boxShadow: '0 0 20px rgba(0, 212, 255, 0.5), 0 0 40px rgba(139, 92, 246, 0.3)',
            transform: 'scale(1)',
          },
          '50%': { 
            boxShadow: '0 0 40px rgba(0, 212, 255, 0.8), 0 0 80px rgba(139, 92, 246, 0.5)',
            transform: 'scale(1.02)',
          },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-20px)' },
        },
        scan: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100vw)' },
        },
        particleFloat: {
          '0%, 100%': { transform: 'translateY(0px) translateX(0px) rotate(0deg)' },
          '33%': { transform: 'translateY(-30px) translateX(20px) rotate(120deg)' },
          '66%': { transform: 'translateY(10px) translateX(-20px) rotate(240deg)' },
        },
      },
    },
  },
  plugins: [],
}
