// API Response Types
export interface PromptAnalysis {
  prompt_id: string
  goal_alignment: number
  effectiveness: number
  suggestions: string[]
  status: string
  inferred_goal?: string
}

export interface PromptFragment {
  text: string
  fragment_type: string
  goal_alignment: number
  improvement_suggestion: string
}

export interface AnalyzePromptResponse {
  analysis: PromptAnalysis
  fragments: PromptFragment[]
}

export interface ExecutePromptResponse {
  result: string
  model_used: string
  duration: number
}

export interface TestCase {
  input_variables: Record<string, any>
  expected_output: string
  goal_relevance: number
}

export interface GenerateTestResponse {
  test_case: TestCase
}

export interface Prompt {
  id: string
  text: string
  goal?: string
  created_at?: string
  updated_at?: string
}

export interface Template {
  id: string
  name: string
  description: string
  content: string
  category: string
  tags: string[]
  author: string
  version: string
  variables: string[]
  usage_count: number
  created_at?: string
  updated_at?: string
}

export interface RenderTemplateResponse {
  rendered_content: string
}

// API Request Types
export interface AnalyzePromptRequest {
  prompt_text: string
  judge_model: string
  goal?: string
}

export interface ExecutePromptRequest {
  prompt_text: string
  target_model: string
}

export interface GenerateTestRequest {
  prompt_text: string
  judge_model: string
  goal?: string
}

export interface CreatePromptRequest {
  text: string
  goal?: string
}

export interface CreateTemplateRequest {
  template_id: string
  name: string
  description: string
  content: string
  category?: string
  tags?: string[]
  author?: string
}

export interface RenderTemplateRequest {
  template_id: string
  variables: Record<string, any>
}

// UI State Types
export interface ApiError {
  error: string
  detail: string
}

export interface LoadingState {
  [key: string]: boolean
}

// Navigation
export interface NavItem {
  name: string
  path: string
  icon?: string
  children?: NavItem[]
}