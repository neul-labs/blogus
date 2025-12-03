<template>
  <div class="max-w-4xl mx-auto space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-gray-900 mb-2">Analyze Prompt</h1>
      <p class="text-gray-600">
        Analyze your prompts for effectiveness and goal alignment with advanced AI models.
      </p>
    </div>

    <!-- Input Form -->
    <div class="card p-6">
      <form @submit.prevent="analyzePrompt" class="space-y-4">
        <!-- Prompt Selection -->
        <div>
          <label class="label">
            <span class="label-text">Select Prompt *</span>
          </label>
          <select
            v-model="selectedPromptId"
            @change="loadSelectedPrompt"
            class="select"
            required
          >
            <option value="">-- Select a prompt to analyze --</option>
            <option v-for="p in savedPrompts" :key="p.id" :value="p.id">
              {{ p.name }} (v{{ p.version }})
            </option>
          </select>
          <p class="text-xs text-gray-500 mt-1">
            <router-link to="/prompts/studio" class="text-blue-600 hover:underline">
              Create a new prompt in the Studio
            </router-link>
            to analyze it here.
          </p>
        </div>

        <!-- Selected Prompt Display -->
        <div v-if="selectedPrompt" class="bg-gray-50 rounded-lg p-4 border">
          <div class="flex items-center justify-between mb-3">
            <span class="font-medium text-gray-900">{{ selectedPrompt.name }}</span>
            <div class="flex items-center gap-2">
              <span class="badge bg-gray-200 text-gray-700">v{{ selectedPrompt.version }}</span>
              <router-link
                :to="`/prompts/studio/${selectedPrompt.id}`"
                class="text-xs text-blue-600 hover:underline"
              >
                Edit
              </router-link>
            </div>
          </div>
          <pre class="text-sm text-gray-700 font-mono whitespace-pre-wrap bg-white rounded p-3 max-h-48 overflow-y-auto">{{ selectedPrompt.content }}</pre>
          <div v-if="selectedPrompt.goal" class="mt-3 text-sm">
            <span class="font-medium text-gray-700">Goal:</span>
            <span class="text-gray-600 ml-1">{{ selectedPrompt.goal }}</span>
          </div>
          <div v-if="selectedPrompt.variables?.length" class="mt-2 text-sm">
            <span class="font-medium text-purple-700">Variables:</span>
            <span class="text-purple-600 ml-1">{{ selectedPrompt.variables.join(', ') }}</span>
          </div>
        </div>

        <div>
          <label class="label">
            <span class="label-text">Judge Model</span>
          </label>
          <select v-model="judgeModel" class="select">
            <option v-for="model in availableModels" :key="model" :value="model">
              {{ model }}
            </option>
          </select>
        </div>

        <div class="flex justify-end">
          <button
            type="submit"
            class="btn variant-filled-primary"
            :disabled="loading || !selectedPromptId"
          >
            <svg v-if="loading" class="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ loading ? 'Analyzing...' : 'Analyze Prompt' }}
          </button>
        </div>
      </form>
    </div>

    <!-- Error Message -->
    <div v-if="error" class="card bg-red-50 border-red-200 p-4">
      <p class="text-red-600">{{ error }}</p>
    </div>

    <!-- Results -->
    <div v-if="result" class="space-y-6">
      <!-- Overview -->
      <div class="card p-6">
        <h2 class="text-lg font-semibold mb-4">Analysis Overview</h2>

        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div class="text-center p-4 bg-gray-50 rounded-lg">
            <div class="text-2xl font-bold" :class="getScoreColor(result.analysis.goal_alignment)">
              {{ (result.analysis.goal_alignment * 100).toFixed(0) }}%
            </div>
            <div class="text-sm text-gray-600">Goal Alignment</div>
          </div>
          <div class="text-center p-4 bg-gray-50 rounded-lg">
            <div class="text-2xl font-bold" :class="getScoreColor(result.analysis.effectiveness)">
              {{ (result.analysis.effectiveness * 100).toFixed(0) }}%
            </div>
            <div class="text-sm text-gray-600">Effectiveness</div>
          </div>
          <div class="text-center p-4 bg-gray-50 rounded-lg">
            <div class="text-2xl font-bold text-blue-600">
              {{ result.fragments.length }}
            </div>
            <div class="text-sm text-gray-600">Fragments</div>
          </div>
          <div class="text-center p-4 bg-gray-50 rounded-lg">
            <div class="text-2xl font-bold text-purple-600">
              {{ result.analysis.suggestions.length }}
            </div>
            <div class="text-sm text-gray-600">Suggestions</div>
          </div>
        </div>

        <div v-if="result.analysis.inferred_goal" class="p-4 bg-blue-50 rounded-lg">
          <p class="text-sm text-blue-800">
            <strong>Inferred Goal:</strong> {{ result.analysis.inferred_goal }}
          </p>
        </div>
      </div>

      <!-- Suggestions -->
      <div v-if="result.analysis.suggestions.length > 0" class="card p-6">
        <h2 class="text-lg font-semibold mb-4">Improvement Suggestions</h2>
        <ul class="space-y-3">
          <li
            v-for="(suggestion, index) in result.analysis.suggestions"
            :key="index"
            class="flex gap-3 p-3 bg-yellow-50 rounded-lg"
          >
            <svg class="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
            </svg>
            <span class="text-gray-700">{{ suggestion }}</span>
          </li>
        </ul>
      </div>

      <!-- Fragment Analysis -->
      <div v-if="result.fragments.length > 0" class="card p-6">
        <h2 class="text-lg font-semibold mb-4">Fragment Analysis</h2>
        <div class="space-y-4">
          <div
            v-for="(fragment, index) in result.fragments"
            :key="index"
            class="border rounded-lg p-4"
          >
            <div class="flex items-start justify-between gap-4 mb-2">
              <code class="text-sm bg-gray-100 px-2 py-1 rounded flex-1">{{ fragment.text }}</code>
              <span class="badge" :class="getFragmentTypeBadge(fragment.fragment_type)">
                {{ fragment.fragment_type }}
              </span>
            </div>
            <div class="flex items-center gap-4 text-sm">
              <span class="text-gray-600">
                Alignment:
                <span :class="getScoreColor(fragment.goal_alignment)" class="font-medium">
                  {{ (fragment.goal_alignment * 100).toFixed(0) }}%
                </span>
              </span>
            </div>
            <p v-if="fragment.improvement_suggestion" class="mt-2 text-sm text-gray-600 italic">
              {{ fragment.improvement_suggestion }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { promptApi } from '@/services/api'
import type { AnalyzePromptResponse, Prompt } from '@/types'

const loading = ref(false)
const error = ref('')
const result = ref<AnalyzePromptResponse | null>(null)
const savedPrompts = ref<Prompt[]>([])
const selectedPromptId = ref('')
const judgeModel = ref('gpt-4o')
const availableModels = ref<string[]>([])

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
      'claude-3-5-sonnet-20241022',
      'claude-3-haiku-20240307'
    ]
  }

  // Check for prompt ID passed from another page
  const savedData = sessionStorage.getItem('analyzePrompt')
  if (savedData) {
    try {
      const { id } = JSON.parse(savedData)
      if (id) {
        selectedPromptId.value = id
      }
      sessionStorage.removeItem('analyzePrompt')
    } catch (e) {
      // Ignore
    }
  }
})

function loadSelectedPrompt() {
  // Clear previous results when selection changes
  result.value = null
  error.value = ''
}

async function analyzePrompt() {
  if (!selectedPromptId.value) {
    error.value = 'Please select a prompt to analyze'
    return
  }

  loading.value = true
  error.value = ''
  result.value = null

  try {
    result.value = await promptApi.analyze({
      prompt_id: selectedPromptId.value,
      judge_model: judgeModel.value
    })
  } catch (e: any) {
    error.value = e.response?.data?.detail || e.message || 'Failed to analyze prompt'
  } finally {
    loading.value = false
  }
}

function getScoreColor(score: number): string {
  if (score >= 0.8) return 'text-green-600'
  if (score >= 0.6) return 'text-yellow-600'
  return 'text-red-600'
}

function getFragmentTypeBadge(type: string): string {
  const badges: Record<string, string> = {
    instruction: 'bg-blue-100 text-blue-800',
    context: 'bg-purple-100 text-purple-800',
    example: 'bg-green-100 text-green-800',
    constraint: 'bg-orange-100 text-orange-800',
    output_format: 'bg-cyan-100 text-cyan-800'
  }
  return badges[type] || 'bg-gray-100 text-gray-800'
}
</script>
