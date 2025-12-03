<template>
  <div class="create-deployment-page max-w-3xl mx-auto">
    <!-- Header -->
    <div class="mb-6">
      <div class="flex items-center gap-3 mb-2">
        <router-link to="/deployments" class="text-gray-400 hover:text-gray-600">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </router-link>
        <h1 class="text-2xl font-bold text-gray-900">Create Deployment</h1>
      </div>
      <p class="text-gray-500">Register a new prompt deployment with locked-in model configuration.</p>
    </div>

    <!-- Form -->
    <form @submit.prevent="createDeployment" class="space-y-6">
      <!-- Basic Info -->
      <div class="card p-6">
        <h2 class="text-lg font-medium mb-4">Basic Information</h2>

        <div class="space-y-4">
          <div>
            <label class="label">
              <span class="label-text">Name *</span>
            </label>
            <input
              v-model="form.name"
              type="text"
              class="input"
              placeholder="my-prompt-name"
              pattern="[a-z0-9][a-z0-9-]*[a-z0-9]|[a-z0-9]"
              required
            />
            <p class="text-xs text-gray-500 mt-1">
              Lowercase alphanumeric with hyphens (e.g., customer-support-v2)
            </p>
          </div>

          <div>
            <label class="label">
              <span class="label-text">Description *</span>
            </label>
            <textarea
              v-model="form.description"
              class="textarea"
              rows="2"
              placeholder="Brief description of what this prompt does..."
              maxlength="500"
              required
            ></textarea>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="label">
                <span class="label-text">Category</span>
              </label>
              <input
                v-model="form.category"
                type="text"
                class="input"
                placeholder="general"
              />
            </div>
            <div>
              <label class="label">
                <span class="label-text">Author</span>
              </label>
              <input
                v-model="form.author"
                type="text"
                class="input"
                placeholder="Your name"
              />
            </div>
          </div>

          <div>
            <label class="label">
              <span class="label-text">Tags</span>
            </label>
            <input
              v-model="tagsInput"
              type="text"
              class="input"
              placeholder="Comma-separated tags (e.g., support, chatbot, v2)"
            />
          </div>
        </div>
      </div>

      <!-- Prompt Selection -->
      <div class="card p-6">
        <h2 class="text-lg font-medium mb-4">Select Prompt</h2>

        <div class="space-y-4">
          <div>
            <label class="label">
              <span class="label-text">Prompt *</span>
            </label>
            <select
              v-model="selectedPromptId"
              @change="loadSelectedPrompt"
              class="select"
              required
            >
              <option value="">-- Select a prompt --</option>
              <option v-for="p in savedPrompts" :key="p.id" :value="p.id">
                {{ p.name }} (v{{ p.version }})
              </option>
            </select>
            <p class="text-xs text-gray-500 mt-1">
              <router-link to="/prompts/studio" class="text-blue-600 hover:underline">
                Create a new prompt in the Studio
              </router-link>
              to deploy it.
            </p>
          </div>

          <div v-if="selectedPrompt" class="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <div class="flex items-center justify-between mb-3">
              <span class="font-medium text-blue-900">{{ selectedPrompt.name }}</span>
              <div class="flex items-center gap-2">
                <span class="badge bg-blue-100 text-blue-800">v{{ selectedPrompt.version }}</span>
                <router-link
                  :to="`/prompts/studio/${selectedPrompt.id}`"
                  class="text-xs text-blue-600 hover:underline"
                >
                  Edit
                </router-link>
              </div>
            </div>
            <pre class="text-sm text-blue-800 font-mono whitespace-pre-wrap bg-white rounded p-3 max-h-48 overflow-y-auto">{{ selectedPrompt.content }}</pre>
            <div v-if="selectedPrompt.goal" class="mt-3 text-sm">
              <span class="font-medium text-blue-700">Goal:</span>
              <span class="text-blue-600 ml-1">{{ selectedPrompt.goal }}</span>
            </div>
            <div v-if="selectedPrompt.variables?.length" class="mt-2 text-sm">
              <span class="font-medium text-purple-700">Variables:</span>
              <span class="text-purple-600 ml-1">{{ selectedPrompt.variables.join(', ') }}</span>
            </div>
          </div>

          <div v-if="!selectedPromptId" class="bg-gray-50 rounded-lg p-6 text-center">
            <svg class="w-12 h-12 mx-auto mb-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
            <p class="text-gray-600 mb-2">Select a prompt to deploy</p>
            <p class="text-sm text-gray-500">
              All prompts must be created in the
              <router-link to="/prompts/studio" class="text-blue-600 hover:underline">Prompt Studio</router-link>
              first.
            </p>
          </div>
        </div>
      </div>

      <!-- Model Configuration -->
      <div class="card p-6">
        <h2 class="text-lg font-medium mb-4">Model Configuration</h2>

        <div class="space-y-4">
          <div>
            <label class="label">
              <span class="label-text">Model *</span>
            </label>
            <select v-model="form.model_id" class="select" required>
              <option value="">Select a model...</option>
              <option v-for="model in availableModels" :key="model" :value="model">
                {{ model }}
              </option>
            </select>
          </div>

          <div class="grid grid-cols-3 gap-4">
            <div>
              <label class="label">
                <span class="label-text">Temperature</span>
              </label>
              <input
                v-model.number="form.temperature"
                type="number"
                class="input"
                min="0"
                max="2"
                step="0.1"
              />
            </div>
            <div>
              <label class="label">
                <span class="label-text">Max Tokens</span>
              </label>
              <input
                v-model.number="form.max_tokens"
                type="number"
                class="input"
                min="1"
                max="128000"
              />
            </div>
            <div>
              <label class="label">
                <span class="label-text">Top P</span>
              </label>
              <input
                v-model.number="form.top_p"
                type="number"
                class="input"
                min="0"
                max="1"
                step="0.1"
              />
            </div>
          </div>

          <div>
            <label class="label">
              <span class="label-text">Fallback Models</span>
            </label>
            <input
              v-model="fallbackModelsInput"
              type="text"
              class="input"
              placeholder="Comma-separated model IDs for fallback (e.g., gpt-4o-mini, gpt-3.5-turbo)"
            />
          </div>
        </div>
      </div>

      <!-- Error Message -->
      <div v-if="error" class="card variant-ghost-error p-4">
        <p class="text-error-500">{{ error }}</p>
      </div>

      <!-- Actions -->
      <div class="flex gap-4 justify-end">
        <router-link to="/deployments" class="btn variant-ghost">Cancel</router-link>
        <button type="submit" class="btn variant-filled-primary" :disabled="loading || !selectedPromptId">
          <span v-if="loading">Creating...</span>
          <span v-else>Create Deployment</span>
        </button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useDeploymentsStore } from '@/stores/deployments'
