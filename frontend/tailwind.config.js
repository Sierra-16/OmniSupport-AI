/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{vue,ts,js}"],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          '-apple-system', 'BlinkMacSystemFont', '"SF Pro Display"',
          '"PingFang SC"', '"Helvetica Neue"', 'Arial', 'sans-serif',
        ],
      },
      colors: {
        apple: {
          blue: '#007AFF',
          green: '#34C759',
          red: '#FF3B30',
          gray: '#8E8E93',
          bg: '#F2F2F7',
          card: '#FFFFFF',
        },
      },
      animation: {
        breathe: 'breathe 2s ease-in-out infinite',
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.4s ease-out',
      },
    },
  },
  plugins: [],
};
