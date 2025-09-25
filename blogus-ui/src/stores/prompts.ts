import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import { promptApi } from '@/services/api'
import type {
  Prompt,
  AnalyzePromptRequest,
  AnalyzePromptResponse,
  ExecutePromptRequest,
  ExecutePromptResponse,
  GenerateTestRequest,
  GenerateTestResponse,
  CreatePromptRequest,
  ApiError,
  LoadingState
} from '@/types'

export const usePromptStore = defineStore('prompts', () => {
  // State
  const prompts = ref<Prompt[]>([])
  const currentPrompt = ref<Prompt | null>(null)
  const currentAnalysis = ref<AnalyzePromptResponse | null>(null)
  const currentExecution = ref<ExecutePromptResponse | null>(null)
  const currentTest = ref<GenerateTestResponse | null>(null)

  const loading = reactive<LoadingState>({
    analyze: false,
    execute: false,
    test: false,
    create: false,
    fetch: false,
    list: false
  })

  const errors = reactive<Record<string, ApiError | null>>({
    analyze: null,
    execute: null,
    test: null,
    create: null,
    fetch: null,
    list: null
  })

  // Actions
  const analyzePrompt = async (request: AnalyzePromptRequest): Promise<AnalyzePromptResponse | null> => {
    loading.analyze = true
    errors.analyze = null

    try {
      const response = await promptApi.analyze(request)
      currentAnalysis.value = response
      return response
    } catch (error: any) {
      errors.analyze = {
        error: 'Analysis Failed',
        detail: error.response?.data?.detail || error.message
      }
      return null
    } finally {
      loading.analyze = false
    }
  }

  const executePrompt = async (request: ExecutePromptRequest): Promise<ExecutePromptResponse | null> => {
    loading.execute = true
    errors.execute = null

    try {
      const response = await promptApi.execute(request)
      currentExecution.value = response
      return response
    } catch (error: any) {
      errors.execute = {
        error: 'Execution Failed',
        detail: error.response?.data?.detail || error.message
      }
      return null
    } finally {
      loading.execute = false
    }
  }

  const generateTest = async (request: GenerateTestRequest): Promise<GenerateTestResponse | null> => {
    loading.test = true
    errors.test = null

    try {
      const response = await promptApi.generateTest(request)
      currentTest.value = response
      return response
    } catch (error: any) {
      errors.test = {
        error: 'Test Generation Failed',
        detail: error.response?.data?.detail || error.message
      }
      return null
    } finally {
      loading.test = false
    }
  }

  const createPrompt = async (request: CreatePromptRequest): Promise<Prompt | null> => {
    loading.create = true
    errors.create = null

    try {
      const response = await promptApi.create(request)
      prompts.value.unshift(response)
      return response
    } catch (error: any) {
      errors.create = {
        error: 'Creation Failed',
        detail: error.response?.data?.detail || error.message
      }
      return null
    } finally {
      loading.create = false
    }
  }

  const fetchPrompt = async (id: string): Promise<Prompt | null> => {
    loading.fetch = true
    errors.fetch = null

    try {
      const response = await promptApi.get(id)
      currentPrompt.value = response
      return response
    } catch (error: any) {
      errors.fetch = {
        error: 'Fetch Failed',
        detail: error.response?.data?.detail || error.message
      }
      return null
    } finally {
      loading.fetch = false
    }
  }

  const listPrompts = async (): Promise<Prompt[]> => {
    loading.list = true
    errors.list = null

    try {
      const response = await promptApi.list()
      prompts.value = response
      return response
    } catch (error: any) {
      errors.list = {
        error: 'List Failed',
        detail: error.response?.data?.detail || error.message
      }
      return []
    } finally {
      loading.list = false
    }
  }

  const clearResults = () => {
    currentAnalysis.value = null
    currentExecution.value = null
    currentTest.value = null
  }

  const clearErrors = () => {
    Object.keys(errors).forEach(key => {
      errors[key] = null
    })
  }

  return {
    // State
    prompts,
    currentPrompt,
    currentAnalysis,
    currentExecution,
    currentTest,
    loading,
    errors,

    // Actions
    analyzePrompt,
    executePrompt,
    generateTest,
    createPrompt,
    fetchPrompt,
    listPrompts,
    clearResults,
    clearErrors
  }
})