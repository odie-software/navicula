<template>
  <q-layout view="lHh Lpr lFf">
    <q-drawer
      v-model="leftDrawerOpen"
      :mini="isMini"
      bordered
      behavior="desktop"
      @mouseover="handleMouseOver"
      @mouseout="handleMouseOut"
    >
      <q-scrollable-area
        v-if="!pending && navigationItems.length > 0"
        class="q-p"
      >
        <q-list v-if="!pending && navigationItems.length > 0" class="q-pa-0">
          <template v-for="item in navigationItems" :key="item.id">
            <!-- App Link Item -->
            <q-item
              v-if="isAppLink(item)"
              clickable
              :active="activeAppId === item.id && loadedAppIds.length === 1"
              active-class="active-item"
              class="nav-item"
              @click="selectItem(item)"
              @mouseover="hoveredItemId = item.id"
              @mouseleave="hoveredItemId = null"
            >
              <q-item-section avatar>
                <q-icon :name="item.icon" size="sm" />
              </q-item-section>
              <q-item-section>
                <q-item-label class="row items-center no-wrap">
                  <span class="ellipsis q-mini-drawer-hide">{{
                    item.title
                  }}</span>
                  <!-- Notification Badge - Ensure count is number > 0 -->

                  <q-btn
                    v-if="item.type"
                    flat
                    dense
                    round
                    icon="settings"
                    size="xs"
                    class="q-ml-xs"
                    @click.stop="openSettingsDialog(item)"
                  >
                    <q-tooltip anchor="center right" self="center left"
                      >Configure {{ item.title }}</q-tooltip
                    >
                  </q-btn>
                  <q-chip
                    v-if="Number(notificationCounts[item.id]) > 0"
                    color="red"
                    floating
                    rounded
                    class="q-ml-sm"
                    :label="notificationCounts[item.id] as number"
                  />
                </q-item-label>
              </q-item-section>
              <!-- Add/Settings Buttons Container -->
              <q-item-section
                side
                top
                class="q-mini-drawer-hide split-button-container"
              >
                <q-btn
                  v-show="
                    hoveredItemId === item.id &&
                    !loadedAppIds.includes(item.id) &&
                    loadedAppIds.length > 0
                  "
                  flat
                  dense
                  round
                  icon="add_box"
                  size="md"
                  @click.stop="addWindow(item)"
                >
                  <q-tooltip anchor="center right" self="center left"
                    >Add to view</q-tooltip
                  >
                </q-btn>
              </q-item-section>
            </q-item>

            <!-- Category Item -->
            <q-expansion-item
              v-else-if="isCategory(item) && item.apps.length > 0"
              expand-separator
              default-opened
              class="nav-item"
            >
              <template #header>
                <q-item-section avatar>
                  <q-icon :name="item.icon" size="sm" />
                </q-item-section>
                <q-item-section class="q-mini-drawer-hide">
                  <q-item-label>{{ item.title }}</q-item-label>
                </q-item-section>
              </template>

              <q-list dense class="q-pl-lg">
                <q-item
                  v-for="app in item.apps"
                  :key="app.id"
                  clickable
                  :active="activeAppId === app.id && loadedAppIds.length === 1"
                  active-class="active-item"
                  dense
                  class="nav-item"
                  @click="selectItem(app)"
                  @mouseover="hoveredItemId = app.id"
                  @mouseleave="hoveredItemId = null"
                >
                  <q-item-section avatar>
                    <q-icon :name="app.icon" size="xs" />
                  </q-item-section>
                  <q-item-section>
                    <q-item-label class="text-body2 row items-center no-wrap">
                      <span class="ellipsis q-mini-drawer-hide">{{
                        app.title
                      }}</span>
                      <!-- Notification Badge (Nested) - Ensure count is number > 0 -->
                      <q-badge
                        v-if="Number(notificationCounts[app.id]) > 0"
                        color="red"
                        floating
                        rounded
                        class="q-ml-sm"
                        :label="notificationCounts[app.id] as number"
                        style="margin-bottom: 2px"
                      />
                      <!-- Settings Button (Nested) -->
                      <q-btn
                        v-if="app.type"
                        flat
                        dense
                        round
                        icon="settings"
                        size="xs"
                        class="q-ml-xs"
                        @click.stop="openSettingsDialog(app)"
                      >
                        <q-tooltip anchor="center right" self="center left"
                          >Configure {{ app.title }}</q-tooltip
                        >
                      </q-btn>
                    </q-item-label>
                  </q-item-section>
                  <!-- Add Button Container (Nested) -->
                  <q-item-section
                    side
                    top
                    class="q-mini-drawer-hide split-button-container"
                  >
                    <q-btn
                      v-show="
                        hoveredItemId === app.id &&
                        !loadedAppIds.includes(app.id) &&
                        loadedAppIds.length > 0
                      "
                      flat
                      dense
                      round
                      icon="add_box"
                      size="xs"
                      @click.stop="addWindow(app)"
                    >
                      <q-tooltip anchor="center right" self="center left"
                        >Add to view</q-tooltip
                      >
                    </q-btn>
                  </q-item-section>
                </q-item>
              </q-list>
            </q-expansion-item>
          </template>
        </q-list>
      </q-scrollable-area>
      <!-- Loading/Error/Empty states -->
      <q-item v-else-if="pending">
        <q-item-section class="absolute-center">
          <q-spinner color="primary" size="3em" />
          <div class="q-mt-md text-center q-mini-drawer-hide">Loading...</div>
        </q-item-section>
      </q-item>
      <q-item v-else-if="error">
        <q-item-section class="text-negative q-pa-md q-mini-drawer-hide"
          >Error loading configuration.</q-item-section
        >
      </q-item>
      <q-item v-else>
        <q-item-section class="q-pa-md q-mini-drawer-hide"
          >No navigation items found.</q-item-section
        >
      </q-item>

      <div style="flex-grow: 1" />

      <!-- User Info -->
      <q-item v-if="userInfo.userEmail" class="q-mini-drawer-hide" dense>
        <q-item-section avatar>
          <q-icon name="person" size="sm" />
        </q-item-section>
        <q-item-section>
          <q-item-label class="text-caption ellipsis">{{
            userInfo.userEmail
          }}</q-item-label>
          <q-item-label caption>Role: {{ userInfo.role }}</q-item-label>
        </q-item-section>
      </q-item>

      <!-- Dark Mode Toggle -->
      <q-item clickable dense @click="$q.dark.toggle()">
        <q-item-section avatar>
          <q-icon
            :name="$q.dark.isActive ? 'dark_mode' : 'light_mode'"
            size="sm"
          />
        </q-item-section>
        <q-item-section class="q-mini-drawer-hide">
          <q-item-label>Dark Mode</q-item-label>
        </q-item-section>
      </q-item>

      <!-- Drawer Mode Toggle -->
      <q-item clickable dense @click="toggleDrawerMode">
        <q-item-section avatar>
          <q-icon
            :name="
              drawerMode === 'always-open'
                ? 'keyboard_arrow_left'
                : 'keyboard_arrow_right'
            "
            size="sm"
          />
        </q-item-section>
        <q-item-section class="q-mini-drawer-hide">
          <q-item-label>{{
            drawerMode === 'always-open' ? 'Auto Hide' : 'Keep Open'
          }}</q-item-label>
        </q-item-section>
        <q-tooltip anchor="center right" self="center left">{{
          drawerMode === 'always-open'
            ? 'Switch to auto-hide mode'
            : 'Keep drawer always open'
        }}</q-tooltip>
      </q-item>

      <!-- Version Display -->
      <div
        class="absolute-bottom q-pa-sm text-center text-caption text-grey-7 q-mini-drawer-hide"
      >
        Version: {{ appVersion }}
      </div>
    </q-drawer>

    <q-page-container>
      <q-page class="page-flex-container">
        <!-- Use ViewSplitter to manage AppWindows -->
        <view-splitter v-show="loadedAppIds.length > 0" style="flex-grow: 1">
          <AppWindow
            v-for="appId in activeAppIds"
            v-show="loadedAppIds.includes(appId)"
            :ref="
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              (el: ComponentPublicInstance | Element | null) => {
                // Ensure refs are correctly assigned/removed
                if (el && '$props' in el && 'appLink' in el.$props) {
                  // Check if el is a component instance with expected props
                  appWindowRefs[appId] = el as InstanceType<typeof AppWindow>
                } else if (!el) {
                  // Handle element being detached
                  // eslint-disable-next-line @typescript-eslint/no-dynamic-delete
                  delete appWindowRefs[appId]
                }
              }
            "
            :key="appId"
            :app-link="getAppLinkById(appId)!"
            :is-active="activeAppId === appId"
            :is-same-origin="isAppLinkSameOrigin(getAppLinkById(appId))"
            :default-toolbar-color="defaultToolbarColor"
            :show-swap-button="loadedAppIds.length > 1 && activeAppId === appId"
            @activate-window="activateWindow(appId)"
            @close-window="closeWindow(appId)"
            @copy-iframe-url="copyIframeUrl(appId)"
            @reload-iframe="reloadIframe(appId)"
            @swap-window="swapWindows"
          />
        </view-splitter>

        <!-- Placeholder when no apps are displayed -->
        <div
          v-show="loadedAppIds.length === 0 && !pending"
          class="flex flex-center text-h6 text-grey-7"
          style="height: 100%"
        >
          {{
            navigationItems.length > 0
              ? 'Select an item from the menu'
              : 'No items configured'
          }}
        </div>
        <div v-if="pending" class="flex flex-center" style="height: 100%">
          <q-spinner color="primary" size="xl" />
        </div>
      </q-page>
    </q-page-container>

    <!-- App Settings Dialog -->
    <app-settings-dialog
      v-model="showSettingsDialog"
      :app-link="configuringApp"
      @settings-saved="handleSettingsSaved"
    />
  </q-layout>
