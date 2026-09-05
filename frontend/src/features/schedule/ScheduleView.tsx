import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import { DataTable } from '../../components/ui/Table'
import { Download, Upload } from 'lucide-react'

const mockActivities = [
  { id: 1, code: 'PIP-1023', name: 'Erect Line 24-XX-101', discipline: 'Piping', wbs: 'PIP.10.23', plannedStart: '2026-08-15', plannedFinish: '2026-08-30', actualStart: '2026-08-16', actualFinish: null, status: 'In Progress' },
  { id: 2, code: 'PIP-1027', name: 'Install Support for XX-101', discipline: 'Piping', wbs: 'PIP.10.27', plannedStart: '2026-08-10', plannedFinish: '2026-08-20', actualStart: '2026-08-10', actualFinish: '2026-08-18', status: 'Complete' },
  { id: 3, code: 'PIP-1042', name: 'Inspect XX-101', discipline: 'Piping', wbs: 'PIP.10.42', plannedStart: '2026-09-01', plannedFinish: '2026-09-05', actualStart: null, actualFinish: null, status: 'Not Started' },
  { id: 4, code: 'PIP-1050', name: 'Hydrotest Line XX-101', discipline: 'Piping', wbs: 'PIP.10.50', plannedStart: '2026-09-05', plannedFinish: '2026-09-10', actualStart: null, actualFinish: null, status: 'Not Started' },
  { id: 5, code: 'MEC-2011', name: 'Install Pump P-101', discipline: 'Mechanical', wbs: 'MEC.20.11', plannedStart: '2026-08-25', plannedFinish: '2026-09-05', actualStart: '2026-08-26', actualFinish: null, status: 'In Progress' },
  { id: 6, code: 'CIV-3011', name: 'Construct Foundation A1', discipline: 'Civil', wbs: 'CIV.30.11', plannedStart: '2026-08-01', plannedFinish: '2026-08-15', actualStart: '2026-08-01', actualFinish: '2026-08-14', status: 'Complete' },
]

const columns = [
  { key: 'code', header: 'Code', width: '100px' },
  { key: 'name', header: 'Activity Name', width: '250px' },
  { key: 'discipline', header: 'Discipline', width: '120px' },
  { key: 'wbs', header: 'WBS', width: '100px' },
  { key: 'plannedStart', header: 'Planned Start', width: '130px' },
  { key: 'plannedFinish', header: 'Planned Finish', width: '130px' },
  { key: 'actualStart', header: 'Actual Start', width: '130px' },
  { key: 'actualFinish', header: 'Actual Finish', width: '130px' },
  { key: 'status', header: 'Status', width: '120px' },
]

export function ScheduleView() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white">Schedule</h1>
          <p className="text-textMuted mt-1">View and manage project schedule, import/export XER files</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="secondary" size="sm">
            <Download className="w-4 h-4" />
            Export XER
          </Button>
          <Button variant="secondary" size="sm">
            <Upload className="w-4 h-4" />
            Import XER
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card className="p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <Input placeholder="Search activities..." />
          </div>
          <div className="flex gap-2">
            <select className="input px-3 py-2 rounded-lg bg-surfaceRaised border border-border text-sm">
              <option value="">All Disciplines</option>
              <option value="Piping">Piping</option>
              <option value="Civil">Civil</option>
              <option value="Mechanical">Mechanical</option>
              <option value="Electrical">Electrical</option>
            </select>
            <select className="input px-3 py-2 rounded-lg bg-surfaceRaised border border-border text-sm">
              <option value="">All Status</option>
              <option value="Not Started">Not Started</option>
              <option value="In Progress">In Progress</option>
              <option value="Complete">Complete</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Schedule Table */}
      <Card>
        <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <CardTitle>Schedule Activities ({mockActivities.length})</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <DataTable
            columns={columns}
            data={mockActivities}
            keyExtractor={(row) => String(row.id)}
            emptyMessage="No activities found"
            onRowClick={(row) => console.log('Row clicked', row)}
          />
        </CardContent>
      </Card>
    </div>
  )
}