import { useState, useRef, useEffect } from 'react'
import { uploadImage, importImages, getImportStatus } from '../../api/admin'

interface Props {
  projectId: string
}

interface FileUploadState {
  file: File
  status: 'pending' | 'uploading' | 'done' | 'error'
  error?: string
}

export function ImageUploadSection({ projectId }: Props) {
  const [tab, setTab] = useState<'upload' | 'import'>('upload')
  const [files, setFiles] = useState<FileUploadState[]>([])
  const [prefix, setPrefix] = useState('')
  const [importStatus, setImportStatus] = useState<{
    status: string
    imported: number
    error: string | null
  } | null>(null)
  const [importLoading, setImportLoading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const pollRef = useRef<number | null>(null)

  useEffect(() => {
    return () => {
      if (pollRef.current !== null) clearInterval(pollRef.current)
    }
  }, [])

  const handleFiles = async (newFiles: File[]) => {
    const entries: FileUploadState[] = newFiles.map((f) => ({ file: f, status: 'pending' }))
    setFiles((prev) => [...prev, ...entries])

    for (const entry of entries) {
      setFiles((prev) =>
        prev.map((f) => (f.file === entry.file ? { ...f, status: 'uploading' } : f)),
      )
      try {
        await uploadImage(projectId, entry.file)
        setFiles((prev) =>
          prev.map((f) => (f.file === entry.file ? { ...f, status: 'done' } : f)),
        )
      } catch {
        setFiles((prev) =>
          prev.map((f) =>
            f.file === entry.file ? { ...f, status: 'error', error: 'Upload failed' } : f,
          ),
        )
      }
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const dropped = Array.from(e.dataTransfer.files).filter((f) =>
      f.type.startsWith('image/'),
    )
    if (dropped.length) handleFiles(dropped)
  }

  const handleImport = async () => {
    if (!prefix.trim()) return
    setImportLoading(true)
    setImportStatus(null)
    try {
      const job = await importImages(projectId, prefix.trim())
      setImportStatus({ status: job.status, imported: job.imported, error: null })

      if (job.status === 'running') {
        pollRef.current = window.setInterval(async () => {
          try {
            const updated = await getImportStatus(projectId, job.import_id)
            setImportStatus({ status: updated.status, imported: updated.imported, error: updated.error })
            if (updated.status !== 'running') {
              clearInterval(pollRef.current!)
              pollRef.current = null
              setImportLoading(false)
            }
          } catch {
            if (pollRef.current !== null) clearInterval(pollRef.current)
            pollRef.current = null
            setImportLoading(false)
          }
        }, 2000)
      } else {
        setImportLoading(false)
      }
    } catch {
      setImportStatus({ status: 'failed', imported: 0, error: 'Failed to start import' })
      setImportLoading(false)
    }
  }

  return (
    <div>
      <div className="flex gap-1 mb-3 bg-gray-100 rounded-lg p-1">
        <button
          type="button"
          onClick={() => setTab('upload')}
          className={`flex-1 px-3 py-1.5 text-sm font-medium rounded-md transition-colors cursor-pointer ${
            tab === 'upload' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Upload Files
        </button>
        <button
          type="button"
          onClick={() => setTab('import')}
          className={`flex-1 px-3 py-1.5 text-sm font-medium rounded-md transition-colors cursor-pointer ${
            tab === 'import' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Import by Prefix
        </button>
      </div>

      {tab === 'upload' && (
        <div>
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-primary-400 hover:bg-primary-50/50 transition-colors cursor-pointer"
          >
            <svg
              className="w-8 h-8 text-gray-400 mx-auto mb-2"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 16.5V9.75m0 0l3 3m-3-3l-3 3M6.75 19.5a4.5 4.5 0 01-1.41-8.775 5.25 5.25 0 0110.233-2.33 3 3 0 013.758 3.848A3.752 3.752 0 0118 19.5H6.75z"
              />
            </svg>
            <p className="text-sm text-gray-600">
              Drop images here or <span className="text-primary-600 font-medium">click to browse</span>
            </p>
            <p className="text-xs text-gray-400 mt-1">Supports JPG, PNG, WebP</p>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept="image/*"
            className="hidden"
            onChange={(e) => {
              const selected = Array.from(e.target.files || [])
              if (selected.length) handleFiles(selected)
              e.target.value = ''
            }}
          />

          {files.length > 0 && (
            <div className="mt-3 max-h-40 overflow-y-auto space-y-1.5">
              {files.map((f, i) => (
                <div key={i} className="flex items-center gap-2 text-sm">
                  {f.status === 'uploading' && (
                    <div className="w-4 h-4 border-2 border-gray-300 border-t-primary-600 rounded-full animate-spin shrink-0" />
                  )}
                  {f.status === 'done' && (
                    <svg className="w-4 h-4 text-green-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                    </svg>
                  )}
                  {f.status === 'error' && (
                    <svg className="w-4 h-4 text-red-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  )}
                  {f.status === 'pending' && (
                    <div className="w-4 h-4 bg-gray-200 rounded-full shrink-0" />
                  )}
                  <span className="truncate text-gray-700">{f.file.name}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {tab === 'import' && (
        <div>
          <div className="flex gap-2">
            <input
              type="text"
              value={prefix}
              onChange={(e) => setPrefix(e.target.value)}
              placeholder="e.g. raw/batch-01/"
              className="flex-1 px-3 py-2 rounded-lg border border-gray-300 focus:border-primary-500 focus:ring-2 focus:ring-primary-200 outline-none transition-all text-sm"
            />
            <button
              type="button"
              onClick={handleImport}
              disabled={importLoading || !prefix.trim()}
              className="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer transition-colors"
            >
              {importLoading ? 'Importing...' : 'Import'}
            </button>
          </div>
          <p className="text-xs text-gray-400 mt-1.5">
            Path prefix in the object store where images are located
          </p>

          {importStatus && (
            <div
              className={`mt-3 text-sm px-3 py-2 rounded-lg ${
                importStatus.status === 'done'
                  ? 'bg-green-50 text-green-700'
                  : importStatus.status === 'failed'
                    ? 'bg-red-50 text-red-700'
                    : 'bg-blue-50 text-blue-700'
              }`}
            >
              {importStatus.status === 'running' && (
                <span>Importing... {importStatus.imported} images imported so far</span>
              )}
              {importStatus.status === 'done' && (
                <span>Import complete. {importStatus.imported} images imported.</span>
              )}
              {importStatus.status === 'failed' && (
                <span>Import failed: {importStatus.error || 'Unknown error'}</span>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
