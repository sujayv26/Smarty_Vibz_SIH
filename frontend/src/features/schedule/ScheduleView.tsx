import { useState, useEffect, useCallback } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import { DataTable } from '../../components/ui/Table'
import { Badge } from '../../components/ui/Badge'
import { EmptyState } from '../../components/ui/EmptyState'
import { Skeleton } from '../../components/ui/Skeleton'
import { api } from '../../lib/api'
import { Download, Upload, FileText, X, AlertTriangle, RefreshCw, Save } from 'lucide-react'

interface ScheduleActivity {
  id: number
  activity_code: string
  activity_name: string
  discipline: string
  wbs: string
  planned_start: string | null
  planned_finish: string | null
  actual_start: string | null
  actual_finish: string | null
  external_activity_id: string | null
  source_format: string | null
}

interface ImportPreviewActivity {
  activity_id: string
  activity_code: string
  activity_name: string
  discipline: string
  wbs_code: string | null
  wbs_name: string | null
  planned_start: string | null
  planned_finish: string | null
  is_new: boolean
  is_updated: boolean
  changes?: string[]
}

interface ImportResult {
  source_format: string
  source_filename: string
  external_schedule_id: string
  external_schedule_name: string
  internal_schedule_id: number
  imported_activity_count: number
  rejected_activity_count: number
  rejected_activities: Array<{ activity_id: string; activity_code: string; error: string }>
  imported_relationship_count: number
  rejected_relationship_count: number
  rejected_relationships: Array<{ predecessor: string; successor: string; error: string }>
  validation_errors: any[]
}

interface ExternalSchedule {
  id: number
  external_schedule_id: string
  schedule_name: string | null
  source_filename: string | null
  source_format: string
  imported_at: string
  activity_count: number
}

const columns = [
  { key: 'activity_code', header: 'Code', width: '100px' },
  { key: 'activity_name', header: 'Activity Name', width: '250px' },
  { key: 'discipline', header: 'Discipline', width: '120px' },
  { key: 'wbs', header: 'WBS', width: '100px' },
  { key: 'planned_start', header: 'Planned Start', width: '130px' },
  { key: 'planned_finish', header: 'Planned Finish', width: '130px' },
  { key: 'actual_start', header: 'Actual Start', width: '130px' },
  { key: 'actual_finish', header: 'Actual Finish', width: '130px' },
  { key: 'status', header: 'Status', width: '120px', render: (row: ScheduleActivity) => (
    <Badge variant={
      row.actual_finish ? 'auto-commit' :
      row.actual_start ? 'review' :
      'new-activity'
    } dot>
      {row.actual_finish ? 'Complete' : row.actual_start ? 'In Progress' : 'Not Started'}
    </Badge>
  ) },
]

const previewColumns = [
  { key: 'activity_code', header: 'Code', width: '100px' },
  { key: 'activity_name', header: 'Activity Name', width: '250px' },
  { key: 'discipline', header: 'Discipline', width: '120px' },
  { key: 'wbs_code', header: 'WBS Code', width: '100px' },
  { key: 'planned_start', header: 'Planned Start', width: '130px' },
  { key: 'planned_finish', header: 'Planned Finish', width: '130px' },
  { key: 'status', header: 'Status', width: '130px', render: (row: ImportPreviewActivity) => (
    <Badge variant={row.is_new ? 'new-activity' : row.is_updated ? 'review' : 'auto-commit'} dot>
      {row.is_new ? 'New' : row.is_updated ? 'Updated' : 'Unchanged'}
    </Badge>
  ) },
]

