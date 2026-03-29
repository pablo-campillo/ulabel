import { request, requestMultipart } from './client'
import type {
  Project,
  PaginatedResponse,
  CreateProjectPayload,
  UpdateProjectPayload,
  ImageResponse,
  ImportJobResponse,
  LabelerAutocompleteItem,
  ProjectStats,
} from '../types/api'

export function getProjects(limit = 20, offset = 0, name?: string) {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  if (name) params.set('name', name)
  return request<PaginatedResponse<Project>>(`/projects?${params}`)
}

export function createProject(payload: CreateProjectPayload) {
  return request<Project>('/projects', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateProject(projectId: string, payload: UpdateProjectPayload) {
  return request<Project>(`/projects/${projectId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function uploadImage(projectId: string, file: File) {
  const form = new FormData()
  form.append('file', file)
  return requestMultipart<ImageResponse>(
    `/projects/${projectId}/images/upload`,
    form,
  )
}

export function importImages(projectId: string, prefix: string) {
  return request<ImportJobResponse>(`/projects/${projectId}/images/import`, {
    method: 'POST',
    body: JSON.stringify({ prefix }),
  })
}

export function getImportStatus(projectId: string, importId: string) {
  return request<ImportJobResponse>(
    `/projects/${projectId}/images/imports/${importId}`,
  )
}

export function exportProject(projectId: string, format: 'json' | 'csv') {
  window.open(`/v1/projects/${projectId}/export?format=${format}`, '_blank')
}

export function searchLabelers(query: string, limit = 10) {
  return request<LabelerAutocompleteItem[]>(
    `/labelers/autocomplete?q=${encodeURIComponent(query)}&limit=${limit}`,
  )
}

export function getProjectStats(projectId: string) {
  return request<ProjectStats>(`/projects/${projectId}/stats`)
}
