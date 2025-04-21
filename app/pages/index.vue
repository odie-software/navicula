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

      <div style="flex-grow: 1"/>

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
// Imports (reverting explicit Nuxt imports, trying relative path for component)
import { ref, watch, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import AppWindow from '../components/AppWindow.vue' // Use relative path

const $q = useQuasar()
const route = useRoute()
const router = useRouter()

// --- Interfaces ---
interface AppLink {
  id: string
  title: string
  icon: string
  url: string
  toolbarColor?: string
  autoload?: boolean
  apps?: never
}

interface NavCategory {
  id: string
  title: string
  icon: string
  apps: AppLink[]
  toolbarColor?: string
  url?: never
}

type NavigationItem = AppLink | NavCategory
type DrawerMode = 'auto-hide' | 'always-open'

interface UserInfo {
  userEmail: string | null
  role: string
}

interface ConfigResponse {
  userEmail: string | null
  role: string
  navigationItems: NavigationItem[]
  defaultToolbarColor: string
  keybindings?: Record<string, string>
  error?: string
}

// --- Type Guards ---
function isCategory(item: NavigationItem): item is NavCategory {
  return Array.isArray((item as NavCategory).apps)
}
function isAppLink(item: NavigationItem): item is AppLink {
  return typeof (item as AppLink).url === 'string'
}

// --- Refs ---
const leftDrawerOpen = ref(true)
const miniState = ref(true)
const drawerMode = ref<DrawerMode>('auto-hide')
const activeAppId = ref<string | null>(null)
const displayedAppIds = ref<string[]>([])
const previousActiveAppId = ref<string | null>(null)
const navigationItems = ref<NavigationItem[]>([])
const userInfo = ref<UserInfo>({ userEmail: null, role: 'Guest' })
// const iframeReloadKeys = ref<Record<string, number>>({}); // Removed for keep-alive
const defaultToolbarColor = ref('primary')
const appWindowRefs = ref<Record<string, InstanceType<typeof AppWindow>>>({})
const keybindingsConfig = ref<Record<string, string>>({})
const hoveredItemId = ref<string | null>(null)
const splitterModel = ref(50)

// --- Methods ---
function toggleDrawerMode() {
  drawerMode.value =
    drawerMode.value === 'auto-hide' ? 'always-open' : 'auto-hide'
  if (drawerMode.value === 'always-open') {
    miniState.value = false
  } else {
    miniState.value = true
  }
}

function handleMouseOver() {
  if (drawerMode.value === 'auto-hide') {
    miniState.value = false
  }
}

function handleMouseOut() {
  if (drawerMode.value === 'auto-hide') {
    miniState.value = true
  }
}

// Selects an item: if already displayed, activate; otherwise, replace active window.
function selectItem(item: AppLink | null) {
  if (!item) {
    activateWindow(null)
    return
  }

  if (displayedAppIds.value.includes(item.id)) {
    // If already displayed, just activate it
    activateWindow(item.id)
  } else {
    // If not displayed, replace the currently active window (or add if none active/displayed)
    const activeIndex = activeAppId.value
      ? displayedAppIds.value.indexOf(activeAppId.value)
      : -1
    if (activeIndex !== -1 && displayedAppIds.value.length > 0) {
      displayedAppIds.value.splice(activeIndex, 1, item.id)
    } else {
      displayedAppIds.value = [item.id]
    }
    activateWindow(item.id)
    // ensureIframeKey(item.id); // Removed call
  }
  updateQueryParam()
}

// Adds a window alongside existing ones
function addWindow(itemToAdd: AppLink) {
  if (displayedAppIds.value.length >= 2) {
    displayedAppIds.value = [displayedAppIds.value[0]]
  }

  if (!displayedAppIds.value.includes(itemToAdd.id)) {
    displayedAppIds.value.push(itemToAdd.id)
    activateWindow(itemToAdd.id) // Activate the newly added window
    // ensureIframeKey(itemToAdd.id); // Removed call
    updateQueryParam()
  } else {
    // If already displayed, just activate it
    activateWindow(itemToAdd.id)
  }
}

function closeWindow(appIdToClose: string) {
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

function activateWindow(appId: string | null) {
  if (activeAppId.value !== appId) {
    previousActiveAppId.value = activeAppId.value
    activeAppId.value = appId
  }
  // Ensure activated window is displayed
  if (appId && !displayedAppIds.value.includes(appId)) {
    displayedAppIds.value.push(appId)
    // ensureIframeKey(appId); // Removed call
  }
  updateQueryParam()
}

function updateQueryParam() {
  const query: Record<string, string | string[]> = {}
  if (displayedAppIds.value.length > 0) {
    query.apps = displayedAppIds.value.join(',')
  }
  if (activeAppId.value) {
    query.active = activeAppId.value
  }
  router.replace({ query }).catch((err) => {
    if (err.name !== 'NavigationDuplicated') {
      console.error('Router replace error:', err)
    }
  })
}

function swapWindows() {
  if (displayedAppIds.value.length === 2) {
    displayedAppIds.value.reverse()
    updateQueryParam() // Update URL to reflect the new order
  }
}

// Removed ensureIframeKey function definition

function reloadIframe(appId: string) {
  // iframeReloadKeys.value[appId] = Date.now(); // Removed for keep-alive
  // Attempt direct reload via ref if possible
  const targetWindow = appWindowRefs.value[appId]
  const iframe = targetWindow?.iframeElement
  const app = allAppLinks.value.find((a) => a.id === appId)
  if (iframe) {
    iframe.contentWindow?.location.reload()
    $q.notify({ type: 'info', message: `Reloading ${app?.title}...` })
  } else {
    $q.notify({
      type: 'warning',
      message: `Could not find iframe to reload ${app?.title}.`,
    })
  }
}

async function copyIframeUrl(appId: string) {
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

// --- Keybinding Logic ---
function handleKeydown(event: KeyboardEvent) {
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
      activateWindow(previousActiveAppId.value)
    }
    return
  }

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
        currentActiveIndex >= links.length - 1 ? 0 : currentActiveIndex + 1
    } else {
      nextIndex =
        currentActiveIndex <= 0 ? links.length - 1 : currentActiveIndex - 1
    }

    if (nextIndex !== -1 && links[nextIndex]) {
      selectItem(links[nextIndex])
    }
    return
  }

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