export function ScheduleView() {
  const [activities, setActivities] = useState<ScheduleActivity[]>([])
  const [externalSchedules, setExternalSchedules] = useState<ExternalSchedule[]>([])
  const [selectedScheduleId, setSelectedScheduleId] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isImporting, setIsImporting] = useState(false)
  const [isExporting, setIsExporting] = useState(false)
  const [importPreview, setImportPreview] = useState<ImportPreviewActivity[] | null>(null)
  const [importResult, setImportResult] = useState<ImportResult | null>(null)
  const [importError, setImportError] = useState<string | null>(null)
  const [showImportModal, setShowImportModal] = useState(false)

  const fetchActivities = useCallback(async () => {
    try {
      const params = selectedScheduleId ? { schedule_id: selectedScheduleId } : {}
      const response = await api.get('/schedule/external-schedules/activities', { params })
      setActivities(response.data)
    } catch (error) {
      console.error('Failed to fetch activities:', error)
      setActivities([])
    } finally {
      setIsLoading(false)
    }
  }, [selectedScheduleId])

  const fetchExternalSchedules = useCallback(async () => {
    try {
      const response = await api.get('/schedule/external-schedules')
      setExternalSchedules(response.data)
      if (response.data.length > 0 && !selectedScheduleId) {
        setSelectedScheduleId(response.data[0].id)
      }
    } catch (error) {
      console.error('Failed to fetch external schedules:', error)
    }
  }, [selectedScheduleId])

  useEffect(() => {
    fetchExternalSchedules()
  }, [fetchExternalSchedules])

  useEffect(() => {
    if (selectedScheduleId) {
      fetchActivities()
    }
  }, [selectedScheduleId, fetchActivities])

  const handleImportPreview = async (file: File) => {
    setIsImporting(true)
    setImportError(null)
    setImportPreview(null)
    setImportResult(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await api.post('/schedule/import/p6', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })

      const result: ImportResult = response.data
      setImportResult(result)

      if (result.imported_activity_count > 0 || result.rejected_activity_count > 0) {
        const previewData: ImportPreviewActivity[] = []
        
        if (result.source_format === 'XER' || result.source_format === 'MPP') {
          const activitiesResponse = await api.get(`/schedule/external-schedules/${result.internal_schedule_id}/activities`)
          const importedActivities = activitiesResponse.data

          importedActivities.forEach((act: any) => {
            previewData.push({
              activity_id: act.external_activity_id || act.activity_code,
              activity_code: act.activity_code,
              activity_name: act.activity_name,
              discipline: act.discipline,
              wbs_code: act.wbs,
              wbs_name: act.wbs,
              planned_start: act.planned_start,
              planned_finish: act.planned_finish,
              is_new: true,
              is_updated: false,
            })
          })
        }

        setImportPreview(previewData)
      }
    } catch (error: any) {
      setImportError(error.response?.data?.detail || 'Import failed')
    } finally {
      setIsImporting(false)
    }
  }

  const handleCommitImport = async () => {
    if (!importResult) return

    setIsImporting(true)
    try {
      // Import already commits to database, just close modal and refresh
      setShowImportModal(false)
      setImportPreview(null)
      setImportResult(null)
      fetchActivities()
      fetchExternalSchedules()
    } catch (error: any) {
      setImportError(error.response?.data?.detail || 'Commit failed')
    } finally {
      setIsImporting(false)
    }
  }

  const handleExport = async () => {
    if (!selectedScheduleId) return

    setIsExporting(true)
    try {
      const response = await api.post(`/schedule/export/p6/${selectedScheduleId}`, null, {
        responseType: 'blob',
      })

      const blob = new Blob([response.data], { type: 'application/octet-stream' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `schedule_${externalSchedules.find(s => s.id === selectedScheduleId)?.external_schedule_id || selectedScheduleId}.xer`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Export failed:', error)
      alert('Export failed. Please try again.')
    } finally {
      setIsExporting(false)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      handleImportPreview(file)
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white">Schedule</h1>
          <p className="text-textMuted mt-1">View and manage project schedule, import/export XER/MSP files</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="secondary" size="sm" onClick={handleExport} disabled={isExporting || !selectedScheduleId}>
            <Download className="w-4 h-4" />
            {isExporting ? 'Exporting...' : 'Export XER'}
          </Button>
          <Button variant="secondary" size="sm" onClick={() => setShowImportModal(true)}>
            <Upload className="w-4 h-4" />
            Import XER/MSP
          </Button>
        </div>
      </div>

      {/* Schedule Selector */}
      {externalSchedules.length > 0 && (
        <Card className="p-4">
          <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
            <div className="flex-1">
              <label className="label">Select Schedule</label>
              <select
                className="input w-full sm:w-80"
                value={selectedScheduleId || ''}
                onChange={(e) => setSelectedScheduleId(e.target.value ? parseInt(e.target.value) : null)}
              >
                <option value="">-- Select a schedule --</option>
                {externalSchedules.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.schedule_name || s.external_schedule_id} ({s.source_format}) - {s.activity_count} activities
                  </option>
                ))}
              </select>
            </div>
            <div className="flex items-center gap-4 text-sm text-textMuted">
              <span>{externalSchedules.find(s => s.id === selectedScheduleId)?.activity_count || 0} activities</span>
              <span>•</span>
              <span>Last import: {externalSchedules.find(s => s.id === selectedScheduleId)?.imported_at ? new Date(externalSchedules.find(s => s.id === selectedScheduleId)!.imported_at).toLocaleDateString() : 'N/A'}</span>
            </div>
          </div>
        </Card>
      )}

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
          <CardTitle>Schedule Activities ({activities.length})</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-4 space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="flex gap-4 px-4 py-3">
                  <Skeleton className="w-24 h-4" />
                  <Skeleton className="flex-1 h-4" />
                  <Skeleton className="w-24 h-4" />
                  <Skeleton className="w-24 h-4" />
                  <Skeleton className="w-28 h-4" />
                  <Skeleton className="w-28 h-4" />
                  <Skeleton className="w-28 h-4" />
                  <Skeleton className="w-28 h-4" />
                </div>
              ))}
            </div>
          ) : activities.length === 0 ? (
            <EmptyState
              icon={<FileText className="w-16 h-16" />}
              title="No activities found"
              description={selectedScheduleId ? "This schedule has no activities yet." : "Select a schedule or import a new one."}
            />
          ) : (
            <DataTable
              columns={columns}
              data={activities}
              keyExtractor={(row) => String(row.id)}
              emptyMessage="No activities found"
              onRowClick={(row) => console.log('Row clicked', row)}
            />
          )}
        </CardContent>
      </Card>

      {/* Import Modal */}
      {showImportModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-surface border border-border rounded-card w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col animate-scale-in">
            <div className="p-4 border-b border-border flex items-center justify-between">
              <h2 className="text-xl font-semibold text-white">Import Schedule Preview</h2>
              <button onClick={() => { setShowImportModal(false); setImportPreview(null); setImportResult(null); }} className="p-2 text-textMuted hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            {importError && (
              <div className="p-4 border-b border-border bg-status-new-activity/10">
                <div className="flex items-center gap-2 text-status-new-activity">
                  <AlertTriangle className="w-5 h-5" />
                  <span>{importError}</span>
                </div>
              </div>
            )}

            {importPreview && importPreview.length > 0 && (
              <div className="flex-1 overflow-auto p-4">
                <div className="mb-4 flex items-center justify-between">
                  <p className="text-sm text-textMuted">
                    {importResult?.imported_activity_count || 0} activities to import, {importResult?.rejected_activity_count || 0} rejected
                  </p>
                  <div className="flex items-center gap-2">
                    <Badge variant="new-activity" dot>New</Badge>
                    <Badge variant="review" dot>Updated</Badge>
                    <Badge variant="auto-commit" dot>Unchanged</Badge>
                  </div>
                </div>
                <DataTable
                  columns={previewColumns}
                  data={importPreview}
                  keyExtractor={(row) => row.activity_id}
                  emptyMessage="No preview data"
                />
              </div>
            )}

            {!importPreview && !importResult && (
              <div className="flex-1 flex items-center justify-center p-8">
                <div className="text-center">
                  <Upload className="w-16 h-16 text-textMuted/50 mx-auto mb-4" />
                  <p className="text-lg text-textMuted mb-4">Drop .xer or .mpp file here</p>
                  <input
                    type="file"
                    accept=".xer,.mpp"
                    onChange={handleFileSelect}
                    className="hidden"
                    id="import-file-input"
                    ref={(el) => el?.click()}
                  />
                  <Button variant="secondary" onClick={() => document.getElementById('import-file-input')?.click()}>
                    <Upload className="w-4 h-4" />
                    Browse Files
                  </Button>
                </div>
              </div>
            )}

            {importPreview && importPreview.length === 0 && importResult && (
              <div className="flex-1 flex items-center justify-center p-8">
                <EmptyState
                  icon={<AlertTriangle className="w-16 h-16" />}
                  title="No valid activities found"
                  description={importResult.rejected_activities.length > 0 ? `All ${importResult.rejected_activities.length} activities were rejected.` : "The file appears to be empty or invalid."}
                />
              </div>
            )}

            <div className="p-4 border-t border-border flex justify-end gap-3">
              <Button variant="ghost" onClick={() => { setShowImportModal(false); setImportPreview(null); setImportResult(null); }}>
                Cancel
              </Button>
              {importPreview && importPreview.length > 0 && (
                <Button onClick={handleCommitImport} disabled={isImporting}>
                  <Save className="w-4 h-4" />
                  {isImporting ? 'Committing...' : 'Commit Import'}
                </Button>
              )}
              {!importPreview && !importResult && (
                <Button variant="secondary" onClick={() => document.getElementById('import-file-input')?.click()}>
                  <RefreshCw className="w-4 h-4" />
                  Try Another File
                </Button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}