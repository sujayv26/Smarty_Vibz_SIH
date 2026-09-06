import { useState, useEffect, useCallback } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui'
import { Badge } from '../../components/ui/Badge'
import { DataTable } from '../../components/ui/Table'
import { Button } from '../../components/ui/Button'
import { Skeleton } from '../../components/ui/Skeleton'
import { EmptyState } from '../../components/ui/EmptyState'
import { AlertTriangle, TrendingUp, Clock, Download, RefreshCw, Brain } from 'lucide-react'
import { api } from '../../lib/api'
import { cn } from '../../lib/utils'
import { formatDistanceToNow } from 'date-fns'

interface DelayPrediction {
  id: number
  project_id: number
  wbs_node_id: number
  model_version: string
  delay_probability: number
  expected_delay_days: number
  confidence_score: number
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  feature_importance: string | null
  features_json: string | null
  prediction_date: string
  valid_until: string | null
  created_at: string
  updated_at: string | null
  activity_code: string | null
  activity_name: string | null
  discipline: string | null
  wbs: string | null
  planned_start: string | null
  planned_finish: string | null
  actual_start: string | null
}

interface WatchlistResponse {
  predictions: DelayPrediction[]
  total: number
  high_risk_count: number
  critical_risk_count: number
  model_version: string
  last_training_date: string | null
}

interface TrainingRun {
  id: number
  model_version: string
  project_id: number | null
  train_samples: number
  test_samples: number
  auc_roc: number | null
  auc_pr: number | null
  mae_delay_days: number | null
  rmse_delay_days: number | null
  status: string
  error_message: string | null
  started_at: string
  completed_at: string | null
}

const columns = [
  { key: 'activity', header: 'Activity', width: '250px', render: (row: DelayPrediction) => (
    <div>
      <p className="font-medium text-white">{row.activity_code}: {row.activity_name}</p>
      <p className="text-xs text-textMuted">{row.wbs}</p>
    </div>
  )},
  { key: 'discipline', header: 'Discipline', width: '120px' },
  { key: 'riskScore', header: 'Risk Score', width: '120px', render: (row: DelayPrediction) => (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-surfaceRaised rounded-full overflow-hidden">
        <div
          className="h-full rounded-full bg-gradient-to-r"
          style={{
            width: `${(row.delay_probability * 100).toFixed(0)}%`,
            backgroundColor: row.risk_level === 'CRITICAL' ? '#ef4444' :
              row.risk_level === 'HIGH' ? '#f97316' :
              row.risk_level === 'MEDIUM' ? '#fbbf24' : '#34d399'
          }}
        />
      </div>
      <span className="text-sm font-mono text-white w-10 text-right">
        {(row.delay_probability * 100).toFixed(0)}%
      </span>
    </div>
  )},
  { key: 'delayPrediction', header: 'Predicted Delay', width: '150px', render: (row: DelayPrediction) => (
    <span className={cn('font-medium', row.expected_delay_days >= 5 ? 'text-red-400' : row.expected_delay_days >= 2 ? 'text-amber-400' : 'text-green-400')}>
      {row.expected_delay_days < 1 ? '< 1 day' : row.expected_delay_days === 1 ? '1 day' : `${row.expected_delay_days.toFixed(1)} days`}
    </span>
  )},
  { key: 'criticalPath', header: 'Critical Path', width: '120px', render: (row: DelayPrediction) => (
    <Badge variant={row.activity_code && row.activity_code.includes('critical') ? 'new-activity' : 'auto-commit'} dot>
      {row.activity_code && row.activity_code.includes('critical') ? 'Yes' : 'No'}
    </Badge>
  )},
  { key: 'confidence', header: 'ML Confidence', width: '130px', render: (row: DelayPrediction) => (
    <span className={cn('font-mono', row.confidence_score >= 0.8 ? 'text-green-400' : row.confidence_score >= 0.6 ? 'text-amber-400' : 'text-red-400')}>
      {(row.confidence_score * 100).toFixed(0)}%
    </span>
  )},
]

