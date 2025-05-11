<template>
  <q-dialog
    :model-value="modelValue"
    persistent
    @update:model-value="emitUpdate(false)"
  >
    <q-card style="min-width: 350px">
      <q-card-section>
        <div class="text-h6">Configure {{ appLink?.title }}</div>
      </q-card-section>

      <q-card-section class="q-pt-none">
        <!-- Specific settings based on app type -->
        <template v-if="appLink?.type === 'vikunja'">
          <q-input
            v-model="apiKey"
            label="API Key"
            placeholder="Enter your Vikunja API Key"
            outlined
            dense
            :type="showApiKey ? 'text' : 'password'"
            :loading="loading"
            :error="!!error"
            :error-message="error"
            class="q-mb-md"
            clearable
            @clear="apiKey = ''"
          >
            <template #append>
              <q-icon
                :name="showApiKey ? 'visibility_off' : 'visibility'"
                class="cursor-pointer"
                @click="showApiKey = !showApiKey"
              />
            </template>
            <template #hint>
              Create an API token in your Vikunja user settings.
            </template>
          </q-input>
        </template>
        <template v-else>
          <p>
            Configuration for this application type ({{ appLink?.type }}) is not
            yet supported.
          </p>
        </template>
      </q-card-section>

      <q-card-actions align="right" class="text-primary">
        <q-btn
          flat
          label="Cancel"
          :disable="saving"
          @click="emitUpdate(false)"
        />
        <q-btn
          flat
          label="Save"
          :loading="saving"
          :disable="!isSaveEnabled"
          @click="saveSettings"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import {
  useQuasar,
  QDialog,
  QCard,
  QCardSection,
  QCardActions,
  QInput,
  QBtn,
  QIcon,
} from 'quasar'
import { $fetch } from 'ofetch'

// --- Props ---
interface AppLink {
  id: string
  title: string
  icon: string
  url: string
  type?: string
  toolbarColor?: string
  autoload?: boolean
}

const props = defineProps<{
  modelValue: boolean // Controls dialog visibility (v-model)
  appLink: AppLink | null // The app being configured
}>()

// --- Emits ---
const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'settings-saved', appId: string): void // Emit when settings are successfully saved
}>()

// --- Composables ---
const $q = useQuasar()

// --- State ---
const apiKey = ref<string>('') // Holds the API key input
const showApiKey = ref<boolean>(false)
const saving = ref<boolean>(false)
const loading = ref<boolean>(false) // For potentially loading existing settings (future enhancement)
const error = ref<string | undefined>(undefined) // Use undefined instead of null
const initialApiKey = ref<string>('') // Store initial value to check for changes

// --- Computed ---
const isSaveEnabled = computed(() => {
  // Enable save only if the API key has actually changed
  return apiKey.value !== initialApiKey.value && !saving.value
})

// --- Methods ---
function emitUpdate(value: boolean) {
  emit('update:modelValue', value)
}

async function saveSettings() {
  if (!props.appLink || !props.appLink.id) return

  saving.value = true
  error.value = undefined // Clear previous errors

  try {
    const userSettingsApiUrl = `/api/users/settings/${props.appLink.id}/` // Added trailing slash for Django convention
    await $fetch(userSettingsApiUrl, {
      method: 'POST',
      body: {
        // Only send relevant settings based on type
        ...(props.appLink.type === 'vikunja' && { api_key: apiKey.value }),
        // Add other types here...
      },
    })

    $q.notify({
      type: 'positive',
      message: `${props.appLink.title} settings saved successfully.`,
      icon: 'check_circle',
    })
    emit('settings-saved', props.appLink.id) // Notify parent
    emitUpdate(false) // Close dialog
  } catch (e: unknown) {
    console.error(`Failed to save settings for ${props.appLink.id}:`, e)
    const defaultMessage = 'Failed to save settings. Please try again.'
    let message = defaultMessage

    if (typeof e === 'object' && e !== null) {
      // Assuming e might have a 'data' object with a 'message' string, or 'e' itself has a 'message' string.
      // This is a common pattern for API error responses.
      const errorWithData = e as {
        data?: { message?: string }
        message?: string
      }
      message =
        errorWithData.data?.message || errorWithData.message || defaultMessage
    } else if (e instanceof Error) {
      // Fallback if e is an Error instance but not fitting the object structure above
      // (e.g., a basic Error without a 'data' property).
      message = e.message || defaultMessage
    }
    // If 'e' is a string or other primitive, it won't be handled by the above,
    // 'message' will remain 'defaultMessage'.

    error.value = message
    $q.notify({
      type: 'negative',
      message: error.value,
      icon: 'error',
    })
  } finally {
    saving.value = false
  }
}

// --- Watchers ---
watch(
  () => props.modelValue,
  (newValue) => {
    if (newValue && props.appLink) {
      // Reset state when dialog opens
      apiKey.value = '' // Clear previous input
      initialApiKey.value = ''
      showApiKey.value = false
      saving.value = false
      loading.value = false // Set to true if loading existing settings
      error.value = undefined

      // TODO: Future enhancement - Load existing settings
      // loading.value = true;
      // try {
      //   const existingSettings = await $fetch(`/api/user-settings/${props.appLink.id}`);
      //   if (props.appLink.type === 'vikunja' && existingSettings?.api_key) {
      //     apiKey.value = existingSettings.api_key;
      //     initialApiKey.value = existingSettings.api_key;
      //   }
      // } catch (loadErr) {
      //   console.warn(`Could not load existing settings for ${props.appLink.id}:`, loadErr);
      //   // Don't block opening the dialog, just log the warning
      // } finally {
      //   loading.value = false;
      // }
    }
  }
)

// Watch the appLink prop itself in case it changes while dialog is open (unlikely but safe)
watch(
  () => props.appLink,
  (newAppLink) => {
    if (props.modelValue && newAppLink) {
      // Reset state if the app context changes
      apiKey.value = ''
      initialApiKey.value = ''
      showApiKey.value = false
      saving.value = false
      loading.value = false
      error.value = undefined
      // Potentially re-trigger loading existing settings here if implemented
    }
  }
)
</script>

<style scoped>
/* Add any specific styles for the dialog here */
</style>
