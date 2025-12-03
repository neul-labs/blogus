import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { registryApi } from '@/services/api'
import type {
  Deployment,
  DeploymentSummary,
  RegisterDeploymentRequest,
  UpdateContentRequest,
  UpdateModelRequest,
  SetTrafficConfigRequest,
  ExecuteDeploymentRequest,
  ExecutionResult,
  MetricsSummary
} from '@/types'

export const useDeploymentsStore = defineStore('deployments', () => {
  // State
  const deployments = ref<DeploymentSummary[]>([])
  const currentDeployment = ref<Deployment | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const lastExecution = ref<ExecutionResult | null>(null)
  const metrics = ref<MetricsSummary | null>(null)

  // Computed
  const activeDeployments = computed(() =>
    deployments.value.filter(d => d.status === 'active')
  )

  const deploymentsByCategory = computed(() => {
    const grouped: Record<string, DeploymentSummary[]> = {}
    for (const d of deployments.value) {
      if (!grouped[d.category]) {
        grouped[d.category] = []
      }
      grouped[d.category].push(d)
    }
    return grouped
  })

  const categories = computed(() =>
    [...new Set(deployments.value.map(d => d.category))]
  )

  // Actions
  async function fetchDeployments(params?: {
    limit?: number
    offset?: number
    status?: string
    category?: string
  }) {
    loading.value = true
    error.value = null
    try {
      deployments.value = await registryApi.list(params)
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message || 'Failed to fetch deployments'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function searchDeployments(query?: string, category?: string, author?: string, tags?: string[]) {
    loading.value = true
    error.value = null
    try {
      deployments.value = await registryApi.search(query, category, author, tags)
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message || 'Search failed'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchDeployment(name: string) {
    loading.value = true
    error.value = null
    try {
      currentDeployment.value = await registryApi.get(name)
      return currentDeployment.value
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message || 'Failed to fetch deployment'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function createDeployment(request: RegisterDeploymentRequest) {
    loading.value = true
    error.value = null
    try {
      const response = await registryApi.register(request)
      currentDeployment.value = response.deployment
      // Refresh list
      await fetchDeployments()
      return response.deployment
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message || 'Failed to create deployment'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function updateContent(request: UpdateContentRequest) {
    loading.value = true
    error.value = null
    try {
      currentDeployment.value = await registryApi.updateContent(request)
      await fetchDeployments()
      return currentDeployment.value
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message || 'Failed to update content'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function updateModel(request: UpdateModelRequest) {
    loading.value = true
    error.value = null
    try {
      currentDeployment.value = await registryApi.updateModel(request)
      await fetchDeployments()
      return currentDeployment.value
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message || 'Failed to update model config'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function setTrafficConfig(request: SetTrafficConfigRequest) {
    loading.value = true
    error.value = null
    try {
      currentDeployment.value = await registryApi.setTrafficConfig(request)
      return currentDeployment.value
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message || 'Failed to set traffic config'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function clearTrafficConfig(name: string) {
    loading.value = true
    error.value = null
    try {
      currentDeployment.value = await registryApi.clearTrafficConfig(name)
      return currentDeployment.value
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message || 'Failed to clear traffic config'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function rollback(name: string, targetVersion: number, author: string) {
    loading.value = true
    error.value = null
    try {
      currentDeployment.value = await registryApi.rollback({
        name,
        target_version: targetVersion,
        author
      })
      await fetchDeployments()
      return currentDeployment.value
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message || 'Failed to rollback'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function setStatus(name: string, status: 'active' | 'inactive' | 'archived') {
    loading.value = true
    error.value = null
    try {
      currentDeployment.value = await registryApi.setStatus(name, status)
      await fetchDeployments()
      return currentDeployment.value
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message || 'Failed to update status'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteDeployment(name: string) {
    loading.value = true
    error.value = null
    try {
      await registryApi.delete(name)
      if (currentDeployment.value?.name === name) {
        currentDeployment.value = null
      }
      await fetchDeployments()
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message || 'Failed to delete deployment'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function executeDeployment(request: ExecuteDeploymentRequest) {
    loading.value = true
    error.value = null
    try {
      const response = await registryApi.execute(request)
      lastExecution.value = response.result
      return response.result
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message || 'Execution failed'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchMetrics(name: string, version?: number, periodHours?: number) {
    loading.value = true
    error.value = null
    try {
      metrics.value = await registryApi.getMetrics(name, version, periodHours)
      return metrics.value
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message || 'Failed to fetch metrics'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function compareVersions(name: string, versions: number[], periodHours?: number) {
    loading.value = true
    error.value = null
    try {
      return await registryApi.compareVersions(name, versions, periodHours)
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message || 'Failed to compare versions'
      throw e
    } finally {
      loading.value = false
    }
  }

  function clearError() {
    error.value = null
  }

  function clearCurrentDeployment() {
    currentDeployment.value = null
  }

  return {
    // State
    deployments,
    currentDeployment,
    loading,
    error,
    lastExecution,
    metrics,
    // Computed
    activeDeployments,
    deploymentsByCategory,
    categories,
    // Actions
    fetchDeployments,
    searchDeployments,
    fetchDeployment,
    createDeployment,
    updateContent,
    updateModel,
    setTrafficConfig,
    clearTrafficConfig,
    rollback,
    setStatus,
    deleteDeployment,
    executeDeployment,
    fetchMetrics,
    compareVersions,
    clearError,
    clearCurrentDeployment
  }
})
