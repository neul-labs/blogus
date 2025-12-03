<template>
  <div class="max-w-7xl mx-auto space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 mb-2">Prompt Studio</h1>
        <p class="text-gray-600">
          Create, edit, and test prompts with Git-native versioning.
        </p>
      </div>
      <div v-if="currentPrompt" class="text-right">
        <div class="text-sm text-gray-500">Editing Prompt</div>
        <div class="flex items-center gap-2 justify-end">
          <span class="font-semibold text-gray-900">{{ currentPrompt.name }}</span>
          <span
            v-if="currentPrompt.is_dirty"
            class="badge bg-yellow-100 text-yellow-800 text-xs"
            title="Uncommitted changes"
          >
            Modified
          </span>
        </div>
        <div class="text-xs text-gray-500">
          Version {{ currentPrompt.version }}
          <span v-if="currentPrompt.commit_sha" class="ml-1 font-mono">
            ({{ currentPrompt.commit_sha.slice(0, 7) }})
          </span>
        </div>
      </div>
    </div>

    <div class="grid lg:grid-cols-3 gap-6">
      <!-- Input Form -->
      <div class="lg:col-span-1 space-y-4">
        <!-- Prompt Selector -->
        <div class="card p-4">
          <div class="flex items-center justify-between mb-3">
            <h3 class="font-medium text-gray-900">Load Prompt</h3>
            <button
              @click="newPrompt"
              class="btn btn-xs variant-ghost"
              title="Start fresh"
            >
              New
            </button>
          </div>
          <select
            v-model="selectedPromptName"
            @change="loadPrompt"
            class="select w-full"
          >
            <option value="">-- Select .prompt file --</option>
            <option v-for="p in savedPrompts" :key="p.name" :value="p.name">
              {{ p.name }} (v{{ p.version }})
              <template v-if="p.is_dirty"> *</template>
            </option>
          </select>
        </div>

        <!-- Version History Panel -->
        <div v-if="currentPrompt && versionHistory.length > 0" class="card p-4">
          <div class="flex items-center justify-between mb-3">
            <h3 class="font-medium text-gray-900">Version History</h3>
            <button
              @click="loadVersionHistory"
              class="btn btn-xs variant-ghost"
              title="Refresh history"
            >
              Refresh
            </button>
          </div>
          <div class="space-y-2 max-h-48 overflow-y-auto">
            <button
              v-for="ver in versionHistory"
              :key="ver.version"
              @click="loadVersion(ver.version)"
              class="w-full text-left p-2 rounded hover:bg-gray-100 transition-colors"
              :class="{
                'bg-blue-50 border-l-2 border-blue-500': viewingVersion === ver.version
              }"
            >
              <div class="flex items-center justify-between">
                <span class="font-medium text-sm">v{{ ver.version }}</span>
                <span class="text-xs text-gray-500 font-mono">
                  {{ ver.commit_sha?.slice(0, 7) || 'local' }}
                </span>
              </div>
              <div class="text-xs text-gray-500 truncate">
                {{ ver.message || 'No message' }}
              </div>
              <div class="text-xs text-gray-400">
                {{ formatDate(ver.timestamp) }}
                <span v-if="ver.author"> by {{ ver.author }}</span>
              </div>
            </button>
          </div>
          <div v-if="viewingVersion && viewingVersion !== currentPrompt.version" class="mt-2 pt-2 border-t">
            <button
              @click="restoreCurrentVersion"
              class="btn btn-xs variant-ghost w-full"
            >
              Back to latest (v{{ currentPrompt.version }})
            </button>
          </div>
        </div>

        <!-- Configuration Form -->
        <div class="card p-6">
          <h2 class="text-lg font-semibold mb-4">Configuration</h2>
          <form @submit.prevent="executeAndCompare" class="space-y-4">
            <!-- Name (for saving) -->
            <div>
              <label class="label">
                <span class="label-text">Name</span>
              </label>
              <input
                v-model="form.name"
                type="text"
                class="input"
                placeholder="my-prompt"
                pattern="[a-z0-9-]+"
                title="Lowercase letters, numbers, and hyphens only"
              />
              <p class="text-xs text-gray-500 mt-1">Will be saved as {{ form.name || 'name' }}.prompt</p>
            </div>

            <div>
              <label class="label">
                <span class="label-text">Prompt Text *</span>
              </label>
              <textarea
                v-model="form.prompt_text"
                class="textarea font-mono"
                rows="8"
                placeholder="Enter your prompt here... Use {{variable}} for templates"
                required
              ></textarea>
              <p v-if="detectedVariables.length > 0" class="text-xs text-gray-500 mt-1">
                Variables: {{ detectedVariables.join(', ') }}
              </p>
            </div>

            <!-- Variable inputs -->
            <div v-if="detectedVariables.length > 0" class="space-y-2">
              <label class="label">
                <span class="label-text">Variable Values</span>
              </label>
              <div v-for="variable in detectedVariables" :key="variable" class="flex items-center gap-2">
                <span class="text-sm text-gray-600 w-24">{{ variable }}:</span>
                <input
                  v-model="form.variables[variable]"
                  type="text"
                  class="input input-sm flex-1"
                  :placeholder="`Value for ${variable}`"
                />
              </div>
            </div>

            <div>
              <label class="label">
                <span class="label-text">Goal (optional)</span>
              </label>
              <input
                v-model="form.goal"
                type="text"
                class="input"
                placeholder="What should this prompt achieve?"
              />
            </div>

            <div>
              <label class="label">
                <span class="label-text">Description (optional)</span>
              </label>
              <textarea
                v-model="form.description"
                class="textarea"
                rows="2"
                placeholder="Brief description of this prompt"
              ></textarea>
            </div>

            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="label">
                  <span class="label-text">Category</span>
                </label>
                <input
                  v-model="form.category"
                  type="text"
                  class="input input-sm"
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
                  class="input input-sm"
                  placeholder="your name"
                />
              </div>
            </div>

            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="label">
                  <span class="label-text">Model</span>
                </label>
                <select v-model="form.model_id" class="select select-sm w-full">
                  <option v-for="model in availableModels" :key="model" :value="model">
                    {{ model }}
                  </option>
                </select>
              </div>
              <div>
                <label class="label">
                  <span class="label-text">Temperature</span>
                </label>
                <input
                  v-model.number="form.temperature"
                  type="number"
                  min="0"
                  max="2"
                  step="0.1"
                  class="input input-sm"
                />
              </div>
            </div>

            <div>
              <label class="label">
                <span class="label-text">Execution Models *</span>
              </label>
              <div class="space-y-2 max-h-48 overflow-y-auto border rounded-lg p-3">
                <label v-for="model in availableModels" :key="model" class="flex items-center gap-2 cursor-pointer hover:bg-gray-50 p-1 rounded">
                  <input
                    type="checkbox"
                    :value="model"
                    v-model="form.models"
                    class="checkbox checkbox-sm"
                  />
                  <span class="text-sm">{{ model }}</span>
                </label>
              </div>
              <p class="text-xs text-gray-500 mt-1">{{ form.models.length }} model(s) selected for execution</p>
            </div>

            <div>
              <label class="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  v-model="form.include_llm_assessment"
                  class="checkbox checkbox-sm"
                />
                <span class="text-sm">Include LLM-as-Judge Assessment</span>
              </label>
            </div>

            <!-- Action Buttons -->
            <div class="flex flex-wrap gap-2">
              <button
                type="submit"
                class="btn variant-filled-primary flex-1"
                :disabled="loading || !form.prompt_text.trim() || form.models.length < 1"
              >
                <svg v-if="loading" class="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                {{ loading ? 'Executing...' : (form.models.length > 1 ? 'Execute & Compare' : 'Execute') }}
              </button>
              <button
                type="button"
                @click="savePrompt"
                class="btn variant-filled-secondary"
                :disabled="saving || !form.prompt_text.trim() || !form.name.trim()"
              >
                {{ saving ? 'Saving...' : (currentPrompt ? 'Update' : 'Save') }}
              </button>
              <button
                v-if="currentPrompt"
                type="button"
                @click="saveAsNew"
                class="btn variant-ghost"
                :disabled="saving || !form.prompt_text.trim()"
              >
                Save As New
              </button>
            </div>

            <!-- Save Status -->
            <div v-if="saveMessage" class="text-sm" :class="saveError ? 'text-red-600' : 'text-green-600'">
              {{ saveMessage }}
            </div>
          </form>
        </div>
      </div>

      <!-- Results Panel -->
      <div class="lg:col-span-2 space-y-6">
        <!-- Error Message -->
        <div v-if="error" class="card p-4 bg-red-50">
          <p class="text-red-600">{{ error }}</p>
        </div>

        <!-- No Result Yet -->
        <div v-else-if="!result" class="card p-12 text-center text-gray-500">
          <svg class="w-16 h-16 mx-auto mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
          </svg>
          <p class="text-lg">Select models and execute to see results</p>
          <p class="text-sm mt-2">Select 2+ models for comparison analysis</p>
        </div>

        <!-- Results -->
        <template v-else>
          <!-- Summary Card (only for multi-model) -->
          <div v-if="result.comparison" class="card p-6">
            <h3 class="text-lg font-semibold mb-4">Comparison Summary</h3>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div class="text-center p-3 bg-gray-50 rounded-lg">
                <div class="text-2xl font-bold text-gray-900">{{ result.comparison.summary.total_models }}</div>
                <div class="text-sm text-gray-600">Models</div>
              </div>
              <div class="text-center p-3 bg-green-50 rounded-lg">
                <div class="text-2xl font-bold text-green-700">{{ result.comparison.summary.best_performing_model || 'N/A' }}</div>
                <div class="text-sm text-gray-600">Best Model</div>
              </div>
              <div class="text-center p-3 bg-blue-50 rounded-lg">
                <div class="text-2xl font-bold text-blue-700">{{ result.comparison.summary.fastest_model || 'N/A' }}</div>
                <div class="text-sm text-gray-600">Fastest</div>
              </div>
              <div class="text-center p-3 bg-purple-50 rounded-lg">
                <div class="text-2xl font-bold text-purple-700">{{ (result.comparison.summary.average_agreement_score * 100).toFixed(1) }}%</div>
                <div class="text-sm text-gray-600">Avg Agreement</div>
              </div>
            </div>
            <div class="mt-4 text-sm text-gray-500 text-right">
              Total duration: {{ result.total_duration_ms.toFixed(0) }}ms
            </div>
          </div>

          <!-- Model Outputs -->
          <div class="card p-6">
            <h3 class="text-lg font-semibold mb-4">Model Outputs</h3>
            <div class="grid md:grid-cols-2 gap-4">
              <div
                v-for="execution in result.executions"
                :key="execution.id"
                class="border rounded-lg p-4"
                :class="{ 'border-green-500 bg-green-50': result.comparison && execution.model === result.comparison.summary.best_performing_model }"
              >
                <div class="flex items-center justify-between mb-3">
                  <span class="font-medium text-gray-900">{{ execution.model }}</span>
                  <div class="flex items-center gap-2">
                    <span v-if="execution.success" class="badge bg-green-100 text-green-800">{{ execution.latency_ms.toFixed(0) }}ms</span>
                    <span v-else class="badge bg-red-100 text-red-800">Failed</span>
                    <span v-if="result.comparison?.model_metrics[execution.model]?.llm_evaluation_score" class="badge bg-blue-100 text-blue-800">
                      Score: {{ result.comparison.model_metrics[execution.model].llm_evaluation_score.toFixed(1) }}
                    </span>
                  </div>
                </div>
                <div class="bg-white rounded p-3 max-h-64 overflow-y-auto">
                  <pre class="whitespace-pre-wrap text-sm text-gray-700">{{ execution.output }}</pre>
                </div>
                <div class="mt-2 flex gap-2">
                  <button @click="copyToClipboard(execution.output)" class="btn btn-xs variant-ghost">
                    Copy
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Semantic Similarity Matrix (only for multi-model) -->
          <div v-if="result.comparison?.semantic_similarities?.length" class="card p-6">
            <h3 class="text-lg font-semibold mb-4">Semantic Similarity</h3>
            <div class="overflow-x-auto">
              <table class="table table-sm">
                <thead>
                  <tr>
                    <th>Model A</th>
                    <th>Model B</th>
                    <th>Similarity</th>
                    <th>Visual</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(sim, index) in result.comparison.semantic_similarities" :key="index">
                    <td>{{ sim.model_a }}</td>
                    <td>{{ sim.model_b }}</td>
                    <td class="font-mono">{{ (sim.similarity_score * 100).toFixed(1) }}%</td>
                    <td>
                      <div class="w-24 bg-gray-200 rounded-full h-2">
                        <div
                          class="h-2 rounded-full"
                          :class="getSimilarityColor(sim.similarity_score)"
                          :style="{ width: `${sim.similarity_score * 100}%` }"
                        ></div>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- LLM Assessment -->
          <div v-if="result.comparison?.llm_assessment" class="card p-6">
            <h3 class="text-lg font-semibold mb-4">LLM Assessment</h3>
            <div class="mb-4 p-4 bg-blue-50 rounded-lg">
              <p class="font-medium text-blue-900">Recommendation</p>
              <p class="text-blue-800">{{ result.comparison.llm_assessment.recommendation }}</p>
            </div>

            <div v-if="result.comparison.llm_assessment.key_differences.length > 0" class="mb-4">
              <p class="font-medium text-gray-700 mb-2">Key Differences:</p>
              <ul class="list-disc list-inside text-sm text-gray-600">
                <li v-for="(diff, index) in result.comparison.llm_assessment.key_differences" :key="index">
                  {{ diff }}
                </li>
              </ul>
            </div>

            <div class="space-y-4">
              <div v-for="evaluation in result.comparison.llm_assessment.evaluations" :key="evaluation.model" class="border rounded-lg p-4">
                <div class="flex items-center justify-between mb-3">
                  <span class="font-medium">{{ evaluation.model }}</span>
                  <span class="badge bg-gray-100 text-gray-800">Overall: {{ evaluation.overall_score.toFixed(1) }}/10</span>
                </div>

                <div class="grid grid-cols-4 gap-2 mb-3">
                  <div v-for="(score, criterion) in evaluation.scores" :key="criterion" class="text-center p-2 bg-gray-50 rounded">
                    <div class="text-lg font-semibold">{{ score }}</div>
                    <div class="text-xs text-gray-500 capitalize">{{ String(criterion).replace('_', ' ') }}</div>
                  </div>
                </div>

                <div class="grid md:grid-cols-2 gap-4 text-sm">
                  <div v-if="evaluation.strengths.length > 0">
                    <p class="font-medium text-green-700 mb-1">Strengths:</p>
                    <ul class="list-disc list-inside text-gray-600">
                      <li v-for="(s, i) in evaluation.strengths" :key="i">{{ s }}</li>
                    </ul>
                  </div>
                  <div v-if="evaluation.weaknesses.length > 0">
                    <p class="font-medium text-red-700 mb-1">Weaknesses:</p>
                    <ul class="list-disc list-inside text-gray-600">
                      <li v-for="(w, i) in evaluation.weaknesses" :key="i">{{ w }}</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { promptApi, promptFilesApi } from '@/services/api'
