import { useState, useEffect, useCallback } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui'
import { Button } from '../../components/ui/Button'
import { Select } from '../../components/ui/Select'
import { Skeleton } from '../../components/ui/Skeleton'
import { EmptyState } from '../../components/ui/EmptyState'
import { cn } from '../../lib/utils'
import { api } from '../../lib/api'
import {
  BarChart3,
  TrendingUp,
  AlertTriangle,
  Building2,
  Download,
  RefreshCw,
} from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
} from 'recharts'

interface DisciplineStat {
  discipline: string
  total_activities: number
  completed_activities: number
  in_progress_activities: number
  not_started_activities: number
  planned_duration_days: number
  actual_duration_days: number | null
  variance_days: number | null
  variance_pct: number | null
  productivity_index: number | null
  delay_events: number
  delay_days: number
  delay_categories: Record<string, number>
}

interface DelayCategoryStat {
  category: string
  count: number
  total_days: number
  avg_days: number
  critical_path_count: number
}

interface DelayPatterns {
  by_category: DelayCategoryStat[]
  by_discipline: Record<string, Record<string, number>>
  top_causes: Array<{cause: string} & DelayCategoryStat>
  total_delay_events: number
  total_delay_days: number
  period_weeks: number
}

interface BenchmarkActivity {
  activity_type: string
  unit: string
  planned_quantity: number | null
  actual_quantity: number | null
  planned_duration_days: number | null
  actual_duration_days: number | null
  productivity_rate: number | null
  sample_size: number
  period_start: string | null
  period_end: string | null
}

interface DisciplineBenchmark {
  discipline: string
  activity_types: BenchmarkActivity[]
  avg_productivity_rate: number
  total_planned_quantity: number
  total_actual_quantity: number
  total_planned_duration: number
  total_actual_duration: number
  sample_size: number
}

interface WeeklyVariance {
  week_start: string
  planned_days: number
  actual_days: number
  variance_days: number
  variance_pct: number
  completed_count: number
  delay_events: number
}

interface MatchingQuality {
  total_reviews: number
  auto_commit_rate: number
  review_rate: number
  correction_rate: number
  rejection_rate: number
  new_activity_rate: number
  avg_confidence: number
  period_weeks: number
}

const COLORS = ['#34d399', '#60a5fa', '#fbbf24', '#f87171', '#a78bfa', '#f472b6', '#22d3ee', '#4ade80']

