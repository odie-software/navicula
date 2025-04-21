<template>
  <q-layout view="lHh Lpr lFf" class="bg-white">
    <q-drawer
      v-model="leftDrawerOpen"
      :mini="drawerMode === 'auto-hide' && miniState"
      bordered
      class="drawer-column"
      @mouseover="handleMouseOver"
      @mouseout="handleMouseOut"
      @update:mini="(val: boolean) => (miniState = val)"
    >
      <q-list v-if="!pending && navigationItems.length > 0" padding>
        <template v-for="item in navigationItems" :key="item.id">
          <!-- App Link Item -->
          <q-item
            v-if="isAppLink(item)"
            clickable
            :active="activeAppId === item.id && displayedAppIds.length === 1"
            active-class="active-item"
            class="nav-item"
            @click="selectItem(item)"
            @mouseover="hoveredItemId = item.id"
            @mouseleave="hoveredItemId = null"
          >
            <q-item-section avatar>
              <q-icon :name="item.icon" size="sm" />
            </q-item-section>
            <q-item-section class="q-mini-drawer-hide">
              <q-item-label>{{ item.title }}</q-item-label>
            </q-item-section>
            <!-- Add Button: Show if item not displayed -->
            <q-item-section
              side
              top
              class="q-mini-drawer-hide split-button-container"
            >
              <q-btn
                v-show="
                  hoveredItemId === item.id &&
                  !displayedAppIds.includes(item.id) &&
                  displayedAppIds.length > 0
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

            <q-list dense padding class="q-pl-lg">
              <q-item
                v-for="app in item.apps"
                :key="app.id"
                clickable
                :active="activeAppId === app.id && displayedAppIds.length === 1"
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
                <q-item-section class="q-mini-drawer-hide">
                  <q-item-label class="text-body2">{{
                    app.title
                  }}</q-item-label>
                </q-item-section>
                <!-- Add Button (Nested) -->
                <q-item-section
                  side
                  top
                  class="q-mini-drawer-hide split-button-container"
                >
                  <q-btn
                    v-show="
                      hoveredItemId === app.id &&
                      !displayedAppIds.includes(app.id) &&
                      displayedAppIds.length > 0
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
        <!-- Single Window View -->
        <div
          v-if="displayedAppIds.length === 1"
          class="app-window-container single-window"
        >
          <keep-alive>
            <AppWindow
              v-if="getAppLinkById(displayedAppIds[0])"
              :ref="
                (el: any) => {
                  if (el)
                    appWindowRefs[displayedAppIds[0]] = el as InstanceType<
                      typeof AppWindow
                    >
                }
              "
              :key="displayedAppIds[0]"
              :app-link="getAppLinkById(displayedAppIds[0])!"
              :is-active="true"
              :is-same-origin="
                isAppLinkSameOrigin(getAppLinkById(displayedAppIds[0]))
              "
              :default-toolbar-color="defaultToolbarColor"
              @activate-window="activateWindow"
              @close-window="closeWindow"
              @copy-iframe-url="copyIframeUrl(displayedAppIds[0])"
              @reload-iframe="reloadIframe(displayedAppIds[0])"
            />
          </keep-alive>
        </div>
        <!-- Split View (for exactly 2 windows) -->
        <q-splitter
          v-else-if="displayedAppIds.length === 2"
          v-model="splitterModel"
          class="splitter-container"
          unit="%"
          style="flex-grow: 1"
        >
          <template #before>
            <keep-alive>
              <AppWindow
                v-if="getAppLinkById(displayedAppIds[0])"
                :ref="
                  (el: any) => {
                    if (el)
                      appWindowRefs[displayedAppIds[0]] = el as InstanceType<
                        typeof AppWindow
                      >
                  }
                "
                :key="displayedAppIds[0]"
                :app-link="getAppLinkById(displayedAppIds[0])!"
                :is-active="activeAppId === displayedAppIds[0]"
                :is-same-origin="
                  isAppLinkSameOrigin(getAppLinkById(displayedAppIds[0]))
                "
                :default-toolbar-color="defaultToolbarColor"
                :show-swap-button="activeAppId === displayedAppIds[0]"
                class="split-window"
                @activate-window="activateWindow"
                @close-window="closeWindow"
                @copy-iframe-url="copyIframeUrl(displayedAppIds[0])"
                @reload-iframe="reloadIframe(displayedAppIds[0])"
                @swap-window="swapWindows"
              />
            </keep-alive>
          </template>
          <template #after>
            <keep-alive>
              <AppWindow
                v-if="getAppLinkById(displayedAppIds[1])"
                :ref="
                  (el: any) => {
                    if (el)
                      appWindowRefs[displayedAppIds[1]] = el as InstanceType<
                        typeof AppWindow
                      >
                  }
                "
                :key="displayedAppIds[1]"
                :app-link="getAppLinkById(displayedAppIds[1])!"
                :is-active="activeAppId === displayedAppIds[1]"
                :is-same-origin="
                  isAppLinkSameOrigin(getAppLinkById(displayedAppIds[1]))
                "
                :default-toolbar-color="defaultToolbarColor"
                :show-swap-button="activeAppId === displayedAppIds[1]"
                class="split-window"
                @activate-window="activateWindow"
                @close-window="closeWindow"
                @copy-iframe-url="copyIframeUrl(displayedAppIds[1])"
                @reload-iframe="reloadIframe(displayedAppIds[1])"
                @swap-window="swapWindows"
              />
            </keep-alive>
          </template>
        </q-splitter>
        <!-- Placeholder when no windows are open -->
        <div
          v-else-if="displayedAppIds.length === 0 && !pending"
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
  </q-layout>
