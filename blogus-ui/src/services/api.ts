import axios, { type AxiosResponse } from 'axios'
import type {
  AnalyzePromptRequest,
  AnalyzePromptResponse,
  ExecutePromptRequest,
  ExecutePromptResponse,
  GenerateTestRequest,
  GenerateTestResponse,
  CreatePromptRequest,
  UpdatePromptRequest,
  Prompt,
  PromptListResponse,
  // Registry types
  Deployment,
  DeploymentSummary,
  RegisterDeploymentRequest,
  RegisterDeploymentResponse,
  UpdateContentRequest,
  UpdateModelRequest,
  SetTrafficConfigRequest,
  ExecuteDeploymentRequest,
  ExecuteDeploymentResponse,
  RollbackRequest,
  GetMetricsResponse,
  CompareVersionsResponse,
  MetricsSummary,
  // Multi-model types
  MultiModelExecuteRequest,
  MultiModelExecuteResponse,
  MultiModelCompareRequest,
  MultiModelCompareResponse,
  AvailableModelsResponse,
  // File-based prompt types
  PromptFile,
  PromptFileSummary,
  PromptFileListResponse,
  VersionHistoryResponse,
  CreatePromptFileRequest,
  UpdatePromptFileRequest,
  RenderPromptFileResponse,
  ValidatePromptFileResponse,
  ScanResult,
  // Git types
  GitStatusResponse,
  CommitResponse
} from '@/types'

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle authentication errors
      console.error('Authentication required')
    }
    return Promise.reject(error)
  }
)

// Prompt API
export const promptApi = {
  async analyze(request: AnalyzePromptRequest): Promise<AnalyzePromptResponse> {
    const response: AxiosResponse<AnalyzePromptResponse> = await api.post('/prompts/analyze', request)
    return response.data
  },

  async execute(request: ExecutePromptRequest): Promise<ExecutePromptResponse> {
    const response: AxiosResponse<ExecutePromptResponse> = await api.post('/prompts/execute', request)
    return response.data
  },

  async generateTest(request: GenerateTestRequest): Promise<GenerateTestResponse> {
    const response: AxiosResponse<GenerateTestResponse> = await api.post('/prompts/test', request)
    return response.data
  },

  async create(request: CreatePromptRequest): Promise<Prompt> {
    const response: AxiosResponse<Prompt> = await api.post('/prompts/', request)
    return response.data
  },

  async get(id: string): Promise<Prompt> {
    const response: AxiosResponse<Prompt> = await api.get(`/prompts/${id}`)
    return response.data
  },

  async list(params?: { category?: string; has_variables?: boolean }): Promise<Prompt[]> {
    const queryParams = new URLSearchParams()
    if (params?.category) queryParams.append('category', params.category)
    if (params?.has_variables !== undefined) queryParams.append('has_variables', params.has_variables.toString())

    const url = queryParams.toString() ? `/prompts/?${queryParams}` : '/prompts/'
    const response: AxiosResponse<PromptListResponse> = await api.get(url)
    return response.data.prompts
  },

  async update(id: string, request: UpdatePromptRequest): Promise<Prompt> {
    const response: AxiosResponse<Prompt> = await api.put(`/prompts/${id}`, request)
    return response.data
  },

  async delete(id: string): Promise<{ message: string }> {
    const response: AxiosResponse<{ message: string }> = await api.delete(`/prompts/${id}`)
    return response.data
  },

  // Multi-model execution
  async executeMultiModel(request: MultiModelExecuteRequest): Promise<MultiModelExecuteResponse> {
    const response: AxiosResponse<MultiModelExecuteResponse> = await api.post('/prompts/execute/multi', request)
    return response.data
  },

  async executeAndCompare(request: MultiModelCompareRequest): Promise<MultiModelCompareResponse> {
    const response: AxiosResponse<MultiModelCompareResponse> = await api.post('/prompts/execute/compare', request)
    return response.data
  },

  async getAvailableModels(): Promise<string[]> {
    const response: AxiosResponse<AvailableModelsResponse> = await api.get('/prompts/models/available')
    return response.data.models
  }
}

