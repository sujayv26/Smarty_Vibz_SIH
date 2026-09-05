import { useState, useEffect, useCallback } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { RefreshCw, CheckCircle, AlertCircle, Loader2, MessageSquare, Mic, FileText, FileSpreadsheet, FileSearch, Hash, Zap } from 'lucide-react'
import { api } from '../../lib/api'

type MessageStatus = 'matched' | 'review' | 'processing' | 'new-activity' | 'rejected'

interface InboundMessage {
  id: number
  source: string
  from: string
  text: string
  time: string
  status: MessageStatus
  match: string | null
  event_type: string
  created_at: string
}

interface SourceStatus {
  name: string
  code: string
  status: 'connected' | 'idle' | 'error'
  count: number
  icon: React.ReactNode
}

const SOURCE_CONFIG: Record<string, SourceStatus> = {
  WHATSAPP: { name: 'WhatsApp', code: 'WHATSAPP', status: 'connected', count: 0, icon: <MessageSquare className="w-5 h-5" /> },
  TIME_AGENT: { name: 'Time Agent', code: 'TIME_AGENT', status: 'connected', count: 0, icon: <Zap className="w-5 h-5" /> },
  VOICE: { name: 'Voice', code: 'VOICE', status: 'connected', count: 0, icon: <Mic className="w-5 h-5" /> },
  SPREADSHEET: { name: 'Spreadsheet', code: 'SPREADSHEET', status: 'connected', count: 0, icon: <FileSpreadsheet className="w-5 h-5" /> },
  PDF_OCR: { name: 'PDF/OCR', code: 'PDF_OCR', status: 'connected', count: 0, icon: <FileSearch className="w-5 h-5" /> },
  PMIS_EXPORT: { name: 'PMIS Export', code: 'PMIS_EXPORT', status: 'idle', count: 0, icon: <Hash className="w-5 h-5" /> },
  TEXT_DIARY: { name: 'Text Diary', code: 'TEXT_DIARY', status: 'idle', count: 0, icon: <FileText className="w-5 h-5" /> },
}

const STATUS_CONFIG: Record<MessageStatus, { variant: 'auto-commit' | 'review' | 'new-activity' | 'neutral'; icon: React.ElementType; label: string }> = {
  matched: { variant: 'auto-commit' as const, icon: CheckCircle, label: 'Auto-matched' },
  review: { variant: 'review' as const, icon: AlertCircle, label: 'Needs review' },
  processing: { variant: 'neutral' as const, icon: Loader2, label: 'Processing' },
  'new-activity': { variant: 'new-activity' as const, icon: AlertCircle, label: 'New activity' },
  rejected: { variant: 'new-activity' as const, icon: AlertCircle, label: 'Rejected' },
}

function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffSecs = Math.floor(diffMs / 1000)
  const diffMins = Math.floor(diffSecs / 60)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffSecs < 60) return `${diffSecs}s ago`
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  return `${diffDays}d ago`
}

