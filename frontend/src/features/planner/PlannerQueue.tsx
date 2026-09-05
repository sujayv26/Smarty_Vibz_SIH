import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui'
import { Badge } from '../../components/ui/Badge'
import { DataTable } from '../../components/ui/Table'
import { Clock, CheckCircle, XCircle, Edit } from 'lucide-react'

const mockReviews = [
  { id: 1, eventId: 101, eventText: 'Started erection of XX-101 spool', proposedActivity: 'PIP-1023: Erect Line 24-XX-101', confidence: 0.72, status: 'PENDING', discipline: 'Piping', time: '2h ago' },
  { id: 2, eventId: 102, eventText: 'Completed pump installation', proposedActivity: 'MEC-2011: Install Pump P-101', confidence: 0.88, status: 'PENDING', discipline: 'Mechanical', time: '4h ago' },
  { id: 3, eventId: 103, eventText: 'Foundation concrete pouring', proposedActivity: 'CIV-3011: Construct Foundation A1', confidence: 0.55, status: 'PENDING', discipline: 'Civil', time: '6h ago' },
  { id: 4, eventId: 104, eventText: 'Cable pull level 3', proposedActivity: 'ELC-4012: Cable Pull Level 3', confidence: 0.42, status: 'PENDING', discipline: 'Electrical', time: '8h ago' },
]

const columns = [
  { key: 'eventText', header: 'Field Event', width: '250px' },
  { key: 'proposedActivity', header: 'Proposed Match', width: '200px' },
  { key: 'confidence', header: 'Confidence', width: '120px' },
  { key: 'discipline', header: 'Discipline', width: '120px' },
  { key: 'time', header: 'Received', width: '100px' },
  { key: 'actions', header: 'Actions', width: '200px' },
]

export function PlannerQueue() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white">Planner Exception Queue</h1>
          <p className="text-textMuted mt-1">Review and resolve low-confidence matches</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="auto-commit" dot>Auto-commit: ≥85%</Badge>
          <Badge variant="review" dot>Review: 60-85%</Badge>
          <Badge variant="new-activity" dot>{'New: <60%'}</Badge>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <Card hover>
          <CardContent className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-amber-500/20 flex items-center justify-center text-amber-400">
              <Clock className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm text-textMuted">Pending Review</p>
              <p className="text-3xl font-bold text-white kpi">12</p>
            </div>
          </CardContent>
        </Card>
        <Card hover>
          <CardContent className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-green-500/20 flex items-center justify-center text-green-400">
              <CheckCircle className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm text-textMuted">Approved Today</p>
              <p className="text-3xl font-bold text-white kpi">8</p>
            </div>
          </CardContent>
        </Card>
        <Card hover>
          <CardContent className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-red-500/20 flex items-center justify-center text-red-400">
              <XCircle className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm text-textMuted">Rejected Today</p>
              <p className="text-3xl font-bold text-white kpi">2</p>
            </div>
          </CardContent>
        </Card>
        <Card hover>
          <CardContent className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-purple-500/20 flex items-center justify-center text-purple-400">
              <Edit className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm text-textMuted">Corrected Today</p>
              <p className="text-3xl font-bold text-white kpi">3</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Review Table */}
      <Card>
        <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <CardTitle>Pending Reviews ({mockReviews.length})</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <DataTable
            columns={columns}
            data={mockReviews}
            keyExtractor={(row) => String(row.id)}
            emptyMessage="No pending reviews"
          />
        </CardContent>
      </Card>
    </div>
  )
}