</template>

<script lang="ts" setup>
import {
  ref,
  watch,
  computed,
  onMounted,
  onUnmounted,
  type Ref,
  type ComponentPublicInstance,
} from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  useQuasar,
  QSpinner,
  QLayout,
  QDrawer,
  QList,
  QItem,
  QItemSection,
  QIcon,
  QItemLabel,
  QBtn,
  QTooltip,
  QExpansionItem,
  QPageContainer,
  QPage,
  QBadge, // Added QBadge import
} from 'quasar'
import AppWindow from '../components/AppWindow.vue'
import ViewSplitter from '../components/ViewSplitter.vue'
import AppSettingsDialog from '../components/AppSettingsDialog.vue' // Import the dialog

/**
 * Represents a direct link to an application within the navigation.
 * @interface AppLink
 */
interface AppLink {
  /** Unique identifier for the app link. */
  id: string
  /** Display title for the app link. */
  title: string
  /** Material icon name for the app link. */
  icon: string
  /** URL the app link points to. */
  url: string
  /** Optional color for the AppWindow toolbar. */
  toolbarColor?: string
  /** If true, this app should be loaded automatically on startup if no other apps are specified in the URL. */
  autoload?: boolean
  /** Optional type identifier for service integrations (e.g., 'vikunja'). */
  type?: string // NEW: Add type field
  /** Ensures AppLink doesn't have an 'apps' property. */
  apps?: never
}