import { promptApi } from '@/services/api'
import { storeToRefs } from 'pinia'
import type { RegisterDeploymentRequest, Prompt } from '@/types'

const router = useRouter()
const store = useDeploymentsStore()
const { loading, error } = storeToRefs(store)

const savedPrompts = ref<Prompt[]>([])
const selectedPromptId = ref('')
const availableModels = ref<string[]>([])

const form = reactive<RegisterDeploymentRequest>({
  name: '',
  description: '',
  content: '',
  model_id: 'gpt-4o',
  goal: '',
  temperature: 0.7,
  max_tokens: 1000,
  top_p: 1.0,
  tags: [],
  category: 'general',
  author: ''
})

const tagsInput = ref('')
const fallbackModelsInput = ref('')

const selectedPrompt = computed(() => {
  if (!selectedPromptId.value) return null
  return savedPrompts.value.find(p => p.id === selectedPromptId.value) || null
})

onMounted(async () => {
  // Load saved prompts
  try {
    savedPrompts.value = await promptApi.list()
  } catch (e) {
    console.error('Failed to load prompts:', e)
  }

  // Load available models
  try {
    availableModels.value = await promptApi.getAvailableModels()
  } catch (e) {
    availableModels.value = [
      'gpt-4o',
      'gpt-4o-mini',
      'gpt-4-turbo',
      'gpt-3.5-turbo',
      'claude-3-5-sonnet-20241022',
      'claude-3-opus-20240229',
      'claude-3-sonnet-20240229',
      'claude-3-haiku-20240307',
      'groq/llama3-70b-8192',
      'groq/mixtral-8x7b-32768'
    ]
  }
})

function loadSelectedPrompt() {
  if (selectedPrompt.value) {
    // Auto-fill some fields from the prompt
    if (!form.name) {
      // Convert prompt name to deployment-friendly format
      form.name = selectedPrompt.value.name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
    }
    if (!form.description) {
      form.description = selectedPrompt.value.description || `Deployment of ${selectedPrompt.value.name}`
    }
    form.content = selectedPrompt.value.content
    form.goal = selectedPrompt.value.goal || ''
    if (selectedPrompt.value.category) {
      form.category = selectedPrompt.value.category
    }
    if (selectedPrompt.value.author) {
      form.author = selectedPrompt.value.author
    }
    if (selectedPrompt.value.tags?.length) {
      tagsInput.value = selectedPrompt.value.tags.join(', ')
    }
  }
}

async function createDeployment() {
  // Require a selected prompt
  if (!selectedPromptId.value || !selectedPrompt.value) {
    store.error = 'Please select a prompt to deploy'
    return
  }

  // Use the selected prompt's content and goal
  form.content = selectedPrompt.value.content
  form.goal = selectedPrompt.value.goal || ''

  // Parse tags
  form.tags = tagsInput.value
    .split(',')
    .map(t => t.trim().toLowerCase())
    .filter(t => t.length > 0)

  // Parse fallback models
  form.fallback_models = fallbackModelsInput.value
    .split(',')
    .map(m => m.trim())
    .filter(m => m.length > 0)

  try {
    const deployment = await store.createDeployment(form)
    router.push(`/deployments/${deployment.name}`)
  } catch (e) {
    // Error is handled by store
  }
}
</script>

<style scoped>
.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
