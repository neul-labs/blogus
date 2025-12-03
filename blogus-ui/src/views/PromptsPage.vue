<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Prompts</h1>
        <p class="text-gray-600">Git-versioned prompt files with template variables.</p>
      </div>
      <div class="flex items-center gap-3">
        <button
          v-if="dirtyCount > 0"
          @click="showCommitModal = true"
          class="btn variant-filled bg-green-600 hover:bg-green-700 text-white"
        >
          <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
          </svg>
          Commit ({{ dirtyCount }})
        </button>
        <router-link to="/prompts/studio" class="btn variant-filled-primary">
          <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd"/>
          </svg>
          New Prompt
        </router-link>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <router-link to="/prompts/studio" class="card p-4 hover:bg-gray-50 transition-colors border-2 border-transparent hover:border-blue-200">
        <div class="flex items-center gap-3">
          <div class="p-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg">
            <svg class="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M5 2a1 1 0 011 1v1h1a1 1 0 010 2H6v1a1 1 0 01-2 0V6H3a1 1 0 010-2h1V3a1 1 0 011-1zm0 10a1 1 0 011 1v1h1a1 1 0 110 2H6v1a1 1 0 11-2 0v-1H3a1 1 0 110-2h1v-1a1 1 0 011-1zM12 2a1 1 0 01.967.744L14.146 7.2 17.5 9.134a1 1 0 010 1.732l-3.354 1.935-1.18 4.455a1 1 0 01-1.933 0L9.854 12.8 6.5 10.866a1 1 0 010-1.732l3.354-1.935 1.18-4.455A1 1 0 0112 2z" clip-rule="evenodd"/>
            </svg>
          </div>
          <div>
            <h3 class="font-medium text-gray-900">Prompt Studio</h3>
            <p class="text-sm text-gray-500">Multi-model execution</p>
          </div>
        </div>
      </router-link>

      <router-link to="/prompts/analyze" class="card p-4 hover:bg-gray-50 transition-colors">
        <div class="flex items-center gap-3">
          <div class="p-2 bg-blue-100 rounded-lg">
            <svg class="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
              <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"/>
            </svg>
          </div>
          <div>
            <h3 class="font-medium text-gray-900">Analyze</h3>
            <p class="text-sm text-gray-500">Check effectiveness</p>
          </div>
        </div>
      </router-link>

      <router-link to="/prompts/test" class="card p-4 hover:bg-gray-50 transition-colors">
        <div class="flex items-center gap-3">
          <div class="p-2 bg-purple-100 rounded-lg">
            <svg class="w-5 h-5 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M7 2a1 1 0 00-.707 1.707L7 4.414v3.758a1 1 0 01-.293.707l-4 4C.817 14.769 2.156 18 4.828 18h10.343c2.673 0 4.012-3.231 2.122-5.121l-4-4A1 1 0 0113 8.172V4.414l.707-.707A1 1 0 0013 2H7zm2 6.172V4h2v4.172a3 3 0 00.879 2.12l1.027 1.028a4 4 0 00-2.171.102l-.47.156a4 4 0 01-2.53 0l-.563-.187a1.993 1.993 0 00-.306-.084l1.342-1.342A3 3 0 009 8.172z" clip-rule="evenodd"/>
            </svg>
          </div>
          <div>
            <h3 class="font-medium text-gray-900">Generate Tests</h3>
            <p class="text-sm text-gray-500">Create test cases</p>
          </div>
        </div>
      </router-link>

      <router-link to="/prompts/scan" class="card p-4 hover:bg-gray-50 transition-colors">
        <div class="flex items-center gap-3">
          <div class="p-2 bg-green-100 rounded-lg">
            <svg class="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"/>
            </svg>
          </div>
          <div>
            <h3 class="font-medium text-gray-900">Scan Project</h3>
            <p class="text-sm text-gray-500">Find LLM calls</p>
          </div>
        </div>
      </router-link>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap gap-3 items-center">
      <select v-model="filter.category" class="select select-sm w-auto" @change="loadPrompts">
        <option value="">All Categories</option>
        <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
      </select>
      <label class="flex items-center gap-2 cursor-pointer">
        <input type="checkbox" v-model="filter.includeDirty" @change="loadPrompts" class="checkbox checkbox-sm" />
        <span class="text-sm">Show modified</span>
      </label>
      <div class="flex-1"></div>
      <span class="text-sm text-gray-500">
        {{ prompts.length }} prompt{{ prompts.length !== 1 ? 's' : '' }}
        <span v-if="dirtyCount > 0" class="text-yellow-600">
          ({{ dirtyCount }} modified)
        </span>
      </span>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="card bg-red-50 border-red-200 p-6 text-center">
      <p class="text-red-600 mb-4">{{ error }}</p>
      <button @click="loadPrompts" class="btn variant-filled-primary">
        Retry
      </button>
    </div>

    <!-- Empty State -->
    <div v-else-if="prompts.length === 0" class="card p-12 text-center">
      <svg class="w-16 h-16 mx-auto mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
      </svg>
      <h3 class="text-lg font-medium text-gray-900 mb-2">No .prompt files found</h3>
      <p class="text-gray-500 mb-4">Create your first prompt in the Prompt Studio or add .prompt files to your project.</p>
      <router-link to="/prompts/studio" class="btn variant-filled-primary">
        Open Studio
      </router-link>
    </div>

    <!-- Prompts List -->
    <div v-else class="space-y-4">
      <div
        v-for="prompt in prompts"
        :key="prompt.name"
        class="card p-4 hover:shadow-md transition-shadow"
        :class="{ 'border-l-4 border-yellow-400': prompt.is_dirty }"
      >
        <div class="flex items-start justify-between gap-4">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-2 flex-wrap">
              <h3 class="font-semibold text-gray-900">{{ prompt.name }}</h3>
              <span class="badge bg-gray-100 text-gray-600 text-xs">v{{ prompt.version }}</span>
              <span
                v-if="prompt.is_dirty"
                class="badge bg-yellow-100 text-yellow-800 text-xs"
                title="Uncommitted changes"
              >
                Modified
              </span>
              <span v-if="prompt.variable_count > 0" class="badge bg-purple-100 text-purple-800">
                {{ prompt.variable_count }} var{{ prompt.variable_count !== 1 ? 's' : '' }}
              </span>
              <span class="badge bg-gray-100 text-gray-500">{{ prompt.category }}</span>
            </div>
            <p v-if="prompt.description" class="text-sm text-gray-600 mb-2">{{ prompt.description }}</p>
            <div class="flex flex-wrap gap-3 text-sm text-gray-500">
              <span class="font-mono text-xs text-gray-400">{{ prompt.file_path }}</span>
            </div>
            <div class="mt-2 flex flex-wrap gap-3 text-sm text-gray-500">
              <span v-if="prompt.author">
                <strong>By:</strong> {{ prompt.author }}
              </span>
              <span>
                <strong>Model:</strong> {{ prompt.model_id }}
              </span>
              <span>
                <strong>Updated:</strong> {{ formatDate(prompt.last_modified) }}
              </span>
            </div>
            <div v-if="prompt.tags?.length" class="mt-2 flex flex-wrap gap-1">
              <span v-for="tag in prompt.tags" :key="tag" class="badge badge-sm bg-gray-200 text-gray-700">
                {{ tag }}
              </span>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <router-link
              :to="`/prompts/studio/${prompt.name}`"
              class="btn btn-sm variant-filled-primary"
              title="Edit in Studio"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
              </svg>
            </router-link>
            <button
              @click="analyzePrompt(prompt)"
              class="btn btn-sm variant-ghost"
              title="Analyze"
            >
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"/>
              </svg>
            </button>
            <button
              @click="confirmDelete(prompt)"
              class="btn btn-sm variant-ghost text-red-600 hover:bg-red-50"
              title="Delete"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Commit Modal -->
    <div v-if="showCommitModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="card p-6 max-w-lg w-full">
        <h2 class="text-lg font-bold text-gray-900 mb-2">Commit Changes</h2>
        <p class="text-gray-600 mb-4">
          Commit {{ dirtyCount }} modified prompt file{{ dirtyCount !== 1 ? 's' : '' }} to Git.
        </p>

        <!-- Modified files list -->
        <div class="bg-gray-50 rounded-lg p-3 mb-4 max-h-40 overflow-y-auto">
          <div class="text-xs font-medium text-gray-500 mb-2">Files to commit:</div>
          <div v-for="prompt in dirtyPrompts" :key="prompt.name" class="text-sm text-gray-700 flex items-center gap-2 py-1">
            <span class="w-2 h-2 bg-yellow-400 rounded-full"></span>
            {{ prompt.name }}.prompt
          </div>
        </div>

        <!-- Commit message input -->
        <label class="block mb-4">
          <span class="text-sm font-medium text-gray-700 mb-1 block">Commit message</span>
          <input
            v-model="commitMessage"
            type="text"
            class="input w-full"
            placeholder="Update prompts"
            @keyup.enter="commitChanges"
          />
        </label>

        <!-- Error message -->
        <div v-if="commitError" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
          {{ commitError }}
        </div>

        <!-- Success message -->
        <div v-if="commitSuccess" class="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-green-600 text-sm">
          Committed successfully! SHA: {{ commitSuccess }}
        </div>

        <div class="flex justify-end gap-3">
          <button @click="closeCommitModal" class="btn variant-ghost">
            {{ commitSuccess ? 'Close' : 'Cancel' }}
          </button>
          <button
            v-if="!commitSuccess"
            @click="commitChanges"
            class="btn variant-filled bg-green-600 hover:bg-green-700 text-white"
            :disabled="committing || !commitMessage.trim()"
          >
            <svg v-if="committing" class="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ committing ? 'Committing...' : 'Commit' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div v-if="deleteTarget" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="card p-6 max-w-md w-full">
        <h2 class="text-lg font-bold text-gray-900 mb-2">Delete Prompt File?</h2>
        <p class="text-gray-600 mb-2">
          Are you sure you want to delete "<strong>{{ deleteTarget.name }}.prompt</strong>"?
        </p>
        <p class="text-sm text-yellow-600 mb-4">
          This will delete the file from disk. You can recover it from Git if committed.
        </p>
        <div class="flex justify-end gap-3">
          <button @click="deleteTarget = null" class="btn variant-ghost">
            Cancel
          </button>
          <button @click="deletePrompt" class="btn variant-filled bg-red-600 hover:bg-red-700 text-white" :disabled="deleting">
            {{ deleting ? 'Deleting...' : 'Delete' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { promptFilesApi } from '@/services/api'
import type { PromptFileSummary } from '@/types'

const router = useRouter()

const loading = ref(false)
const error = ref('')
const prompts = ref<PromptFileSummary[]>([])
const categories = ref<string[]>([])
const deleteTarget = ref<PromptFileSummary | null>(null)
const deleting = ref(false)

// Commit modal state
const showCommitModal = ref(false)
const commitMessage = ref('')
const committing = ref(false)
const commitError = ref('')
const commitSuccess = ref('')

const filter = reactive({
  category: '',
  includeDirty: true
})

const dirtyCount = computed(() => prompts.value.filter(p => p.is_dirty).length)
const dirtyPrompts = computed(() => prompts.value.filter(p => p.is_dirty))

async function loadPrompts() {
  loading.value = true
  error.value = ''

  try {
    const params: { category?: string; include_dirty?: boolean } = {}
    if (filter.category) params.category = filter.category
    params.include_dirty = filter.includeDirty

    prompts.value = await promptFilesApi.list(params)

    // Extract unique categories from prompts
    const cats = new Set(prompts.value.map(p => p.category).filter(Boolean))
    categories.value = Array.from(cats).sort()
  } catch (e: any) {
    error.value = e.response?.data?.detail || e.message || 'Failed to load prompts'
  } finally {
    loading.value = false
  }
}

function formatDate(dateString: string): string {
  if (!dateString) return 'Unknown'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function analyzePrompt(prompt: PromptFileSummary) {
  sessionStorage.setItem('analyzePrompt', JSON.stringify({ name: prompt.name }))
  router.push('/prompts/analyze')
}

function confirmDelete(prompt: PromptFileSummary) {
  deleteTarget.value = prompt
}

async function deletePrompt() {
  if (!deleteTarget.value) return

  deleting.value = true
  try {
    await promptFilesApi.delete(deleteTarget.value.name)
    prompts.value = prompts.value.filter(p => p.name !== deleteTarget.value!.name)
    deleteTarget.value = null
  } catch (e: any) {
    error.value = e.response?.data?.detail || e.message || 'Failed to delete prompt'
  } finally {
    deleting.value = false
  }
}

async function commitChanges() {
  if (!commitMessage.value.trim()) return

  committing.value = true
  commitError.value = ''
  commitSuccess.value = ''

  try {
    const result = await promptFilesApi.commitAll(commitMessage.value.trim())
    commitSuccess.value = result.commit_sha.substring(0, 8)
    // Reload prompts to reflect the new state
    await loadPrompts()
  } catch (e: any) {
    commitError.value = e.response?.data?.detail || e.message || 'Failed to commit changes'
  } finally {
    committing.value = false
  }
}

function closeCommitModal() {
  showCommitModal.value = false
  commitMessage.value = ''
  commitError.value = ''
  commitSuccess.value = ''
}

onMounted(() => {
  loadPrompts()
})
</script>