export function InboundChannels() {
  const [messages, setMessages] = useState<InboundMessage[]>([])
  const [sourceStatus, setSourceStatus] = useState<Record<string, SourceStatus>>(SOURCE_CONFIG)
  const [isLoading, setIsLoading] = useState(true)
  const [isLive, setIsLive] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)

  const fetchMessages = useCallback(async () => {
    try {
      const response = await api.get('/progress/inbound/recent', {
        params: { hours: 24, limit: 100 }
      })
      
      const newMessages = response.data
      setMessages(newMessages)
      setLastUpdate(new Date())
      setError(null)
      
      // Update source counts
      const counts: Record<string, number> = {}
      newMessages.forEach((msg: InboundMessage) => {
        counts[msg.source] = (counts[msg.source] || 0) + 1
      })
      
      setSourceStatus(prev => {
        const updated = { ...prev }
        Object.keys(counts).forEach(key => {
          if (updated[key]) {
            updated[key] = { ...updated[key], count: counts[key] }
          }
        })
        return updated
      })
    } catch (err) {
      console.error('Failed to fetch inbound messages:', err)
      setError('Failed to load messages')
    } finally {
      setIsLoading(false)
    }
  }, [])

  // Initial load
  useEffect(() => {
    fetchMessages()
  }, [fetchMessages])

  // Auto-refresh every 10 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchMessages()
    }, 10000)
    return () => clearInterval(interval)
  }, [fetchMessages])

  // Simulate live connection status
  useEffect(() => {
    setIsLive(true)
    const interval = setInterval(() => {
      setIsLive(prev => !prev) // Blink effect
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white">Inbound Channels</h1>
          <p className="text-textMuted mt-1">Live feed of field reports from all ingestion sources</p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="neutral">{Object.keys(SOURCE_CONFIG).length} sources configured</Badge>
          <Badge variant={isLive ? 'auto-commit' : 'neutral'} dot>
            {isLive ? 'Live' : 'Connecting...'}
          </Badge>
          <Button variant="secondary" size="sm" onClick={fetchMessages} disabled={isLoading}>
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Source Status */}
      <Card>
        <CardHeader>
          <CardTitle>Source Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
            {Object.values(SOURCE_CONFIG).map((source) => (
              <div key={source.code} className="p-3 rounded-lg bg-surfaceRaised border border-border">
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <span className="text-textMuted">{source.icon}</span>
                    <span className="font-medium text-white">{source.name}</span>
                  </div>
                  <Badge variant={source.status === 'connected' ? 'auto-commit' : 'neutral'} dot>
                    {source.status}
                  </Badge>
                </div>
                <p className="text-2xl font-bold text-white">{sourceStatus[source.code]?.count || 0}</p>
                <p className="text-xs text-textMuted">messages (24h)</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Live Feed */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Live Message Feed</CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="auto-commit" dot>Live</Badge>
            <Loader2 className="w-4 h-4 animate-spin text-textMuted" />
            {lastUpdate && (
              <span className="text-xs text-textMuted">
                Updated {formatTimeAgo(lastUpdate.toISOString())}
              </span>
            )}
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-4 space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex gap-4 p-4 animate-pulse">
                  <div className="w-8 h-8 rounded-full bg-white/10" />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 w-3/4 bg-white/10 rounded" />
                    <div className="h-3 w-full bg-white/10 rounded" />
                    <div className="h-3 w-1/2 bg-white/10 rounded" />
                  </div>
                </div>
              ))}
            </div>
          ) : error ? (
            <div className="p-8 text-center">
              <AlertCircle className="w-12 h-12 text-status-new-activity mx-auto mb-4" />
              <p className="text-status-new-activity">{error}</p>
              <Button variant="secondary" onClick={fetchMessages} className="mt-4">
                <RefreshCw className="w-4 h-4" />
                Retry
              </Button>
            </div>
          ) : messages.length === 0 ? (
            <div className="p-8 text-center">
              <MessageSquare className="w-16 h-16 text-textMuted/50 mx-auto mb-4" />
              <p className="text-textMuted">No messages in the last 24 hours</p>
              <p className="text-xs text-textMuted mt-1">Send a WhatsApp message or upload a report to see it here</p>
            </div>
          ) : (
            <div className="divide-y divide-border max-h-[600px] overflow-y-auto">
              {messages.map((msg) => {
                const statusConfig = STATUS_CONFIG[msg.status as keyof typeof STATUS_CONFIG] || STATUS_CONFIG.processing
                const StatusIcon = statusConfig.icon
                return (
                  <div key={msg.id} className="p-4 hover:bg-white/5 transition-colors">
                    <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1 flex-wrap">
                          <Badge variant="neutral" className="text-xs">{msg.source}</Badge>
                          <span className="text-sm text-textMuted">from field user</span>
                          <span className="text-xs text-textMuted">{formatTimeAgo(msg.created_at)}</span>
                        </div>
                        <p className="text-white mb-2 truncate-2">{msg.text}</p>
                        <div className="flex items-center gap-2 flex-wrap">
                          <Badge variant={statusConfig.variant} dot>
                            {statusConfig.label}
                          </Badge>
                          {msg.match && (
                            <span className="text-sm font-mono text-textMuted bg-surfaceRaised px-2 py-0.5 rounded">
                              → {msg.match}
                            </span>
                          )}
                          <span className="text-xs text-textMuted capitalize">{msg.event_type.toLowerCase()}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <StatusIcon className={`w-5 h-5 ${statusConfig.variant === 'auto-commit' ? 'text-green-400' : statusConfig.variant === 'review' ? 'text-amber-400' : statusConfig.variant === 'new-activity' ? 'text-red-400' : 'text-textMuted'} ${msg.status === 'processing' ? 'animate-spin' : ''}`} />
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}