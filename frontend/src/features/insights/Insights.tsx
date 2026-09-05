import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui'
import { Button } from '../../components/ui/Button'
import { cn } from '../../lib/utils'
import {
  BarChart3,
  TrendingUp,
  AlertTriangle,
  Building2,
  Download,
} from 'lucide-react'

export function Insights() {
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

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Avg. Productivity Index', value: '0.87', trend: '+0.03', trendUp: true, icon: TrendingUp, color: 'text-green-400' },
          { label: 'Schedule Variance', value: '-12%', trend: '-2%', trendUp: true, icon: TrendingUp, color: 'text-green-400' },
          { label: 'Recurring Delay Causes', value: 'Weather (34%)', trend: '+5%', trendUp: false, icon: AlertTriangle, color: 'text-amber-400' },
          { label: 'On-Time Completion', value: '78%', trend: '+3%', trendUp: true, icon: () => <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>, color: 'text-blue-400' },
        ].map((item) => (
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
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Productivity by Discipline
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-80 flex items-end justify-around gap-4 px-4">
              {[
                { discipline: 'Piping', value: 0.92, target: 1.0 },
                { discipline: 'Civil', value: 0.89, target: 1.0 },
                { discipline: 'Structural', value: 0.85, target: 1.0 },
                { discipline: 'Mechanical', value: 0.78, target: 1.0 },
                { discipline: 'Electrical', value: 0.91, target: 1.0 },
                { discipline: 'Instrumentation', value: 0.83, target: 1.0 },
              ].map((item) => (
                <div key={item.discipline} className="flex-1 flex flex-col items-center gap-2">
                  <div
                    className="w-full bg-gradient-to-t from-blue-500/60 to-blue-500/20 rounded-t"
                    style={{ height: `${item.value * 100}%`, minHeight: '20px' }}
                  />
                  <span className="text-xs text-textMuted mt-2">{item.discipline}</span>
                  <span className="text-sm font-medium text-white">{Math.round(item.value * 100)}%</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Delay Patterns & Benchmarks */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
              Top Delay Causes (30 days)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {[
              { cause: 'Weather', count: 12, pct: 34, trend: '+5%' },
              { cause: 'Material Delivery', count: 8, pct: 23, trend: '+2%' },
              { cause: 'Resource Shortage', count: 6, pct: 17, trend: '-1%' },
              { cause: 'Design Changes', count: 4, pct: 11, trend: '0%' },
              { cause: 'Permit Delays', count: 3, pct: 9, trend: '+3%' },
              { cause: 'Subcontractor', count: 2, pct: 6, trend: '-2%' },
            ].map((item) => (
              <div key={item.cause} className="flex items-center gap-3">
                <div className="w-24 text-sm text-textMuted">{item.cause}</div>
                <div className="flex-1 h-2 bg-surfaceRaised rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-amber-500 to-red-500 rounded-full"
                    style={{ width: `${item.pct}%` }}
                  />
                </div>
                <span className="w-12 text-sm font-medium text-white text-right">{item.pct}%</span>
                <span className={cn('text-xs', item.trend.startsWith('+') ? 'text-red-400' : 'text-green-400')}>
                  {item.trend}
                </span>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Building2 className="w-5 h-5 text-blue-400" />
              Productivity Benchmarks
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-textMuted border-b border-border">
                    <th className="text-left p-2">Activity</th>
                    <th className="text-right p-2">Unit</th>
                    <th className="text-right p-2">Plan</th>
                    <th className="text-right p-2">Actual</th>
                    <th className="text-right p-2">Variance</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/50">
                  {[
                    { activity: 'Pipe Erection', unit: 'm/day', plan: 120, actual: 115 },
                    { activity: 'Excavation', unit: 'm³/day', plan: 80, actual: 85 },
                    { activity: 'Concrete Pour', unit: 'm³/day', plan: 50, actual: 48 },
                    { activity: 'Cable Pull', unit: 'm/day', plan: 200, actual: 195 },
                    { activity: 'Equipment Install', unit: 'units/day', plan: 15, actual: 12 },
                  ].map((item) => (
                    <tr key={item.activity}>
                      <td className="p-2 text-white">{item.activity}</td>
                      <td className="p-2 text-textMuted text-right">{item.unit}</td>
                      <td className="p-2 text-textMuted text-right">{item.plan}</td>
                      <td className="p-2 text-white text-right">{item.actual}</td>
                      <td className={cn('p-2 text-right font-medium', item.actual >= item.plan ? 'text-green-400' : 'text-red-400')}>
                        {item.actual >= item.plan ? '+' : ''}{Math.round(((item.actual - item.plan) / item.plan) * 100)}%
                      </td>
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