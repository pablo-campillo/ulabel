import { useEffect, useState, useCallback, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router'
import { useAuthStore } from '../stores/authStore'
import {
  useLabelingStore,
  type LabelingPhase,
} from '../stores/labelingStore'
import { getLabelerProjects } from '../api/projects'
import { getProjectStats } from '../api/stats'
import { getNextImage, submitLabel } from '../api/images'
import { deriveLabelerStats } from '../lib/stats'
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts'
import { Header } from '../components/Header'
import { LabelSidebar } from '../components/LabelSidebar'
import { ImageViewer } from '../components/ImageViewer'
import { ActionButton } from '../components/ActionButton'
import { RankingBadge } from '../components/RankingBadge'

export function LabelingPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)!

  const {
    project,
    image,
    labelCount,
    ranking,
    totalLabelers,
    previousRanking,
    phase,
    setProject,
    setImage,
    setInitialStats,
    onLabelSubmitted,
    setPhase,
    reset,
  } = useLabelingStore()

  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  // Load project data on mount
  useEffect(() => {
    async function load() {
      if (!projectId) return

      try {
        const projects = await getLabelerProjects(user.id)
        const proj = projects.find((p) => p.id === projectId)
        if (!proj) {
          setError('Project not found.')
          setLoading(false)
          return
        }
        setProject(proj)

        try {
          const stats = await getProjectStats(projectId)
          const derived = deriveLabelerStats(stats, user.id)
          setInitialStats(derived.count, derived.ranking, derived.totalLabelers)
        } catch {
          setInitialStats(0, 0, 0)
        }

        setPhase('idle')
      } catch {
        setError('Failed to load project.')
      } finally {
        setLoading(false)
      }
    }

    reset()
    load()

    return () => {
      reset()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, user.id])

  const fetchNextImage = useCallback(async () => {
    if (!projectId) return

    setLoading(true)
    try {
      const img = await getNextImage(projectId, user.id)
      if (img) {
        setImage(img)
        setPhase('labeling')
      } else {
        setPhase('no_more_images')
      }
    } catch {
      setError('Failed to load next image.')
    } finally {
      setLoading(false)
    }
  }, [projectId, user.id, setImage, setPhase])

  const handleStart = useCallback(() => {
    fetchNextImage()
  }, [fetchNextImage])

  const handleLabelSelect = useCallback(
    async (label: string) => {
      if (!projectId || !image || submitting) return

      setSubmitting(true)
      try {
        const result = await submitLabel(projectId, image.id, {
          labeler_id: user.id,
          assignment_id: image.assignment_id,
          label,
        })
        onLabelSubmitted(result)
        setImage(null)
      } catch {
        setError('Failed to submit label.')
      } finally {
        setSubmitting(false)
      }
    },
    [projectId, image, user.id, submitting, onLabelSubmitted, setImage],
  )

  const handleNext = useCallback(() => {
    fetchNextImage()
  }, [fetchNextImage])

  const handleFinish = useCallback(() => {
    navigate('/dashboard')
  }, [navigate])

  // Sort labels for consistent keyboard mapping
  const sortedLabels = useMemo(
    () => (project ? [...project.labels].sort() : []),
    [project],
  )

  // Keyboard shortcuts per phase
  const shortcuts = useMemo(() => {
    const map: Record<string, () => void> = {}

    if (phase === 'idle') {
      map['Enter'] = handleStart
    } else if (phase === 'labeling') {
      sortedLabels.forEach((label, index) => {
        if (index < 9) {
          map[String(index + 1)] = () => handleLabelSelect(label)
        }
      })
    } else if (phase === 'submitted') {
      map['Enter'] = handleNext
      map['Escape'] = handleFinish
    } else if (phase === 'no_more_images') {
      map['Escape'] = handleFinish
    }

    return map
  }, [
    phase,
    sortedLabels,
    handleStart,
    handleLabelSelect,
    handleNext,
    handleFinish,
  ])

  useKeyboardShortcuts(shortcuts, !loading && !submitting)

  if (loading && !project) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="flex items-center justify-center py-32">
          <div className="w-10 h-10 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
        </div>
      </div>
    )
  }

  if (error && !project) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="max-w-2xl mx-auto px-6 py-16 text-center">
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3">
            {error}
          </div>
          <button
            onClick={() => navigate('/dashboard')}
            className="mt-4 text-primary-600 hover:text-primary-800 font-medium cursor-pointer"
          >
            Back to Projects
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Header />

      {project && (
        <main className="flex-1 flex flex-col max-w-7xl mx-auto w-full px-6 py-6">
          {/* Project header */}
          <div className="flex items-start justify-between mb-6">
            <div className="flex-1 min-w-0 mr-6">
              <h1 className="text-2xl font-bold text-gray-900 mb-1">
                {project.name}
              </h1>
              <p className="text-gray-500 text-sm leading-relaxed">
                {project.description}
              </p>
            </div>
            <RankingBadge
              ranking={ranking}
              totalLabelers={totalLabelers}
              previousRanking={previousRanking}
              labelCount={labelCount}
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3 mb-4">
              {error}
            </div>
          )}

          {/* Main content area */}
          <div className="flex-1 flex gap-6">
            {/* Sidebar */}
            <LabelSidebar
              labels={sortedLabels}
              disabled={phase !== 'labeling' || submitting}
              onSelect={handleLabelSelect}
            />

            {/* Center area */}
            <div className="flex-1 flex items-center justify-center">
              <CenterContent
                phase={phase}
                image={image}
                loading={loading}
                submitting={submitting}
                onStart={handleStart}
                onNext={handleNext}
                onFinish={handleFinish}
              />
            </div>
          </div>
        </main>
      )}
    </div>
  )
}

