<template>
  <!-- Add conditional class/style for active state -->
  <q-card
    bordered
    class="app-window q-ma-sm rounded-borders column no-wrap"
    :class="{ 'active-window': isActive }"
    @click="$emit('activate-window', appLink.id)"
  >
    <q-toolbar :class="toolbarClasses" dense>
      <q-icon :name="appLink.icon || 'web_asset'" size="xs" class="q-mr-sm" />
      <q-toolbar-title class="text-caption ellipsis">
        {{ appLink.title }}
      </q-toolbar-title>
      <q-space />
      <q-btn
        v-if="isSameOrigin"
        flat
        dense
        round
        icon="content_copy"
        aria-label="Copy Current Frame URL"
        size="sm"
        class="q-mr-xs"
        @click.stop="$emit('copy-iframe-url')"
      >
        <q-tooltip>Copy Current Frame URL</q-tooltip>
      </q-btn>
      <q-btn
        v-if="appLink.url"
        flat
        dense
        round
        icon="refresh"
        aria-label="Reload Frame"
        size="sm"
        class="q-mr-xs"
        @click.stop="$emit('reload-iframe')"
      >
        <q-tooltip>Reload Frame</q-tooltip>
      </q-btn>
      <!-- Swap Button (only if active and showSwapButton is true) -->
      <q-btn
        v-if="isActive && showSwapButton"
        flat
        dense
        round
        icon="swap_horiz"
        aria-label="Swap Window Position"
        size="sm"
        class="q-mr-xs"
        @click.stop="$emit('swap-window')"
      >
        <q-tooltip>Swap with other window</q-tooltip>
      </q-btn>
      <!-- Close Button -->
      <q-btn
        flat
        dense
        round
        icon="close"
        aria-label="Close Window"
        size="sm"
        @click.stop="$emit('close-window', appLink.id)"
      >
        <q-tooltip>Close</q-tooltip>
      </q-btn>
    </q-toolbar>

    <q-card-section class="col q-pa-none">
      <iframe
        ref="iframeElement"
        :src="appLink.url"
        class="app-iframe"
        frameborder="0"
        :title="appLink.title"
      />
    </q-card-section>
  </q-card>
</template>

<script lang="ts" setup>
import { ref, computed } from 'vue'
import type { PropType } from 'vue'

interface AppLink {
  id: string
  title: string
  icon: string
  url: string
  toolbarColor?: string
  autoload?: boolean
  apps?: never
}

const props = defineProps({
  appLink: {
    type: Object as PropType<AppLink>,
    required: true,
  },
  isSameOrigin: {
    type: Boolean,
    required: true,
  },
  defaultToolbarColor: {
    type: String,
    default: 'primary',
  },
  isActive: {
    type: Boolean,
    default: false,
  },
  // New prop to control swap button visibility
  showSwapButton: {
    type: Boolean,
    default: false,
  },
})

// Added swap-window emit
defineEmits([
  'copy-iframe-url',
  'reload-iframe',
  'activate-window',
  'close-window',
  'swap-window',
])

const iframeElement = ref<HTMLIFrameElement | null>(null)

const toolbarClasses = computed(() => {
  const color = props.appLink.toolbarColor || props.defaultToolbarColor
  if (
    color.startsWith('#') ||
    color.startsWith('rgb') ||
    color.startsWith('hsl') ||
    ['transparent', 'white', 'black'].includes(color)
  ) {
    return { style: { backgroundColor: color } }
  } else {
    // Add text-white for better contrast on Quasar colors
    return `bg-${color} text-white`
  }
})

defineExpose({ iframeElement })
</script>

<style scoped>
.app-window {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: box-shadow 0.3s ease-in-out; /* Add transition for active state */
  min-width: 300px; /* Prevent windows from becoming too small */
}

/* Style for active window */
.active-window {
  box-shadow: 0 0 10px 2px var(--q-color-primary); /* Highlight active window */
}

.app-iframe {
  display: block;
  border: none;
  width: 100%;
  height: 100%;
}

/* Ensure toolbar buttons are visible */
.q-toolbar .q-btn {
  color: inherit; /* Inherit color from toolbar text */
}
</style>
