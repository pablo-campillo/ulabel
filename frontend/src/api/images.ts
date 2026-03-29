import { request } from './client'
import type { AssignedImage, SubmitLabelResult } from '../types/api'

export function createAssignment(
  projectId: string,
  labelerId: string,
): Promise<AssignedImage | null> {
  return request<AssignedImage | null>(
    `/projects/${projectId}/assignments`,
    {
      method: 'POST',
      body: JSON.stringify({ labeler_id: labelerId }),
    },
  )
}

export function submitLabel(
  projectId: string,
  imageId: string,
  body: { labeler_id: string; assignment_id: string; label: string },
): Promise<SubmitLabelResult> {
  return request<SubmitLabelResult>(
    `/projects/${projectId}/images/${imageId}/label`,
    {
      method: 'POST',
      body: JSON.stringify(body),
    },
  )
}
