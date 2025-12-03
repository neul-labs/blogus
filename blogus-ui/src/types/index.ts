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
  prompt_id?: string
}

export interface TestCase {
  input_variables: Record<string, any>
  expected_output: string
  goal_relevance: number
}

export interface GenerateTestResponse {
  test_case: TestCase
  prompt_id?: string
}

// Unified Prompt - the core entity
export interface Prompt {
  id: string
  name: string
  description: string
  content: string
  goal?: string
  category: string
  tags: string[]
  author: string
  version: number
  variables: string[]
  is_template: boolean
  usage_count: number
  created_at: string
  updated_at: string
}

export interface PromptListResponse {
  prompts: Prompt[]
  total: number
}

// API Request Types
export interface AnalyzePromptRequest {
  prompt_text?: string
  prompt_id?: string
  judge_model: string
  goal?: string
}

export interface ExecutePromptRequest {
  prompt_text?: string
  prompt_id?: string
  target_model: string
  variables?: Record<string, string>
}

export interface GenerateTestRequest {
  prompt_text?: string
  prompt_id?: string
  judge_model: string
  goal?: string
}

export interface CreatePromptRequest {
  name: string
  content: string
  description?: string
  goal?: string
  category?: string
  tags?: string[]
  author?: string
}

export interface UpdatePromptRequest {
  name?: string
  content?: string
  description?: string
  goal?: string
  category?: string
  tags?: string[]
  author?: string
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

// ==================== Registry Types ====================

export interface ModelParameters {
  temperature: number
  max_tokens: number
  top_p: number
  frequency_penalty: number
  presence_penalty: number
  stop_sequences: string[]
}

export interface ModelConfig {
  model_id: string
  parameters: ModelParameters
  fallback_models: string[]
}

export interface VersionRecord {
  version: number
  content_hash: string
  content: string
  model_config: ModelConfig
  created_at: string
  created_by: string
  change_summary?: string
}

export interface TrafficRoute {
  version: number
  weight: number
  model_override?: string
}

export interface TrafficConfig {
  routes: TrafficRoute[]
  shadow_version?: number
}

export interface Deployment {
  id: string
  name: string
  description: string
  content: string
  goal?: string
  model_config: ModelConfig
  tags: string[]
  category: string
  author: string
  version: number
  version_history: VersionRecord[]
  traffic_config?: TrafficConfig
  status: 'active' | 'inactive' | 'archived'
  is_template: boolean
  template_variables: string[]
  created_at: string
  updated_at: string
}

export interface DeploymentSummary {
  id: string
  name: string
  description: string
  model_id: string
  version: number
  status: string
  category: string
  author: string
  tags: string[]
  is_template: boolean
  updated_at: string
}

export interface ExecutionResult {
  prompt_name: string
  version: number
  model_used: string
  response: string
  latency_ms: number
  input_tokens: number
  output_tokens: number
  total_tokens: number
  estimated_cost_usd: number
  shadow_response?: string
}

export interface MetricsSummary {
  prompt_name: string
  version?: number
  total_executions: number
  success_rate: number
  avg_latency_ms: number
  p95_latency_ms: number
  total_tokens: number
  total_cost_usd: number
  period_hours: number
}

// Registry Request Types
export interface RegisterDeploymentRequest {
  name: string
  description: string
  content: string
  model_id: string
  goal?: string
  temperature?: number
  max_tokens?: number
  top_p?: number
  fallback_models?: string[]
  tags?: string[]
  category?: string
  author?: string
}

export interface UpdateContentRequest {
  name: string
  new_content: string
  author: string
  change_summary?: string
}

export interface UpdateModelRequest {
  name: string
  model_id: string
  temperature?: number
  max_tokens?: number
  top_p?: number
  fallback_models?: string[]
  author: string
  change_summary?: string
}

export interface SetTrafficConfigRequest {
  name: string
  routes: TrafficRoute[]
  shadow_version?: number
}

export interface ExecuteDeploymentRequest {
  name: string
  variables?: Record<string, string>
}

export interface RollbackRequest {
  name: string
  target_version: number
  author: string
}

// Registry Response Types
export interface RegisterDeploymentResponse {
  deployment: Deployment
}

export interface ExecuteDeploymentResponse {
  result: ExecutionResult
}

export interface GetMetricsResponse {
  metrics: MetricsSummary
}

export interface CompareVersionsResponse {
  comparisons: Record<number, MetricsSummary>
}

// ==================== Multi-Model Execution Types ====================

export interface MultiModelExecuteRequest {
  prompt_text: string
  models: string[]
  variables?: Record<string, string>
}

export interface MultiModelCompareRequest {
  prompt_text: string
  models: string[]
  goal?: string
  reference_output?: string
  variables?: Record<string, string>
  include_llm_assessment?: boolean
}

export interface ModelExecution {
  id: string
  model: string
  output: string
  latency_ms: number
  success: boolean
  error?: string
}

export interface MultiModelExecuteResponse {
  prompt_id: string
  prompt_text: string
  total_duration_ms: number
  executions: ModelExecution[]
}

export interface SemanticSimilarity {
  model_a: string
  model_b: string
  similarity_score: number
  method: string
}

export interface ModelEvaluation {
  model: string
  scores: {
    goal_achievement: number
    accuracy: number
    clarity: number
    completeness: number
  }
  overall_score: number
  strengths: string[]
  weaknesses: string[]
}

export interface LLMAssessment {
  judge_model: string
  evaluations: ModelEvaluation[]
  recommendation: string
  key_differences: string[]
}

export interface ModelMetrics {
  output_length: number
  latency_ms: number
  token_count: number
  semantic_similarity_avg: number
  llm_evaluation_score?: number
}

export interface ComparisonSummary {
  total_models: number
  best_performing_model?: string
  fastest_model?: string
  average_agreement_score: number
  most_similar_pair?: [string, string]
  least_similar_pair?: [string, string]
}

export interface OutputComparison {
  semantic_similarities: SemanticSimilarity[]
  llm_assessment?: LLMAssessment
  model_metrics: Record<string, ModelMetrics>
  summary: ComparisonSummary
}

export interface MultiModelCompareResponse {
  prompt_id: string
  prompt_text: string
  total_duration_ms: number
  executions: ModelExecution[]
  comparison: OutputComparison
}

export interface AvailableModelsResponse {
  models: string[]
}

// ==================== File-Based Prompt Types ====================

export interface PromptFileVariable {
  name: string
  description: string
  required: boolean
  default?: string
  enum?: string[]
}

export interface PromptFileModel {
  id: string
  temperature: number
  max_tokens?: number
}

export interface PromptFileVersion {
  version: number
  content_hash: string
  commit_sha?: string
  timestamp: string
  author: string
  message: string
  tag?: string
}

export interface PromptFile {
  name: string
  file_path: string
  description: string
  category: string
  author: string
  tags: string[]
  model: PromptFileModel
  goal?: string
  variables: PromptFileVariable[]
  content: string
  content_hash: string
  version: number
  commit_sha?: string
  is_dirty: boolean
  last_modified: string
}

export interface PromptFileSummary {
  name: string
  file_path: string
  description: string
  category: string
  author: string
  tags: string[]
  model_id: string
  version: number
  is_dirty: boolean
  variable_count: number
  last_modified: string
}

export interface PromptFileListResponse {
  prompts: PromptFileSummary[]
  total: number
}

export interface VersionHistoryResponse {
  prompt_name: string
  versions: PromptFileVersion[]
  total: number
}

export interface CreatePromptFileRequest {
  name: string
  content: string
  description?: string
  goal?: string
  category?: string
  tags?: string[]
  author?: string
  model_id?: string
  temperature?: number
  max_tokens?: number
  variables?: PromptFileVariable[]
}

export interface UpdatePromptFileRequest {
  content?: string
  description?: string
  goal?: string
  category?: string
  tags?: string[]
  model_id?: string
  temperature?: number
  max_tokens?: number
  variables?: PromptFileVariable[]
}

export interface RenderPromptFileRequest {
  name: string
  variables: Record<string, string>
}

export interface RenderPromptFileResponse {
  rendered_content: string
  variables_used: string[]
}

export interface ValidatePromptFileResponse {
  is_valid: boolean
  errors: string[]
  warnings: string[]
}

// Scan types
export interface DetectedPrompt {
  file: string
  line: number
  type: string
  language: string
  api?: string
  linked_to?: string
  status: 'versioned' | 'unversioned'
  hash: string
}

export interface ScanPromptFile {
  name: string
  path: string
  version: number
  hash: string
  is_dirty: boolean
}

export interface ScanResult {
  project_path: string
  scan_time: string
  stats: {
    total_detections: number
    versioned: number
    unversioned: number
  }
  prompt_files: ScanPromptFile[]
  detections: DetectedPrompt[]
}

// Git types
export interface DirtyFile {
  name: string
  path: string
  status: string
}

export interface GitStatusResponse {
  branch: string | null
  head_sha: string | null
  dirty_files: DirtyFile[]
  total_dirty: number
}

export interface CommitResponse {
  commit_sha: string
  message: string
  files_committed: string[]
}