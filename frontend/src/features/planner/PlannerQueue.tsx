import { useState, useEffect, useCallback } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui'
import { Badge } from '../../components/ui/Badge'
import { DataTable } from '../../components/ui/Table'
import { Button } from '../../components/ui/Button'
import { Skeleton } from '../../components/ui/Skeleton'
import { EmptyState } from '../../components/ui/EmptyState'
import { Clock, CheckCircle, XCircle, Edit, AlertTriangle, ChevronUp } from 'lucide-react'
import { api } from '../../lib/api'
import { DelayImpactPanel } from '../../components/DelayImpactPanel'
import { formatDistanceToNow } from 'date-fns'

interface Review {
  id: number
  progress_event_id: number
  event_text: string
  event_type: string
  proposed_activity: string
  proposed_activity_id: number | null
  confidence_score: number
  confidence_level: 'HIGH' | 'MEDIUM' | 'LOW'
  status: 'PENDING' | 'APPROVED' | 'CORRECTED' | 'REJECTED' | 'NEW_ACTIVITY_CREATED'
  discipline: string
  project_id: number
  created_at: string
  top_candidates: Array<{
    activity_id: number
    activity_code: string
    activity_name: string
    discipline: string
    final_score: number
  }>
}

interface PlannerQueueProps {
  projectId?: number
}

const columns = [
  { key: 'event_text', header: 'Field Event', width: '250px' },
  { key: 'proposed_activity', header: 'Proposed Match', width: '200px' },
  { key: 'confidence', header: 'Confidence', width: '120px', render: (row: Review) => (
    <Badge variant={
      row.confidence_score >= 0.85 ? 'auto-commit' :
      row.confidence_score >= 0.60 ? 'review' :
      'new-activity'
    } dot>
      {(row.confidence_score * 100).toFixed(0)}%
    </Badge>
  )},
  { key: 'discipline', header: 'Discipline', width: '120px' },
  { key: 'created_at', header: 'Received', width: '130px', render: (row: Review) => (
    <span className="text-textMuted">{formatDistanceToNow(new Date(row.created_at), { addSuffix: true })}</span>
  )},
]

