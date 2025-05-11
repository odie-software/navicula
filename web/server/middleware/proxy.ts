import { createProxyEventHandler } from "h3-proxy"

export default defineEventHandler(
  createProxyEventHandler({
    target: useRuntimeConfig().public.apiBaseUrl,
    changeOrigin: true,
    pathRewrite: {
      "^/api": "",
    },
    pathFilter: ["/api"],
  }),
)