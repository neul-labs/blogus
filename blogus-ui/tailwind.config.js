import { skeleton } from '@skeletonlabs/skeleton/tailwind/skeleton.cjs'
import * as themes from '@skeletonlabs/skeleton/themes'

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
    require('path').join(require.resolve('@skeletonlabs/skeleton'), '../**/*.{html,js,svelte,ts}')
  ],
  theme: {
    extend: {
      fontFamily: {
        'mono': ['JetBrains Mono', 'Fira Code', 'monospace'],
      }
    },
  },
  plugins: [
    skeleton({
      themes: [
        themes.cerberus,
        themes.rose
      ]
    })
  ]
}