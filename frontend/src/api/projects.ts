import { request } from './client'
import type { Project } from '../types/api'

export function getLabelerProjects(labelerId: string): Promise<Project[]> {
  return request<Project[]>(`/labelers/${labelerId}/projects`)
}