function buildKeyString(event: KeyboardEvent): string {
  const parts: string[] = []
  if (event.ctrlKey) parts.push('Ctrl')
  if (event.altKey) parts.push('Alt')
  if (event.shiftKey) parts.push('Shift')
  if (event.metaKey) parts.push('Meta')

  let key = event.key
  if (['Control', 'Shift', 'Alt', 'Meta'].includes(key)) return ''

  if (key.length === 1) key = key.toUpperCase()

  parts.push(key)
  return parts.join('+')
}

// --- API Fetch ---
// Relying on Nuxt auto-import for useFetch
const {
  data: configData,
  pending,
  error,
} = useFetch<ConfigResponse>('/api/config')

// --- Computed Properties ---
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

function getAppLinkById(id: string): AppLink | undefined {
  return allAppLinks.value.find((app) => app.id === id)
}

function isAppLinkSameOrigin(appLink: AppLink | null | undefined): boolean {
  const url = appLink?.url
  if (!url) return false
  if (!url.startsWith('http://') && !url.startsWith('https://')) return true
  try {
    return new URL(url).origin === window.location.origin
  } catch {
    return false
  }
}

// --- Watchers ---
watch(
  configData,
  (newConfig) => {
    if (
      newConfig &&
      !newConfig.error &&
      Array.isArray(newConfig.navigationItems)
    ) {
      navigationItems.value = newConfig.navigationItems
      userInfo.value = { userEmail: newConfig.userEmail, role: newConfig.role }
      defaultToolbarColor.value = newConfig.defaultToolbarColor || 'primary'
      keybindingsConfig.value = newConfig.keybindings || {}

      const autoLoadIds = new Set<string>()
      allAppLinks.value.forEach((app) => {
        if (app.autoload) {
          autoLoadIds.add(app.id)
        }
      })

      const appsQuery = route.query.apps as string | undefined
      const appsFromQuery = appsQuery ? appsQuery.split(',') : []
      const activeFromQuery = route.query.active as string | undefined

      const validAppIdsFromQuery = appsFromQuery.filter((id) =>
        allAppLinks.value.some((app) => app.id === id)
      )
      const validActiveIdFromQuery = validAppIdsFromQuery.includes(
        activeFromQuery ?? ''
      )
        ? activeFromQuery
        : null

      // Determine initial displayed apps: Prioritize query, then first autoload, then first app
      let initialDisplayedIds: string[] = []
      let initialActiveId: string | null = null

      if (validAppIdsFromQuery.length > 0) {
        initialDisplayedIds = validAppIdsFromQuery
        initialActiveId =
          validActiveIdFromQuery || initialDisplayedIds[0] || null
      } else if (autoLoadIds.size > 0) {
        // Default to showing only the *first* autoload app if query is empty
        const firstAutoload = Array.from(autoLoadIds)[0]
        initialDisplayedIds = [firstAutoload]
        initialActiveId = firstAutoload
      } else if (flatAppLinks.value.length > 0) {
        // Default to the very first app link if no query and no autoload
        initialDisplayedIds = [flatAppLinks.value[0].id]
        initialActiveId = initialDisplayedIds[0]
      }

      // Corrected logic: Ensure initialDisplayedIds is set before using it
      if (initialDisplayedIds.length === 0 && flatAppLinks.value.length > 0) {
        initialDisplayedIds = [flatAppLinks.value[0].id]
        initialActiveId = initialDisplayedIds[0]
      }

      displayedAppIds.value = initialDisplayedIds
      activeAppId.value = initialActiveId // Set active ID after determining displayed IDs

      // displayedAppIds.value.forEach(ensureIframeKey); // Removed call

      if (displayedAppIds.value.length > 1 && activeAppId.value) {
        previousActiveAppId.value =
          displayedAppIds.value.find((id) => id !== activeAppId.value) || null
      } else {
        previousActiveAppId.value = null
      }

      // Update URL if initial state differs from query
      updateQueryParam()
    } else {
      console.error(
        'Failed to load or parse configuration:',
        newConfig?.error || error.value || 'Invalid config format'
      )
      navigationItems.value = []
      activeAppId.value = null
      displayedAppIds.value = []
      userInfo.value = { userEmail: null, role: 'Error' }
      keybindingsConfig.value = {}
      updateQueryParam()
    }
  },
  { immediate: true }
)

