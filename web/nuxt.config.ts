import pkg from './package.json'
import { defineNuxtConfig } from 'nuxt/config'

// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2024-11-01',
  devtools: { enabled: true },
  modules: ['nuxt-quasar-ui', '@nuxt/eslint'],

  quasar: {
    extras: {
      fontIcons: ['material-icons', 'mdi-v7'],
    },
    config: {
      dark: 'auto',
    },
    plugins: ['Notify'],
  },

  // Make package version available at runtime
  runtimeConfig: {
    public: {
      appVersion: pkg.version,
      // Base URL for the Django API
      // It's recommended to set this via an environment variable (e.g., NUXT_PUBLIC_API_BASE_URL)
      // Defaulting to localhost:8000 for local Django development server
      apiBaseUrl: process.env.NUXT_PUBLIC_API_BASE_URL || 'http://api:8000/api',
    },
  },
})
