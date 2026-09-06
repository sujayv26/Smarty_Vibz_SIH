import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui'
import { Button } from '../../components/ui/Button'
import { Badge } from '../../components/ui/Badge'
import { Textarea } from '../../components/ui/Input'
import { useState, useRef, useEffect, useCallback } from 'react'
import { cn } from '../../lib/utils'
import { Send, MessageSquare, Loader2 } from 'lucide-react'
import { api } from '../../lib/api'
import { formatDistanceToNow } from 'date-fns'
import { VoiceRecorder } from '../../components/VoiceRecorder'

interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  time: string
  understood?: any
  agentResponse?: any
}

interface UnderstoodProgress {
  activity_reference: string | null
  event_type: string | null
  event_date: string | null
  event_time: string | null
  discipline: string | null
  location: string | null
  equipment_tag: string | null
}

interface AgentChatResponse {
  understood: UnderstoodProgress
  progress_event_id: number
  matched_activity: any
  confidence: number | null
  reply: string
  follow_up: string
}

const SESSION_ID = `CONS-${new Date().toISOString().split('T')[0].replace(/-/g, '')}-001`

export function TimeAgent() {
  const [messages, setMessages] = useState<Message[]>([])
  const [message, setMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [preferredLanguage, setPreferredLanguage] = useState('en')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  // Load initial message
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([
        {
          id: 1,
          role: 'assistant',
          content: "Hello! I'm your ConSight Time Agent. How can I help you log progress today?",
          time: new Date().toISOString(),
        }
      ])
    }
  }, [])

  const addMessage = (role: 'user' | 'assistant', content: string, understood?: any, agentResponse?: any) => {
    const newMessage: Message = {
      id: Date.now(),
      role,
      content,
      time: new Date().toISOString(),
      understood,
      agentResponse,
    }
    setMessages(prev => [...prev, newMessage])
  }

  const handleSend = async () => {
    if (!message.trim() || isLoading) return
    
    const userMessage = message.trim()
    setMessage('')
    setIsLoading(true)
    
    // Add user message immediately
    addMessage('user', userMessage)
    
    try {
      const response = await api.post('/agent/chat', {
        message: userMessage,
        session_id: SESSION_ID,
      })
      
      const agentResponse: AgentChatResponse = response.data
      
      // Add assistant response
      addMessage('assistant', agentResponse.reply, agentResponse.understood, agentResponse)
      
    } catch (err: any) {
      console.error('Agent chat failed:', err)
      addMessage('assistant', 'Sorry, I encountered an error. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleVoiceTranscript = useCallback(async (transcript: string, detectedLanguage: string) => {
    setPreferredLanguage(detectedLanguage)
    setMessage(transcript)
    // Auto-send after a brief delay to show the transcript
    setTimeout(() => {
      handleSend()
    }, 500)
  }, [])

  const handleVoiceError = useCallback((error: string) => {
    console.error('Voice error:', error)
    addMessage('assistant', `Voice input error: ${error}`)
  }, [])

  const formatTime = (isoString: string) => {
    return formatDistanceToNow(new Date(isoString), { addSuffix: true })
      .replace('about ', '')
      .replace('less than a minute', 'just now')
  }

  const formatUnderstood = (understood: UnderstoodProgress) => {
    const parts = []
    if (understood.event_type) parts.push(understood.event_type)
    if (understood.activity_reference) parts.push(understood.activity_reference)
    if (understood.event_time) parts.push(`at ${understood.event_time}`)
    if (understood.location) parts.push(`in ${understood.location}`)
    if (understood.discipline) parts.push(`(${understood.discipline})`)
    return parts.join(' — ') || 'No details extracted'
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
            Session: {SESSION_ID}
          </CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="auto-commit" dot>Active</Badge>
            <select
              value={preferredLanguage}
              onChange={(e) => setPreferredLanguage(e.target.value)}
              className="bg-surfaceRaised border border-border rounded-lg px-2 py-1 text-sm text-white"
              aria-label="Language"
            >
              <option value="en">English</option>
              <option value="hi">Hindi</option>
              <option value="ta">Tamil</option>
              <option value="te">Telugu</option>
              <option value="kn">Kannada</option>
            </select>
          </div>
        </CardHeader>
        <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
          <div ref={messagesEndRef} />
          {messages.map((msg) => (
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
                {msg.understood && (
                  <p className="text-xs text-textMuted/80 mt-1 font-mono">
                    Understood: {formatUnderstood(msg.understood)}
                  </p>
                )}
                {msg.agentResponse?.matched_activity && (
                  <div className="mt-2 p-2 bg-green-500/10 border border-green-500/30 rounded-lg">
                    <p className="text-xs font-medium text-green-400 mb-1">Matched Activity</p>
                    <p className="text-xs text-white">{msg.agentResponse.matched_activity.activity_code}: {msg.agentResponse.matched_activity.activity_name}</p>
                    <p className="text-xs text-textMuted">{msg.agentResponse.matched_activity.discipline} • {(msg.agentResponse.confidence || 0) * 100}% confidence</p>
                  </div>
                )}
                <p className="text-xs text-textMuted/60 mt-1 text-right">{formatTime(msg.time)}</p>
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
          <VoiceRecorder
            sessionId={SESSION_ID}
            preferredLanguage={preferredLanguage}
            onTranscript={handleVoiceTranscript}
            onError={handleVoiceError}
          />
          
          <div className="flex items-end gap-3 mt-4">
            <Textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
              placeholder="Type your progress update... (e.g., 'Completed pump P-101 installation at 2 PM')"
              rows={1}
              disabled={isLoading}
              className="flex-1 min-h-[44px] max-h-32 resize-none"
            />
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