import type { MultiModelCompareResponse, PromptFile, PromptFileSummary, PromptFileVersion } from '@/types'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const saving = ref(false)
const error = ref('')
const saveMessage = ref('')
const saveError = ref(false)
const result = ref<MultiModelCompareResponse | null>(null)
const availableModels = ref<string[]>([])
const savedPrompts = ref<PromptFileSummary[]>([])
const currentPrompt = ref<PromptFile | null>(null)
const selectedPromptName = ref('')
const versionHistory = ref<PromptFileVersion[]>([])
const viewingVersion = ref<number | null>(null)

const form = reactive({
  name: '',
  prompt_text: '',
  goal: '',
  description: '',
  category: 'general',
  author: '',
  model_id: 'gpt-4o',
  temperature: 0.7,
  models: [] as string[],
  variables: {} as Record<string, string>,
  include_llm_assessment: true
})

// Detect template variables
const detectedVariables = computed(() => {
  const matches = form.prompt_text.match(/\{\{\s*(\w+)\s*\}\}/g) || []
  return [...new Set(matches.map(m => m.replace(/\{\{\s*|\s*\}\}/g, '')))]
})

// Watch for route changes to load prompt by name
watch(() => route.params.name, async (newName) => {
  if (newName && typeof newName === 'string') {
    selectedPromptName.value = newName
    await loadPromptByName(newName)
  }
}, { immediate: true })

