export interface ColumnStats {
  mean?: number;
  median?: number;
  std?: number;
  min?: number;
  max?: number;
}

export interface ColumnProfile {
  column: string;
  dtype: string;
  detected_type: string;
  unique_count: number;
  missing_count: number;
  missing_percentage: number;
  sample_values: unknown[];
  stats?: ColumnStats;
  note?: string;
}

export interface DataQuality {
  total_missing_values: number;
  duplicate_rows: number;
  duplicate_percentage: number;
  id_like_columns: string[];
  constant_columns: string[];
  high_cardinality_columns: string[];
}

export interface DatasetMetadata {
  filename: string;
  file_type: string;
  file_size_mb: number;
  rows: number;
  columns: number;
}

export interface DatasetFingerprint {
  metadata: DatasetMetadata;
  column_names: string[];
  preview_rows: Record<string, unknown>[];
  column_profiles: ColumnProfile[];
  data_quality: DataQuality;
  target_column_selected_by_user: string | null;
}

export interface Overview {
  rows: number;
  columns: number;
  numeric_columns: number;
  categorical_columns: number;
  datetime_columns: number;
  boolean_columns: number;
  text_columns: number;
  id_like_columns: number;
  duplicate_rows: number;
  total_missing_values: number;
  suggested_task: string;
}

export interface RuleBasedTaskSuggestion {
  suggested_task: string;
  reason: string;
  target_column: string | null;
}

export interface PrimaryTaskSuggestion {
  suggested_task: string;
  reason: string;
  target_column: string | null;
  source: 'llm' | 'rule_based';
  confidence: string | null;
  target_candidates: { column: string; reason: string; confidence: string }[] | null;
  domain_guess: string | null;
}

export interface ChartData {
  chart_type: string;
  title: string;
  data: Record<string, unknown>[];
}

export interface RecommendedChart {
  chart_type: 'bar' | 'histogram' | 'pie' | 'scatter' | 'boxplot' | 'grouped_bar';
  title: string;
  columns: string[];
  reason: string;
}

export interface PreprocessingStep {
  step_type: 'handle_missing' | 'label_encode' | 'one_hot_encode' | 'drop_column' | 'scale' | 'handle_outlier';
  columns: string[];
  method: string;
  reason: string;
}

export interface PreprocessingPreview {
  step_type: string;
  column: string;
  method: string;
  reason: string;
  before_sample: unknown[];
  after_sample: unknown[];
  summary: string;
}

export interface UploadResponse {
  success: boolean;
  dataset_id: string;
  filename: string;
  file_type: string;
  file_size_mb: number;
  rows: number;
  columns: number;
  preview: Record<string, unknown>[];
}

export interface AnalyzeResponse {
  success: boolean;
  dataset_id: string;
  overview: Overview;
  preview: Record<string, unknown>[];
  column_profiles: ColumnProfile[];
  data_quality: DataQuality;
  eda_charts: ChartData[];
  dataset_fingerprint: DatasetFingerprint;
  rule_based_task_suggestion: RuleBasedTaskSuggestion;
  llm_understanding: LLMUnderstanding | null;
  primary_task_suggestion: PrimaryTaskSuggestion;
  preprocessing_previews: PreprocessingPreview[];
}

export interface ResearchTitleSuggestion {
  title: string;
  description: string;
  task: string;
  method_suggestion: string;
}

export interface ResearchTaskSuggestion {
  task: string;
  description: string;
  suitable_methods: string[];
  evaluation_metrics: string[];
}

export interface ResearchPRDSuggestionsResponse {
  success: boolean;
  dataset_id: string;
  title_suggestions: ResearchTitleSuggestion[];
  task_suggestions: ResearchTaskSuggestion[];
  research_questions: string[];
}

export interface ResearchPRDResponse {
  success: boolean;
  dataset_id: string;
  prd_markdown: string;
}

export interface TargetCandidate {
  column: string;
  reason: string;
  confidence: string;
}

export interface LLMUnderstanding {
  dataset_understanding: string;
  domain_guess: string;
  target_candidates: TargetCandidate[];
  suggested_task: string;
  task_reason: string;
  recommended_eda: string[];
  recommended_charts: RecommendedChart[];
  preprocessing_recommendations: string[];
  preprocessing_steps: PreprocessingStep[];
  methodological_warnings: string[];
  user_confirmation_needed: string[];
}

export interface LLMResponse {
  success: boolean;
  dataset_id: string;
  llm_understanding?: LLMUnderstanding;
  message?: string;
}