// Registry API
export const registryApi = {
  // Deployment CRUD
  async register(request: RegisterDeploymentRequest): Promise<RegisterDeploymentResponse> {
    const response: AxiosResponse<RegisterDeploymentResponse> = await api.post('/registry/deployments', request)
    return response.data
  },

  async get(name: string): Promise<Deployment> {
    const response: AxiosResponse<Deployment> = await api.get(`/registry/deployments/${name}`)
    return response.data
  },

  async list(params?: {
    limit?: number
    offset?: number
    status?: string
    category?: string
    tags?: string[]
  }): Promise<DeploymentSummary[]> {
    const queryParams = new URLSearchParams()
    if (params?.limit) queryParams.append('limit', params.limit.toString())
    if (params?.offset) queryParams.append('offset', params.offset.toString())
    if (params?.status) queryParams.append('status', params.status)
    if (params?.category) queryParams.append('category', params.category)
    if (params?.tags) params.tags.forEach(t => queryParams.append('tags', t))

    const response: AxiosResponse<DeploymentSummary[]> = await api.get(`/registry/deployments?${queryParams}`)
    return response.data
  },

  async search(query?: string, category?: string, author?: string, tags?: string[]): Promise<DeploymentSummary[]> {
    const queryParams = new URLSearchParams()
    if (query) queryParams.append('query', query)
    if (category) queryParams.append('category', category)
    if (author) queryParams.append('author', author)
    if (tags) tags.forEach(t => queryParams.append('tags', t))

    const response: AxiosResponse<DeploymentSummary[]> = await api.get(`/registry/deployments/search?${queryParams}`)
    return response.data
  },

  async delete(name: string): Promise<{ message: string }> {
    const response: AxiosResponse<{ message: string }> = await api.delete(`/registry/deployments/${name}`)
    return response.data
  },

  // Content & Model Updates
  async updateContent(request: UpdateContentRequest): Promise<Deployment> {
    const response: AxiosResponse<{ deployment: Deployment }> = await api.put('/registry/deployments/content', request)
    return response.data.deployment
  },

  async updateModel(request: UpdateModelRequest): Promise<Deployment> {
    const response: AxiosResponse<{ deployment: Deployment }> = await api.put('/registry/deployments/model', request)
    return response.data.deployment
  },

  // Traffic Management
  async setTrafficConfig(request: SetTrafficConfigRequest): Promise<Deployment> {
    const response: AxiosResponse<{ deployment: Deployment }> = await api.put('/registry/deployments/traffic', request)
    return response.data.deployment
  },

  async clearTrafficConfig(name: string): Promise<Deployment> {
    const response: AxiosResponse<{ deployment: Deployment }> = await api.delete(`/registry/deployments/${name}/traffic`)
    return response.data.deployment
  },

  // Versioning
  async rollback(request: RollbackRequest): Promise<Deployment> {
    const response: AxiosResponse<{ deployment: Deployment }> = await api.post('/registry/deployments/rollback', request)
    return response.data.deployment
  },

  // Status
  async setStatus(name: string, status: 'active' | 'inactive' | 'archived'): Promise<Deployment> {
    const response: AxiosResponse<{ deployment: Deployment }> = await api.put(`/registry/deployments/${name}/status`, { status })
    return response.data.deployment
  },

  // Execution
  async execute(request: ExecuteDeploymentRequest): Promise<ExecuteDeploymentResponse> {
    const response: AxiosResponse<ExecuteDeploymentResponse> = await api.post('/registry/execute', request)
    return response.data
  },

  // Metrics
  async getMetrics(name: string, version?: number, periodHours?: number): Promise<MetricsSummary> {
    const queryParams = new URLSearchParams()
    queryParams.append('name', name)
    if (version !== undefined) queryParams.append('version', version.toString())
    if (periodHours) queryParams.append('period_hours', periodHours.toString())

    const response: AxiosResponse<GetMetricsResponse> = await api.get(`/registry/metrics?${queryParams}`)
    return response.data.metrics
  },

  async compareVersions(name: string, versions: number[], periodHours?: number): Promise<Record<number, MetricsSummary>> {
    const response: AxiosResponse<CompareVersionsResponse> = await api.post('/registry/metrics/compare', {
      name,
      versions,
      period_hours: periodHours || 24
    })
    return response.data.comparisons
  },

  // Export/Import
  async export(name: string, format: 'json' | 'yaml' | 'markdown' = 'json', includeHistory: boolean = false): Promise<string> {
    const queryParams = new URLSearchParams()
    queryParams.append('format', format)
    queryParams.append('include_history', includeHistory.toString())

    const response: AxiosResponse<string> = await api.get(`/registry/deployments/${name}/export?${queryParams}`)
    return response.data
  },

  async import(content: string, format: 'json' | 'yaml' = 'json', author: string = 'import'): Promise<Deployment> {
    const response: AxiosResponse<{ deployment: Deployment }> = await api.post('/registry/deployments/import', {
      content,
      format,
      author
    })
    return response.data.deployment
  }
}