export function PlannerQueue({ projectId: propProjectId }: PlannerQueueProps) {
  const [reviews, setReviews] = useState<Review[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [projectId, setProjectId] = useState<number | null>(propProjectId || null)
  const [expandedReviewId, setExpandedReviewId] = useState<number | null>(null)
  const [selectedReview, setSelectedReview] = useState<Review | null>(null)

  const fetchReviews = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const params = projectId ? { project_id: projectId } : {}
      const response = await api.get('/reviews/pending', { params })
      setReviews(response.data.reviews || [])
      // Extract project_id from first review if not set
      if (!projectId && response.data.reviews?.[0]?.project_id) {
        setProjectId(response.data.reviews[0].project_id)
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch reviews')
    } finally {
      setIsLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    fetchReviews()
  }, [fetchReviews])

  const handleApprove = async (review: Review) => {
    try {
      await api.post(`/reviews/${review.id}/approve`, { reviewer_note: 'Approved via queue' })
      setReviews(prev => prev.filter(r => r.id !== review.id))
      if (expandedReviewId === review.id) {
        setExpandedReviewId(null)
      }
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to approve review')
    }
  }

  const handleReject = async (review: Review) => {
    try {
      await api.post(`/reviews/${review.id}/reject`, { reviewer_note: 'Rejected via queue' })
      setReviews(prev => prev.filter(r => r.id !== review.id))
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to reject review')
    }
  }

  const handleCorrectReview = async (review: Review, activityId: number) => {
    try {
      await api.post(`/reviews/${review.id}/correct`, { activity_id: activityId, reviewer_note: 'Corrected via queue' })
      setReviews(prev => prev.filter(r => r.id !== review.id))
      if (expandedReviewId === review.id) {
        setExpandedReviewId(null)
      }
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to correct review')
    }
  }

  const toggleExpand = (review: Review) => {
    setExpandedReviewId(prev => prev === review.id ? null : review.id)
    setSelectedReview(prev => prev?.id === review.id ? null : review)
  }

  const getEventTypeBadge = (eventType: string) => {
    const variants: Record<string, 'auto-commit' | 'review' | 'new-activity'> = {
      START: 'auto-commit',
      PROGRESS: 'review',
      COMPLETE: 'auto-commit',
      DELAY: 'new-activity',
      HOLD: 'review',
    }
    return <Badge variant={variants[eventType] || 'review'} dot>{eventType}</Badge>
  }

  const pendingCount = reviews.filter(r => r.status === 'PENDING').length

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
              <p className="text-3xl font-bold text-white kpi">{pendingCount}</p>
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
          <CardTitle>Pending Reviews ({pendingCount})</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-4 space-y-3">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="flex gap-4 px-4 py-3">
                  <Skeleton className="w-64 h-4" />
                  <Skeleton className="w-48 h-4" />
                  <Skeleton className="w-24 h-4" />
                  <Skeleton className="w-24 h-4" />
                  <Skeleton className="w-24 h-4" />
                </div>
              ))}
            </div>
          ) : error ? (
            <EmptyState
              icon={<AlertTriangle className="w-16 h-16" />}
              title="Error loading reviews"
              description={error}
            />
          ) : reviews.length === 0 ? (
            <EmptyState
              icon={<CheckCircle className="w-16 h-16" />}
              title="No pending reviews"
              description="All caught up! No reviews requiring attention."
            />
          ) : (
            <DataTable
              columns={columns}
              data={reviews}
              keyExtractor={(row) => String(row.id)}
              emptyMessage="No pending reviews"
              onRowClick={(row) => toggleExpand(row)}
            />
          )}
        </CardContent>
      </Card>

      {/* Expanded Review Detail with Delay Impact */}
      {expandedReviewId && selectedReview && (
        <div className="animate-slide-up">
          <Card className="mt-4">
            <CardHeader className="flex flex-row items-center justify-between">
              <div className="flex items-center gap-3">
                <h3 className="text-lg font-semibold text-white">Review Detail</h3>
                {getEventTypeBadge(selectedReview.event_type)}
              </div>
              <Button variant="ghost" size="sm" onClick={() => { setExpandedReviewId(null); setSelectedReview(null); }}>
                <ChevronUp className="w-4 h-4" />
              </Button>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-textMuted">Field Event</p>
                  <p className="text-white">{selectedReview.event_text}</p>
                </div>
                <div>
                  <p className="text-sm text-textMuted">Proposed Match</p>
                  <p className="text-white">{selectedReview.proposed_activity}</p>
                </div>
                <div>
                  <p className="text-sm text-textMuted">Confidence</p>
                  <p className="text-white">
                    <Badge variant={
                      selectedReview.confidence_score >= 0.85 ? 'auto-commit' :
                      selectedReview.confidence_score >= 0.60 ? 'review' :
                      'new-activity'
                    }>
                      {(selectedReview.confidence_score * 100).toFixed(0)}%
                    </Badge>
                  </p>
                </div>
                <div>
                  <p className="text-sm text-textMuted">Discipline</p>
                  <p className="text-white">{selectedReview.discipline}</p>
                </div>
              </div>

              {selectedReview.top_candidates && selectedReview.top_candidates.length > 1 && (
                <div>
                  <p className="text-sm text-textMuted mb-2">Alternative Candidates</p>
                  <div className="space-y-2">
                    {selectedReview.top_candidates.slice(1).map((cand, idx) => (
                      <div key={idx} className="p-3 bg-surfaceRaised rounded-lg flex items-center justify-between">
                        <div>
                          <p className="font-medium">{cand.activity_code}: {cand.activity_name}</p>
                          <p className="text-sm text-textMuted">{cand.discipline} • {(cand.final_score * 100).toFixed(0)}%</p>
                        </div>
                        <Button variant="secondary" size="sm" onClick={() => handleCorrectReview(selectedReview, cand.activity_id)}>
                          Select
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex gap-3 pt-2 border-t border-border">
                <Button variant="secondary" onClick={() => handleReject(selectedReview)}>
                  <XCircle className="w-4 h-4" />
                  Reject
                </Button>
                <Button onClick={() => handleApprove(selectedReview)}>
                  <CheckCircle className="w-4 h-4" />
                  Approve
                </Button>
              </div>

              {/* Delay Impact Panel for DELAY events */}
              {selectedReview.event_type === 'DELAY' && projectId && (
                <DelayImpactPanel 
                  projectId={projectId}
                  eventId={selectedReview.progress_event_id}
                />
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {projectId && !expandedReviewId && (
        <DelayImpactPanel 
          projectId={projectId}
          className="mt-6"
        />
      )}
    </div>
  )
}