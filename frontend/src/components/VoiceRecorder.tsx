import { useState, useRef, useEffect, useCallback } from 'react'
import { Mic, Loader2 } from 'lucide-react'
import { cn } from '../lib/utils'
import { api } from '../lib/api'

interface VoiceRecorderProps {
  sessionId: string
  preferredLanguage: string
  onTranscript: (transcript: string, detectedLanguage: string) => void
  onError: (error: string) => void
  className?: string
}

export function VoiceRecorder({
  sessionId,
  preferredLanguage,
  onTranscript,
  onError,
  className = '',
}: VoiceRecorderProps) {
  const [isRecording, setIsRecording] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [audioLevel, setAudioLevel] = useState(0)
  const [transcript, setTranscript] = useState<string | null>(null)
  const [detectedLanguage, setDetectedLanguage] = useState<string | null>(null)
  const [duration, setDuration] = useState(0)
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const animationFrameRef = useRef<number | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const startTimeRef = useRef<number>(0)
  const durationIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopRecording()
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current)
      }
    }
  }, [])

  const updateAudioLevel = useCallback(() => {
    if (!analyserRef.current) return
    
    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount)
    analyserRef.current.getByteFrequencyData(dataArray)
    
    // Calculate average volume (0-255) and normalize to 0-1
    const average = dataArray.reduce((a, b) => a + b, 0) / dataArray.length
    setAudioLevel(Math.min(average / 128, 1))
    
    animationFrameRef.current = requestAnimationFrame(updateAudioLevel)
  }, [])

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000,
        } 
      })
      
      streamRef.current = stream
      
      // Set up audio context for visualization
      const audioContext = new AudioContext()
      audioContextRef.current = audioContext
      
      const source = audioContext.createMediaStreamSource(stream)
      const analyser = audioContext.createAnalyser()
      analyser.fftSize = 256
      analyser.smoothingTimeConstant = 0.8
      source.connect(analyser)
      analyserRef.current = analyser
      
      // Set up media recorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus',
      })
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }
      
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
        await processAudioBlob(audioBlob)
      }
      
      mediaRecorder.start(100) // Collect data every 100ms
      setIsRecording(true)
      setTranscript(null)
      setDetectedLanguage(null)
      startTimeRef.current = Date.now()
      
      // Start duration timer
      durationIntervalRef.current = setInterval(() => {
        setDuration(Math.floor((Date.now() - startTimeRef.current) / 1000))
      }, 1000)
      
      // Start audio level visualization
      updateAudioLevel()
      
    } catch (err) {
      console.error('Failed to start recording:', err)
      onError('Failed to access microphone. Please check permissions.')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
    }
    
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
      streamRef.current = null
    }
    
    if (audioContextRef.current) {
      audioContextRef.current.close()
      audioContextRef.current = null
    }
    
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current)
      animationFrameRef.current = null
    }
    
    if (durationIntervalRef.current) {
      clearInterval(durationIntervalRef.current)
      durationIntervalRef.current = null
    }
    
    setIsRecording(false)
    setAudioLevel(0)
  }

  const processAudioBlob = async (audioBlob: Blob) => {
    setIsProcessing(true)
    
    try {
      const formData = new FormData()
      formData.append('file', audioBlob, `recording-${Date.now()}.webm`)
      formData.append('session_id', sessionId)
      formData.append('preferred_language', preferredLanguage)
      
      const response = await api.post('/voice/process', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      
      const { transcript, detected_language } = response.data
      
      setTranscript(transcript)
      setDetectedLanguage(detected_language)
      onTranscript(transcript, detected_language)
      
    } catch (err: any) {
      console.error('Voice processing failed:', err)
      onError(err.response?.data?.detail || 'Failed to process voice input')
    } finally {
      setIsProcessing(false)
    }
  }

  const handleToggleRecording = () => {
    if (isProcessing) return
    
    if (isRecording) {
      stopRecording()
    } else {
      startRecording()
    }
  }

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className={cn('space-y-4', className)}>
      {/* Recording Button */}
      <button
        onClick={handleToggleRecording}
        disabled={isProcessing}
        className={cn(
          'relative w-20 h-20 mx-auto rounded-full transition-all duration-300 flex items-center justify-center',
          isRecording
            ? 'bg-red-500 animate-pulse ring-4 ring-red-500/30'
            : isProcessing
            ? 'bg-amber-500 cursor-wait'
            : 'bg-white/10 hover:bg-white/20 text-textMuted hover:text-white'
        )}
        aria-label={isRecording ? 'Stop recording' : 'Start recording'}
      >
        {isProcessing ? (
          <Loader2 className="w-8 h-8 animate-spin text-white" />
        ) : isRecording ? (
          <Mic className="w-8 h-8 text-white" />
        ) : (
          <Mic className={cn('w-8 h-8', isRecording ? 'text-red-400' : 'text-textMuted')} />
        )}
        
        {/* Pulsing ring when recording */}
        {isRecording && (
          <div className="absolute inset-0 rounded-full border-2 border-red-500/50 animate-pulse" />
        )}
      </button>

      {/* Status Text */}
      <div className="text-center space-y-1">
        {isRecording && (
          <p className="text-red-400 font-medium animate-pulse">
            Recording... {formatDuration(duration)}
          </p>
        )}
        {isProcessing && (
          <p className="text-amber-400 font-medium">Processing...</p>
        )}
        {transcript && !isRecording && !isProcessing && (
          <p className="text-green-400 font-medium">Transcribed successfully</p>
        )}
        {detectedLanguage && (
          <p className="text-xs text-textMuted">
            Detected: {detectedLanguage.toUpperCase()}
          </p>
        )}
      </div>

      {/* Audio Level Visualizer */}
      <div className="h-8 flex items-end justify-center gap-1">
        {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((i) => (
          <div
            key={i}
            className="w-2 rounded-t transition-all duration-75 bg-gradient-to-t"
            style={{
              height: `${Math.max(4, audioLevel * 40 * (0.5 + Math.random() * 0.5))}px`,
              backgroundColor: isRecording
                ? `hsl(${120 - audioLevel * 120}, 70%, 50%)`
                : 'rgba(255,255,255,0.1)',
            }}
          />
        ))}
      </div>

      {/* Transcript Display */}
      {transcript && !isRecording && !isProcessing && (
        <div className="p-3 bg-surfaceRaised rounded-lg border border-border animate-slide-up">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-textMuted">Transcript</span>
            <span className="text-xs text-textMuted/60">
              {detectedLanguage?.toUpperCase() || 'EN'}
            </span>
          </div>
          <p className="text-white text-sm">{transcript}</p>
        </div>
      )}
    </div>
  )
}