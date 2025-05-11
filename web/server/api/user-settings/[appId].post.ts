// File: app/server/api/user-settings/[appId].post.ts
import { promises as fs } from 'fs'
// import { join } from 'path'; // Unused
import {
  defineEventHandler,
  getHeader,
  setResponseStatus,
  createError,
  getRouterParam,
  readBody,
  type H3Event, // Added for type safety
} from 'h3'
import yaml from 'js-yaml'

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
    return config.users['default'] ? 'default' : null
  }
}

// --- Helper to load/save User App Settings from users.yml ---
const USER_SETTINGS_PATH =
  process.env.APP_USER_SETTINGS_PATH || '/app/users.yml'

// Loads the settings for a SPECIFIC user from the main users.yml file
async function loadUserSettingsForUser(
  userIdentifier: string
): Promise<UserAppSettings> {
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
    // Don't throw an error here, allow saving to create the file if needed
    return {} // Treat read error as empty settings
  }
}

// Saves the settings for a SPECIFIC user back into the main users.yml file
async function saveUserSettingsForUser(
  userIdentifier: string,
  userSettings: UserAppSettings
): Promise<void> {
  let allSettings: AllUserSettings = {}
  try {
    // Try reading existing file first
    const fileContent = await fs.readFile(USER_SETTINGS_PATH, 'utf-8')
    allSettings = (yaml.load(fileContent) as AllUserSettings | null) || {}
  } catch (e: unknown) {
    const error = e as { code?: string; message?: string } // Type assertion
    if (error.code !== 'ENOENT') {
      // If error is not 'file not found', rethrow
      console.error(
        `Error reading user settings file before writing at ${USER_SETTINGS_PATH}:`,
        error
      )
      throw createError({
        statusCode: 500,
        statusMessage:
          'Internal Server Error: Could not read user settings before saving.',
      })
    }
    // If file doesn't exist, allSettings remains {} which is fine
  }

  // Update the settings for the specific user
  if (Object.keys(userSettings).length > 0) {
    allSettings[userIdentifier] = userSettings
  } else {
    // If the user's settings are now empty, remove the user entry
    // eslint-disable-next-line @typescript-eslint/no-dynamic-delete
    delete allSettings[userIdentifier]
  }

  try {
    // Write the entire updated structure back to the YAML file
    const yamlContent = yaml.dump(allSettings)
    await fs.writeFile(USER_SETTINGS_PATH, yamlContent, 'utf-8')
  } catch (e: unknown) {
    const error = e as { code?: string; message?: string } // Type assertion
    console.error(
      `Error writing user settings file to ${USER_SETTINGS_PATH}:`,
      error.message || error
    )
    throw createError({
      statusCode: 500,
      statusMessage: 'Internal Server Error: Could not save user settings.',
    })
  }
}

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
  if (!userIdentifier) {
    // Handle cases where user cannot be identified based on config mode
    if (config.useRemoteAuth) {
      console.warn(
        'User Settings Save: Could not identify user with remote auth enabled.'
      )
      throw createError({
        statusCode: 401, // Unauthorized
        statusMessage: 'Unauthorized: User identification failed',
      })
    } else {
      console.warn(
        "User Settings Save: 'default' user not found in config for non-remote auth mode."
      )
      throw createError({
        statusCode: 403, // Forbidden (config issue)
        statusMessage: 'Forbidden: Default user configuration missing',
      })
    }
  }

  // --- Read Request Body ---
  const body = await readBody(event)
  if (!body || typeof body !== 'object') {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request: Invalid or missing request body.',
    })
  }

  // --- Validate expected settings (e.g., api_key for Vikunja) ---
  // This could be more sophisticated based on app type later
  if (typeof body.api_key !== 'string') {
    // Allow empty string to clear the key
    if (body.api_key !== '') {
      throw createError({
        statusCode: 400,
        statusMessage:
          'Bad Request: Missing or invalid api_key in request body.',
      })
    }
  }

  // --- Load, Update, and Save Settings using users.yml ---
  try {
    // Load settings specifically for this user
    const currentUserSettings = await loadUserSettingsForUser(userIdentifier)

    // Get the specific app's settings within the user's settings
    const appSettings = currentUserSettings[appId] || {}

    // Update the api_key for the specific app
    if (body.api_key === '') {
      delete appSettings.api_key // Remove key if value is empty string
    } else {
      appSettings.api_key = body.api_key // Set or update the key
    }

    // Update the user's settings object
    if (Object.keys(appSettings).length > 0) {
      currentUserSettings[appId] = appSettings // Put updated/new app settings back
    } else {
      // eslint-disable-next-line @typescript-eslint/no-dynamic-delete
      delete currentUserSettings[appId] // Remove app entry if it's now empty
    }

    // Save the updated settings for this user back to the main file
    await saveUserSettingsForUser(userIdentifier, currentUserSettings)

    setResponseStatus(event, 200) // OK
    return {
      success: true,
      message: `Settings for ${appId} saved successfully.`,
    }
  } catch (e: unknown) {
    const error = e as { message?: string } // Basic error structure
    // Errors during load/save are already handled and throw h3 errors
    // This catch is for unexpected issues, though load/save should cover most file-related ones.
    console.error(
      `Unexpected error saving settings for ${appId} / ${userIdentifier}:`,
      error.message || error
    )
    if (!event.res.writableEnded) {
      // Check if response hasn't already been sent by createError
      throw createError({
        statusCode: 500,
        statusMessage:
          'Internal Server Error: An unexpected error occurred while saving settings.',
      })
    }
  }
})
