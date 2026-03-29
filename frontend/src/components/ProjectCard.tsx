import { useNavigate } from 'react-router'

interface ProjectCardProps {
  id: string
  name: string
  createdAt: string
  labelCount: number
  ranking: number
  totalLabelers: number
  completionPct: number
}

export function ProjectCard({
  id,
  name,
  createdAt,
  labelCount,
  ranking,
  totalLabelers,
  completionPct,
}: ProjectCardProps) {
  const navigate = useNavigate()
  const date = new Date(createdAt).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })

  return (
    <button
      onClick={() => navigate(`/project/${id}`)}
      className="w-full bg-white rounded-xl border border-gray-200 p-5 hover:border-primary-300 hover:shadow-md transition-all text-left cursor-pointer group"
    >
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-gray-900 group-hover:text-primary-700 transition-colors truncate">
            {name}
          </h3>
          <p className="text-sm text-gray-500 mt-1">{date}</p>
          <div className="mt-2 flex items-center gap-2">
            <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden max-w-[180px]">
              <div
                className="h-full bg-primary-500 rounded-full transition-all"
                style={{ width: `${completionPct}%` }}
              />
            </div>
            <span className="text-xs font-medium text-gray-500">{completionPct}%</span>
          </div>
        </div>

        <div className="flex items-center gap-3 ml-4">
          <div className="bg-primary-50 rounded-lg px-3 py-1.5 text-center min-w-[70px]">
            <div className="text-xs text-primary-600 font-medium">Labels</div>
            <div className="text-lg font-bold text-primary-700">
              {labelCount}
            </div>
          </div>
          <div className="bg-gray-50 rounded-lg px-3 py-1.5 text-center min-w-[70px]">
            <div className="text-xs text-gray-500 font-medium">Rank</div>
            <div className="text-lg font-bold text-gray-700">
              {ranking > 0 ? `#${ranking}` : '---'}
              {totalLabelers > 0 && ranking > 0 && (
                <span className="text-xs font-normal text-gray-400">
                  /{totalLabelers}
                </span>
              )}
            </div>
          </div>

          <svg
            className="w-5 h-5 text-gray-300 group-hover:text-primary-500 transition-colors"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M9 5l7 7-7 7"
            />
          </svg>
        </div>
      </div>
    </button>
  )
}