onMounted(async () => {
  // Load available models
  try {
    availableModels.value = await promptApi.getAvailableModels()
    if (availableModels.value.length >= 2) {
      form.models = availableModels.value.slice(0, 2)
    }
  } catch (e) {
    availableModels.value = [
      'gpt-4o',
      'gpt-4o-mini',
      'gpt-4-turbo',
      'gpt-3.5-turbo',
      'claude-3-5-sonnet-20241022',
      'claude-3-opus-20240229',
      'claude-3-haiku-20240307',
      'groq/llama3-70b-8192',
      'groq/mixtral-8x7b-32768'
    ]
    form.models = ['gpt-4o', 'claude-3-5-sonnet-20241022']
  }

  // Load saved prompts list
  await loadPromptsList()

  // Check for prompt passed from another page via session storage
  const savedPromptData = sessionStorage.getItem('studioPrompt')
  if (savedPromptData && !route.params.name) {
    try {
      const { text, goal, name } = JSON.parse(savedPromptData)
      if (name) {
        selectedPromptName.value = name
        await loadPromptByName(name)
      } else {
        if (text) form.prompt_text = text
        if (goal) form.goal = goal
      }
      sessionStorage.removeItem('studioPrompt')
    } catch (e) {
      // Ignore parse errors
    }
  }
})

