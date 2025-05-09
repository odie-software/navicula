import { promises as fs } from 'fs'
import { defineEventHandler, getHeader, setResponseStatus } from 'h3'
import yaml from 'js-yaml' // Import js-yaml

// --- Interfaces matching the new config structure ---
interface AppLink {
  id: string
  title: string
  icon: string
  url: string
  toolbarColor?: string
  autoload?: boolean
}

interface NavCategory {
  id: string
  title: string
  icon: string
  apps: AppLink[]
  toolbarColor?: string
}

type NavigationItem = AppLink | NavCategory

interface Role {
  description: string
  permissions: string[]
}

interface Config {
  roles: Record<string, Role>
  acl: Record<string, string>
  navigationItems: NavigationItem[]
  defaultToolbarColor: string
  keybindings?: Record<string, string>
  useRemoteAuth?: boolean
}

// --- Type Guards ---
function isCategory(item: NavigationItem): item is NavCategory {
  return Array.isArray((item as NavCategory).apps)
}
function isAppLink(item: NavigationItem): item is AppLink {
  return typeof (item as AppLink).url === 'string'
}

const DEFAULT_ROLE = 'Guest'

export default defineEventHandler(async (event) => {
  // --- Configuration Loading ---
  // Default to config.yml, ensure path is correct for runtime context
  const configPath = process.env.APP_CONFIG_PATH || '/app/config.yml' // Use absolute path in container
  let config: Config
  try {
    const fileContent = await fs.readFile(configPath, 'utf-8')
    // Use yaml.load instead of JSON.parse
    config = yaml.load(fileContent) as Config

    // Basic validation (remains the same)
    if (
      !config ||
      typeof config !== 'object' ||
      !Array.isArray(config.navigationItems)
    ) {
      throw new Error(
        "Invalid config format: 'navigationItems' array is missing or invalid."
      )
    }
    if (!config.roles || !config.acl || !config.defaultToolbarColor) {
      console.warn(
        "Config warning: 'roles', 'acl', or 'defaultToolbarColor' might be missing."
      )
    }
  } catch (error) {
    console.error(
      `Error reading or parsing config file at ${configPath}:`,
      error
    )
    setResponseStatus(event, 500)
    return {
      error: 'Failed to load server configuration',
      userEmail: null,
      role: DEFAULT_ROLE,
      navigationItems: [],
      defaultToolbarColor: 'primary',
      keybindings: {},
    }
  }

  // --- User Identification & Role Calculation ---
  let userEmail: string | null = null
  let userRoleName: string
  let userRole: Role | undefined

  if (config.useRemoteAuth) {
    const userEmailHeader = (
      getHeader(event, 'remote-user') ||
      getHeader(event, 'x-forwarded-user') ||
      ''
    ).toLowerCase()
    userEmail = userEmailHeader || null
    userRoleName = userEmail
      ? config.acl[userEmail] || DEFAULT_ROLE
      : DEFAULT_ROLE
    userRole = config.roles[userRoleName]
  } else {
    userRoleName = config.roles['Admin'] ? 'Admin' : DEFAULT_ROLE
    userRole = config.roles[userRoleName]
    userEmail = 'localuser@navicula.local'
  }

  if (!userRole) {
    userRoleName = DEFAULT_ROLE
    userRole = config.roles[DEFAULT_ROLE]
  }

  if (!userRole) {
    console.error(
      `Default role "${DEFAULT_ROLE}" or assigned role "${userRoleName}" not found in config`
    )
    setResponseStatus(event, 500)
    return {
      error: 'Server configuration error: Role definition missing',
      userEmail,
      role: DEFAULT_ROLE,
      navigationItems: [],
      defaultToolbarColor: config.defaultToolbarColor || 'primary',
      keybindings: config.keybindings || {},
    }
  }

  const userPermissions = new Set(userRole.permissions)
  const hasWildcard = userPermissions.has('*')

  // --- Filtering Navigation Items ---
  const accessibleNavigationItems: NavigationItem[] = []

  if (config.navigationItems) {
    config.navigationItems.forEach((item) => {
      if (isAppLink(item)) {
        if (hasWildcard || userPermissions.has(item.id)) {
          accessibleNavigationItems.push(item)
        }
      } else if (isCategory(item)) {
        const canAccessCategory = hasWildcard || userPermissions.has(item.id)
        const accessibleApps = item.apps.filter(
          (app) =>
            hasWildcard || userPermissions.has(app.id) || canAccessCategory
        )

        if (accessibleApps.length > 0) {
          accessibleNavigationItems.push({
            ...item,
            apps: accessibleApps,
          })
        }
      }
    })
  }

  // --- Return Response ---
  return {
    userEmail: userEmail,
    role: userRoleName,
    navigationItems: accessibleNavigationItems,
    defaultToolbarColor: config.defaultToolbarColor || 'primary',
    keybindings: config.keybindings || {},
  }
})
