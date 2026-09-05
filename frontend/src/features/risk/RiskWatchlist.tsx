import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui'
import { Badge } from '../../components/ui/Badge'
import { DataTable } from '../../components/ui/Table'
import { Button } from '../../components/ui/Button'
import { AlertTriangle, TrendingUp, Clock, Download } from 'lucide-react'

const mockRisks = [
  { id: 1, activity: 'MEC-2011: Install Pump P-101', discipline: 'Mechanical', riskScore: 0.87, delayPrediction: '5-7 days', criticalPath: true, confidence: 0.82, factors: ['Material delay', 'Resource conflict'] },
  { id: 2, activity: 'CIV-3011: Foundation A1', discipline: 'Civil', riskScore: 0.76, delayPrediction: '2-3 days', criticalPath: true, confidence: 0.75, factors: ['Weather forecast', 'Concrete supply'] },
  { id: 3, activity: 'PIP-1050: Hydrotest Line XX-101', discipline: 'Piping', riskScore: 0.68, delayPrediction: '1-2 days', criticalPath: false, confidence: 0.71, factors: ['Dependency delay', 'Inspection queue'] },
  { id: 4, activity: 'ELC-4012: Cable Pull Level 3', discipline: 'Electrical', riskScore: 0.62, delayPrediction: '1 day', criticalPath: false, confidence: 0.68, factors: ['Conduit congestion', 'Crew availability'] },
  { id: 5, activity: 'STR-2005: Column Pour Zone 3', discipline: 'Structural', riskScore: 0.58, delayPrediction: '< 1 day', criticalPath: false, confidence: 0.65, factors: ['Formwork delay', 'Rebar inspection'] },
]

const columns = [
  { key: 'activity', header: 'Activity', width: '250px' },
  { key: 'discipline', header: 'Discipline', width: '120px' },
  { key: 'riskScore', header: 'Risk Score', width: '120px' },
  { key: 'delayPrediction', header: 'Predicted Delay', width: '150px' },
  { key: 'criticalPath', header: 'Critical Path', width: '120px' },
  { key: 'confidence', header: 'ML Confidence', width: '130px' },
  { key: 'actions', header: 'Actions', width: '100px' },
]

export function RiskWatchlist() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white">Risk Watchlist</h1>
          <p className="text-textMuted mt-1">ML-predicted delay risks ranked by severity</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="secondary">
            <Download className="w-4 h-4" />
            Export Watchlist
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
              <p className="text-3xl font-bold text-white kpi">2</p>
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
              <p className="text-3xl font-bold text-white kpi">3</p>
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
              <p className="text-3xl font-bold text-white kpi">2</p>
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
              <p className="text-3xl font-bold text-white kpi">3.2 days</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Risk Table */}
      <Card>
        <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <CardTitle>Ranked Risk Watchlist ({mockRisks.length})</CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="review">ML Model v2.1</Badge>
            <Badge variant="neutral">Updated 2h ago</Badge>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <DataTable
            columns={columns}
            data={mockRisks}
            keyExtractor={(row) => String(row.id)}
            emptyMessage="No risk predictions available"
            onRowClick={(row) => console.log('Risk detail', row)}
          />
        </CardContent>
      </Card>

      {/* Model Info */}
      <Card>
        <CardHeader>
          <CardTitle>Model Information</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <div className="p-4 rounded-lg bg-surfaceRaised border border-border">
            <p className="text-sm text-textMuted mb-1">Features</p>
            <ul className="space-y-1 text-sm text-white">
              <li>• Predecessor/Successor topology</li>
              <li>• Historical delay patterns</li>
              <li>• Weather forecast integration</li>
              <li>• Resource allocation</li>
              <li>• Discipline productivity</li>
            </ul>
          </div>
          <div className="p-4 rounded-lg bg-surfaceRaised border border-border">
            <p className="text-sm text-textMuted mb-1">Performance</p>
            <ul className="space-y-1 text-sm text-white">
              <li>• MAE: 1.8 days</li>
              <li>• RMSE: 2.4 days</li>
              <li>• Precision@High: 0.84</li>
              <li>• Recall@High: 0.79</li>
              <li>• AUC-ROC: 0.87</li>
            </ul>
          </div>
          <div className="p-4 rounded-lg bg-surfaceRaised border border-border">
            <p className="text-sm text-textMuted mb-1">Training Data</p>
            <ul className="space-y-1 text-sm text-white">
              <li>• 3 projects, 18 months</li>
              <li>• 1,247 delay events</li>
              <li>• 8 delay categories</li>
              <li>• Retrained weekly</li>
              <li>• Next retrain: Tomorrow</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}