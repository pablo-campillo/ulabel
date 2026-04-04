import { useEffect, useState } from 'react'
import { useAuthStore } from '../stores/authStore'
import { getLabelerProjects } from '../api/projects'
import { getProjectStats } from '../api/stats'
import { deriveLabelerStats } from '../lib/stats'
import { Header } from '../components/Header'
import { ProjectCard } from '../components/ProjectCard'
import type { ProjectSummary } from '../types/api'

interface ProjectWithStats {
  project: ProjectSummary
  count: number
  ranking: number
  totalLabelers: number
  completionPct: number
}

export function DashboardPage() {
  const user = useAuthStore((s) => s.user)!
  const [projects, setProjects] = useState<ProjectWithStats[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function load() {
      try {
        const projectList = await getLabelerProjects(user.id)

        const withStats = await Promise.all(
          projectList.map(async (project) => {
            try {
              const stats = await getProjectStats(project.id)
              const derived = deriveLabelerStats(stats, user.id)
              const completionPct = stats.total_images > 0
                ? Math.round((stats.labeled_images / stats.total_images) * 100)
                : 0
              return { project, ...derived, completionPct }
            } catch {
              return { project, count: 0, ranking: 0, totalLabelers: 0, completionPct: 0 }
            }
          }),
        )

        withStats.sort(
          (a, b) =>
            new Date(a.project.created_at).getTime() -
            new Date(b.project.created_at).getTime(),
        )

        setProjects(withStats)
      } catch {
        setError('Failed to load projects.')
      } finally {
        setLoading(false)
      }
    }

    load()
  }, [user.id])

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="max-w-4xl mx-auto px-6 py-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">
          Your Projects
        </h1>

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
            <p className="text-gray-500 text-lg">No projects assigned yet.</p>
            <p className="text-gray-400 text-sm mt-1">
              Ask an admin to add you to a project.
            </p>
          </div>
        )}

        {!loading && !error && projects.length > 0 && (
          <div className="space-y-3">
            {projects.map(({ project, count, ranking, totalLabelers, completionPct }) => (
              <ProjectCard
                key={project.id}
                id={project.id}
                name={project.name}
                createdAt={project.created_at}
                labelCount={count}
                ranking={ranking}
                totalLabelers={totalLabelers}
                completionPct={completionPct}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