</template>

<script lang="ts" setup>
import { ref, watch, computed, onMounted, onUnmounted, type Ref } from 'vue'
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
  QSplitter,
} from 'quasar'
import AppWindow from '../components/AppWindow.vue' // Use relative path

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

// --- Composables ---
const $q = useQuasar()
const route = useRoute()
const router = useRouter()
const config = useRuntimeConfig()

// --- State Refs ---

/** Controls the visibility (open/closed) of the left navigation drawer. */
const leftDrawerOpen: Ref<boolean> = ref(true)
/** Controls the mini-mode state of the drawer (true = minimized). */
const miniState: Ref<boolean> = ref(true)
/** Current behavior mode of the drawer ('auto-hide' or 'always-open'). */
const drawerMode: Ref<DrawerMode> = ref('auto-hide')
/** ID of the currently active AppWindow, or null if none is active. */
const activeAppId: Ref<string | null> = ref(null)
/** Array of AppLink IDs currently displayed in AppWindows. */
const displayedAppIds: Ref<string[]> = ref([])
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
/** Model for the QSplitter component, controlling the split percentage. */
const splitterModel: Ref<number> = ref(50)
/** Application version from runtime config. */
const appVersion: string = config.public.appVersion

// --- API Fetch ---

/**
 * Fetches the application configuration from the `/api/config` endpoint.
 * Provides reactive `data`, `pending`, and `error` states.
 */
const {
  data: configData,
  pending,
  error,
} = useFetch<ConfigResponse>('/api/config')

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
 * Toggles the drawer mode between 'auto-hide' and 'always-open'.
 * Adjusts the miniState accordingly.
 */
function toggleDrawerMode(): void {
  drawerMode.value =
    drawerMode.value === 'auto-hide' ? 'always-open' : 'auto-hide'
  if (drawerMode.value === 'always-open') {
    miniState.value = false
  } else {
    miniState.value = true
  }
}

/**
 * Handles the mouseover event on the drawer.
 * Expands the drawer if it's in 'auto-hide' mode.
 */
function handleMouseOver(): void {
  if (drawerMode.value === 'auto-hide') {
    miniState.value = false
  }
}

/**
 * Handles the mouseout event on the drawer.
 * Minimizes the drawer if it's in 'auto-hide' mode.
 */
