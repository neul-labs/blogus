<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Project Scan</h1>
        <p class="text-gray-600">Scan your codebase for prompts and LLM API calls.</p>
      </div>
      <button
        @click="runScan"
        class="btn variant-filled-primary"
        :disabled="scanning"
      >
        <svg v-if="scanning" class="animate-spin -ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <svg v-else class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"/>
        </svg>
        {{ scanning ? 'Scanning...' : 'Run Scan' }}
      </button>
    </div>

    <!-- Scan Options -->
    <div class="card p-4">
      <h3 class="font-medium text-gray-900 mb-3">Scan Options</h3>
      <div class="flex flex-wrap gap-4">
        <label class="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" v-model="options.includePython" class="checkbox checkbox-sm" />
          <span class="text-sm">Python files</span>
        </label>
        <label class="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" v-model="options.includeJs" class="checkbox checkbox-sm" />
          <span class="text-sm">JavaScript/TypeScript files</span>
        </label>
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="card bg-red-50 border-red-200 p-6">
      <p class="text-red-600">{{ error }}</p>
    </div>

    <!-- No Results Yet -->
    <div v-else-if="!result && !scanning" class="card p-12 text-center text-gray-500">
      <svg class="w-16 h-16 mx-auto mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
      </svg>
      <p class="text-lg">Click "Run Scan" to analyze your project</p>
      <p class="text-sm mt-2">Detects .prompt files and LLM API calls in Python and JavaScript</p>
    </div>

    <!-- Results -->
    <template v-else-if="result">
      <!-- Summary Cards -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="card p-4 text-center">
          <div class="text-3xl font-bold text-gray-900">{{ result.stats.total_detections || 0 }}</div>
          <div class="text-sm text-gray-600">Total Detections</div>
        </div>
        <div class="card p-4 text-center">
          <div class="text-3xl font-bold text-green-600">{{ result.stats.versioned || 0 }}</div>
          <div class="text-sm text-gray-600">Versioned</div>
        </div>
        <div class="card p-4 text-center">
          <div class="text-3xl font-bold text-yellow-600">{{ result.stats.unversioned || 0 }}</div>
          <div class="text-sm text-gray-600">Unversioned</div>
        </div>
        <div class="card p-4 text-center">
          <div class="text-3xl font-bold text-blue-600">{{ result.prompt_files?.length || 0 }}</div>
          <div class="text-sm text-gray-600">.prompt Files</div>
        </div>
      </div>

      <!-- Prompt Files -->
      <div v-if="result.prompt_files?.length" class="card p-6">
        <h3 class="text-lg font-semibold mb-4">.prompt Files</h3>
        <div class="space-y-2">
          <div
            v-for="pf in result.prompt_files"
            :key="pf.name"
            class="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
          >
            <div class="flex items-center gap-3">
              <div class="p-2 bg-blue-100 rounded">
                <svg class="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd"/>
                </svg>
              </div>
              <div>
                <div class="font-medium text-gray-900">{{ pf.name }}</div>
                <div class="text-xs text-gray-500 font-mono">{{ pf.path }}</div>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <span class="badge bg-gray-100 text-gray-600 text-xs">v{{ pf.version }}</span>
              <span
                v-if="pf.is_dirty"
                class="badge bg-yellow-100 text-yellow-800 text-xs"
              >
                Modified
              </span>
              <span v-else class="badge bg-green-100 text-green-800 text-xs">
                Clean
              </span>
              <router-link
                :to="`/prompts/studio/${pf.name}`"
                class="btn btn-xs variant-ghost"
              >
                Edit
              </router-link>
            </div>
          </div>
        </div>
      </div>

      <!-- Code Detections -->
      <div v-if="result.detections?.length" class="card p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold">LLM API Calls Detected</h3>
          <div class="flex gap-2">
            <select v-model="detectionFilter" class="select select-sm">
              <option value="">All</option>
              <option value="versioned">Versioned</option>
              <option value="unversioned">Unversioned</option>
            </select>
          </div>
        </div>
        <div class="space-y-2">
          <div
            v-for="(det, idx) in filteredDetections"
            :key="idx"
            class="p-3 border rounded-lg"
            :class="{
              'border-green-200 bg-green-50': det.status === 'versioned',
              'border-yellow-200 bg-yellow-50': det.status === 'unversioned'
            }"
          >
            <div class="flex items-start justify-between gap-4">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1 flex-wrap">
                  <span class="font-mono text-sm text-gray-900">{{ getRelativePath(det.file) }}:{{ det.line }}</span>
                  <span class="badge bg-gray-100 text-gray-600 text-xs">{{ det.language }}</span>
                  <span v-if="det.api" class="badge bg-blue-100 text-blue-800 text-xs">{{ det.api }}</span>
                  <span
                    :class="{
                      'badge bg-green-100 text-green-800 text-xs': det.status === 'versioned',
                      'badge bg-yellow-100 text-yellow-800 text-xs': det.status === 'unversioned'
                    }"
                  >
                    {{ det.status }}
                  </span>
                </div>
                <div class="text-sm text-gray-600">
                  Type: {{ det.type }}
                  <span v-if="det.linked_to" class="ml-2">
                    Linked to: <span class="font-medium">{{ det.linked_to }}</span>
                  </span>
                </div>
                <div class="mt-1 text-xs text-gray-400 font-mono truncate">
                  Hash: {{ det.hash }}
                </div>
              </div>
              <div class="flex items-center gap-2">
                <button
                  v-if="det.status === 'unversioned'"
                  @click="linkToPrompt(det)"
                  class="btn btn-xs variant-ghost"
                  title="Link to a .prompt file"
                >
                  Link
                </button>
              </div>
            </div>
          </div>
        </div>

        <div v-if="filteredDetections.length === 0" class="text-center py-8 text-gray-500">
          No detections match the current filter
        </div>
      </div>

      <!-- No Detections -->
      <div v-if="!result.detections?.length && !result.prompt_files?.length" class="card p-12 text-center">
        <svg class="w-16 h-16 mx-auto mb-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        <h3 class="text-lg font-medium text-gray-900 mb-2">No prompts detected</h3>
        <p class="text-gray-500">No .prompt files or LLM API calls found in the project.</p>
      </div>

      <!-- Scan Info -->
      <div class="text-sm text-gray-500 text-right">
        Scanned: {{ result.project_path }}<br>
        Time: {{ formatDate(result.scan_time) }}
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { promptFilesApi } from '@/services/api'
import type { ScanResult } from '@/types'

