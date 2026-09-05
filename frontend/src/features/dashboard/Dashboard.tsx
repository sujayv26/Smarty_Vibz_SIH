import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui'
import { Badge } from '../../components/ui/Badge'
import { useAuth } from '../auth/AuthContext'
import { cn } from '../../lib/utils'
import {
  GitBranch,
  ClipboardList,
  AlertTriangle,
  TrendingUp,
  Clock,
  CheckCircle,
  AlertCircle,
  XCircle,
  MessageSquare,
  BarChart3,
} from 'lucide-react'

const stats = [
  { label: 'Total Activities', value: '274', icon: GitBranch, color: 'text-blue-400' },
  { label: 'Field Events (7d)', value: '42', icon: Clock, color: 'text-green-400' },
  { label: 'Pending Reviews', value: '8', icon: ClipboardList, color: 'text-amber-400' },
  { label: 'Critical Delays', value: '3', icon: AlertTriangle, color: 'text-red-400' },
]

const recentActivity = [
  { id: 1, activity: 'Erect Line 24-XX-101', discipline: 'Piping', status: 'START', time: '2h ago', confidence: 0.92 },
  { id: 2, activity: 'Install Support for XX-101', discipline: 'Piping', status: 'COMPLETE', time: '4h ago', confidence: 0.88 },
  { id: 3, activity: 'Pump P-101 Installation', discipline: 'Mechanical', status: 'DELAY', time: '6h ago', confidence: 0.65 },
  { id: 4, activity: 'Foundation A1 Pour', discipline: 'Civil', status: 'PROGRESS', time: '8h ago', confidence: 0.78 },
  { id: 5, activity: 'Hydrotest Line XX-101', discipline: 'Piping', status: 'HOLD', time: '1d ago', confidence: 0.45 },
]

