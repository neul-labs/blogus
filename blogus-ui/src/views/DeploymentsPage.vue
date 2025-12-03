<template>
  <div class="deployments-page">
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Deployments</h1>
        <p class="text-gray-500 mt-1">Manage your prompt deployments</p>
      </div>
      <router-link
        to="/deployments/create"
        class="btn variant-filled-primary flex items-center gap-2"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
        </svg>
        New Deployment
      </router-link>
    </div>

    <!-- Filters -->
    <div class="card p-4 mb-6">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div>
          <label class="label">
            <span class="label-text">Search</span>
          </label>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search deployments..."
            class="input"
            @input="debouncedSearch"
          />
        </div>
        <div>
          <label class="label">
            <span class="label-text">Status</span>
          </label>
          <select v-model="filterStatus" class="select" @change="applyFilters">
            <option value="">All</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="archived">Archived</option>
          </select>
        </div>
        <div>
          <label class="label">
            <span class="label-text">Category</span>
          </label>
          <select v-model="filterCategory" class="select" @change="applyFilters">
            <option value="">All Categories</option>
            <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
          </select>
        </div>
        <div class="flex items-end">
          <button class="btn variant-ghost-surface w-full" @click="resetFilters">
            Reset Filters
          </button>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="card variant-ghost-error p-6 text-center">
      <p class="text-error-500">{{ error }}</p>
      <button class="btn variant-filled-error mt-4" @click="loadDeployments">
        Retry
      </button>
    </div>

    <!-- Empty State -->
    <div v-else-if="deployments.length === 0" class="card p-12 text-center">
      <svg class="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
      </svg>
      <h3 class="text-lg font-medium text-gray-900 mb-2">No deployments yet</h3>
      <p class="text-gray-500 mb-4">Create your first prompt deployment to get started.</p>
      <router-link to="/deployments/create" class="btn variant-filled-primary">
        Create Deployment
      </router-link>
    </div>

    <!-- Deployments Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <router-link
        v-for="deployment in deployments"
        :key="deployment.id"
        :to="`/deployments/${deployment.name}`"
        class="card p-4 hover:shadow-lg transition-shadow cursor-pointer"
      >
        <div class="flex items-start justify-between mb-3">
          <div class="flex items-center gap-2">
            <span
              class="w-2 h-2 rounded-full"
              :class="{
                'bg-green-500': deployment.status === 'active',
                'bg-yellow-500': deployment.status === 'inactive',
                'bg-gray-400': deployment.status === 'archived'
              }"
            ></span>
            <span class="font-mono text-sm font-medium text-gray-900">{{ deployment.name }}</span>
          </div>
          <span class="badge" :class="statusBadgeClass(deployment.status)">
            {{ deployment.status }}
          </span>
        </div>

        <p class="text-sm text-gray-600 mb-3 line-clamp-2">
          {{ deployment.description || 'No description' }}
        </p>

        <div class="flex items-center gap-2 text-xs text-gray-500 mb-3">
          <span class="badge variant-soft">{{ deployment.model_id }}</span>
          <span>v{{ deployment.version }}</span>
        </div>

        <div class="flex items-center justify-between text-xs text-gray-400">
          <span>{{ deployment.category }}</span>
          <span>{{ formatDate(deployment.updated_at) }}</span>
        </div>

        <div v-if="deployment.tags.length > 0" class="flex flex-wrap gap-1 mt-3">
          <span
            v-for="tag in deployment.tags.slice(0, 3)"
            :key="tag"
            class="badge variant-soft-secondary text-xs"
          >
            {{ tag }}
          </span>
          <span v-if="deployment.tags.length > 3" class="text-xs text-gray-400">
            +{{ deployment.tags.length - 3 }} more
          </span>
        </div>
      </router-link>
    </div>

    <!-- Pagination -->
    <div v-if="deployments.length > 0" class="flex justify-center mt-8">
      <div class="btn-group">
        <button
          class="btn variant-ghost-surface"
          :disabled="currentPage === 1"
          @click="prevPage"
        >
          Previous
        </button>
        <button class="btn variant-filled-surface">{{ currentPage }}</button>
        <button
          class="btn variant-ghost-surface"
          :disabled="deployments.length < pageSize"
          @click="nextPage"
        >
          Next
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useDeploymentsStore } from '@/stores/deployments'
import { storeToRefs } from 'pinia'

const store = useDeploymentsStore()
const { deployments, loading, error, categories } = storeToRefs(store)

// Filters
const searchQuery = ref('')
const filterStatus = ref('')
const filterCategory = ref('')

// Pagination
const currentPage = ref(1)
const pageSize = 12

// Debounce search
let searchTimeout: number | null = null
const debouncedSearch = () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    applyFilters()
  }, 300) as unknown as number
}

async function loadDeployments() {
  await store.fetchDeployments({
    limit: pageSize,
    offset: (currentPage.value - 1) * pageSize,
    status: filterStatus.value || undefined,
    category: filterCategory.value || undefined
  })
}

async function applyFilters() {
  currentPage.value = 1
  if (searchQuery.value) {
    await store.searchDeployments(
      searchQuery.value,
      filterCategory.value || undefined
    )
  } else {
    await loadDeployments()
  }
}

function resetFilters() {
  searchQuery.value = ''
  filterStatus.value = ''
  filterCategory.value = ''
  currentPage.value = 1
  loadDeployments()
}

function prevPage() {
  if (currentPage.value > 1) {
    currentPage.value--
    loadDeployments()
  }
}

function nextPage() {
  currentPage.value++
  loadDeployments()
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
    year: 'numeric'
  })
}

onMounted(() => {
  loadDeployments()
})
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
