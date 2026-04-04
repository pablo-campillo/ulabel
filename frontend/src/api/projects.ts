import { request } from './client'
import type { ProjectSummary } from '../types/api'

export function getLabelerProjects(labelerId: string): Promise<ProjectSummary[]> {
  return request<ProjectSummary[]>(`/labelers/${labelerId}/projects`)
}
