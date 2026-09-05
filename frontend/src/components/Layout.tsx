import { useState } from 'react'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { cn } from '../lib/utils'
import { useAuth } from '../features/auth/AuthContext'
import {
  LayoutDashboard,
  GitBranch,
  ClipboardList,
  MessageSquare,
  Inbox,
  BarChart3,
  AlertTriangle,
  Box,
  Settings,
  Users,
  LogOut,
  Menu,
  ChevronDown,
  Building2,
} from 'lucide-react'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Schedule', href: '/schedule', icon: GitBranch },
  { name: 'Planner Queue', href: '/planner-queue', icon: ClipboardList },
  { name: 'Time Agent', href: '/time-agent', icon: MessageSquare },
  { name: 'Inbound', href: '/inbound', icon: Inbox },
  { name: 'Insights', href: '/insights', icon: BarChart3 },
  { name: 'Risk Watchlist', href: '/risk', icon: AlertTriangle },
  { name: 'BIM Viewer', href: '/bim', icon: Box },
]

const adminNavigation = [
  { name: 'Users & Roles', href: '/admin', icon: Users },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const { user, logout, hasRole } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-bgApp flex">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed lg:static inset-y-0 left-0 z-50 w-64 bg-surface border-r border-border transform transition-transform duration-300 ease-in-out',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="p-6 border-b border-border">
            <NavLink to="/dashboard" className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-white/10 flex items-center justify-center">
                <LayoutDashboard className="w-6 h-6 text-white" />
              </div>
              <span className="font-display text-xl font-bold text-white">ConSight</span>
            </NavLink>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-1 overflow-y-auto" role="navigation" aria-label="Main navigation">
            {navigation.map((item) => (
              <NavLink
                key={item.name}
                to={item.href}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200',
                    isActive
                      ? 'bg-white/10 text-white'
                      : 'text-textMuted hover:text-white hover:bg-white/5'
                  )
                }
                onClick={() => setSidebarOpen(false)}
              >
                <item.icon className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
                {item.name}
              </NavLink>
            ))}

            {hasRole(['SYSTEM_ADMIN', 'CONTRACTOR_ADMIN']) && (
              <>
                <div className="pt-4 border-t border-border" />
                <p className="px-3 text-xs font-semibold text-textMuted uppercase tracking-wider">
                  Administration
                </p>
                {adminNavigation.map((item) => (
                  <NavLink
                    key={item.name}
                    to={item.href}
                    className={({ isActive }) =>
                      cn(
                        'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200',
                        isActive
                          ? 'bg-white/10 text-white'
                          : 'text-textMuted hover:text-white hover:bg-white/5'
                      )
                    }
                    onClick={() => setSidebarOpen(false)}
                  >
                    <item.icon className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
                    {item.name}
                  </NavLink>
                ))}
              </>
            )}
          </nav>

          {/* User section */}
          <div className="p-4 border-t border-border">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center">
                <span className="text-sm font-medium text-white">
                  {user?.full_name?.split(' ').map(n => n[0]).join('').toUpperCase() || 'U'}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">{user?.full_name}</p>
                <p className="text-xs text-textMuted truncate capitalize">{user?.role?.toLowerCase().replace('_', ' ')}</p>
              </div>
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="p-1.5 rounded-lg text-textMuted hover:text-white hover:bg-white/5 transition-colors"
                aria-expanded={userMenuOpen}
                aria-haspopup="true"
              >
                <ChevronDown className={cn('w-4 h-4 transition-transform', userMenuOpen && 'rotate-180')} />
              </button>
            </div>

            {userMenuOpen && (
              <div className="mt-3 py-2 bg-surfaceRaised rounded-lg border border-border animate-slide-up">
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-3 px-3 py-2 text-sm text-textMuted hover:text-status-new-activity hover:bg-white/5 rounded-lg transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  Sign out
                </button>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col lg:ml-0">
        {/* Top bar */}
        <header className="sticky top-0 z-30 bg-surface/80 backdrop-blur-sm border-b border-border">
          <div className="flex items-center justify-between h-16 px-4 lg:px-6">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 rounded-lg text-textMuted hover:text-white hover:bg-white/5 transition-colors"
              aria-label="Open menu"
            >
              <Menu className="w-6 h-6" />
            </button>

            <div className="flex-1 lg:flex-none" />

            <div className="flex items-center gap-4">
              {/* Project switcher */}
              <div className="hidden lg:block relative">
                <button className="flex items-center gap-2 px-3 py-1.5 bg-surfaceRaised border border-border rounded-lg text-sm text-textMuted hover:text-white hover:border-white/20 transition-colors">
                  <Building2 className="w-4 h-4" />
                  <span>Demo Highway Project</span>
                  <ChevronDown className="w-4 h-4" />
                </button>
              </div>

              {/* Notifications */}
              <button className="p-2 rounded-lg text-textMuted hover:text-white hover:bg-white/5 transition-colors relative">
                <Inbox className="w-5 h-5" />
                <span className="absolute -top-1 -right-1 w-4 h-4 bg-status-new-activity text-[10px] font-bold rounded-full flex items-center justify-center">
                  3
                </span>
              </button>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 p-4 lg:p-6" role="main">
          <Outlet />
        </main>
      </div>
    </div>
  )
}