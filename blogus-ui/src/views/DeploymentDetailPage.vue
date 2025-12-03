<template>
  <div class="deployment-detail-page">
    <!-- Loading -->
    <div v-if="loading && !deployment" class="flex justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
    </div>

    <!-- Error -->
    <div v-else-if="error && !deployment" class="card variant-ghost-error p-6 text-center">
      <p class="text-error-500">{{ error }}</p>
      <router-link to="/deployments" class="btn variant-filled mt-4">
        Back to Deployments
      </router-link>
    </div>

    <!-- Content -->
    <template v-else-if="deployment">
      <!-- Header -->
      <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 mb-6">
        <div>
          <div class="flex items-center gap-3 mb-2">
            <router-link to="/deployments" class="text-gray-400 hover:text-gray-600">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
              </svg>
            </router-link>
            <h1 class="text-2xl font-bold font-mono text-gray-900">{{ deployment.name }}</h1>
            <span class="badge" :class="statusBadgeClass(deployment.status)">
              {{ deployment.status }}
            </span>
          </div>
          <p class="text-gray-500">{{ deployment.description }}</p>
        </div>

        <div class="flex gap-2">
          <button
            v-if="deployment.status !== 'active'"
            class="btn variant-filled-success"
            @click="activateDeployment"
          >
            Activate
          </button>
          <button
            v-if="deployment.status === 'active'"
            class="btn variant-ghost-warning"
            @click="deactivateDeployment"
          >
            Deactivate
          </button>
          <button class="btn variant-ghost-error" @click="showDeleteModal = true">
            Delete
          </button>
        </div>
      </div>

      <!-- Stats Cards -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div class="card p-4">
          <p class="text-sm text-gray-500">Version</p>
          <p class="text-2xl font-bold">v{{ deployment.version }}</p>
        </div>
        <div class="card p-4">
          <p class="text-sm text-gray-500">Model</p>
          <p class="text-lg font-medium truncate">{{ deployment.model_config.model_id }}</p>
        </div>
        <div class="card p-4">
          <p class="text-sm text-gray-500">Category</p>
          <p class="text-lg font-medium">{{ deployment.category }}</p>
        </div>
        <div class="card p-4">
          <p class="text-sm text-gray-500">Template</p>
          <p class="text-lg font-medium">{{ deployment.is_template ? 'Yes' : 'No' }}</p>
        </div>
      </div>

      <!-- Tabs -->
      <div class="card">
        <div class="border-b border-gray-200">
          <nav class="flex -mb-px">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              class="px-6 py-3 text-sm font-medium border-b-2 transition-colors"
              :class="activeTab === tab.id
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'"
              @click="activeTab = tab.id"
            >
              {{ tab.label }}
            </button>
          </nav>
        </div>

        <div class="p-6">
          <!-- Content Tab -->
          <div v-if="activeTab === 'content'">
            <div class="flex justify-between items-center mb-4">
              <h3 class="text-lg font-medium">Prompt Content</h3>
              <button class="btn variant-ghost-primary btn-sm" @click="showEditContent = true">
                Edit
              </button>
            </div>
            <pre class="bg-gray-50 rounded-lg p-4 text-sm overflow-x-auto whitespace-pre-wrap">{{ deployment.content }}</pre>

            <div v-if="deployment.is_template && deployment.template_variables.length > 0" class="mt-4">
              <h4 class="text-sm font-medium text-gray-700 mb-2">Template Variables</h4>
              <div class="flex flex-wrap gap-2">
                <span
                  v-for="v in deployment.template_variables"
                  :key="v"
                  class="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-0.5 rounded"
                  v-text="'{{' + v + '}}'"
                ></span>
              </div>
            </div>

            <div v-if="deployment.goal" class="mt-4">
              <h4 class="text-sm font-medium text-gray-700 mb-2">Goal</h4>
              <p class="text-gray-600">{{ deployment.goal }}</p>
            </div>
          </div>

          <!-- Model Config Tab -->
          <div v-if="activeTab === 'model'">
            <div class="flex justify-between items-center mb-4">
              <h3 class="text-lg font-medium">Model Configuration</h3>
              <button class="btn variant-ghost-primary btn-sm" @click="showEditModel = true">
                Edit
              </button>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label class="text-sm text-gray-500">Model ID</label>
                <p class="font-medium">{{ deployment.model_config.model_id }}</p>
              </div>
              <div>
                <label class="text-sm text-gray-500">Temperature</label>
                <p class="font-medium">{{ deployment.model_config.parameters.temperature }}</p>
              </div>
              <div>
                <label class="text-sm text-gray-500">Max Tokens</label>
                <p class="font-medium">{{ deployment.model_config.parameters.max_tokens }}</p>
              </div>
              <div>
                <label class="text-sm text-gray-500">Top P</label>
                <p class="font-medium">{{ deployment.model_config.parameters.top_p }}</p>
              </div>
              <div v-if="deployment.model_config.fallback_models.length > 0" class="md:col-span-2">
                <label class="text-sm text-gray-500">Fallback Models</label>
                <div class="flex flex-wrap gap-2 mt-1">
                  <span
                    v-for="model in deployment.model_config.fallback_models"
                    :key="model"
                    class="badge variant-soft"
                  >
                    {{ model }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Versions Tab -->
          <div v-if="activeTab === 'versions'">
            <h3 class="text-lg font-medium mb-4">Version History</h3>

            <div class="space-y-4">
              <!-- Current Version -->
              <div class="border border-primary-200 bg-primary-50 rounded-lg p-4">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-3">
                    <span class="badge variant-filled-primary">Current</span>
                    <span class="font-medium">Version {{ deployment.version }}</span>
                  </div>
                  <span class="text-sm text-gray-500">{{ formatDate(deployment.updated_at) }}</span>
                </div>
              </div>

              <!-- History -->
              <div
                v-for="version in deployment.version_history"
                :key="version.version"
                class="border rounded-lg p-4 hover:bg-gray-50"
              >
                <div class="flex items-center justify-between mb-2">
                  <span class="font-medium">Version {{ version.version }}</span>
                  <div class="flex items-center gap-2">
                    <span class="text-sm text-gray-500">{{ formatDate(version.created_at) }}</span>
                    <button
                      class="btn variant-ghost-primary btn-sm"
                      @click="rollbackToVersion(version.version)"
                    >
                      Rollback
                    </button>
                  </div>
                </div>
                <p v-if="version.change_summary" class="text-sm text-gray-600">
                  {{ version.change_summary }}
                </p>
                <p class="text-xs text-gray-400 mt-1">by {{ version.created_by }}</p>
              </div>

              <p v-if="deployment.version_history.length === 0" class="text-gray-500 text-center py-4">
                No previous versions
              </p>
            </div>
          </div>

          <!-- Traffic Tab -->
          <div v-if="activeTab === 'traffic'">
            <div class="flex justify-between items-center mb-4">
              <h3 class="text-lg font-medium">Traffic Configuration</h3>
              <button class="btn variant-ghost-primary btn-sm" @click="showTrafficConfig = true">
                Configure
              </button>
            </div>

            <div v-if="deployment.traffic_config && deployment.traffic_config.routes.length > 0">
              <div class="space-y-3">
                <div
                  v-for="route in deployment.traffic_config.routes"
                  :key="route.version"
                  class="flex items-center gap-4 p-3 bg-gray-50 rounded-lg"
                >
                  <div class="flex-1">
                    <span class="font-medium">Version {{ route.version }}</span>
                    <span v-if="route.model_override" class="text-sm text-gray-500 ml-2">
                      ({{ route.model_override }})
                    </span>
                  </div>
                  <div class="w-32">
                    <div class="bg-gray-200 rounded-full h-2">
                      <div
                        class="bg-primary-500 rounded-full h-2"
                        :style="{ width: route.weight + '%' }"
                      ></div>
                    </div>
                  </div>
                  <span class="font-medium w-12 text-right">{{ route.weight }}%</span>
                </div>
              </div>

              <div v-if="deployment.traffic_config.shadow_version" class="mt-4 p-3 bg-yellow-50 rounded-lg">
                <span class="text-sm text-yellow-700">
                  Shadow testing: Version {{ deployment.traffic_config.shadow_version }}
                </span>
              </div>
            </div>

            <div v-else class="text-center py-8 text-gray-500">
              <p>No traffic routing configured.</p>
              <p class="text-sm">All traffic goes to the latest version.</p>
            </div>
          </div>

          <!-- Execute Tab -->
          <div v-if="activeTab === 'execute'">
            <h3 class="text-lg font-medium mb-4">Execute Deployment</h3>

            <div v-if="deployment.is_template" class="mb-4">
              <h4 class="text-sm font-medium text-gray-700 mb-2">Variables</h4>
              <div class="space-y-3">
                <div v-for="v in deployment.template_variables" :key="v">
                  <label class="label">
                    <span class="label-text">{{ v }}</span>
                  </label>
                  <input
                    v-model="executeVariables[v]"
                    type="text"
                    class="input"
                    :placeholder="`Enter ${v}...`"
                  />
                </div>
              </div>
            </div>

            <button
              class="btn variant-filled-primary"
              :disabled="loading"
              @click="executePrompt"
            >
              <span v-if="loading">Executing...</span>
              <span v-else>Execute</span>
            </button>

            <div v-if="lastExecution" class="mt-6">
              <h4 class="text-sm font-medium text-gray-700 mb-2">Result</h4>
              <div class="bg-gray-50 rounded-lg p-4">
                <pre class="whitespace-pre-wrap text-sm">{{ lastExecution.response }}</pre>
              </div>
              <div class="flex gap-4 mt-3 text-sm text-gray-500">
                <span>{{ lastExecution.latency_ms.toFixed(0) }}ms</span>
                <span>{{ lastExecution.total_tokens }} tokens</span>
                <span>${{ lastExecution.estimated_cost_usd.toFixed(4) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="card p-6 max-w-md w-full mx-4">
        <h3 class="text-lg font-bold mb-2">Delete Deployment</h3>
        <p class="text-gray-600 mb-4">
          Are you sure you want to delete <strong>{{ deployment?.name }}</strong>?
          This action cannot be undone.
        </p>
        <div class="flex gap-3 justify-end">
          <button class="btn variant-ghost" @click="showDeleteModal = false">Cancel</button>
          <button class="btn variant-filled-error" @click="confirmDelete">Delete</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDeploymentsStore } from '@/stores/deployments'
import { storeToRefs } from 'pinia'

const route = useRoute()
const router = useRouter()
const store = useDeploymentsStore()

const { currentDeployment: deployment, loading, error, lastExecution } = storeToRefs(store)

const activeTab = ref('content')
const showDeleteModal = ref(false)
const showEditContent = ref(false)
const showEditModel = ref(false)
const showTrafficConfig = ref(false)
const executeVariables = reactive<Record<string, string>>({})

const tabs = [
  { id: 'content', label: 'Content' },
  { id: 'model', label: 'Model Config' },
  { id: 'versions', label: 'Versions' },
  { id: 'traffic', label: 'Traffic' },
  { id: 'execute', label: 'Execute' }
]

const deploymentName = computed(() => route.params.name as string)

async function loadDeployment() {
  await store.fetchDeployment(deploymentName.value)
}

async function activateDeployment() {
  await store.setStatus(deploymentName.value, 'active')
}

async function deactivateDeployment() {
  await store.setStatus(deploymentName.value, 'inactive')
}

async function confirmDelete() {
  await store.deleteDeployment(deploymentName.value)
  showDeleteModal.value = false
  router.push('/deployments')
}

async function rollbackToVersion(version: number) {
  if (confirm(`Rollback to version ${version}?`)) {
    await store.rollback(deploymentName.value, version, 'web-ui')
  }
}

async function executePrompt() {
  const variables = deployment.value?.is_template ? executeVariables : undefined
  await store.executeDeployment({
    name: deploymentName.value,
    variables
  })
}

function statusBadgeClass(status: string) {
  switch (status) {
    case 'active':
      return 'variant-filled-success'
    case 'inactive':
      return 'variant-filled-warning'
    case 'archived':
      return 'variant-filled-surface'
    default:
      return 'variant-filled-surface'
  }
}

function formatDate(dateStr: string) {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  loadDeployment()
})
</script>
