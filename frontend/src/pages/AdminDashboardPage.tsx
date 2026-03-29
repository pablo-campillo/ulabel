import { useEffect, useState, useCallback } from 'react'
import { Header } from '../components/Header'
import { AdminProjectCard } from '../components/admin/AdminProjectCard'
import { Pagination } from '../components/admin/Pagination'
import { FAB } from '../components/admin/FAB'
import { ProjectFormDialog } from '../components/admin/ProjectFormDialog'
import { getProjects, getProjectStats } from '../api/admin'
import { useDebounce } from '../hooks/useDebounce'
import type { Project } from '../types/api'

const PAGE_SIZE = 12

export function AdminDashboardPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [completionMap, setCompletionMap] = useState<Record<string, number>>({})
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [editProject, setEditProject] = useState<Project | null>(null)
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebounce(search, 300)

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  const fetchProjects = useCallback(async (p: number, name?: string) => {
    setLoading(true)
    setError('')
    try {
      const res = await getProjects(PAGE_SIZE, (p - 1) * PAGE_SIZE, name || undefined)
      setProjects(res.items)
      setTotal(res.total)

      const statsEntries = await Promise.all(
        res.items.map(async (project) => {
          try {
            const stats = await getProjectStats(project.id)
            const pct = stats.total_images > 0
              ? Math.round((stats.labeled_images / stats.total_images) * 100)
              : 0
            return [project.id, pct] as const
          } catch {
            return [project.id, 0] as const
          }
        }),
      )
      setCompletionMap(Object.fromEntries(statsEntries))
    } catch {
      setError('Failed to load projects.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchProjects(page, debouncedSearch)
  }, [page, debouncedSearch, fetchProjects])

  const handlePageChange = (p: number) => {
    setPage(p)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  useEffect(() => {
    setPage(1)
  }, [debouncedSearch])

  const handleDialogClose = (refreshNeeded?: boolean) => {
    setShowCreate(false)
    setEditProject(null)
    if (refreshNeeded) fetchProjects(page, debouncedSearch)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="max-w-5xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Projects</h1>
          {!loading && (
            <span className="text-sm text-gray-500">{total} total</span>
          )}
        </div>

        <div className="mb-6">
          <input
            type="text"
            placeholder="Search projects by name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
          />
        </div>

        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="w-10 h-10 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3">
            {error}
          </div>
        )}

        {!loading && !error && projects.length === 0 && (
          <div className="text-center py-20">
            <svg
              className="w-16 h-16 text-gray-300 mx-auto mb-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z"
              />
            </svg>
            <p className="text-gray-500 text-lg">No projects yet.</p>
            <p className="text-gray-400 text-sm mt-1">
              Click the + button to create your first project.
            </p>
          </div>
        )}

        {!loading && !error && projects.length > 0 && (
          <>
            <div className="grid gap-4 sm:grid-cols-2">
              {projects.map((project) => (
                <AdminProjectCard
                  key={project.id}
                  project={project}
                  onEdit={setEditProject}
                  completionPct={completionMap[project.id] ?? 0}
                />
              ))}
            </div>
            <Pagination
              currentPage={page}
              totalPages={totalPages}
              onPageChange={handlePageChange}
            />
          </>
        )}
      </main>

      <FAB onClick={() => setShowCreate(true)} />

      {(showCreate || editProject) && (
        <ProjectFormDialog
          project={editProject ?? undefined}
          onClose={handleDialogClose}
        />
      )}
    </div>
  )
}
