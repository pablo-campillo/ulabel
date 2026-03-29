import { useNavigate } from 'react-router'
import { useAuthStore } from '../stores/authStore'

export function Header() {
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  const homeLink = user?.role === 'admin' ? '/admin' : '/dashboard'

  return (
    <header className="bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <button
          onClick={() => navigate(homeLink)}
          className="flex items-center gap-3 cursor-pointer"
        >
          <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
            <svg
              className="w-5 h-5 text-white"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A2 2 0 013 12V7a4 4 0 014-4z"
              />
            </svg>
          </div>
          <span className="text-xl font-bold text-gray-900">uLabel</span>
        </button>

        {user && (
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-500">
              Signed in as{' '}
              <span className="font-medium text-gray-800">{user.username}</span>
              {user.role === 'admin' && (
                <span className="ml-2 px-2 py-0.5 text-xs font-semibold bg-primary-100 text-primary-700 rounded-full">
                  Admin
                </span>
              )}
            </span>
            <button
              onClick={handleLogout}
              className="px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors cursor-pointer"
            >
              Logout
            </button>
          </div>
        )}
      </div>
    </header>
  )
}
