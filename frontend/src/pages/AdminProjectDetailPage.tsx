import { useCallback, useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router'
import { Header } from '../components/Header'
import { CopyableUuid } from '../components/CopyableUuid'
import { ProjectFormDialog } from '../components/admin/ProjectFormDialog'
import { RefreshControl } from '../components/admin/RefreshControl'
import { DailyProgressChart } from '../components/admin/charts/DailyProgressChart'
import { LabelDistributionChart } from '../components/admin/charts/LabelDistributionChart'
import { LabelerActivityChart } from '../components/admin/charts/LabelerActivityChart'
import { LabelerLeaderboardChart } from '../components/admin/charts/LabelerLeaderboardChart'
import { getProject, getProjectStats, exportProject } from '../api/admin'
import type { ProjectDetail, ProjectStats } from '../types/api'

export function AdminProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const [project, setProject] = useState<ProjectDetail | null>(null)
  const [stats, setStats] = useState<ProjectStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showEdit, setShowEdit] = useState(false)
  const [exportError, setExportError] = useState('')
  const [refreshing, setRefreshing] = useState(false)

  const fetchData = async () => {
    if (!projectId) return
    setLoading(true)
    setError('')
    try {
      const [projectRes, statsRes] = await Promise.all([
        getProject(projectId),
        getProjectStats(projectId),
      ])
      setProject(projectRes)
      setStats(statsRes)
    } catch {
      setError('Failed to load project data.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [projectId])

  const refreshStats = useCallback(async () => {
    if (!projectId) return
    setRefreshing(true)
    try {
      const statsRes = await getProjectStats(projectId)
      setStats(statsRes)
    } catch {
      // silently fail on auto-refresh to avoid disrupting the view
    } finally {
      setRefreshing(false)
    }
  }, [projectId])

  const handleEditClose = (refreshNeeded?: boolean) => {
    setShowEdit(false)
    if (refreshNeeded) fetchData()
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="flex items-center justify-center py-20">
          <div className="w-10 h-10 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
        </div>
      </div>
    )
  }

  if (error || !project || !stats) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <main className="max-w-5xl mx-auto px-6 py-8">
          <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3">
            {error || 'Project not found'}
          </div>
          <button
            onClick={() => navigate('/admin')}
            className="mt-4 text-sm text-primary-600 hover:text-primary-700 cursor-pointer"
          >
            Back to projects
          </button>
        </main>
      </div>
    )
  }

  const completionPct =
    stats.total_images > 0
      ? Math.round((stats.labeled_images / stats.total_images) * 100)
      : 0

  const labels = [...project.labels].sort()

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* Back navigation */}
        <button
          onClick={() => navigate('/admin')}
          className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-primary-600 mb-4 cursor-pointer transition-colors"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
          </svg>
          Back to projects
        </button>

        {/* Project header */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{project.name}</h1>
              <CopyableUuid uuid={project.id} />
              <p className="text-gray-600 mt-2">{project.description}</p>
            </div>
            <button
              onClick={() => setShowEdit(true)}
              className="px-4 py-2 text-sm font-medium text-primary-600 bg-primary-50 rounded-lg hover:bg-primary-100 transition-colors cursor-pointer flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
              </svg>
              Edit
            </button>
          </div>

          {/* Labels */}
          <div className="flex flex-wrap gap-2 mt-4">
            {labels.map((label) => (
              <span
                key={label}
                className="px-2.5 py-1 bg-primary-50 text-primary-700 text-xs font-medium rounded-lg"
              >
                {label}
              </span>
            ))}
          </div>

          {/* Labelers */}
          {project.labelers.length > 0 && (
            <div className="mt-4">
              <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                Assigned Labelers
              </span>
              <div className="flex flex-wrap gap-2 mt-1.5">
                {project.labelers.map((labeler) => (
                  <span
                    key={labeler.id}
                    className="px-2.5 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded-lg"
                  >
                    {labeler.username}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Stats summary */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Total Images</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">{stats.total_images.toLocaleString()}</p>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Labeled</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">{stats.labeled_images.toLocaleString()}</p>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Completion</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">{completionPct}%</p>
            <div className="mt-2 h-1.5 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-primary-600 rounded-full transition-all"
                style={{ width: `${completionPct}%` }}
              />
            </div>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Remaining</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">
              {(stats.total_images - stats.labeled_images).toLocaleString()}
            </p>
          </div>
        </div>

        {/* Export & Refresh controls */}
        <div className="flex flex-col gap-2 mb-6">
          <div className="flex items-center gap-2">
            <div className="flex gap-2">
            <button
              onClick={() => {
                setExportError('')
                exportProject(projectId!, 'json').catch((e) => setExportError(e.message))
              }}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
              </svg>
              Export JSON
            </button>
            <button
              onClick={() => {
                setExportError('')
                exportProject(projectId!, 'csv').catch((e) => setExportError(e.message))
              }}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
              </svg>
              Export CSV
            </button>
            </div>
            <div className="ml-auto">
              <RefreshControl onRefresh={refreshStats} refreshing={refreshing} />
            </div>
          </div>
          {exportError && (
            <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-2">
              {exportError}
            </div>
          )}
        </div>

        {/* Charts grid */}
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="lg:col-span-2">
            <DailyProgressChart stats={stats} labels={labels} />
          </div>
          <LabelDistributionChart distribution={stats.class_distribution} />
          <LabelerLeaderboardChart
            labelerCounts={stats.labeler_class_counts}
            labels={labels}
          />
          <div className="lg:col-span-2">
            <LabelerActivityChart
              labelerActivity={stats.labeler_daily_activity}
              labels={labels}
            />
          </div>
        </div>
      </main>

      {showEdit && (
        <ProjectFormDialog project={project} onClose={handleEditClose} />
      )}
    </div>
  )
}
