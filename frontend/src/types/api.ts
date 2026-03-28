export interface User {
  id: string
  username: string
  role: 'admin' | 'labeler'
}

export interface LabelerInfo {
  id: string
  username: string
}

export interface Project {
  id: string
  owner_id: string
  name: string
  description: string
  labels: string[]
  labelers: LabelerInfo[]
  created_at: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  limit: number
  offset: number
}

export interface AssignedImage {
  id: string
  project_id: string
  status: string
  assignment_id: string
  presigned_url: string
  presigned_url_expires_in: number
}

export interface SubmitLabelResult {
  id: string
  project_id: string
  image_id: string
  labeler_id: string
  label: string
  labeler_count: number
  ranking: number
  total_labelers: number
}

export interface LabelerClassCount {
  labeler_id: string
  username: string
  counts: Record<string, number>
}

export interface LabelerDailyEntry {
  date: string
  counts: Record<string, number>
}

export interface LabelerDailyActivity {
  labeler_id: string
  username: string
  daily: LabelerDailyEntry[]
}

export interface DailyLabelerTotal {
  labeler_id: string
  username: string
  count: number
}

export interface DailyTotal {
  date: string
  labelers: DailyLabelerTotal[]
}

export interface ProjectStats {
  total_images: number
  labeled_images: number
  class_distribution: Record<string, number>
  labeler_class_counts: LabelerClassCount[]
  labeler_daily_activity: LabelerDailyActivity[]
  daily_totals: DailyTotal[]
}

export interface CreateProjectPayload {
  owner_id: string
  name: string
  description: string
  labels: string[]
}

export interface UpdateProjectPayload {
  name?: string
  description?: string
  labeler_ids?: string[]
}

export interface ImageResponse {
  id: string
  project_id: string
  storage_key: string
  status: string
}

export interface ImportJobResponse {
  import_id: string
  project_id: string
  prefix: string
  status: 'running' | 'done' | 'failed'
  imported: number
  error: string | null
}

export interface LabelerAutocompleteItem {
  id: string
  username: string
}