/**
 * Represents a category containing multiple AppLinks in the navigation.
 * @interface NavCategory
 */
interface NavCategory {
  /** Unique identifier for the category. */
  id: string
  /** Display title for the category. */
  title: string
  /** Material icon name for the category. */
  icon: string
  /** Array of AppLinks within this category. */
  apps: AppLink[]
  /** Ensures NavCategory doesn't have a 'toolbarColor' property directly. */
  toolbarColor?: string
  /** Ensures NavCategory doesn't have a 'url' property. */
  url?: never
}

/**
 * Union type representing either an AppLink or a NavCategory.
 * @typedef {AppLink | NavCategory} NavigationItem
 */
type NavigationItem = AppLink | NavCategory

/**
 * Defines the behavior modes for the navigation drawer.
 * 'auto-hide': Drawer minimizes and expands on hover.
 * 'always-open': Drawer stays fully open.
 * @typedef {'auto-hide' | 'always-open'} DrawerMode
 */
type DrawerMode = 'auto-hide' | 'always-open'

/**
 * Holds information about the current user.
 * @interface UserInfo
 */
interface UserInfo {
  /** The email address of the logged-in user, or null if anonymous. */
  userEmail: string | null
  /** The role assigned to the user. */
  role: string
}

/**
 * Structure of the response expected from the `/api/config` endpoint.
 * @interface ConfigResponse
 */
interface ConfigResponse {
  /** The email address of the logged-in user, or null. */
  userEmail: string | null
  /** The role assigned to the user. */
  role: string
  /** Array of navigation items (AppLink or NavCategory). */
  navigationItems: NavigationItem[]
  /** Default color for AppWindow toolbars if not specified per app. */
  defaultToolbarColor: string
  /** Optional keybindings configuration. Maps key combinations (e.g., "Ctrl+Alt+K") to AppLink IDs. */
  keybindings?: Record<string, string>
  /** Optional error message if configuration loading failed. */
  error?: string
}

// Structure for the notification count response
interface NotificationCountResponse {
  count: number | null
  error?: string // Optional error indicator (e.g., 'unauthorized', 'timeout', 'fetch_failed')
}

// --- Composables ---
const $q = useQuasar()
const route = useRoute()
const router = useRouter()
const config = useRuntimeConfig()

// --- State Refs ---

/** Controls the visibility (open/closed) of the left navigation drawer. */
const leftDrawerOpen: Ref<boolean> = ref(true)
/** Current behavior mode of the drawer ('auto-hide' or 'always-open'). */
const drawerMode: Ref<DrawerMode> = ref('auto-hide')
/** Controls the mini-mode state of the drawer (true = minimized). This is the direct source for the :mini prop. */
const isMini: Ref<boolean> = ref(true)
/** ID of the currently active AppWindow, or null if none is active. */
const activeAppId: Ref<string | null> = ref(null)
/** Array of AppLink IDs currently active in AppWindows. */
const activeAppIds: Ref<string[]> = ref([])
/** Array of AppLink IDs currently displayed in AppWindows. */
const loadedAppIds: Ref<string[]> = ref([])
/** ID of the previously active AppWindow, used for Alt+Tab switching. */
const previousActiveAppId: Ref<string | null> = ref(null)
/** Array of navigation items fetched from the config API. */
const navigationItems: Ref<NavigationItem[]> = ref([])
/** User information fetched from the config API. */
const userInfo: Ref<UserInfo> = ref({ userEmail: null, role: 'Guest' })
/** Default color for AppWindow toolbars. */
const defaultToolbarColor: Ref<string> = ref('primary')
/** References to the AppWindow component instances, keyed by AppLink ID. */
const appWindowRefs: Ref<Record<string, InstanceType<typeof AppWindow>>> = ref(
  {}
)
/** Keybinding configuration fetched from the API. */
const keybindingsConfig: Ref<Record<string, string>> = ref({})
/** ID of the navigation item currently being hovered over. */
const hoveredItemId: Ref<string | null> = ref(null)
/** Application version from runtime config. */
const appVersion: string = config.public.appVersion
/** Stores notification counts keyed by AppLink ID. */
const notificationCounts: Ref<Record<string, number | null>> = ref({})
/** Controls the visibility of the App Settings Dialog. */
const showSettingsDialog: Ref<boolean> = ref(false)
/** Holds the AppLink object for the app currently being configured. */
const configuringApp: Ref<AppLink | null> = ref(null)

