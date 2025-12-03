<template>
  <div class="max-w-4xl mx-auto space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-gray-900 mb-2">Generate Tests</h1>
      <p class="text-gray-600">
        Automatically generate comprehensive test cases for your prompts.
      </p>
    </div>

    <!-- Input Form -->
    <div class="card p-6">
      <form @submit.prevent="generateTest" class="space-y-4">
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
            <option value="">-- Select a prompt --</option>
            <option v-for="p in savedPrompts" :key="p.id" :value="p.id">
              {{ p.name }} (v{{ p.version }})
            </option>
          </select>
          <p class="text-xs text-gray-500 mt-1">
            <router-link to="/prompts/studio" class="text-blue-600 hover:underline">
              Create a new prompt in the Studio
            </router-link>
            to generate tests for it.
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

        <div class="flex justify-end gap-3">
          <button
            type="submit"
            class="btn variant-filled-primary"
            :disabled="loading || !selectedPromptId"
          >
            <svg v-if="loading" class="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <svg v-else class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M7 2a1 1 0 00-.707 1.707L7 4.414v3.758a1 1 0 01-.293.707l-4 4C.817 14.769 2.156 18 4.828 18h10.343c2.673 0 4.012-3.231 2.122-5.121l-4-4A1 1 0 0113 8.172V4.414l.707-.707A1 1 0 0013 2H7zm2 6.172V4h2v4.172a3 3 0 00.879 2.12l1.027 1.028a4 4 0 00-2.171.102l-.47.156a4 4 0 01-2.53 0l-.563-.187a1.993 1.993 0 00-.306-.084l1.342-1.342A3 3 0 009 8.172z" clip-rule="evenodd"/>
            </svg>
            {{ loading ? 'Generating...' : 'Generate Test Case' }}
          </button>
        </div>
      </form>
    </div>

    <!-- Error Message -->
    <div v-if="error" class="card bg-red-50 border-red-200 p-4">
      <p class="text-red-600">{{ error }}</p>
    </div>

    <!-- Generated Test Cases -->
    <div v-if="testCases.length > 0" class="space-y-4">
      <div class="flex items-center justify-between">
        <h2 class="text-lg font-semibold">Generated Test Cases ({{ testCases.length }})</h2>
        <div class="flex gap-2">
          <button @click="exportTests" class="btn btn-sm variant-ghost">
            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
            </svg>
            Export JSON
          </button>
          <button @click="testCases = []" class="btn btn-sm variant-ghost-error">
            Clear All
          </button>
        </div>
      </div>

      <div
        v-for="(testCase, index) in testCases"
        :key="index"
        class="card p-6"
      >
        <div class="flex items-start justify-between mb-4">
          <h3 class="font-medium text-gray-900">Test Case #{{ index + 1 }}</h3>
          <div class="flex items-center gap-2">
            <span class="text-sm text-gray-600">Goal Relevance:</span>
            <span
              class="font-medium"
              :class="getScoreColor(testCase.goal_relevance)"
            >
              {{ (testCase.goal_relevance * 100).toFixed(0) }}%
            </span>
          </div>
        </div>

        <!-- Input Variables -->
        <div v-if="Object.keys(testCase.input_variables).length > 0" class="mb-4">
          <h4 class="text-sm font-medium text-gray-700 mb-2">Input Variables</h4>
          <div class="bg-gray-50 rounded-lg p-3">
            <div
              v-for="(value, key) in testCase.input_variables"
              :key="key"
              class="flex gap-2 text-sm"
            >
              <span class="font-mono text-blue-600">{{ key }}:</span>
              <span class="text-gray-700">{{ value }}</span>
            </div>
          </div>
        </div>

        <!-- Expected Output -->
        <div>
          <h4 class="text-sm font-medium text-gray-700 mb-2">Expected Output</h4>
          <div class="bg-gray-50 rounded-lg p-3">
            <pre class="whitespace-pre-wrap text-sm text-gray-700">{{ testCase.expected_output }}</pre>
          </div>
        </div>

        <div class="mt-4 flex gap-2">
          <button
            @click="copyTestCase(testCase)"
            class="btn btn-sm variant-ghost"
          >
            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/>
            </svg>
            Copy
          </button>
          <button
            @click="removeTestCase(index)"
            class="btn btn-sm variant-ghost-error"
          >
            Remove
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { promptApi } from '@/services/api'
import type { TestCase, Prompt } from '@/types'

const loading = ref(false)
const error = ref('')
const testCases = ref<TestCase[]>([])
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
  const savedData = sessionStorage.getItem('testPrompt')
  if (savedData) {
    try {
      const { id } = JSON.parse(savedData)
      if (id) {
        selectedPromptId.value = id
      }
      sessionStorage.removeItem('testPrompt')
    } catch (e) {
      // Ignore
    }
  }
})

function loadSelectedPrompt() {
  // Clear error when selection changes
  error.value = ''
}

async function generateTest() {
  if (!selectedPromptId.value) {
    error.value = 'Please select a prompt'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const response = await promptApi.generateTest({
      prompt_id: selectedPromptId.value,
      judge_model: judgeModel.value
    })
    testCases.value.push(response.test_case)
  } catch (e: any) {
    error.value = e.response?.data?.detail || e.message || 'Failed to generate test case'
  } finally {
    loading.value = false
  }
}

function getScoreColor(score: number): string {
  if (score >= 0.8) return 'text-green-600'
  if (score >= 0.6) return 'text-yellow-600'
  return 'text-red-600'
}

function copyTestCase(testCase: TestCase) {
  navigator.clipboard.writeText(JSON.stringify(testCase, null, 2))
}

function removeTestCase(index: number) {
  testCases.value.splice(index, 1)
}

function exportTests() {
  const blob = new Blob([JSON.stringify(testCases.value, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'test-cases.json'
  a.click()
  URL.revokeObjectURL(url)
}
</script>