function CenterContent({
  phase,
  image,
  loading,
  submitting,
  onStart,
  onNext,
  onFinish,
}: {
  phase: LabelingPhase
  image: ReturnType<typeof useLabelingStore.getState>['image']
  loading: boolean
  submitting: boolean
  onStart: () => void
  onNext: () => void
  onFinish: () => void
}) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-10 h-10 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
      </div>
    )
  }

  if (phase === 'idle') {
    return (
      <div className="text-center">
        <div className="w-24 h-24 bg-primary-50 rounded-full flex items-center justify-center mx-auto mb-6">
          <svg
            className="w-12 h-12 text-primary-500"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909M3.75 21h16.5A2.25 2.25 0 0022.5 18.75V5.25A2.25 2.25 0 0020.25 3H3.75A2.25 2.25 0 001.5 5.25v13.5A2.25 2.25 0 003.75 21z"
            />
          </svg>
        </div>
        <p className="text-gray-500 mb-6">
          Ready to start labeling images?
        </p>
        <ActionButton label="Start" shortcutHint="Enter" onClick={onStart} />
      </div>
    )
  }

  if (phase === 'labeling' && image) {
    return (
      <div className="w-full relative">
        <ImageViewer url={image.presigned_url} />
        {submitting && (
          <div className="absolute inset-0 bg-white/60 flex items-center justify-center rounded-xl">
            <div className="w-8 h-8 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
          </div>
        )}
      </div>
    )
  }

  if (phase === 'submitted') {
    return (
      <div className="text-center">
        <div className="w-20 h-20 bg-green-50 rounded-full flex items-center justify-center mx-auto mb-6">
          <svg
            className="w-10 h-10 text-green-500"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M4.5 12.75l6 6 9-13.5"
            />
          </svg>
        </div>
        <p className="text-gray-600 font-medium mb-6">Label submitted!</p>
        <div className="flex items-center gap-3 justify-center">
          <ActionButton label="Next" shortcutHint="Enter" onClick={onNext} />
          <ActionButton
            label="Finish"
            shortcutHint="Esc"
            variant="secondary"
            onClick={onFinish}
          />
        </div>
      </div>
    )
  }

  if (phase === 'no_more_images') {
    return (
      <div className="text-center">
        <div className="w-20 h-20 bg-amber-50 rounded-full flex items-center justify-center mx-auto mb-6">
          <svg
            className="w-10 h-10 text-amber-500"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
            />
          </svg>
        </div>
        <p className="text-gray-600 font-medium mb-2">
          No more images available
        </p>
        <p className="text-gray-400 text-sm mb-6">
          All images in this project have been labeled.
        </p>
        <ActionButton
          label="Back to Projects"
          shortcutHint="Esc"
          variant="secondary"
          onClick={onFinish}
        />
      </div>
    )
  }

  return null
}
