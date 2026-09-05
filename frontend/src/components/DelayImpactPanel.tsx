import { useState, useEffect, useCallback } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from './ui/Card'
import { Badge } from './ui/Badge'
import { DataTable } from './ui/Table'
import { Skeleton } from './ui/Skeleton'
import { EmptyState } from './ui/EmptyState'
import { AlertTriangle, GitBranch, AlertCircle } from 'lucide-react'
import { api } from '../lib/api'

interface DelayImpact {
  id: number
  source_event_id: number
  source_activity_code: string | null
  source_activity_name: string | null
  impacted_activity_code: string
  impacted_activity_name: string
  impacted_discipline: string
  impacted_wbs: string
  impacted_planned_start: string | null
  impacted_planned_finish: string | null
  impact_type: 'DIRECT' | 'PROPAGATED' | 'FLOAT_CONSUMED' | 'CRITICAL_PATH'
  relationship_type: string | null
  lag_days: number
  original_delay_days: number
  propagated_delay_days: number
  float_consumed_days: number
  remaining_float_days: number | null
  is_critical_path: boolean
  critical_path_exposure: boolean
  path_depth: number
  computed_at: string
}

interface DelayImpactPanelProps {
  projectId: number
  eventId?: number
  activityId?: number
  className?: string
}

const impactTypeColors: Record<string, 'auto-commit' | 'review' | 'new-activity'> = {
  DIRECT: 'review',
  PROPAGATED: 'new-activity',
  FLOAT_CONSUMED: 'review',
  CRITICAL_PATH: 'new-activity',
}

const impactTypeLabels = {
  DIRECT: 'Direct Impact',
  PROPAGATED: 'Propagated',
  FLOAT_CONSUMED: 'Float Consumed',
  CRITICAL_PATH: 'Critical Path',
} as const

const impactTypeIcons = {
  DIRECT: GitBranch,
  PROPAGATED: GitBranch,
  FLOAT_CONSUMED: AlertTriangle,
  CRITICAL_PATH: AlertCircle,
} as const

export function DelayImpactPanel({ projectId, eventId, activityId, className = '' }: DelayImpactPanelProps) {
  const [impacts, setImpacts] = useState<DelayImpact[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchImpacts = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      let url = `/delay-impacts/project/${projectId}/critical`
      if (eventId) {
        url = `/delay-impacts/event/${eventId}`
      } else if (activityId) {
        url = `/delay-impacts/activity/${activityId}?project_id=${projectId}`
      }
      const response = await api.get(url)
      setImpacts(response.data.impacts || [])
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch delay impacts')
    } finally {
      setIsLoading(false)
    }
  }, [projectId, eventId, activityId])

  useEffect(() => {
    fetchImpacts()
  }, [fetchImpacts])

  const getImpactTypeBadge = (impact: DelayImpact) => {
    const Icon = impactTypeIcons[impact.impact_type]
    const variant = impactTypeColors[impact.impact_type]
    return (
      <Badge variant={variant} dot className="flex items-center gap-1">
        <Icon className="w-3 h-3" />
        {impactTypeLabels[impact.impact_type]}
      </Badge>
    )
  }

  const columns = [
    { key: 'impact_type', header: 'Type', width: '140px', render: (row: DelayImpact) => getImpactTypeBadge(row) },
    { key: 'impacted_activity_code', header: 'Activity Code', width: '130px' },
    { key: 'impacted_activity_name', header: 'Activity Name', width: '200px' },
    { key: 'impacted_discipline', header: 'Discipline', width: '100px' },
    { key: 'impacted_wbs', header: 'WBS', width: '100px' },
    { key: 'propagated_delay_days', header: 'Delay (days)', width: '100px', render: (row: DelayImpact) => (
      <span className={row.is_critical_path ? 'text-status-new-activity font-medium' : 'text-textMuted'}>
        +{row.propagated_delay_days}d
      </span>
    )},
    { key: 'float_consumed_days', header: 'Float Used', width: '100px', render: (row: DelayImpact) => (
      <span className={row.float_consumed_days > 0 ? 'text-status-review' : 'text-textMuted'}>
        {row.float_consumed_days}d
      </span>
    )},
    { key: 'remaining_float_days', header: 'Remaining Float', width: '120px', render: (row: DelayImpact) => (
      <span className={row.remaining_float_days !== null && row.remaining_float_days <= 0 ? 'text-status-new-activity font-medium' : 'text-textMuted'}>
        {row.remaining_float_days !== null ? `${row.remaining_float_days}d` : 'N/A'}
      </span>
    )},
    { key: 'relationship_type', header: 'Rel. Type', width: '90px', render: (row: DelayImpact) => (
      <Badge variant="auto-commit" className="text-xs">{row.relationship_type || '—'}</Badge>
    )},
    { key: 'lag_days', header: 'Lag', width: '70px', render: (row: DelayImpact) => (
      row.lag_days > 0 ? `${row.lag_days}d` : '—'
    )},
    { key: 'critical_path_exposure', header: 'Critical Path', width: '110px', render: (row: DelayImpact) => (
      <Badge variant={row.critical_path_exposure ? 'new-activity' : 'auto-commit'} dot>
        {row.critical_path_exposure ? 'At Risk' : 'Safe'}
      </Badge>
    )},
  ]

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-status-new-activity" />
            Delay Impact Analysis
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4 space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="flex gap-4 px-4 py-3">
              <Skeleton className="w-24 h-4" />
              <Skeleton className="flex-1 h-4" />
              <Skeleton className="w-24 h-4" />
              <Skeleton className="w-20 h-4" />
              <Skeleton className="w-20 h-4" />
              <Skeleton className="w-20 h-4" />
            </div>
          ))}
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-status-new-activity" />
            Delay Impact Analysis
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4">
          <EmptyState
            icon={<AlertTriangle className="w-16 h-16" />}
            title="Error loading delay impacts"
            description={error}
          />
        </CardContent>
      </Card>
    )
  }

  if (impacts.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-status-review" />
            Delay Impact Analysis
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4">
          <EmptyState
            icon={<GitBranch className="w-16 h-16" />}
            title="No delay impacts detected"
            description={eventId 
              ? "This delay event has no propagated impacts on downstream activities."
              : activityId
              ? "This activity has no incoming delay impacts."
              : "No critical path delay impacts for this project."}
          />
        </CardContent>
      </Card>
    )
  }

  // Summary stats
  const totalImpacted = impacts.length
  const criticalCount = impacts.filter(i => i.is_critical_path).length
  const floatConsumed = impacts.reduce((sum, i) => sum + i.float_consumed_days, 0)

  return (
    <Card className={className}>
      <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-status-new-activity" />
          <CardTitle>Delay Impact Analysis</CardTitle>
        </div>
        <div className="flex items-center gap-4 text-sm">
          <span className="text-textMuted">{totalImpacted} activities impacted</span>
          <span className="text-status-new-activity font-medium">{criticalCount} on critical path</span>
          <span className="text-status-review">{floatConsumed}d total float consumed</span>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <DataTable
          columns={columns}
          data={impacts}
          keyExtractor={(row) => String(row.id)}
          emptyMessage="No delay impacts found"
        />
      </CardContent>
    </Card>
  )
}