// File-based Prompts API
export const promptFilesApi = {
  // List all .prompt files
  async list(params?: { category?: string; include_dirty?: boolean }): Promise<PromptFileSummary[]> {
    const queryParams = new URLSearchParams()
    if (params?.category) queryParams.append('category', params.category)
    if (params?.include_dirty !== undefined) queryParams.append('include_dirty', params.include_dirty.toString())

    const url = queryParams.toString() ? `/prompt-files/?${queryParams}` : '/prompt-files/'
    const response: AxiosResponse<PromptFileListResponse> = await api.get(url)
    return response.data.prompts
  },

  // Get a specific prompt file by name
  async get(name: string, version?: number): Promise<PromptFile> {
    // Use version-specific endpoint if version is provided
    const url = version !== undefined
      ? `/prompt-files/${name}/version/${version}`
      : `/prompt-files/${name}`
    const response: AxiosResponse<PromptFile> = await api.get(url)
    return response.data
  },

  // Create a new .prompt file
  async create(request: CreatePromptFileRequest): Promise<PromptFile> {
    const response: AxiosResponse<PromptFile> = await api.post('/prompt-files/', request)
    return response.data
  },

  // Update an existing .prompt file
  async update(name: string, request: UpdatePromptFileRequest): Promise<PromptFile> {
    const response: AxiosResponse<PromptFile> = await api.put(`/prompt-files/${name}`, request)
    return response.data
  },

  // Delete a .prompt file
  async delete(name: string): Promise<{ message: string }> {
    const response: AxiosResponse<{ message: string }> = await api.delete(`/prompt-files/${name}`)
    return response.data
  },

  // Get version history from Git
  async getHistory(name: string, limit: number = 20): Promise<VersionHistoryResponse> {
    const response: AxiosResponse<VersionHistoryResponse> = await api.get(`/prompt-files/${name}/history?limit=${limit}`)
    return response.data
  },

  // Get diff between two versions
  async getDiff(name: string, fromVersion: number, toVersion: number): Promise<{ diff: string }> {
    const response: AxiosResponse<{ diff: string }> = await api.get(
      `/prompt-files/${name}/diff?from_version=${fromVersion}&to_version=${toVersion}`
    )
    return response.data
  },

  // Render a prompt with variables
  async render(name: string, variables: Record<string, string>): Promise<RenderPromptFileResponse> {
    const response: AxiosResponse<RenderPromptFileResponse> = await api.post(`/prompt-files/${name}/render`, { variables })
    return response.data
  },

  // Validate a .prompt file
  async validate(name: string): Promise<ValidatePromptFileResponse> {
    const response: AxiosResponse<ValidatePromptFileResponse> = await api.get(`/prompt-files/${name}/validate`)
    return response.data
  },

  // Scan project for prompts
  async scan(params?: { include_python?: boolean; include_js?: boolean }): Promise<ScanResult> {
    const queryParams = new URLSearchParams()
    if (params?.include_python !== undefined) queryParams.append('include_python', params.include_python.toString())
    if (params?.include_js !== undefined) queryParams.append('include_js', params.include_js.toString())

    const url = queryParams.toString() ? `/prompt-files/scan?${queryParams}` : '/prompt-files/scan'
    const response: AxiosResponse<ScanResult> = await api.post(url)
    return response.data
  },

  // Git operations
  async getGitStatus(): Promise<GitStatusResponse> {
    const response: AxiosResponse<GitStatusResponse> = await api.get('/prompt-files/git/status')
    return response.data
  },

  async commit(name: string, message: string): Promise<CommitResponse> {
    const response: AxiosResponse<CommitResponse> = await api.post(`/prompt-files/${name}/commit`, { message })
    return response.data
  },

  async commitAll(message: string): Promise<CommitResponse> {
    const response: AxiosResponse<CommitResponse> = await api.post('/prompt-files/git/commit-all', { message })
    return response.data
  }
}

export default api