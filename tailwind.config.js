/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './**/templates/**/*.html',
    './assets/js/**/*.js',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Montserrat', 'sans-serif'],
      },
      colors: {
        primary: {
          10: '#fbfdff',
          25: '#f8fbff',
          50: '#eff6ff',
          200: '#bfdbfe',
          300: '#93c5fd',
          500: '#3b82f6',
          800: '#14005C',
          900: '#060024',
        },
      },
    },
  },
  plugins: [],
};
