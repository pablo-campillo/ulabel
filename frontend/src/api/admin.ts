import { request, requestMultipart } from './client'
import type {
  ProjectSummary,
  ProjectDetail,
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
  return request<PaginatedResponse<ProjectSummary>>(`/projects?${params}`)
}

export function getProject(projectId: string) {
  return request<ProjectDetail>(`/projects/${projectId}`)
}

export function createProject(payload: CreateProjectPayload) {
  return request<ProjectDetail>('/projects', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateProject(projectId: string, payload: UpdateProjectPayload) {
  return request<ProjectDetail>(`/projects/${projectId}`, {
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

export async function exportProject(projectId: string, format: 'json' | 'csv'): Promise<void> {
  const res = await fetch(`/v1/projects/${projectId}/export?format=${format}`, {
    redirect: 'follow',
  })

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    const code = body?.error?.code
    if (code === 'STORAGE_FULL') {
      throw new ApiError(res.status, 'Storage is full. Please free up space and try again.')
    }
    if (code === 'NO_LABELS_FOUND') {
      throw new ApiError(res.status, 'No labels to export yet.')
    }
    throw new ApiError(res.status, body?.error?.message || 'Export failed')
  }

  // The response followed the redirect to MinIO — trigger download from the blob
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `labels.${format}`
  a.click()
  URL.revokeObjectURL(url)
}

export function searchLabelers(query: string, limit = 10) {
  return request<LabelerAutocompleteItem[]>(
    `/labelers/autocomplete?q=${encodeURIComponent(query)}&limit=${limit}`,
  )
}

export function getProjectStats(projectId: string) {
  return request<ProjectStats>(`/projects/${projectId}/stats`)
}
