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
    },
  },
})