async function loadPromptsList() {
  try {
    savedPrompts.value = await promptFilesApi.list({ include_dirty: true })
  } catch (e) {
    console.error('Failed to load prompts list:', e)
    // Fall back to empty list
    savedPrompts.value = []
  }
}

async function loadPrompt() {
  if (!selectedPromptName.value) {
    newPrompt()
    return
  }
  await loadPromptByName(selectedPromptName.value)
}

async function loadPromptByName(name: string) {
  try {
    const prompt = await promptFilesApi.get(name)
    setPromptFromFile(prompt)
    await loadVersionHistory()
    viewingVersion.value = prompt.version
  } catch (e: any) {
    error.value = `Failed to load prompt: ${e.response?.data?.detail || e.message}`
    currentPrompt.value = null
  }
}

async function loadVersion(version: number) {
  if (!currentPrompt.value) return

  try {
    const prompt = await promptFilesApi.get(currentPrompt.value.name, version)
    // Only update content, keep other metadata from current prompt
    form.prompt_text = prompt.content
    viewingVersion.value = version
    result.value = null
    error.value = ''
  } catch (e: any) {
    error.value = `Failed to load version: ${e.response?.data?.detail || e.message}`
  }
}

async function restoreCurrentVersion() {
  if (currentPrompt.value) {
    form.prompt_text = currentPrompt.value.content
    viewingVersion.value = currentPrompt.value.version
  }
}

