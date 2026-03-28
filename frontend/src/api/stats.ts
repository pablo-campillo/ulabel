import { request } from './client'
import type { ProjectStats } from '../types/api'

export function getProjectStats(projectId: string): Promise<ProjectStats> {
  return request<ProjectStats>(`/projects/${projectId}/stats`)
}
