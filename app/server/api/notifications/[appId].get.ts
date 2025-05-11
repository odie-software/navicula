// File: app/server/api/notifications/[appId].get.ts
import { promises as fs } from 'fs'
// import { join } from 'path' // Unused
import {
  defineEventHandler,
  // getQuery, // Unused
  getHeader,
  // setResponseStatus, // Unused
  createError,
  getRouterParam,
  type H3Event, // Added for type safety
} from 'h3'
import yaml from 'js-yaml'
import { $fetch } from 'ofetch'

// --- Type Guards (defined locally) ---
function isCategory(item: NavigationItem): item is NavCategory {
  return Array.isArray((item as NavCategory).apps)
}
function isAppLink(item: NavigationItem): item is AppLink {
  return typeof (item as AppLink).url === 'string'
}

// --- Helper to find AppLink by ID ---
function findAppLinkById(
  navItems: NavigationItem[],
  appId: string
): AppLink | undefined {
  for (const item of navItems) {
    if (isAppLink(item) && item.id === appId) {
      return item
    } else if (isCategory(item)) {
      const found = item.apps.find((app) => app.id === appId)
      if (found) return found
    }
  }
  return undefined
}

// --- Helper to get User Identifier ---
function getUserIdentifier(event: H3Event, config: Config): string | null {
  if (config.useRemoteAuth) {
    const userEmailHeader = (
      getHeader(event, 'remote-user') ||
      getHeader(event, 'x-forwarded-user') ||
      ''
    ).toLowerCase()
    return userEmailHeader || null
  } else {
    // When not using remote auth, the identifier is 'default' if that user exists
    return config.users['default'] ? 'default' : null
  }
}

// --- Helper to load User App Settings from users.yml ---
const USER_SETTINGS_PATH =
  process.env.APP_USER_SETTINGS_PATH || '/app/users.yml'

// Loads the settings for a SPECIFIC user from the main users.yml file
async function loadUserSettingsForUser(
  userIdentifier: string
): Promise<UserAppSettings | null> {
  // Return null on error, {} if not found/empty
  if (!userIdentifier) return {} // Should not happen if called correctly, but return empty for safety

  try {
    const fileContent = await fs.readFile(USER_SETTINGS_PATH, 'utf-8')
    const allSettings = yaml.load(fileContent) as AllUserSettings | null
    return allSettings?.[userIdentifier] || {} // Return specific user's settings or empty object
  } catch (e: unknown) {
    const error = e as { code?: string; message?: string } // Type assertion
    if (error.code === 'ENOENT') {
      // File not found is expected, treat as empty settings
      return {}
    }
    // Log other read errors
    console.error(
      `Error reading user settings file at ${USER_SETTINGS_PATH}:`,
      error
    )
    // Indicate an error occurred during loading
    return null
  }
}

// const DEFAULT_ROLE = 'Guest'; // Not directly needed here, role logic is in config.get.ts