function handleMouseOut(): void {
  if (drawerMode.value === 'auto-hide') {
    miniState.value = true
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

  if (displayedAppIds.value.includes(item.id)) {
    activateWindow(item.id)
  } else {
    const activeIndex = activeAppId.value
      ? displayedAppIds.value.indexOf(activeAppId.value)
      : -1
    if (activeIndex !== -1 && displayedAppIds.value.length > 0) {
      displayedAppIds.value.splice(activeIndex, 1, item.id)
    } else {
      displayedAppIds.value = [item.id]
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
  if (displayedAppIds.value.length >= 2) {
    displayedAppIds.value = [displayedAppIds.value[0]]
  }

  if (!displayedAppIds.value.includes(itemToAdd.id)) {
    displayedAppIds.value.push(itemToAdd.id)
    activateWindow(itemToAdd.id)
    updateQueryParam()
  } else {
    activateWindow(itemToAdd.id)
  }
}

/**
 * Closes the AppWindow associated with the given AppLink ID.
 * Removes the ID from `displayedAppIds` and cleans up the corresponding ref.
 * Activates the previously active window or the remaining window if necessary.
 * Updates the URL query parameters.
 * @param {string} appIdToClose - The ID of the AppLink whose window should be closed.
 */
function closeWindow(appIdToClose: string): void {
  const index = displayedAppIds.value.indexOf(appIdToClose)
  if (index > -1) {
    displayedAppIds.value.splice(index, 1)
    // eslint-disable-next-line @typescript-eslint/no-dynamic-delete
    delete appWindowRefs.value[appIdToClose]

    if (activeAppId.value === appIdToClose) {
      const newActiveId =
        previousActiveAppId.value &&
        displayedAppIds.value.includes(previousActiveAppId.value)
          ? previousActiveAppId.value
          : (displayedAppIds.value[0] ?? null)
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
 * Ensures the activated window is added to `displayedAppIds` if not already present.
 * Updates the URL query parameters.
 * @param {string | null} appId - The ID of the AppLink to activate, or null to deactivate.
 */
function activateWindow(appId: string | null): void {
  if (activeAppId.value !== appId) {
    previousActiveAppId.value = activeAppId.value
    activeAppId.value = appId
  }
  if (appId && !displayedAppIds.value.includes(appId)) {
    displayedAppIds.value.push(appId)
  }
  updateQueryParam()
}

/**
 * Updates the URL query parameters (`apps` and `active`) based on the current state.
 * Uses `router.replace` to avoid adding history entries.
 */
function updateQueryParam(): void {
  const query: Record<string, string | string[]> = {}
  if (displayedAppIds.value.length > 0) {
    query.apps = displayedAppIds.value.join(',')
  }
  if (activeAppId.value) {
    query.active = activeAppId.value
  }
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
 * Updates the `displayedAppIds` order and the URL query parameters.
 */
function swapWindows(): void {
  if (displayedAppIds.value.length === 2) {
    displayedAppIds.value.reverse()
    updateQueryParam()
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
    if (displayedAppIds.value.length > 1 && activeAppId.value) {
      const currentIndex = displayedAppIds.value.indexOf(activeAppId.value)
      const nextIndex = (currentIndex + 1) % displayedAppIds.value.length
      activateWindow(displayedAppIds.value[nextIndex])
    } else if (
      previousActiveAppId.value &&
      displayedAppIds.value.includes(previousActiveAppId.value)
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
 * - Determines the initial `displayedAppIds` and `activeAppId` based on:
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
      userInfo.value = { userEmail: newConfig.userEmail, role: newConfig.role }
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
      const activeFromQuery = route.query.active as string | undefined

      // Validate query parameters against available apps
      const validAppIdsFromQuery = appsFromQuery
        .filter((id) => allAppLinks.value.some((app) => app.id === id))
        .slice(0, 2) // Limit to max 2 apps from query

      const validActiveIdFromQuery = validAppIdsFromQuery.includes(
        activeFromQuery ?? ''
      )
        ? activeFromQuery
        : null

      // Determine initial state: Query > Autoload > First App
      let initialDisplayedIds: string[] = []
      let initialActiveId: string | null = null

      if (validAppIdsFromQuery.length > 0) {
        initialDisplayedIds = validAppIdsFromQuery
        initialActiveId =
          validActiveIdFromQuery || initialDisplayedIds[0] || null
      } else if (autoLoadIds.size > 0) {
        const firstAutoload = Array.from(autoLoadIds)[0]
        initialDisplayedIds = [firstAutoload]
        initialActiveId = firstAutoload
      } else if (flatAppLinks.value.length > 0) {
        initialDisplayedIds = [flatAppLinks.value[0].id]
        initialActiveId = initialDisplayedIds[0]
      }

      // Apply initial state
      displayedAppIds.value = initialDisplayedIds
      activeAppId.value = initialActiveId

      // Set previous active ID for Alt+Tab
      if (displayedAppIds.value.length > 1 && activeAppId.value) {
        previousActiveAppId.value =
          displayedAppIds.value.find((id) => id !== activeAppId.value) || null
      } else {
        previousActiveAppId.value = null
      }

      // Ensure URL reflects the final initial state
      updateQueryParam()
    } else {
      // Handle config loading error
      console.error(
        'Failed to load or parse configuration:',
        newConfig?.error || error.value || 'Invalid config format'
      )
      navigationItems.value = []
      activeAppId.value = null
      displayedAppIds.value = []
      userInfo.value = { userEmail: null, role: 'Error' }
      keybindingsConfig.value = {}
      updateQueryParam() // Clear query params on error
    }
  },
  { immediate: true } // Run watcher immediately on component mount
)

/**
 * Watches the route query parameters (`apps` and `active`).
 * Updates the component state (`displayedAppIds`, `activeAppId`) if the query changes,
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
    const validAppIdsFromQuery = appsFromQuery
      .filter((id) => allAppLinks.value.some((app) => app.id === id))
      .slice(0, 2) // Limit to max 2

    const validActiveIdFromQuery = validAppIdsFromQuery.includes(
      activeFromQuery ?? ''
    )
      ? (activeFromQuery ?? null) // Ensure undefined becomes null
      : null

    // Check if the displayed apps in the state differ from the valid query apps
    const stateAppsString = displayedAppIds.value.join(',')
    const queryAppsString = validAppIdsFromQuery.join(',')

    if (stateAppsString !== queryAppsString) {
      displayedAppIds.value = validAppIdsFromQuery
      // If displayed apps change, the active app might need recalculation
      const newActive =
        validActiveIdFromQuery || displayedAppIds.value[0] || null
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

<style scoped>
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

/* Container for AppWindow(s) */
.app-window-container {
  display: flex;
  flex-direction: row; /* Arrange windows side-by-side */
  flex-grow: 1; /* Take remaining vertical space */
  height: 100%; /* Use full height of parent */
  width: 100%; /* Use full width of parent */
  overflow: hidden; /* Hide overflow */
}

/* Styling for individual AppWindow components within the container */
.app-window-container > :deep(.app-window) {
  flex-basis: 0; /* Allow flex-grow to distribute space */
  flex-grow: 1; /* Each window takes equal space initially */
  margin: 2px !important; /* Small margin around windows (overridden for single/split) */
  min-width: 200px; /* Minimum width for usability */
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
/* Hide the add button when the drawer is minimized */
.q-drawer--mini .split-button-container {
  display: none;
}

/* Styling for the QSplitter component */
.splitter-container {
  height: 100%; /* Full height */
  width: 100%; /* Full width */
  flex-grow: 1; /* Take available space */
}

/* Styling for AppWindows within the splitter panels */
.split-window {
  height: 100%; /* Full height within the panel */
  width: 100%; /* Full width within the panel */
  margin: 0 !important; /* Remove default margin */
  overflow: hidden; /* Prevent internal scrollbars */
}
.split-window > :deep(.app-window) {
  margin: 0 !important; /* Ensure no margin on the AppWindow itself */
}

/* Ensure single window takes full space without margins */
.single-window {
  height: 100%;
  width: 100%;
  display: flex; /* Use flex to manage the single child */
}
.single-window > :deep(.app-window) {
  margin: 0 !important; /* Remove margin for single view */
  flex-grow: 1; /* Ensure it takes all space */
}
</style>