export function RiskWatchlist() {
  const [watchlist, setWatchlist] = useState<WatchlistResponse | null>(null)
  const [trainingRuns, setTrainingRuns] = useState<TrainingRun[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [projectId] = useState<number | null>(1) // TODO: Get from context

  const fetchWatchlist = useCallback(async () => {
    if (!projectId) return
    setIsLoading(true)
    setError(null)
    try {
      const [watchlistRes, trainingRes] = await Promise.all([
        api.get('/delay-predictions/project/1/watchlist', { params: { limit: 20 } }),
        api.get('/delay-predictions/training-runs', { params: { project_id: projectId, model_version: 'v1' } }),
      ])
      setWatchlist(watchlistRes.data)
      setTrainingRuns(trainingRes.data.runs || [])
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch risk watchlist')
    } finally {
      setIsLoading(false)
    }
  }, [projectId])

  const fetchAll = useCallback(async () => {
    await fetchWatchlist()
  }, [fetchWatchlist])

  useEffect(() => {
    fetchAll()
  }, [fetchAll])

  const handleRetrain = async () => {
    try {
      const response = await api.post('/delay-predictions/train', { project_id: projectId, force_retrain: true })
      if (response.data.status === 'started') {
        setTimeout(fetchWatchlist, 30000) // Refresh after 30 seconds
      }
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to trigger retraining')
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-white">Risk Watchlist</h1>
            <p className="text-textMuted mt-1">ML-predicted delay risks ranked by severity</p>
          </div>
          <Button variant="secondary" disabled>
            <Brain className="w-4 h-4 animate-spin" />
            Retraining...
          </Button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1,2,3,4].map((i) => (
            <Card key={i} hover>
              <CardContent className="flex items-center gap-3">
                <Skeleton className="w-12 h-12 rounded-lg" />
                <div>
                  <Skeleton className="w-24 h-4" />
                  <Skeleton className="w-16 h-8 mt-1" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Ranked Risk Watchlist</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="p-4 space-y-3">
              {[1,2,3,4,5].map((i) => (
                <div key={i} className="flex gap-4 px-4 py-3">
                  <Skeleton className="w-48 h-4" />
                  <Skeleton className="w-20 h-4" />
                  <Skeleton className="w-24 h-4" />
                  <Skeleton className="w-24 h-4" />
                  <Skeleton className="w-24 h-4" />
                  <Skeleton className="w-20 h-4" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6 animate-fade-in">
        <Card>
          <CardContent className="p-8">
            <EmptyState
              icon={<AlertTriangle className="w-16 h-16" />}
              title="Error loading risk watchlist"
              description={error}
            />
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!watchlist) {
    return (
      <div className="space-y-6 animate-fade-in">
        <Card>
          <CardContent className="p-8">
            <EmptyState
              icon={<Brain className="w-16 h-16" />}
              title="No risk predictions available"
              description="Generate predictions to see the risk watchlist."
            />
          </CardContent>
        </Card>
      </div>
    )
  }

  const predictions = watchlist.predictions || []
  const mediumRisk = predictions.filter(p => p.risk_level === 'MEDIUM').length
  const avgDelay = predictions.length > 0 
    ? (predictions.reduce((sum, p) => sum + p.expected_delay_days, 0) / predictions.length).toFixed(1)
    : '0'

  const latestTraining = trainingRuns[0]

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white">Risk Watchlist</h1>
          <p className="text-textMuted mt-1">ML-predicted delay risks ranked by severity</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="secondary" onClick={handleRetrain}>
            <Brain className="w-4 h-4" />
            Retrain Model
          </Button>
          <Button variant="secondary">
            <Download className="w-4 h-4" />
            Export Watchlist
          </Button>
          <Button variant="secondary" onClick={fetchAll}>
            <RefreshCw className="w-4 h-4" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card hover>
          <CardContent className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-red-500/20 flex items-center justify-center text-red-400">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm text-textMuted">High Risk (≥0.75)</p>
              <p className="text-3xl font-bold text-white kpi">{watchlist.high_risk_count}</p>
            </div>
          </CardContent>
        </Card>
        <Card hover>
          <CardContent className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-amber-500/20 flex items-center justify-center text-amber-400">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm text-textMuted">Medium Risk (0.5-0.75)</p>
              <p className="text-3xl font-bold text-white kpi">{mediumRisk}</p>
            </div>
          </CardContent>
        </Card>
        <Card hover>
          <CardContent className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-green-500/20 flex items-center justify-center text-green-400">
              <TrendingUp className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm text-textMuted">Critical Path at Risk</p>
              <p className="text-3xl font-bold text-white kpi">{watchlist.critical_risk_count}</p>
            </div>
          </CardContent>
        </Card>
        <Card hover>
          <CardContent className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-blue-500/20 flex items-center justify-center text-blue-400">
              <Clock className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm text-textMuted">Avg. Pred. Delay</p>
              <p className="text-3xl font-bold text-white kpi">{avgDelay} days</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Risk Table */}
      <Card>
        <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <CardTitle>Ranked Risk Watchlist ({predictions.length})</CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="review">ML Model {watchlist.model_version}</Badge>
            <Badge variant="neutral">
              Updated {latestTraining && latestTraining.completed_at ? formatDistanceToNow(new Date(latestTraining.completed_at), { addSuffix: true }) : 'Never'}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {predictions.length === 0 ? (
            <EmptyState
              icon={<Brain className="w-16 h-16" />}
              title="No risk predictions"
              description="All activities are low risk or no in-progress activities found."
            />
          ) : (
            <DataTable
              columns={columns}
              data={predictions}
              keyExtractor={(row) => String(row.id)}
              emptyMessage="No risk predictions available"
              onRowClick={(row) => console.log('Risk detail', row)}
            />
          )}
        </CardContent>
      </Card>

      {/* Model Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-blue-400" />
            Model Information
          </CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <div className="p-4 rounded-lg bg-surfaceRaised border border-border">
            <p className="text-sm text-textMuted mb-2">Top Features</p>
            <ul className="space-y-1 text-sm text-white">
              <li>• Predecessor/Successor topology</li>
              <li>• Historical delay patterns</li>
              <li>• Discipline productivity benchmarks</li>
              <li>• Schedule float & critical path</li>
              <li>• Matching confidence scores</li>
            </ul>
          </div>
          <div className="p-4 rounded-lg bg-surfaceRaised border border-border">
            <p className="text-sm text-textMuted mb-2">Performance</p>
            <ul className="space-y-1 text-sm text-white">
              {latestTraining ? (
                <>
                  <li>• MAE: {latestTraining.mae_delay_days ? latestTraining.mae_delay_days.toFixed(1) : 'N/A'} days</li>
                  <li>• RMSE: {latestTraining.rmse_delay_days ? latestTraining.rmse_delay_days.toFixed(1) : 'N/A'} days</li>
                  <li>• AUC-ROC: {latestTraining.auc_roc ? latestTraining.auc_roc.toFixed(2) : 'N/A'}</li>
                  <li>• AUC-PR: {latestTraining.auc_pr ? latestTraining.auc_pr.toFixed(2) : 'N/A'}</li>
                  <li>• Train samples: {latestTraining.train_samples}</li>
                </>
              ) : (
                <>
                  <li>• No training runs yet</li>
                  <li>• Trigger training to see metrics</li>
                </>
              )}
            </ul>
          </div>
          <div className="p-4 rounded-lg bg-surfaceRaised border border-border">
            <p className="text-sm text-textMuted mb-2">Training Data</p>
            <ul className="space-y-1 text-sm text-white">
              <li>• Multi-project historical data</li>
              <li>• Delay reasons & productivity benchmarks</li>
              <li>• Schedule topology & float analysis</li>
              <li>• Retrained daily via Celery Beat</li>
              <li>• Next retrain: Tomorrow 00:00 UTC</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}