// --- API Fetch ---

/**
 * Fetches the application configuration from the `/api/config` endpoint.
 * Provides reactive `data`, `pending`, and `error` states.
 */
const runtimeConf = useRuntimeConfig() // Renamed to avoid conflict with 'config' from useRuntimeConfig()
const apiBaseUrl = runtimeConf.public.apiBaseUrl
const configApiUrl = `${apiBaseUrl}/config/configuration/`

const {
  data: configData,
  pending,
  error,
} = useFetch<ConfigResponse>(configApiUrl)

// --- Computed Properties ---

/**
 * Computes a flat array of all AppLinks available in the navigation,
 * extracting them from both top-level items and categories.
 * @returns {AppLink[]} A flat array of all AppLinks.
 */
const allAppLinks = computed((): AppLink[] => {
  const links: AppLink[] = []
  ;(navigationItems.value || []).forEach((item) => {
    if (isAppLink(item)) {
      links.push(item)
    } else if (isCategory(item)) {
      links.push(...item.apps)
    }
  })
  return links
})

/**
 * Computes a flat array of all AppLinks, maintaining the order they appear
 * in the navigation menu (top-level and within categories).
 * Used for sequential keyboard navigation (Alt+Up/Down).
 * @returns {AppLink[]} A flat array of AppLinks in menu order.
 */
const flatAppLinks = computed((): AppLink[] => {
  const flatList: AppLink[] = []
  ;(navigationItems.value || []).forEach((item) => {
    if (isAppLink(item)) {
      flatList.push(item)
    } else if (isCategory(item)) {
      flatList.push(...item.apps)
    }
  })
  return flatList
})

// --- API Call Functions ---

/**
 * Fetches the notification count for a specific app ID.
 * Updates the `notificationCounts` ref.
 * @param {string} appId - The ID of the AppLink to fetch notifications for.
 */