watch(
  () => route.query,
  (newQuery) => {
    const appsQuery = newQuery.apps as string | undefined
    const appsFromQuery = appsQuery ? appsQuery.split(',') : []
    const activeFromQuery = newQuery.active as string | undefined

    const validAppIdsFromQuery = appsFromQuery.filter((id) =>
      allAppLinks.value.some((app) => app.id === id)
    )
    const validActiveIdFromQuery = validAppIdsFromQuery.includes(
      activeFromQuery ?? ''
    )
      ? activeFromQuery
      : null

    // Check if state needs update based on query changes
    const stateAppsSorted = [...displayedAppIds.value].sort()
    const queryAppsSorted = [...validAppIdsFromQuery].sort()

    if (JSON.stringify(stateAppsSorted) !== JSON.stringify(queryAppsSorted)) {
      displayedAppIds.value = validAppIdsFromQuery
      // displayedAppIds.value.forEach(ensureIframeKey); // Removed call
      // If displayed apps change, re-evaluate active app based on new query/displayed list
      activeAppId.value =
        validActiveIdFromQuery || displayedAppIds.value[0] || null
    } else if (activeAppId.value !== validActiveIdFromQuery) {
      // Only update active ID if displayed apps are the same but active differs
      activateWindow(validActiveIdFromQuery)
    }
  },
  { deep: true }
)

// --- Lifecycle Hooks ---
onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})
onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

// --- Runtime Config & Meta ---
// Relying on Nuxt auto-import for useRuntimeConfig and definePageMeta
const config = useRuntimeConfig()
const appVersion = config.public.appVersion

definePageMeta({
  title: 'Navicula',
})
</script>

<style scoped>
.active-item {
  background-color: rgba(0, 0, 0, 0.1);
}

.q-item {
}
.q-item--dense {
  padding: 4px 8px;
  min-height: 32px;
}

.q-item__section--avatar {
  min-width: 40px;
  padding-right: 16px;
}
.q-item--dense .q-item__section--avatar {
  padding-right: 8px;
}

.q-drawer--mini .q-item__section--avatar {
  margin: 0 auto;
  padding-right: 0;
}

html,
body,
#__nuxt {
  height: 100%;
  margin: 0;
  padding: 0;
  overflow: hidden;
}

.page-flex-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.drawer-column .q-drawer__content {
  display: flex;
  flex-direction: column;
}

.ellipsis {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.app-window-container {
  display: flex;
  flex-direction: row;
  flex-grow: 1;
  height: 100%;
  width: 100%;
  overflow: hidden;
}

.app-window-container > :deep(.app-window) {
  flex-basis: 0;
  flex-grow: 1;
  margin: 2px !important;
  min-width: 200px;
}

.nav-item {
  position: relative;
}
.split-button-container {
  position: absolute;
  right: 4px;
  top: 50%;
  transform: translateY(-50%);
  opacity: 0;
  transition: opacity 0.2s ease-in-out;
}
.nav-item:hover .split-button-container {
  opacity: 1;
}
.q-drawer--mini .split-button-container {
  display: none;
}

/* Style for the splitter */
.splitter-container {
  height: 100%;
  width: 100%;
  flex-grow: 1;
}
.after-panel-container {
  display: flex;
  flex-direction: row;
  height: 100%;
  width: 100%;
  overflow: hidden;
}
.split-window {
  height: 100vh;
  width: 100%;
  margin: 0 !important;
}

/* Ensure single window also takes full space */
.single-window {
  height: 100%;
  width: 100%;
  display: flex;
}
.single-window > :deep(.app-window) {
  margin: 0 !important;
}
</style>
