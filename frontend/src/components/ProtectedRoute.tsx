import { Navigate } from 'react-router'
import { useAuthStore } from '../stores/authStore'

interface Props {
  children: React.ReactNode
  requiredRole?: 'admin' | 'labeler'
}

export function ProtectedRoute({ children, requiredRole }: Props) {
  const user = useAuthStore((s) => s.user)

  if (!user) {
    return <Navigate to="/" replace />
  }

  if (requiredRole && user.role !== requiredRole) {
    const redirect = user.role === 'admin' ? '/admin' : '/dashboard'
    return <Navigate to={redirect} replace />
  }

  return <>{children}</>
}
