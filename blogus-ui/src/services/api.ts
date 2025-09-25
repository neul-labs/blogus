import axios, { type AxiosResponse } from 'axios'
import type {
  AnalyzePromptRequest,
  AnalyzePromptResponse,
  ExecutePromptRequest,
  ExecutePromptResponse,
  GenerateTestRequest,
  GenerateTestResponse,
  CreatePromptRequest,
  Prompt,
  Template,
  CreateTemplateRequest,
  RenderTemplateRequest,
  RenderTemplateResponse
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

  async list(): Promise<Prompt[]> {
    const response: AxiosResponse<Prompt[]> = await api.get('/prompts/')
    return response.data
  }
}

// Template API
export const templateApi = {
  async create(request: CreateTemplateRequest): Promise<{ template: Template }> {
    const response: AxiosResponse<{ template: Template }> = await api.post('/templates/', request)
    return response.data
  },

  async get(id: string): Promise<Template> {
    const response: AxiosResponse<Template> = await api.get(`/templates/${id}`)
    return response.data
  },

  async list(category?: string, tag?: string): Promise<Template[]> {
    const params = new URLSearchParams()
    if (category) params.append('category', category)
    if (tag) params.append('tag', tag)

    const response: AxiosResponse<Template[]> = await api.get(`/templates/?${params}`)
    return response.data
  },

  async update(id: string, updates: Partial<Template>): Promise<Template> {
    const response: AxiosResponse<Template> = await api.put(`/templates/${id}`, updates)
    return response.data
  },

  async delete(id: string): Promise<{ message: string }> {
    const response: AxiosResponse<{ message: string }> = await api.delete(`/templates/${id}`)
    return response.data
  },

  async render(request: RenderTemplateRequest): Promise<RenderTemplateResponse> {
    const { template_id, variables } = request
    const response: AxiosResponse<RenderTemplateResponse> = await api.post(
      `/templates/${template_id}/render`,
      { variables }
    )
    return response.data
  },

  async getCategories(): Promise<string[]> {
    const response: AxiosResponse<string[]> = await api.get('/templates/categories/')
    return response.data
  },

  async getTags(): Promise<string[]> {
    const response: AxiosResponse<string[]> = await api.get('/templates/tags/')
    return response.data
  },

  async validate(content: string): Promise<{ issues: string[] }> {
    const response: AxiosResponse<{ issues: string[] }> = await api.post('/templates/validate', { content })
    return response.data
  }
}

export default api