export function Dashboard() {
  const { user } = useAuth()

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white">Dashboard</h1>
          <p className="text-textMuted mt-1">Welcome back, {user?.full_name?.split(' ')[0]}. Here&apos;s your project overview.</p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="neutral">DEMO-001</Badge>
          <Badge variant="auto-commit" dot>Live</Badge>
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <Card key={stat.label} hover>
            <CardContent className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm text-textMuted mb-1">{stat.label}</p>
                <p className="text-3xl font-bold text-white kpi">{stat.value}</p>
              </div>
              <div className={cn('w-12 h-12 rounded-lg flex items-center justify-center', stat.color)}>
                <stat.icon className="w-6 h-6" aria-hidden="true" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Main content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Activity */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Recent Field Events</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-border">
              {recentActivity.map((event) => (
                <div key={event.id} className="p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 hover:bg-white/5 transition-colors">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className={cn('w-10 h-10 rounded-lg flex items-center justify-center', 
                      event.status === 'START' && 'bg-green-500/20 text-green-400',
                      event.status === 'COMPLETE' && 'bg-blue-500/20 text-blue-400',
                      event.status === 'DELAY' && 'bg-red-500/20 text-red-400',
                      event.status === 'PROGRESS' && 'bg-amber-500/20 text-amber-400',
                      event.status === 'HOLD' && 'bg-gray-500/20 text-gray-400'
                    )}>
                      {event.status === 'START' && <CheckCircle className="w-5 h-5" />}
                      {event.status === 'COMPLETE' && <CheckCircle className="w-5 h-5" />}
                      {event.status === 'DELAY' && <AlertCircle className="w-5 h-5" />}
                      {event.status === 'PROGRESS' && <Clock className="w-5 h-5" />}
                      {event.status === 'HOLD' && <XCircle className="w-5 h-5" />}
                    </div>
                    <div className="min-w-0">
                      <p className="font-medium text-white truncate">{event.activity}</p>
                      <p className="text-sm text-textMuted">{event.discipline} • {event.time}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge variant={event.confidence > 0.85 ? 'auto-commit' : event.confidence > 0.6 ? 'review' : 'new-activity'} dot>
                      {event.confidence > 0.85 ? 'Auto-commit' : event.confidence > 0.6 ? 'Review' : 'New Activity'}
                    </Badge>
                    <span className="text-sm font-mono text-textMuted">{Math.round(event.confidence * 100)}%</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <button className="w-full flex items-center gap-3 p-3 rounded-lg bg-surfaceRaised border border-border hover:bg-white/5 hover:border-white/10 transition-all text-left group">
              <div className="w-10 h-10 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center group-hover:scale-110 transition-transform">
                <GitBranch className="w-5 h-5" />
              </div>
              <div>
                <p className="font-medium text-white">View Schedule</p>
                <p className="text-sm text-textMuted">Browse WBS tree & activities</p>
              </div>
            </button>
            <button className="w-full flex items-center gap-3 p-3 rounded-lg bg-surfaceRaised border border-border hover:bg-white/5 hover:border-white/10 transition-all text-left group">
              <div className="w-10 h-10 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center group-hover:scale-110 transition-transform">
                <ClipboardList className="w-5 h-5" />
              </div>
              <div>
                <p className="font-medium text-white">Planner Queue</p>
                <p className="text-sm text-textMuted">Review pending matches (8)</p>
              </div>
            </button>
            <button className="w-full flex items-center gap-3 p-3 rounded-lg bg-surfaceRaised border border-border hover:bg-white/5 hover:border-white/10 transition-all text-left group">
              <div className="w-10 h-10 rounded-lg bg-green-500/20 text-green-400 flex items-center justify-center group-hover:scale-110 transition-transform">
                <MessageSquare className="w-5 h-5" />
              </div>
              <div>
                <p className="font-medium text-white">Time Agent</p>
                <p className="text-sm text-textMuted">Log progress via chat/voice</p>
              </div>
            </button>
            <button className="w-full flex items-center gap-3 p-3 rounded-lg bg-surfaceRaised border border-border hover:bg-white/5 hover:border-white/10 transition-all text-left group">
              <div className="w-10 h-10 rounded-lg bg-purple-500/20 text-purple-400 flex items-center justify-center group-hover:scale-110 transition-transform">
                <BarChart3 className="w-5 h-5" />
              </div>
              <div>
                <p className="font-medium text-white">Insights</p>
                <p className="text-sm text-textMuted">Productivity & delay analytics</p>
              </div>
            </button>
          </CardContent>
        </Card>
      </div>

      {/* Bottom row - Delay & Risk Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-400" />
              Active Delay Risks
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {[
              { activity: 'Pump P-101 Installation', delay: '5 days', critical: true, cause: 'Material delivery' },
              { activity: 'Foundation A1 Pour', delay: '2 days', critical: false, cause: 'Weather' },
              { activity: 'Cable Pull - Level 3', delay: '3 days', critical: true, cause: 'Resource shortage' },
            ].map((item, i) => (
              <div key={i} className="p-3 rounded-lg bg-surfaceRaised border border-border flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-white">{item.activity}</p>
                  <p className="text-sm text-textMuted">Cause: {item.cause}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={item.critical ? 'new-activity' : 'review'}>{item.delay}</Badge>
                  {item.critical && <Badge variant="new-activity" dot>Critical Path</Badge>}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-green-400" />
              Productivity Snapshot
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {[
              { discipline: 'Piping', planned: 120, actual: 105, unit: 'm/day', trend: 'up' },
              { discipline: 'Civil', planned: 80, actual: 85, unit: 'm³/day', trend: 'up' },
              { discipline: 'Mechanical', planned: 15, actual: 12, unit: 'units/day', trend: 'down' },
              { discipline: 'Electrical', planned: 200, actual: 195, unit: 'm/day', trend: 'down' },
            ].map((item, i) => (
              <div key={i} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center text-sm font-medium">
                    {item.discipline.slice(0, 2).toUpperCase()}
                  </div>
                  <div>
                    <p className="font-medium text-white">{item.discipline}</p>
                    <p className="text-sm text-textMuted">Target: {item.planned} {item.unit}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={cn('font-semibold', item.trend === 'up' ? 'text-green-400' : 'text-red-400')}>
                    {item.actual} {item.unit}
                  </p>
                  <p className="text-xs text-textMuted">{item.trend === 'up' ? '+5%' : '-15%'} vs plan</p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}