async function loadVersionHistory() {
  if (!currentPrompt.value) {
    versionHistory.value = []
    return
  }

  try {
    const historyResponse = await promptFilesApi.getHistory(currentPrompt.value.name, 20)
    versionHistory.value = historyResponse.versions
  } catch (e) {
    console.error('Failed to load version history:', e)
    versionHistory.value = []
  }
}

function setPromptFromFile(prompt: PromptFile) {
  currentPrompt.value = prompt
  form.name = prompt.name
  form.prompt_text = prompt.content
  form.goal = prompt.goal || ''
  form.description = prompt.description || ''
  form.category = prompt.category || 'general'
  form.author = prompt.author || ''
  form.model_id = prompt.model?.id || 'gpt-4o'
  form.temperature = prompt.model?.temperature || 0.7

  // Set up variables from prompt definition
  form.variables = {}
  for (const v of prompt.variables || []) {
    form.variables[v.name] = v.default || ''
  }

  result.value = null
  error.value = ''
  saveMessage.value = ''
}

function newPrompt() {
  currentPrompt.value = null
  selectedPromptName.value = ''
  versionHistory.value = []
  viewingVersion.value = null
  form.name = ''
  form.prompt_text = ''
  form.goal = ''
  form.description = ''
  form.category = 'general'
  form.author = ''
  form.model_id = 'gpt-4o'
  form.temperature = 0.7
  form.variables = {}
  result.value = null
  error.value = ''
  saveMessage.value = ''

  // Update URL to remove name
  if (route.params.name) {
    router.push('/prompts/studio')
  }
}