export default defineEventHandler(async (event) => {
  const appId = getRouterParam(event, 'appId')
  if (!appId) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request: Missing appId parameter',
    })
  }

  // --- Load Main Config ---
  const configPath = process.env.APP_CONFIG_PATH || '/app/config.yml'
  let config: Config
  try {
    const fileContent = await fs.readFile(configPath, 'utf-8')
    config = yaml.load(fileContent) as Config
    if (!config || typeof config !== 'object') {
      throw new Error('Invalid main config format.')
    }
  } catch (error) {
    console.error(`Error loading main config file at ${configPath}:`, error)
    throw createError({
      statusCode: 500,
      statusMessage: 'Internal Server Error: Failed to load configuration',
    })
  }

  // --- Identify User ---
  const userIdentifier = getUserIdentifier(event, config)
  if (!userIdentifier && config.useRemoteAuth) {
    // If remote auth is enabled but no user header is found, deny access? Or treat as Guest?
    // For now, let's prevent fetching notifications if user cannot be identified with remote auth.
    // If !useRemoteAuth, userIdentifier should be 'default' or null (if 'default' user missing).
    console.warn(
      'Notifications: Could not identify user with remote auth enabled.'
    )
    throw createError({
      statusCode: 401, // Unauthorized
      statusMessage: 'Unauthorized: User identification failed',
    })
  }
  if (!userIdentifier && !config.useRemoteAuth) {
    console.warn(
      "Notifications: 'default' user not found in config for non-remote auth mode."
    )
    throw createError({
      statusCode: 403, // Forbidden (config issue)
      statusMessage: 'Forbidden: Default user configuration missing',
    })
  }

  // --- Find the AppLink ---
  const appLink = findAppLinkById(config.navigationItems || [], appId)
  if (!appLink || !appLink.type) {
    // App not found or doesn't support notifications (no type)
    return { count: null } // Return null count for unsupported/unknown apps
  }

  // --- Load User-Specific Settings from users.yml ---
  const userSettings = await loadUserSettingsForUser(userIdentifier!) // We know userIdentifier is not null here
  if (userSettings === null) {
    // Error loading settings file (logged in helper)
    throw createError({
      statusCode: 500,
      statusMessage: 'Internal Server Error: Failed to load user settings',
    })
  }

  const appSettings = userSettings[appId]

  // --- Fetch Notifications Based on Type ---
  let notificationCount: number | null = null

  try {
    switch (appLink.type) {
      case 'vikunja': {
        const apiKey = appSettings?.api_key
        if (!apiKey) {
          console.warn(
            `Notifications: Missing api_key for Vikunja (${appId}) for user ${userIdentifier}`
          )
          // Don't throw error, just return null count as it's not configured
          return { count: null }
        }

        // Ensure URL doesn't end with a slash before appending API path
        const baseUrl = appLink.url.replace(/\/$/, '')
        const apiUrl = `${baseUrl}/api/v1/notifications`

        console.log(
          `Fetching Vikunja notifications from ${apiUrl} for user ${userIdentifier}`
        )

        const notifications: unknown[] = await $fetch(apiUrl, {
          method: 'GET',
          headers: {
            Authorization: `Bearer ${apiKey}`,
            Accept: 'application/json',
          },
          // Add timeout? Retry logic?
          timeout: 5000, // 5 second timeout
        })

        if (Array.isArray(notifications)) {
          // Assuming a Vikunja notification object has a 'read_at' property
          type VikunjaNotification = {
            read_at: string | null | undefined
            [key: string]: unknown
          }
          const typedNotifications = notifications as VikunjaNotification[]
          notificationCount = typedNotifications.filter(
            (x) => !x.read_at
          ).length
          console.log(
            `Vikunja notifications count for ${appId} / ${userIdentifier}: ${notificationCount}`
          )
        } else {
          console.warn(
            `Notifications: Unexpected response format from Vikunja (${appId}) for user ${userIdentifier}:`,
            notifications
          )
        }
        break
      }
      // Add cases for other supported types here...
      // case 'another-service': {
      //   // ... implementation ...
      //   break;
      // }
      default: {
        // Type defined but not handled here
        console.log(
          `Notifications: Unsupported type "${appLink.type}" for app ${appId}`
        )
        break
      }
    }
  } catch (e: unknown) {
    const error = e as { message?: string; response?: { status?: number } } // Basic error structure
    // Log specific errors from $fetch or other issues
    console.error(
      `Notifications: Error fetching data for ${appLink.type} (${appId}) for user ${userIdentifier}:`,
      error.message || error
    )
    // Optionally check error status code (e.g., 401 Unauthorized from Vikunja)
    if (error.response?.status === 401) {
      console.warn(
        `Notifications: Unauthorized access to ${appLink.type} API (${appId}) for user ${userIdentifier}. Check API key.`
      )
      // Return null count, maybe frontend can indicate configuration error
      return { count: null, error: 'unauthorized' }
    }
    if (error.message && error.message.includes('timeout')) {
      // Check if message exists
      console.warn(
        `Notifications: Timeout fetching data for ${appLink.type} (${appId}) for user ${userIdentifier}.`
      )
      return { count: null, error: 'timeout' }
    }
    // For other errors, return null count
    return { count: null, error: 'fetch_failed' }
  }

  return { count: notificationCount }
})
