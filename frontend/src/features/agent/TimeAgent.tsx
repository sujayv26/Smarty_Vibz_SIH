import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui'
import { Button } from '../../components/ui/Button'
import { Badge } from '../../components/ui/Badge'
import { Textarea } from '../../components/ui/Input'
import { useState } from 'react'
import { cn } from '../../lib/utils'
import { Mic, Send, MessageSquare, Loader2 } from 'lucide-react'

const mockMessages = [
  { id: 1, role: 'assistant', content: 'Hello! I\'m your ConSight Time Agent. How can I help you log progress today?', time: '09:00' },
  { id: 2, role: 'user', content: 'Started erection of XX-101 spool at 9:30 AM in Area B', time: '09:05' },
  { id: 3, role: 'assistant', content: 'I understood: START — XX-101 spool erection at 09:30 in Area B (Piping). Logged as event #1023.', time: '09:05' },
  { id: 4, role: 'user', content: 'match it', time: '09:06' },
  { id: 5, role: 'assistant', content: 'Found match: PIP-1023 "Erect Line 24-XX-101" (92% confidence). Auto-committed.', time: '09:06' },
]

export function TimeAgent() {
  const [message, setMessage] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const handleSend = async () => {
    if (!message.trim() || isLoading) return
    setIsLoading(true)
    // Simulate API call
    setTimeout(() => {
      setMessage('')
      setIsLoading(false)
    }, 1000)
  }

  const handleVoice = () => {
    setIsRecording(!isRecording)
  }

  return (
    <div className="space-y-6 animate-fade-in max-w-3xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold text-white">Time Agent</h1>
        <p className="text-textMuted mt-1">Log progress naturally via chat or voice</p>
      </div>

      {/* Chat Area */}
      <Card className="flex flex-col h-[600px]">
        <CardHeader className="flex flex-row items-center justify-between p-4 border-b border-border">
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5" />
            Session: CONS-2026-09-05-001
          </CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="auto-commit" dot>Active</Badge>
          </div>
        </CardHeader>
        <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
          {mockMessages.map((msg) => (
            <div
              key={msg.id}
              className={cn(
                'flex gap-3 animate-slide-up',
                msg.role === 'user' && 'flex-row-reverse'
              )}
            >
              <div
                className={cn(
                  'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
                  msg.role === 'user' ? 'bg-white/10' : 'bg-white/20'
                )}
              >
                {msg.role === 'user' ? (
                  <span className="text-xs font-medium text-white">U</span>
                ) : (
                  <MessageSquare className="w-4 h-4 text-textMuted" />
                )}
              </div>
              <div className={cn(
                'max-w-[70%] rounded-2xl px-4 py-2.5',
                msg.role === 'user'
                  ? 'bg-white/10 text-white rounded-tr-none'
                  : 'bg-surfaceRaised text-white rounded-tl-none'
              )}>
                <p className="text-sm">{msg.content}</p>
                <p className="text-xs text-textMuted/60 mt-1 text-right">{msg.time}</p>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex gap-3 animate-slide-up">
              <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center flex-shrink-0">
                <Loader2 className="w-4 h-4 animate-spin text-textMuted" />
              </div>
              <div className="bg-surfaceRaised rounded-2xl rounded-tl-none px-4 py-2.5">
                <div className="flex gap-1">
                  <div className="w-2 h-2 rounded-full bg-textMuted/50 animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 rounded-full bg-textMuted/50 animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 rounded-full bg-textMuted/50 animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}
        </CardContent>

        {/* Input Area */}
        <div className="p-4 border-t border-border">
          <div className="flex items-end gap-3">
            <Textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
              placeholder="Type your progress update... (e.g., 'Completed pump P-101 installation at 2 PM')"
              rows={1}
              className="flex-1 min-h-[44px] max-h-32 resize-none"
            />
            <div className="flex items-center gap-2">
              <button
                onClick={handleVoice}
                disabled={isLoading}
                className={cn(
                  'p-2.5 rounded-lg transition-colors flex-shrink-0',
                  isRecording
                    ? 'bg-red-500/20 text-red-400 animate-pulse'
                    : 'bg-surfaceRaised text-textMuted hover:text-white hover:bg-white/10'
                )}
                aria-label={isRecording ? 'Stop recording' : 'Start voice input'}
              >
                <Mic className="w-5 h-5" />
              </button>
              <button
                onClick={handleSend}
                disabled={!message.trim() || isLoading}
                className={cn(
                  'p-2.5 rounded-lg transition-colors flex-shrink-0',
                  message.trim() && !isLoading
                    ? 'bg-white text-bgApp hover:bg-white/90'
                    : 'bg-surfaceRaised text-textMuted cursor-not-allowed'
                )}
                aria-label="Send message"
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>
          <p className="text-xs text-textMuted mt-2 text-center">
            Try: "Started piping erection at 9 AM", "Pump P-101 complete", "Delay on foundation pour due to rain"
          </p>
        </div>
      </Card>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Templates</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: 'Start Work', icon: '▶️', text: 'Started [activity] at [time] in [location]' },
            { label: 'Complete', icon: '✅', text: 'Completed [activity] at [time]' },
            { label: 'Progress', icon: '📊', text: '[activity] is [X]% complete' },
            { label: 'Delay', icon: '⚠️', text: 'Delay on [activity] due to [reason]' },
          ].map((item) => (
            <Button
              key={item.label}
              variant="ghost"
              className="w-full justify-start gap-2 text-left h-auto py-3"
              onClick={() => setMessage(item.text)}
            >
              <span className="text-2xl">{item.icon}</span>
              <span className="font-medium">{item.label}</span>
            </Button>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}