const scanning = ref(false)
const error = ref('')
const result = ref<ScanResult | null>(null)
const detectionFilter = ref('')

const options = reactive({
  includePython: true,
  includeJs: true
})

const filteredDetections = computed(() => {
  if (!result.value?.detections) return []

  return result.value.detections.filter(det => {
    if (!detectionFilter.value) return true
    return det.status === detectionFilter.value
  })
})

async function runScan() {
  scanning.value = true
  error.value = ''

  try {
    result.value = await promptFilesApi.scan({
      include_python: options.includePython,
      include_js: options.includeJs
    })
  } catch (e: any) {
    error.value = e.response?.data?.detail || e.message || 'Scan failed'
  } finally {
    scanning.value = false
  }
}

function getRelativePath(fullPath: string): string {
  // Try to make the path relative by removing common prefixes
  const parts = fullPath.split('/')
  const idx = parts.findIndex(p => p === 'src' || p === 'lib' || p === 'app')
  if (idx >= 0) {
    return parts.slice(idx).join('/')
  }
  // Return last 3 parts
  return parts.slice(-3).join('/')
}

function formatDate(dateString: string): string {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString()
}

function linkToPrompt(detection: any) {
  // For now, just copy the hash - could open a modal to select a prompt
  navigator.clipboard.writeText(`@blogus:prompt-name sha256:${detection.hash}`)
  alert(`Copied marker to clipboard. Add this comment above your LLM call:\n\n# @blogus:prompt-name sha256:${detection.hash}`)
}
</script>