async function savePrompt() {
  if (!form.name.trim() || !form.prompt_text.trim()) {
    saveMessage.value = 'Name and prompt text are required'
    saveError.value = true
    return
  }

  // Validate name format
  const namePattern = /^[a-z0-9-]+$/
  if (!namePattern.test(form.name)) {
    saveMessage.value = 'Name must contain only lowercase letters, numbers, and hyphens'
    saveError.value = true
    return
  }

  saving.value = true
  saveMessage.value = ''
  saveError.value = false

  try {
    let savedPrompt: PromptFile

    // Build variables array from detected variables
    const variables = detectedVariables.value.map(name => ({
      name,
      description: '',
      required: true,
      default: form.variables[name] || undefined
    }))

    if (currentPrompt.value && currentPrompt.value.name === form.name) {
      // Update existing prompt
      savedPrompt = await promptFilesApi.update(currentPrompt.value.name, {
        content: form.prompt_text,
        description: form.description || undefined,
        goal: form.goal || undefined,
        category: form.category || undefined,
        model_id: form.model_id,
        temperature: form.temperature,
        variables
      })
      saveMessage.value = `Updated! ${savedPrompt.version > currentPrompt.value.version ? `New version: ${savedPrompt.version}` : ''}`
    } else {
      // Create new prompt
      savedPrompt = await promptFilesApi.create({
        name: form.name,
        content: form.prompt_text,
        description: form.description || undefined,
        goal: form.goal || undefined,
        category: form.category || undefined,
        author: form.author || undefined,
        model_id: form.model_id,
        temperature: form.temperature,
        variables
      })
      saveMessage.value = `Created! File: ${savedPrompt.file_path}`
    }

    currentPrompt.value = savedPrompt
    selectedPromptName.value = savedPrompt.name
    viewingVersion.value = savedPrompt.version
    await loadPromptsList()
    await loadVersionHistory()

    // Update URL with new name
    router.replace(`/prompts/studio/${savedPrompt.name}`)
  } catch (e: any) {
    saveMessage.value = e.response?.data?.detail || e.message || 'Failed to save'
    saveError.value = true
  } finally {
    saving.value = false
  }
}

async function saveAsNew() {
  // Clear current prompt to force creation of new one
  const tempPrompt = currentPrompt.value
  currentPrompt.value = null
  form.name = `${form.name}-copy`

  await savePrompt()

  // If save failed, restore the original prompt reference
  if (saveError.value && tempPrompt) {
    currentPrompt.value = tempPrompt
    form.name = tempPrompt.name
  }
}

async function executeAndCompare() {
  loading.value = true
  error.value = ''
  result.value = null

  try {
    if (form.models.length >= 2) {
      // Multi-model comparison
      const response = await promptApi.executeAndCompare({
        prompt_text: form.prompt_text,
        models: form.models,
        goal: form.goal || undefined,
        variables: Object.keys(form.variables).length > 0 ? form.variables : undefined,
        include_llm_assessment: form.include_llm_assessment
      })
      result.value = response
    } else {
      // Single model execution
      const response = await promptApi.executeMultiModel({
        prompt_text: form.prompt_text,
        models: form.models,
        variables: Object.keys(form.variables).length > 0 ? form.variables : undefined
      })
      // Cast to MultiModelCompareResponse format (without comparison data)
      result.value = response as unknown as MultiModelCompareResponse
    }
  } catch (e: any) {
    error.value = e.response?.data?.detail || e.message || 'Failed to execute'
  } finally {
    loading.value = false
  }
}

function formatDate(timestamp: string): string {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function getSimilarityColor(score: number): string {
  if (score >= 0.9) return 'bg-green-500'
  if (score >= 0.7) return 'bg-yellow-500'
  if (score >= 0.5) return 'bg-orange-500'
  return 'bg-red-500'
}

function copyToClipboard(text: string) {
  navigator.clipboard.writeText(text)
}
</script>
