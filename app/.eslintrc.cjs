module.exports = {
  root: true,
  env: {
    browser: true,
    node: true,
  },
  extends: [
    '@nuxtjs/eslint-config-typescript',
    'plugin:vue/vue3-recommended',
    'prettier', // Make sure 'prettier' is the last extension
  ],
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
  },
  rules: {
    // Add any project-specific ESLint rules here
    // Example:
    // 'vue/multi-word-component-names': 'off', // Disable if needed for simple pages like index.vue
  },
}
