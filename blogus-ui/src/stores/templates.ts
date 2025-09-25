import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import { templateApi } from '@/services/api'
import type {
  Template,
  CreateTemplateRequest,
  RenderTemplateRequest,
  RenderTemplateResponse,
  ApiError,
  LoadingState
} from '@/types'

export const useTemplateStore = defineStore('templates', () => {
  // State
  const templates = ref<Template[]>([])
  const currentTemplate = ref<Template | null>(null)
  const renderedContent = ref<string>('')
  const categories = ref<string[]>([])
  const tags = ref<string[]>([])

  const loading = reactive<LoadingState>({
    create: false,
    fetch: false,
    list: false,
    update: false,
    delete: false,
    render: false,
    categories: false,
    tags: false,
    validate: false
  })

  const errors = reactive<Record<string, ApiError | null>>({
    create: null,
    fetch: null,
    list: null,
    update: null,
    delete: null,
    render: null,
    categories: null,
    tags: null,
    validate: null
  })

  // Actions
  const createTemplate = async (request: CreateTemplateRequest): Promise<Template | null> => {
    loading.create = true
    errors.create = null

    try {
      const response = await templateApi.create(request)
      templates.value.unshift(response.template)
      return response.template
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

  const fetchTemplate = async (id: string): Promise<Template | null> => {
    loading.fetch = true
    errors.fetch = null

    try {
      const response = await templateApi.get(id)
      currentTemplate.value = response
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

  const listTemplates = async (category?: string, tag?: string): Promise<Template[]> => {
    loading.list = true
    errors.list = null

    try {
      const response = await templateApi.list(category, tag)
      templates.value = response
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

  const updateTemplate = async (id: string, updates: Partial<Template>): Promise<Template | null> => {
    loading.update = true
    errors.update = null

    try {
      const response = await templateApi.update(id, updates)

      // Update in list
      const index = templates.value.findIndex(t => t.id === id)
      if (index !== -1) {
        templates.value[index] = response
      }

      // Update current if it's the same template
      if (currentTemplate.value?.id === id) {
        currentTemplate.value = response
      }

      return response
    } catch (error: any) {
      errors.update = {
        error: 'Update Failed',
        detail: error.response?.data?.detail || error.message
      }
      return null
    } finally {
      loading.update = false
    }
  }

  const deleteTemplate = async (id: string): Promise<boolean> => {
    loading.delete = true
    errors.delete = null

    try {
      await templateApi.delete(id)

      // Remove from list
      templates.value = templates.value.filter(t => t.id !== id)

      // Clear current if it's the deleted template
      if (currentTemplate.value?.id === id) {
        currentTemplate.value = null
      }

      return true
    } catch (error: any) {
      errors.delete = {
        error: 'Deletion Failed',
        detail: error.response?.data?.detail || error.message
      }
      return false
    } finally {
      loading.delete = false
    }
  }

  const renderTemplate = async (request: RenderTemplateRequest): Promise<RenderTemplateResponse | null> => {
    loading.render = true
    errors.render = null

    try {
      const response = await templateApi.render(request)
      renderedContent.value = response.rendered_content
      return response
    } catch (error: any) {
      errors.render = {
        error: 'Render Failed',
        detail: error.response?.data?.detail || error.message
      }
      return null
    } finally {
      loading.render = false
    }
  }

  const fetchCategories = async (): Promise<string[]> => {
    loading.categories = true
    errors.categories = null

    try {
      const response = await templateApi.getCategories()
      categories.value = response
      return response
    } catch (error: any) {
      errors.categories = {
        error: 'Categories Fetch Failed',
        detail: error.response?.data?.detail || error.message
      }
      return []
    } finally {
      loading.categories = false
    }
  }

  const fetchTags = async (): Promise<string[]> => {
    loading.tags = true
    errors.tags = null

    try {
      const response = await templateApi.getTags()
      tags.value = response
      return response
    } catch (error: any) {
      errors.tags = {
        error: 'Tags Fetch Failed',
        detail: error.response?.data?.detail || error.message
      }
      return []
    } finally {
      loading.tags = false
    }
  }

  const validateTemplate = async (content: string): Promise<string[] | null> => {
    loading.validate = true
    errors.validate = null

    try {
      const response = await templateApi.validate(content)
      return response.issues
    } catch (error: any) {
      errors.validate = {
        error: 'Validation Failed',
        detail: error.response?.data?.detail || error.message
      }
      return null
    } finally {
      loading.validate = false
    }
  }

  const clearErrors = () => {
    Object.keys(errors).forEach(key => {
      errors[key] = null
    })
  }

  return {
    // State
    templates,
    currentTemplate,
    renderedContent,
    categories,
    tags,
    loading,
    errors,

    // Actions
    createTemplate,
    fetchTemplate,
    listTemplates,
    updateTemplate,
    deleteTemplate,
    renderTemplate,
    fetchCategories,
    fetchTags,
    validateTemplate,
    clearErrors
  }
})