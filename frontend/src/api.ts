import axios from 'axios';
import type {
  UploadResponse, AnalyzeResponse, LLMResponse, DatasetFingerprint,
  ResearchPRDSuggestionsResponse, ResearchPRDResponse, LLMUnderstanding, PrimaryTaskSuggestion,
} from './types';

const api = axios.create({ baseURL: '/api', timeout: 180000 });

export async function uploadDataset(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append('file', file);
  const res = await api.post<UploadResponse>('/datasets/upload', form);
  return res.data;
}

export async function analyzeDataset(
  datasetId: string,
  targetColumn?: string,
): Promise<AnalyzeResponse> {
  const res = await api.post<AnalyzeResponse>('/datasets/analyze', {
    dataset_id: datasetId,
    target_column: targetColumn || null,
  });
  return res.data;
}

export async function getLLMUnderstanding(
  datasetId: string,
  fingerprint: DatasetFingerprint,
): Promise<LLMResponse> {
  const res = await api.post<LLMResponse>('/llm/dataset-understanding', {
    dataset_id: datasetId,
    dataset_fingerprint: fingerprint,
  });
  return res.data;
}

export async function getResearchSuggestions(
  datasetId: string,
  fingerprint: DatasetFingerprint,
  llmUnderstanding?: LLMUnderstanding | null,
  primaryTaskSuggestion?: PrimaryTaskSuggestion | null,
): Promise<ResearchPRDSuggestionsResponse> {
  const res = await api.post<ResearchPRDSuggestionsResponse>('/research/suggestions', {
    dataset_id: datasetId,
    dataset_fingerprint: fingerprint,
    llm_understanding: llmUnderstanding || null,
    primary_task_suggestion: primaryTaskSuggestion || null,
  });
  return res.data;
}

export async function generateResearchPRD(data: {
  dataset_id: string;
  selected_title: string;
  selected_task: string;
  research_background: string;
  research_objectives: string[];
  research_questions: string[];
  target_column?: string | null;
  additional_notes?: string | null;
  dataset_fingerprint: DatasetFingerprint;
  llm_understanding?: LLMUnderstanding | null;
}): Promise<ResearchPRDResponse> {
  const res = await api.post<ResearchPRDResponse>('/research/generate-prd', data);
  return res.data;
}
