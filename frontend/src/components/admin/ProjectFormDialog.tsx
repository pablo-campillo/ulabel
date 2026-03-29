import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuthStore } from '../../stores/authStore'
import { createProject, updateProject } from '../../api/admin'
import { TagInput } from './TagInput'
import { LabelerAutocomplete } from './LabelerAutocomplete'
import { ImageUploadSection } from './ImageUploadSection'
import type { Project, LabelerAutocompleteItem } from '../../types/api'

interface Props {
  project?: Project
  onClose: (refreshNeeded?: boolean) => void
}

export function ProjectFormDialog({ project, onClose }: Props) {
  const user = useAuthStore((s) => s.user)!
  const isEdit = !!project

  const [name, setName] = useState(project?.name ?? '')
  const [description, setDescription] = useState(project?.description ?? '')
  const [labels, setLabels] = useState<string[]>(project?.labels ?? [])
  const [labelers, setLabelers] = useState<LabelerAutocompleteItem[]>(
    project?.labelers ?? [],
  )
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)
  const [createdProjectId, setCreatedProjectId] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) return

    setSubmitting(true)
    setError('')

    try {
      if (isEdit) {
        await updateProject(project.id, {
          name: name.trim(),
          description: description.trim(),
          labeler_ids: labelers.map((l) => l.id),
        })
        setSaved(true)
      } else {
        if (labels.length === 0) {
          setError('Please add at least one label.')
          setSubmitting(false)
          return
        }
        const created = await createProject({
          owner_id: user.id,
          name: name.trim(),
          description: description.trim(),
          labels,
        })

        if (labelers.length > 0) {
          await updateProject(created.id, {
            labeler_ids: labelers.map((l) => l.id),
          })
        }

        setCreatedProjectId(created.id)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-black/40"
          onClick={() => onClose()}
        />

        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          className="relative bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto"
        >
          <div className="sticky top-0 bg-white border-b border-gray-100 px-6 py-4 rounded-t-2xl z-10">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">
                {isEdit ? 'Edit Project' : 'New Project'}
              </h2>
              <button
                onClick={() => onClose()}
                className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg cursor-pointer transition-colors"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="px-6 py-4 space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Project Name
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Vehicle Classification"
                required
                className="w-full px-3 py-2 rounded-lg border border-gray-300 focus:border-primary-500 focus:ring-2 focus:ring-primary-200 outline-none transition-all text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Task Description
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe what labelers should do..."
                rows={3}
                className="w-full px-3 py-2 rounded-lg border border-gray-300 focus:border-primary-500 focus:ring-2 focus:ring-primary-200 outline-none transition-all text-sm resize-none"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Labels
                {isEdit && (
                  <span className="ml-2 text-xs text-gray-400 font-normal">
                    (cannot be changed after creation)
                  </span>
                )}
              </label>
              <TagInput tags={labels} onChange={setLabels} disabled={isEdit} />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Assigned Labelers
              </label>
              <LabelerAutocomplete
                selectedLabelers={labelers}
                onChange={setLabelers}
              />
            </div>

            {(isEdit || createdProjectId) && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Images
                </label>
                <ImageUploadSection projectId={isEdit ? project.id : createdProjectId!} />
              </div>
            )}

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-3 py-2">
                {error}
              </div>
            )}

            {saved && !error && (
              <div className="bg-green-50 border border-green-200 text-green-700 text-sm rounded-lg px-3 py-2">
                Changes saved successfully.
              </div>
            )}

            <div className="flex gap-3 pt-2 pb-2">
              {!createdProjectId || isEdit ? (
                <>
                  <button
                    type="button"
                    onClick={() => onClose(saved)}
                    className="flex-1 px-4 py-2.5 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors cursor-pointer"
                  >
                    {isEdit ? 'Close' : 'Cancel'}
                  </button>
                  <button
                    type="submit"
                    disabled={submitting || !name.trim()}
                    className="flex-1 px-4 py-2.5 text-sm font-semibold text-white bg-primary-600 rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer transition-colors"
                  >
                    {submitting ? (
                      <span className="inline-flex items-center gap-2 justify-center">
                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        {isEdit ? 'Saving...' : 'Creating...'}
                      </span>
                    ) : isEdit ? (
                      'Save Changes'
                    ) : (
                      'Create Project'
                    )}
                  </button>
                </>
              ) : (
                <button
                  type="button"
                  onClick={() => onClose(true)}
                  className="w-full px-4 py-2.5 text-sm font-semibold text-white bg-primary-600 rounded-lg hover:bg-primary-700 cursor-pointer transition-colors"
                >
                  Done
                </button>
              )}
            </div>
          </form>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}
