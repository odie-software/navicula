// --- Interfaces matching the config structure ---
interface AppLink {
  id: string
  title: string
  icon: string
  url: string
  type?: string // Optional type for service integrations
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

// Defines the structure for a user entry in the config
interface UserConfig {
  role: string
  // app_settings?: Record<string, Record<string, any>>; // Structure for user-specific settings (handled separately)
}

interface Config {
  roles: Record<string, Role>
  users: Record<string, UserConfig> // Replaces acl
  navigationItems: NavigationItem[]
  defaultToolbarColor: string
  keybindings?: Record<string, string>
  useRemoteAuth?: boolean
}

// --- User Settings Structure
interface UserAppSettings {
  [appId: string]: Record<string, unknown>
}

// Represents the overall structure of the users.yml file
interface AllUserSettings {
  [userIdentifier: string]: UserAppSettings
}