async function fetchNotificationCount(appId: string): Promise<void> {
  try {
    // apiBaseUrl is already defined from the previous change
    const notificationApiUrl = `/api/notifications/${appId}/`
    const response = await $fetch<NotificationCountResponse>(
      notificationApiUrl,
      {
        method: 'GET',
      }
    )
    notificationCounts.value[appId] = response.count
    if (response.error) {
      console.warn(
        `Notification fetch for ${appId} completed with error: ${response.error}`
      )
      // Optionally show a subtle indicator in UI if count is null due to error
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  } catch (err: any) {
    // Changed from error: any
    console.error(`Failed to fetch notification count for ${appId}:`, err)
    notificationCounts.value[appId] = null // Set to null on error
    // Avoid noisy notifications for background fetches, log is sufficient
  }
}

/**
 * Iterates through all known AppLinks and fetches notification counts
 * for those that have a defined `type`.
 */
async function fetchAllNotifications(): Promise<void> {
  console.log('Fetching all notifications for supported apps...')
  const promises: Promise<void>[] = []
  allAppLinks.value.forEach((app) => {
    // Only fetch for apps that have a type defined (indicating potential integration)
    if (app.type) {
      // For now, we only explicitly support 'vikunja', but fetch for any type defined
      // In the future, might check against a list of supported types.
      console.log(
        `Queueing notification fetch for ${app.id} (type: ${app.type})`
      )
      promises.push(fetchNotificationCount(app.id))
    }
  })
  await Promise.allSettled(promises) // Wait for all fetches to complete or fail
  console.log('Finished fetching notifications.', notificationCounts.value)
}

// --- Type Guards ---

/**
 * Type guard to check if a NavigationItem is a NavCategory.
 * @param {NavigationItem} item - The item to check.
 * @returns {boolean} True if the item is a NavCategory, false otherwise.
 */
function isCategory(item: NavigationItem): item is NavCategory {
  return Array.isArray((item as NavCategory).apps)
}

/**
 * Type guard to check if a NavigationItem is an AppLink.
 * @param {NavigationItem} item - The item to check.
 * @returns {boolean} True if the item is an AppLink, false otherwise.
 */
function isAppLink(item: NavigationItem): item is AppLink {
  return typeof (item as AppLink).url === 'string'
}

// --- Methods ---

/**
 * Opens the settings dialog for the specified app.
 * @param {AppLink} app - The application link to configure.
 */
function openSettingsDialog(app: AppLink): void {
  configuringApp.value = app
  showSettingsDialog.value = true
}

/**
 * Handles the event emitted when settings are saved in the dialog.
 * Refetches the notification count for the affected app.
 * @param {string} appId - The ID of the app whose settings were saved.
 */
function handleSettingsSaved(appId: string): void {
  console.log(`Settings saved for ${appId}, refetching notifications...`)
  fetchNotificationCount(appId) // Refetch count after saving API key
}

/**
 * Toggles the drawer mode between 'auto-hide' and 'always-open'.
 * Adjusts the miniState accordingly.
 */
function toggleDrawerMode(): void {
  if (drawerMode.value === 'auto-hide') {
    drawerMode.value = 'always-open'
    isMini.value = false // Keep drawer open
  } else {
    // 'always-open'
    drawerMode.value = 'auto-hide'
    isMini.value = true // Switch to mini, will expand on hover
  }
}

/**
 * Handles the mouseover event on the drawer.
 * Expands the drawer if it's in 'auto-hide' mode.
 */
function handleMouseOver(): void {
  if (drawerMode.value === 'auto-hide') {
    isMini.value = false
  }
}

/**
 * Handles the mouseout event on the drawer.
 * Minimizes the drawer if it's in 'auto-hide' mode.
 */
function handleMouseOut(): void {
  if (drawerMode.value === 'auto-hide') {
    isMini.value = true
  }
}

/**
 * Selects a navigation item (AppLink).
 * If the item is already displayed, it activates its window.
 * If not displayed, it replaces the currently active window with the selected item's window.
 * If no window is active/displayed, it adds the item as the first window.
 * Updates the URL query parameters.
 * @param {AppLink | null} item - The AppLink item to select, or null to deactivate all.
 */
function selectItem(item: AppLink | null): void {
  if (!item) {
    activateWindow(null)
    return
  }

  if (loadedAppIds.value.includes(item.id)) {
    activateWindow(item.id)
  } else {
    const activeIndex = activeAppId.value
      ? loadedAppIds.value.indexOf(activeAppId.value)
      : -1
    if (activeIndex !== -1 && loadedAppIds.value.length > 0) {
      loadedAppIds.value.splice(activeIndex, 1, item.id)
    } else {
      loadedAppIds.value = [item.id]
    }
    activateWindow(item.id)
  }
  updateQueryParam()
}

/**
 * Adds an AppLink's window to the display area.
 * If two windows are already displayed, the first one is replaced.
 * If the window is already displayed, it's just activated.
 * Updates the URL query parameters.
 * @param {AppLink} itemToAdd - The AppLink whose window should be added.
 */
function addWindow(itemToAdd: AppLink): void {
  if (!loadedAppIds.value.includes(itemToAdd.id)) {
    loadedAppIds.value.push(itemToAdd.id)
  }

  if (!activeAppIds.value.includes(itemToAdd.id)) {
    activeAppIds.value.push(itemToAdd.id)
  }
  updateQueryParam()
}

/**
 * Closes the AppWindow associated with the given AppLink ID.
 * Removes the ID from `loadedAppIds` and cleans up the corresponding ref.
 * Activates the previously active window or the remaining window if necessary.
 * Updates the URL query parameters.
 * @param {string} appIdToClose - The ID of the AppLink whose window should be closed.
 */
function closeWindow(appIdToClose: string): void {
  // Remove from `activeAppIds` if present
  const activeIndex = activeAppIds.value.indexOf(appIdToClose)
  if (activeIndex > -1) {
    activeAppIds.value.splice(activeIndex, 1)
  }

  const index = loadedAppIds.value.indexOf(appIdToClose)

  if (index > -1) {
    loadedAppIds.value.splice(index, 1)
    // eslint-disable-next-line @typescript-eslint/no-dynamic-delete
    delete appWindowRefs.value[appIdToClose]

    if (activeAppId.value === appIdToClose) {
      const newActiveId =
        previousActiveAppId.value &&
        loadedAppIds.value.includes(previousActiveAppId.value)
          ? previousActiveAppId.value
          : (loadedAppIds.value[0] ?? null)
      activateWindow(newActiveId)
    }
    if (previousActiveAppId.value === appIdToClose) {
      previousActiveAppId.value = null
    }
    updateQueryParam()
  }
}

/**
 * Sets the active AppWindow.
 * Updates `activeAppId` and `previousActiveAppId`.
 * Ensures the activated window is added to `loadedAppIds` if not already present.
 * Updates the URL query parameters.
 * @param {string | null} appId - The ID of the AppLink to activate, or null to deactivate.
 */
function activateWindow(appId: string | null): void {
  activeAppIds.value = appId ? [appId] : []

  // Update URL regardless of activation/deactivation
  updateQueryParam()
}

/**
 * Updates the URL query parameters (`apps` and `active`) based on the current state.
 * Uses `router.replace` to avoid adding history entries.
 */
function updateQueryParam(): void {
  const query: Record<string, string | string[]> = {}
  console.log(activeAppIds.value)
  if (activeAppIds.value.length > 0) {
    query.apps = activeAppIds.value.join(',')
  }
  // No need to explicitly delete 'active' if null, router.replace handles it.
  router.replace({ query }).catch((err) => {
    if (
      err.name !== 'NavigationDuplicated' &&
      err.name !== 'NavigationCancelled'
    ) {
      console.error('Router replace error:', err)
    }
  })
}

/**
 * Swaps the positions of the two displayed AppWindows in split view.
 * Updates the `loadedAppIds` order and the URL query parameters.
 * Note: This currently only swaps the first two if more than two are displayed.
 */
function swapWindows(): void {
  if (loadedAppIds.value.length >= 2) {
    // Simple swap of the first two elements
    const temp = loadedAppIds.value[0]
    loadedAppIds.value[0] = loadedAppIds.value[1]
    loadedAppIds.value[1] = temp
    // The watcher on loadedAppIds or updateQueryParam call will handle reactivity
    updateQueryParam() // Ensure URL reflects the new order
  }
}

/**
 * Reloads the iframe content of the specified AppWindow.
 * Attempts to use the `contentWindow.location.reload()` method.
 * Shows a notification about the reload attempt.
 * @param {string} appId - The ID of the AppLink whose iframe should be reloaded.
 */
function reloadIframe(appId: string): void {
  const targetWindow = appWindowRefs.value[appId]
  const iframe = targetWindow?.iframeElement
  const app = allAppLinks.value.find((a) => a.id === appId)
  if (iframe?.contentWindow) {
    try {
      iframe.contentWindow.location.reload()
      $q.notify({ type: 'info', message: `Reloading ${app?.title}...` })
    } catch (e) {
      console.error(`Error reloading iframe for ${app?.title}:`, e)
      $q.notify({
        type: 'warning',
        message: `Could not reload ${app?.title} (cross-origin?).`,
      })
    }
  } else {
    $q.notify({
      type: 'warning',
      message: `Could not find iframe to reload ${app?.title}.`,
    })
  }
}

/**
 * Copies the current URL of the specified AppWindow's iframe to the clipboard.
 * Only works for same-origin iframes. Shows notifications on success or failure.
 * @param {string} appId - The ID of the AppLink whose iframe URL should be copied.
 */
async function copyIframeUrl(appId: string): Promise<void> {
  const targetWindow = appWindowRefs.value[appId]
  const iframe = targetWindow?.iframeElement
  const appLink = allAppLinks.value.find((a) => a.id === appId)

  if (!iframe?.contentWindow || !isAppLinkSameOrigin(appLink)) {
    $q.notify({
      type: 'negative',
      message: 'Cannot access iframe URL (cross-origin or not loaded).',
    })
    return
  }
  try {
    const currentIframeUrl = iframe.contentWindow.location.href
    await navigator.clipboard.writeText(currentIframeUrl)
    $q.notify({ type: 'positive', message: 'Current iframe URL copied!' })
  } catch (err) {
    console.error('Failed to copy iframe URL:', err)
    let message = 'Failed to copy URL.'
    if (err instanceof DOMException && err.name === 'SecurityError') {
      message = 'Failed to copy URL due to security restrictions.'
    } else if (err instanceof Error) {
      message = `Failed to copy URL: ${err.message}`
    }
    $q.notify({ type: 'negative', message: message })
  }
}

/**
 * Retrieves the AppLink object corresponding to the given ID.
 * @param {string} id - The ID of the AppLink to find.
 * @returns {AppLink | undefined} The found AppLink object, or undefined if not found.
 */
function getAppLinkById(id: string): AppLink | undefined {
  return allAppLinks.value.find((app) => app.id === id)
}

/**
 * Checks if the URL of an AppLink is considered same-origin relative to the main window.
 * Handles relative URLs, absolute URLs, and potential errors during URL parsing.
 * @param {AppLink | null | undefined} appLink - The AppLink to check.
 * @returns {boolean} True if the URL is same-origin or relative, false otherwise.
 */
function isAppLinkSameOrigin(appLink: AppLink | null | undefined): boolean {
  const url = appLink?.url
  if (!url) return false
  // Assume relative paths are same-origin
  if (!url.startsWith('http://') && !url.startsWith('https://')) return true
  try {
    // Compare origins for absolute URLs
    return new URL(url).origin === window.location.origin
  } catch {
    // Invalid URL format
    return false
  }
}

// --- Keybinding Logic ---

/**
 * Handles global keydown events for application shortcuts.
 * - Alt+Tab: Cycle focus between displayed windows.
 * - Alt+Up/Down: Select previous/next item in the navigation list.
 * - Custom keybindings (from config): Select the associated AppLink.
 * @param {KeyboardEvent} event - The keydown event object.
 */
function handleKeydown(event: KeyboardEvent): void {
  // Alt+Tab: Cycle through displayed windows
  if (event.altKey && event.key === 'Tab') {
    event.preventDefault()
    if (loadedAppIds.value.length > 1 && activeAppId.value) {
      const currentIndex = loadedAppIds.value.indexOf(activeAppId.value)
      const nextIndex = (currentIndex + 1) % loadedAppIds.value.length
      activateWindow(loadedAppIds.value[nextIndex])
    } else if (
      previousActiveAppId.value &&
      loadedAppIds.value.includes(previousActiveAppId.value)
    ) {
      // Switch back to previous if only one or none active
      activateWindow(previousActiveAppId.value)
    }
    return
  }

  // Alt+ArrowUp/Down: Navigate through flat list of apps
  if (event.altKey && (event.key === 'ArrowUp' || event.key === 'ArrowDown')) {
    event.preventDefault()
    const links = flatAppLinks.value
    if (!links.length) return

    const currentActiveIndex = activeAppId.value
      ? links.findIndex((link) => link.id === activeAppId.value)
      : -1
    let nextIndex = -1

    if (event.key === 'ArrowDown') {
      nextIndex =
        currentActiveIndex === -1 || currentActiveIndex >= links.length - 1
          ? 0 // Wrap to start
          : currentActiveIndex + 1
    } else {
      // ArrowUp
      nextIndex =
        currentActiveIndex === -1 || currentActiveIndex <= 0
          ? links.length - 1 // Wrap to end
          : currentActiveIndex - 1
    }

    if (nextIndex !== -1 && links[nextIndex]) {
      selectItem(links[nextIndex])
    }
    return
  }

  // Custom Keybindings
  const keyString = buildKeyString(event)
  const targetAppId = keybindingsConfig.value[keyString]
  if (targetAppId) {
    event.preventDefault()
    const targetApp = allAppLinks.value.find((app) => app.id === targetAppId)
    if (targetApp) {
      selectItem(targetApp)
    } else {
      console.warn(
        `Keybinding "${keyString}" targets unknown app ID "${targetAppId}"`
      )
    }
  }
}

/**
 * Constructs a string representation of a key combination from a KeyboardEvent.
 * Used for matching against the `keybindingsConfig`.
 * Example: "Ctrl+Alt+K", "Shift+F1", "A"
 * @param {KeyboardEvent} event - The keyboard event.
 * @returns {string} The formatted key string, or an empty string if only modifiers were pressed.
 */
function buildKeyString(event: KeyboardEvent): string {
  const parts: string[] = []
  if (event.ctrlKey) parts.push('Ctrl')
  if (event.altKey) parts.push('Alt')
  if (event.shiftKey) parts.push('Shift')
  if (event.metaKey) parts.push('Meta') // Cmd on Mac, Win key on Windows

  let key = event.key
  // Ignore events that are just modifier keys
  if (['Control', 'Shift', 'Alt', 'Meta'].includes(key)) return ''

  // Normalize single character keys to uppercase for consistency
  if (key.length === 1 && key !== key.toLowerCase()) {
    // Check if it's a letter
    key = key.toUpperCase()
  }
  // Handle special keys like 'ArrowUp', 'Enter', 'Tab', 'F1', etc.
  // No extra normalization needed for these as `event.key` provides standard names.

  parts.push(key)
  return parts.join('+')
}

// --- Watchers ---

/**
 * Watches the `configData` fetched from the API.
 * When new config arrives, it updates the component's state:
 * - Populates `navigationItems`, `userInfo`, `defaultToolbarColor`, `keybindingsConfig`.
 * - Determines the initial `loadedAppIds` and `activeAppId` based on:
 *   1. Valid `apps` and `active` query parameters from the URL.
 *   2. The first `autoload` app specified in the config.
 *   3. The very first available AppLink in the config.
 * - Updates the URL query parameters if the initial state differs from the URL.
 * - Handles potential errors during config loading.
 */
watch(
  configData,
  (newConfig) => {
    if (
      newConfig &&
      !newConfig.error &&
      Array.isArray(newConfig.navigationItems)
    ) {
      // Update core state from config
      navigationItems.value = newConfig.navigationItems
      // Assign properties individually with explicit cast for userEmail
      userInfo.value.userEmail = newConfig.userEmail as string | null // Explicit cast
      userInfo.value.role =
        typeof newConfig.role === 'string' ? newConfig.role : 'Guest'
      defaultToolbarColor.value = newConfig.defaultToolbarColor || 'primary'
      keybindingsConfig.value = newConfig.keybindings || {}

      // Find autoload apps
      const autoLoadIds = new Set<string>()
      allAppLinks.value.forEach((app) => {
        if (app.autoload) {
          autoLoadIds.add(app.id)
        }
      })

      // Get initial state from URL query parameters
      const appsQuery = route.query.apps as string | undefined
      const appsFromQuery = appsQuery ? appsQuery.split(',') : []

      // Validate query parameters against available apps
      const validAppIdsFromQuery = appsFromQuery.filter((id) =>
        allAppLinks.value.some((app) => app.id === id)
      )

      // Determine initial state: Query > Autoload > First App
      let initialDisplayedIds: string[] = []

      if (validAppIdsFromQuery.length > 0) {
        initialDisplayedIds = validAppIdsFromQuery
      } else if (autoLoadIds.size > 0) {
        const firstAutoload = Array.from(autoLoadIds)[0]
        initialDisplayedIds = [firstAutoload]
      } else if (flatAppLinks.value.length > 0) {
        initialDisplayedIds = [flatAppLinks.value[0].id]
      }

      // Apply initial state
      loadedAppIds.value = initialDisplayedIds
      activeAppIds.value = initialDisplayedIds

      // Ensure URL reflects the final initial state
      updateQueryParam()

      // --- Fetch notifications AFTER config is loaded and processed ---
      fetchAllNotifications() // Fetch counts for Vikunja etc.
    } else {
      // Handle config loading error
      console.error(
        'Failed to load or parse configuration:',
        newConfig?.error || error.value || 'Invalid config format'
      )
      navigationItems.value = []
      activeAppId.value = null
      loadedAppIds.value = []
      userInfo.value = { userEmail: null, role: 'Error' }
      keybindingsConfig.value = {}
      updateQueryParam() // Clear query params on error
    }
  },
  { immediate: true } // Run watcher immediately on component mount
)

/**
 * Watches the route query parameters (`apps` and `active`).
 * Updates the component state (`loadedAppIds`, `activeAppId`) if the query changes,
 * ensuring the UI stays synchronized with the URL (e.g., browser back/forward).
 */
watch(
  () => route.query,
  (newQuery) => {
    // Avoid reacting to updates triggered by updateQueryParam itself if config isn't loaded yet
    if (pending.value || !configData.value) return

    const appsQuery = newQuery.apps as string | undefined
    const appsFromQuery = appsQuery ? appsQuery.split(',') : []
    const activeFromQuery = newQuery.active as string | undefined

    // Validate query parameters against available apps
    const validAppIdsFromQuery = appsFromQuery.filter((id) =>
      allAppLinks.value.some((app) => app.id === id)
    )

    const validActiveIdFromQuery = validAppIdsFromQuery.includes(
      activeFromQuery ?? ''
    )
      ? (activeFromQuery ?? null) // Ensure undefined becomes null
      : null

    // Check if the displayed apps in the state differ from the valid query apps
    const stateAppsString = loadedAppIds.value.join(',')
    const queryAppsString = validAppIdsFromQuery.join(',')

    if (stateAppsString !== queryAppsString) {
      loadedAppIds.value = validAppIdsFromQuery
      // If displayed apps change, the active app might need recalculation
      const newActive = validActiveIdFromQuery || loadedAppIds.value[0] || null
      if (activeAppId.value !== newActive) {
        activateWindow(newActive) // Use activateWindow to handle previousActiveAppId correctly
      }
    } else if (activeAppId.value !== validActiveIdFromQuery) {
      // Only update active ID if displayed apps are the same but active differs
      activateWindow(validActiveIdFromQuery)
    }

    // If the state was changed *by the query watcher*, we don't need to call updateQueryParam again.
    // This check helps prevent potential infinite loops if router.replace triggers the watcher immediately.
    // Note: This relies on the assumption that updateQueryParam normalizes the query,
    // so if the watcher is triggered by an external change (back/forward button),
    // and the state *already* matches the new query, no updateQueryParam call is needed.
  },
  { deep: true } // Watch nested properties of the query object
)

// --- Lifecycle Hooks ---

/**
 * Registers the global keydown event listener when the component is mounted.
 */
onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

/**
 * Removes the global keydown event listener when the component is unmounted
 * to prevent memory leaks.
 */
onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

// --- Page Meta ---

/**
 * Defines metadata for the page, such as the title.
 */
definePageMeta({
  title: 'Navicula',
})
</script>

<style>
/* Style for the active navigation item */
.active-item {
  background-color: rgba(0, 0, 0, 0.1); /* Subtle background highlight */
}

/* Base item styling */
.q-item {
  /* Add base styles if needed */
}

/* Dense item styling */
.q-item--dense {
  padding: 4px 8px; /* Reduced padding for dense items */
  min-height: 32px; /* Reduced minimum height */
}

/* Avatar section styling */
.q-item__section--avatar {
  min-width: 40px; /* Ensure space for icon */
  padding-right: 16px; /* Space between icon and text */
}
.q-item--dense .q-item__section--avatar {
  padding-right: 8px; /* Reduced space for dense items */
}

/* Avatar styling when drawer is in mini mode */
.q-drawer--mini .q-item__section--avatar {
  margin: 0 auto; /* Center the icon */
  padding-right: 0; /* No padding needed when centered */
}

/* Ensure layout takes full height and removes default margins/paddings */
html,
body,
#__nuxt {
  height: 100%;
  margin: 0;
  padding: 0;
  overflow: hidden; /* Prevent scrollbars on the main layout */
}

/* Flex container for the main page content */
.page-flex-container {
  display: flex;
  flex-direction: column; /* Stack elements vertically */
  height: 100%; /* Take full available height */
  overflow: hidden; /* Prevent internal scrolling */
}

/* Ensure drawer content uses flex column layout */
.drawer-column .q-drawer__content {
  display: flex;
  flex-direction: column;
}

/* Utility class for text ellipsis */
.ellipsis {
  white-space: nowrap; /* Prevent text wrapping */
  overflow: hidden; /* Hide overflow */
  text-overflow: ellipsis; /* Add '...' for overflow */
}

/* Positioning and hover effect for the 'Add to view' button */
.nav-item {
  position: relative; /* Needed for absolute positioning of the button */
}
.split-button-container {
  position: absolute;
  right: 4px; /* Position near the right edge */
  top: 50%; /* Center vertically */
  transform: translateY(-50%); /* Fine-tune vertical centering */
  opacity: 0; /* Hidden by default */
  transition: opacity 0.2s ease-in-out; /* Smooth fade effect */
}
.nav-item:hover .split-button-container {
  opacity: 1; /* Show button on hover */
}
</style>