export function Insights() {
  const [projectId] = useState<number | null>(null)
  const [weeks, setWeeks] = useState(12)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [disciplineSummary, setDisciplineSummary] = useState<DisciplineStat[]>([])
  const [delayPatterns, setDelayPatterns] = useState<DelayPatterns | null>(null)
  const [benchmarks, setBenchmarks] = useState<DisciplineBenchmark[]>([])
  const [varianceTrend, setVarianceTrend] = useState<WeeklyVariance[]>([])
  const [matchingQuality, setMatchingQuality] = useState<MatchingQuality | null>(null)

  const fetchAll = useCallback(async () => {
    if (!projectId) return
    setIsLoading(true)
    setError(null)
    try {
      const [disc, delays, bench, variance, matching] = await Promise.all([
        api.get('/analytics/discipline-summary', { params: { project_id: projectId, weeks } }),
        api.get('/analytics/delay-patterns', { params: { project_id: projectId, weeks } }),
        api.get('/analytics/benchmarks', { params: { project_id: projectId } }),
        api.get('/analytics/variance-trend', { params: { project_id: projectId, weeks } }),
        api.get('/analytics/matching-quality', { params: { project_id: projectId, weeks } }),
      ])
      setDisciplineSummary(disc.data.disciplines || [])
      setDelayPatterns(delays.data)
      setBenchmarks(bench.data.benchmarks || [])
      setVarianceTrend(variance.data.trend || [])
      setMatchingQuality(matching.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch analytics')
    } finally {
      setIsLoading(false)
    }
  }, [projectId, weeks])

  useEffect(() => {
    fetchAll()
  }, [fetchAll])

  // KPI calculations
  const avgProductivityIndex = disciplineSummary.length > 0
    ? disciplineSummary.reduce((sum, d) => sum + (d.productivity_index || 0), 0) / disciplineSummary.filter(d => d.productivity_index).length
    : 0

  const totalVariancePct = disciplineSummary.length > 0
    ? disciplineSummary.reduce((sum, d) => sum + (d.variance_pct || 0), 0) / disciplineSummary.filter(d => d.variance_pct).length
    : 0

  const topDelayCause = delayPatterns?.top_causes[0]?.cause || 'N/A'
  const topDelayPct = delayPatterns?.top_causes[0]
    ? ((delayPatterns.top_causes[0].total_days / delayPatterns.total_delay_days) * 100).toFixed(0)
    : '0'

  const onTimeCompletion = disciplineSummary.length > 0
    ? disciplineSummary.reduce((sum, d) => sum + d.completed_activities, 0) / 
      Math.max(1, disciplineSummary.reduce((sum, d) => sum + d.total_activities, 0)) * 100
    : 0

  const kpiItems = [
    { label: 'Avg. Productivity Index', value: `${(avgProductivityIndex * 100).toFixed(0)}%`, trend: '+2%', trendUp: true, icon: TrendingUp, color: 'text-green-400' },
    { label: 'Schedule Variance', value: `${totalVariancePct >= 0 ? '+' : ''}${totalVariancePct.toFixed(1)}%`, trend: '-1.5%', trendUp: totalVariancePct <= 0, icon: TrendingUp, color: totalVariancePct <= 0 ? 'text-green-400' : 'text-red-400' },
    { label: 'Top Delay Cause', value: `${topDelayCause} (${topDelayPct}%)`, trend: '+5%', trendUp: false, icon: AlertTriangle, color: 'text-amber-400' },
    { label: 'On-Time Completion', value: `${onTimeCompletion.toFixed(0)}%`, trend: '+3%', trendUp: true, icon: () => <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>, color: 'text-blue-400' },
  ]

  if (isLoading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-white">Insights & Institutional Memory</h1>
            <p className="text-textMuted mt-1">Productivity benchmarks, delay patterns, and historical analytics</p>
          </div>
          <Button variant="secondary">
            <Download className="w-4 h-4" />
            Export Report
          </Button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {kpiItems.map((item) => (
            <Card key={item.label} hover>
              <CardContent className="flex items-start justify-between gap-4">
                <Skeleton className="w-24 h-4" />
                <Skeleton className="w-12 h-12 rounded-lg" />
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5" />
                Productivity by Discipline
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Skeleton className="h-80" />
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-amber-400" />
                Top Delay Causes
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Skeleton className="h-64" />
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Building2 className="w-5 h-5 text-blue-400" />
                Productivity Benchmarks
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Skeleton className="h-64" />
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-white">Insights & Institutional Memory</h1>
            <p className="text-textMuted mt-1">Productivity benchmarks, delay patterns, and historical analytics</p>
          </div>
          <Button variant="secondary" onClick={fetchAll}>
            <RefreshCw className="w-4 h-4" />
            Retry
          </Button>
        </div>
        <Card>
          <CardContent className="p-8">
            <EmptyState
              icon={<AlertTriangle className="w-16 h-16" />}
              title="Error loading analytics"
              description={error}
            />
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!projectId) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-white">Insights & Institutional Memory</h1>
            <p className="text-textMuted mt-1">Productivity benchmarks, delay patterns, and historical analytics</p>
          </div>
        </div>
        <Card>
          <CardContent className="p-8">
            <EmptyState
              icon={<Building2 className="w-16 h-16" />}
              title="No project selected"
              description="Select a project from the schedule or dashboard to view insights."
            />
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white">Insights & Institutional Memory</h1>
          <p className="text-textMuted mt-1">Productivity benchmarks, delay patterns, and historical analytics</p>
        </div>
        <div className="flex items-center gap-3">
          <Select
            value={String(weeks)}
            onChange={(e) => setWeeks(parseInt(e.target.value))}
            className="w-40"
            options={[
              { value: "4", label: "4 weeks" },
              { value: "12", label: "12 weeks" },
              { value: "26", label: "26 weeks" },
              { value: "52", label: "52 weeks" },
            ]}
          />
          <Button variant="secondary" onClick={fetchAll}>
            <RefreshCw className="w-4 h-4" />
            Refresh
          </Button>
          <Button variant="secondary">
            <Download className="w-4 h-4" />
            Export Report
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpiItems.map((item) => (
          <Card key={item.label} hover>
            <CardContent className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm text-textMuted mb-1">{item.label}</p>
                <p className="text-3xl font-bold text-white kpi">{item.value}</p>
                <p className={cn('text-sm mt-1', item.trendUp ? 'text-green-400' : 'text-red-400')}>
                  {item.trendUp ? '+' : ''}{item.trend} vs last period
                </p>
              </div>
              <div className={cn('w-12 h-12 rounded-lg flex items-center justify-center', item.color + '/20')}>
                <item.icon className={cn('w-6 h-6', item.color)} />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Productivity by Discipline */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Productivity by Discipline
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={disciplineSummary.filter(d => d.productivity_index !== null)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="discipline" stroke="#888" fontSize={12} />
                <YAxis stroke="#888" fontSize={12} domain={[0, 1.2]} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} />
                <Tooltip 
                  formatter={(value: number) => [`${(value * 100).toFixed(1)}%`, 'Productivity Index']}
                  contentStyle={{ backgroundColor: '#1c1c1f', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '8px' }}
                />
                <Legend />
                <Bar dataKey="productivity_index" name="Productivity Index" fill="#34d399" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Delay Patterns & Variance Trend */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Delay Patterns - Pie Chart + Table */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
              Delay Causes Distribution
            </CardTitle>
          </CardHeader>
          <CardContent>
            {delayPatterns?.by_category.length ? (
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={delayPatterns.by_category}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      dataKey="total_days"
                      nameKey="category"
                      label={({ category, percent }) => `${category} ${(percent * 100).toFixed(0)}%`}
                      labelLine={false}
                    >
                      {delayPatterns.by_category.map((_, i) => (
                        <Cell key={`cell-${i}`} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip 
                      formatter={(value: number) => [`${value} days`, 'Delay Days']}
                      contentStyle={{ backgroundColor: '#1c1c1f', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '8px' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <EmptyState icon={<AlertTriangle className="w-12 h-12" />} title="No delay data" description="No delay events recorded for this period." />
            )}
          </CardContent>
        </Card>

        {/* Variance Trend - Line Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Schedule Variance Trend
            </CardTitle>
          </CardHeader>
          <CardContent>
            {varianceTrend.length > 0 ? (
              <ResponsiveContainer width="100%" height={320}>
                <LineChart data={varianceTrend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis dataKey="week_start" stroke="#888" fontSize={11} tick={{ fill: '#888' }} />
                  <YAxis stroke="#888" fontSize={11} tickFormatter={(v) => `${v >= 0 ? '+' : ''}${v}%`} />
                  <Tooltip
                    labelFormatter={(week) => `Week of ${week}`}
                    formatter={(value: number, name: string) => [value, name]}
                    contentStyle={{ backgroundColor: '#1c1c1f', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '8px' }}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="variance_pct"
                    name="Variance %"
                    stroke="#fbbf24"
                    strokeWidth={2}
                    dot={{ fill: '#fbbf24', strokeWidth: 2 }}
                    activeDot={{ r: 6 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="delay_events"
                    name="Delay Events"
                    stroke="#f87171"
                    strokeWidth={2}
                    dot={{ fill: '#f87171', strokeWidth: 2 }}
                    activeDot={{ r: 6 }}
                    yAxisId="right"
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState icon={<BarChart3 className="w-12 h-12" />} title="No variance data" description="Complete activities with actuals to see variance trend." />
            )}
          </CardContent>
        </Card>
      </div>

      {/* Detailed Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Delay Causes Table */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
              Top Delay Causes ({delayPatterns?.total_delay_events || 0} events, {delayPatterns?.total_delay_days || 0} days)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-textMuted border-b border-border">
                    <th className="text-left p-2">Cause</th>
                    <th className="text-right p-2">Count</th>
                    <th className="text-right p-2">Total Days</th>
                    <th className="text-right p-2">Avg Days</th>
                    <th className="text-right p-2">Critical Path</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/50">
                  {delayPatterns?.top_causes.map((cause) => (
                    <tr key={cause.category}>
                      <td className="p-2 text-white">{cause.category}</td>
                      <td className="p-2 text-textMuted text-right">{cause.count}</td>
                      <td className="p-2 text-white text-right">{cause.total_days}</td>
                      <td className="p-2 text-textMuted text-right">{cause.avg_days.toFixed(1)}</td>
                      <td className="p-2 text-textMuted text-right">{cause.critical_path_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Productivity Benchmarks Table */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Building2 className="w-5 h-5 text-blue-400" />
              Productivity Benchmarks
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-textMuted border-b border-border">
                    <th className="text-left p-2">Discipline</th>
                    <th className="text-left p-2">Activity</th>
                    <th className="text-right p-2">Unit</th>
                    <th className="text-right p-2">Plan Rate</th>
                    <th className="text-right p-2">Actual Rate</th>
                    <th className="text-right p-2">Variance</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/50">
                  {benchmarks.flatMap(bench =>
                    bench.activity_types.map(act => (
                      <tr key={`${bench.discipline}-${act.activity_type}`}>
                        <td className="p-2 text-white">{bench.discipline}</td>
                        <td className="p-2 text-textMuted">{act.activity_type}</td>
                        <td className="p-2 text-textMuted text-right">{act.unit}</td>
                        <td className="p-2 text-textMuted text-right">
                          {act.planned_duration_days && act.planned_quantity
                            ? (act.planned_quantity / act.planned_duration_days).toFixed(1)
                            : '—'}
                        </td>
                        <td className="p-2 text-white text-right">
                          {act.actual_duration_days && act.actual_quantity
                            ? (act.actual_quantity / act.actual_duration_days).toFixed(1)
                            : '—'}
                        </td>
                        <td className={cn('p-2 text-right font-medium', 
                          act.productivity_rate && act.planned_duration_days && act.actual_duration_days
                            ? (act.actual_quantity && act.planned_quantity && act.actual_duration_days && act.planned_duration_days
                                ? (act.actual_quantity / act.actual_duration_days) >= (act.planned_quantity / act.planned_duration_days)
                                    ? 'text-green-400'
                                    : 'text-red-400'
                                : 'text-textMuted'
                            )
                            : 'text-textMuted'
                        )}>
                          {act.productivity_rate ? `${(act.productivity_rate * 100).toFixed(0)}%` : '—'}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Matching Quality & Confidence Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Matching Quality
            </CardTitle>
          </CardHeader>
          <CardContent>
            {matchingQuality ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 bg-surfaceRaised rounded-lg">
                    <p className="text-sm text-textMuted">Auto-commit Rate</p>
                    <p className="text-2xl font-bold text-green-400">{matchingQuality.auto_commit_rate.toFixed(1)}%</p>
                  </div>
                  <div className="p-3 bg-surfaceRaised rounded-lg">
                    <p className="text-sm text-textMuted">Review Rate</p>
                    <p className="text-2xl font-bold text-amber-400">{matchingQuality.review_rate.toFixed(1)}%</p>
                  </div>
                  <div className="p-3 bg-surfaceRaised rounded-lg">
                    <p className="text-sm text-textMuted">Correction Rate</p>
                    <p className="text-2xl font-bold text-blue-400">{matchingQuality.correction_rate.toFixed(1)}%</p>
                  </div>
                  <div className="p-3 bg-surfaceRaised rounded-lg">
                    <p className="text-sm text-textMuted">Avg Confidence</p>
                    <p className="text-2xl font-bold text-white">{matchingQuality.avg_confidence.toFixed(2)}</p>
                  </div>
                </div>
                <div className="pt-4 border-t border-border">
                  <p className="text-sm text-textMuted">Total Reviews: {matchingQuality.total_reviews} | Period: {matchingQuality.period_weeks} weeks</p>
                </div>
              </div>
            ) : (
              <EmptyState icon={<BarChart3 className="w-12 h-12" />} title="No matching data" description="No reviews in this period." />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-green-400" />
              Discipline Summary
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-textMuted border-b border-border">
                    <th className="text-left p-2">Discipline</th>
                    <th className="text-right p-2">Activities</th>
                    <th className="text-right p-2">Completed</th>
                    <th className="text-right p-2">Planned Days</th>
                    <th className="text-right p-2">Actual Days</th>
                    <th className="text-right p-2">Variance</th>
                    <th className="text-right p-2">Productivity</th>
                    <th className="text-right p-2">Delays</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/50">
                  {disciplineSummary.map((disc) => (
                    <tr key={disc.discipline}>
                      <td className="p-2 text-white font-medium">{disc.discipline}</td>
                      <td className="p-2 text-textMuted text-right">{disc.total_activities}</td>
                      <td className="p-2 text-green-400 text-right">{disc.completed_activities}</td>
                      <td className="p-2 text-textMuted text-right">{disc.planned_duration_days}</td>
                      <td className="p-2 text-white text-right">{disc.actual_duration_days || '—'}</td>
                      <td className={cn('p-2 text-right font-medium', 
                        disc.variance_pct !== null
                          ? disc.variance_pct <= 0
                              ? 'text-green-400'
                              : 'text-red-400'
                          : 'text-textMuted'
                      )}>
                        {disc.variance_pct !== null ? `${disc.variance_pct >= 0 ? '+' : ''}${disc.variance_pct.toFixed(1)}%` : '—'}
                      </td>
                      <td className="p-2 text-textMuted text-right">{disc.productivity_index ? `${(disc.productivity_index * 100).toFixed(0)}%` : '—'}</td>
                      <td className="p-2 text-amber-400 text-right">{disc.delay_events} ({disc.delay_days}d)</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}