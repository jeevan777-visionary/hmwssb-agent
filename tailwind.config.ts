import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Cinematic landing colors from CINEMATIC_PLAN.md
        abyss: '#040B14',
        deep: '#071521',
        tide: '#0B2A47',
        aqua: '#22D3EE',
        sky: '#7DD3FC',
        foam: '#E6F6FF',
        mist: '#94A9BD',
        amber: '#F5B544',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Fraunces', 'serif'],
      },
    },
  },
  plugins: [],
}
export default config
