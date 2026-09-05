import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from './AuthContext'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import { Card } from '../../components/ui/Card'
import { Building2, AlertCircle } from 'lucide-react'

export function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      await login(email, password)
      navigate('/dashboard')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid credentials. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-bgApp px-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="flex justify-center mb-10">
          <div className="flex items-center gap-3">
            <div className="w-14 h-14 rounded-xl bg-white/10 flex items-center justify-center">
              <Building2 className="w-8 h-8 text-white" />
            </div>
            <span className="font-display text-3xl font-bold text-white">ConSight</span>
          </div>
        </div>

        {/* Login Card */}
        <Card className="w-full">
          <div className="text-center mb-8">
            <h1 className="text-2xl font-semibold text-white mb-2">Welcome back</h1>
            <p className="text-textMuted">Sign in to your ConSight account</p>
          </div>

          {error && (
            <div className="mb-6 flex items-center gap-2 p-3 bg-status-new-activity/15 border border-status-new-activity/30 rounded-lg text-status-new-activity text-sm" role="alert">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <Input
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="supervisor@demo.com"
              autoComplete="email"
              required
              disabled={isLoading}
            />
            <Input
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              autoComplete="current-password"
              required
              disabled={isLoading}
            />

            <Button type="submit" className="w-full" size="lg" loading={isLoading}>
              Sign in
            </Button>
          </form>

          <div className="mt-6 pt-6 border-t border-border">
            <p className="text-sm text-textMuted text-center mb-4">Demo credentials</p>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between text-textMuted">
                <span>Supervisor</span>
                <code className="bg-surfaceRaised px-2 py-0.5 rounded">supervisor@demo.com / supervisor123</code>
              </div>
              <div className="flex justify-between text-textMuted">
                <span>Planner</span>
                <code className="bg-surfaceRaised px-2 py-0.5 rounded">planner@demo.com / planner123</code>
              </div>
              <div className="flex justify-between text-textMuted">
                <span>Admin</span>
                <code className="bg-surfaceRaised px-2 py-0.5 rounded">admin@demo.com / admin123</code>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}