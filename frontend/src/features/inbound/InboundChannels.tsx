import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { RefreshCw, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'

const mockMessages = [
  { id: 1, source: 'WHATSAPP', from: 'Rajesh Kumar (Supervisor)', text: 'Started piping erection at XX-101. Team on track for completion by 4 PM.', time: '2 min ago', status: 'matched', match: 'PIP-1023' },
  { id: 2, source: 'TIME_AGENT', from: 'Maria Santos', text: 'Pump P-101 installation complete. All connections verified.', time: '15 min ago', status: 'matched', match: 'MEC-2011' },
  { id: 3, source: 'VOICE', from: 'Ahmed Hassan', text: 'Delay on foundation A1 pour due to concrete truck breakdown. Estimated 3 hour delay.', time: '32 min ago', status: 'review', match: 'CIV-3011' },
  { id: 4, source: 'WHATSAPP', from: 'Priya Sharma', text: 'Inspection of weld joints on line XX-101 passed. Ready for hydrotest.', time: '1h ago', status: 'matched', match: 'PIP-1042' },
  { id: 5, source: 'SPREADSHEET', from: 'Daily Report Upload', text: 'Bulk upload: 12 activities updated across Piping and Civil disciplines.', time: '2h ago', status: 'processing', match: null },
  { id: 6, source: 'PDF_OCR', from: 'Scanned Diary - Shift A', text: 'Civil team completed backfill at Area C. Mechanical started pump alignment.', time: '3h ago', status: 'matched', match: 'CIV-3022' },
]

export function InboundChannels() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white">Inbound Channels</h1>
          <p className="text-textMuted mt-1">Live feed of field reports from all ingestion sources</p>
        </div>
<div className="flex items-center gap-3">
            <Badge variant="neutral">7 sources active</Badge>
            <Badge variant="auto-commit" dot>Live</Badge>
            <Button variant="secondary" size="sm">
              <RefreshCw className="w-4 h-4" />
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
            {[
              { name: 'WhatsApp', code: 'WHATSAPP', status: 'connected', count: 3 },
              { name: 'Time Agent', code: 'TIME_AGENT', status: 'connected', count: 5 },
              { name: 'Voice', code: 'VOICE', status: 'connected', count: 2 },
              { name: 'Spreadsheet', code: 'SPREADSHEET', status: 'connected', count: 1 },
              { name: 'PDF/OCR', code: 'PDF_OCR', status: 'connected', count: 2 },
              { name: 'PMIS Export', code: 'PMIS_EXPORT', status: 'idle', count: 0 },
              { name: 'Text Diary', code: 'TEXT_DIARY', status: 'idle', count: 0 },
            ].map((source) => (
              <div key={source.code} className="p-3 rounded-lg bg-surfaceRaised border border-border">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium text-white">{source.name}</span>
                  <Badge variant={source.status === 'connected' ? 'auto-commit' : 'neutral'} dot>
                    {source.status}
                  </Badge>
                </div>
                <p className="text-2xl font-bold text-white">{source.count}</p>
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
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="divide-y divide-border">
            {mockMessages.map((msg) => (
              <div key={msg.id} className="p-4 hover:bg-white/5 transition-colors">
                <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant="neutral" className="text-xs">{msg.source}</Badge>
                      <span className="text-sm text-textMuted">from {msg.from}</span>
                      <span className="text-xs text-textMuted">{msg.time}</span>
                    </div>
                    <p className="text-white mb-2">{msg.text}</p>
                    <div className="flex items-center gap-2">
                      <Badge
                        variant={
                          msg.status === 'matched' ? 'auto-commit' :
                          msg.status === 'review' ? 'review' :
                          msg.status === 'processing' ? 'neutral' : 'new-activity'
                        }
                        dot
                      >
                        {msg.status}
                      </Badge>
                      {msg.match && (
                        <span className="text-sm font-mono text-textMuted bg-surfaceRaised px-2 py-0.5 rounded">
                          → {msg.match}
                        </span>
                      )}
                    </div>
                  </div>
<div className="flex items-center gap-2">
                      {msg.status === 'matched' && (
                        <CheckCircle className="w-5 h-5 text-green-400" />
                      )}
                      {msg.status === 'review' && (
                        <AlertCircle className="w-5 h-5 text-amber-400" />
                      )}
                      {msg.status === 'processing' && (
                        <Loader2 className="w-5 h-5 animate-spin text-textMuted" />
                      )}
                    </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}