import { useState, useRef, useCallback } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { Skeleton } from '../components/ui/Skeleton'
import { FileText, Upload, Loader2, X, RefreshCw, Eye } from 'lucide-react'
import { cn } from '../lib/utils'
import { api } from '../lib/api'

interface DiaryUploadProps {
  sessionId?: string
  onDiaryProcessed?: (result: any) => void
  className?: string
}

interface OCRResult {
  filename: string
  text: string
  language: string
  confidence: number
  pages: number
  words?: any[]
}

export function DiaryUpload({
  sessionId = "default",
  onDiaryProcessed,
  className = '',
}: DiaryUploadProps) {
  const [isUploading, setIsUploading] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [ocrResult, setOcrResult] = useState<OCRResult | null>(null)
  const [agentResponse, setAgentResponse] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [preferredLanguage, setPreferredLanguage] = useState('eng')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const languages = [
    { code: 'eng', name: 'English' },
    { code: 'hin', name: 'Hindi' },
    { code: 'tam', name: 'Tamil' },
    { code: 'tel', name: 'Telugu' },
    { code: 'kan', name: 'Kannada' },
  ]

  const handleFileSelect = useCallback(async (file: File) => {
    setError(null)
    setOcrResult(null)
    setAgentResponse(null)
    setIsUploading(true)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('language', preferredLanguage)
    formData.append('session_id', sessionId)

    try {
      const response = await api.post('/ocr/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      
      setOcrResult(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload and OCR file')
    } finally {
      setIsUploading(false)
    }
  }, [preferredLanguage, sessionId])

  const handleProcess = useCallback(async () => {
    if (!ocrResult) return
    
    setIsProcessing(true)
    setError(null)

    try {
      const response = await api.post('/agent/chat', {
        message: ocrResult.text,
        session_id: sessionId,
      })
      
      setAgentResponse(response.data)
      onDiaryProcessed?.(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to process diary through agent')
    } finally {
      setIsProcessing(false)
    }
  }, [ocrResult, sessionId])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      handleFileSelect(file)
    }
  }

  const clearResult = () => {
    setOcrResult(null)
    setAgentResponse(null)
    setError(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const formatConfidence = (conf: number) => {
    return `${(conf * 100).toFixed(1)}%`
  }

  const getConfidenceColor = (conf: number) => {
    if (conf >= 0.8) return 'text-green-400'
    if (conf >= 0.6) return 'text-amber-400'
    return 'text-red-400'
  }

  if (isUploading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Upload Scanned Diary
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4 space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex gap-4 px-4 py-3">
              <Skeleton className="w-24 h-4" />
              <Skeleton className="flex-1 h-4" />
              <Skeleton className="w-24 h-4" />
            </div>
          ))}
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="w-5 h-5" />
          Upload Scanned Diary
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Upload Zone */}
        {!ocrResult && (
          <div className="border-2 border-dashed border-border/50 rounded-lg p-8 text-center hover:border-white/50 transition-colors">
            <Upload className="w-12 h-12 text-textMuted/50 mx-auto mb-4" />
            <p className="text-lg text-textMuted mb-2">Drop scanned diary (PDF/Image) here</p>
            <p className="text-sm text-textMuted/60 mb-4">
              Supported: PDF, PNG, JPG, TIFF, BMP, WebP • Max 50MB
            </p>
            <div className="flex items-center justify-center gap-4">
              <select
                value={preferredLanguage}
                onChange={(e) => setPreferredLanguage(e.target.value)}
                className="bg-surfaceRaised border border-border rounded-lg px-3 py-2 text-sm text-white"
              >
                {languages.map((lang) => (
                  <option key={lang.code} value={lang.code}>
                    {lang.name} ({lang.code})
                  </option>
                ))}
              </select>
              <Button
                variant="secondary"
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
              >
                <Upload className="w-4 h-4" />
                Browse Files
              </Button>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.png,.jpg,.jpeg,.tiff,.tif,.bmp,.webp"
              onChange={handleFileChange}
              className="hidden"
            />
          </div>
        )}

        {/* OCR Result Preview */}
        {ocrResult && (
          <div className="space-y-4 animate-slide-up">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-green-400" />
                <span className="font-medium text-white">{ocrResult.filename}</span>
                <Badge variant="auto-commit" dot>{ocrResult.pages} page(s)</Badge>
              </div>
              <div className="flex items-center gap-2">
                <span className={cn('font-mono', getConfidenceColor(ocrResult.confidence))}>
                  Confidence: {formatConfidence(ocrResult.confidence)}
                </span>
                <Badge variant="review">{ocrResult.language.toUpperCase()}</Badge>
              </div>
            </div>

            <div className="p-4 bg-surfaceRaised rounded-lg border border-border max-h-60 overflow-auto">
              <pre className="text-sm text-white whitespace-pre-wrap font-mono leading-relaxed">
                {ocrResult.text}
              </pre>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-3">
              <Button
                onClick={handleProcess}
                disabled={isProcessing || isUploading}
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <RefreshCw className="w-4 h-4" />
                    Process & Match
                  </>
                )}
              </Button>
              <Button variant="ghost" onClick={clearResult}>
                <X className="w-4 h-4" />
                Clear
              </Button>
              {agentResponse && (
                <Button variant="ghost" onClick={() => {}}>
                  <Eye className="w-4 h-4" />
                  View Match
                </Button>
              )}
            </div>

            {/* Agent Response Preview */}
            {agentResponse && (
              <div className="p-4 bg-surfaceRaised rounded-lg border border-border animate-slide-up">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-textMuted">Agent Response</span>
                  <Badge variant="auto-commit">Matched</Badge>
                </div>
                <p className="text-white text-sm">{agentResponse.reply}</p>
                {agentResponse.matched_activity && (
                  <div className="mt-2 p-2 bg-green-500/10 border border-green-500/30 rounded-lg">
                    <p className="text-xs font-medium text-green-400 mb-1">Matched Activity</p>
                    <p className="text-xs text-white">
                      {agentResponse.matched_activity.activity_code}: {agentResponse.matched_activity.activity_name}
                    </p>
                    <p className="text-xs text-textMuted">
                      {agentResponse.matched_activity.discipline} • {(agentResponse.confidence || 0) * 100}% confidence
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
            <div className="flex items-center gap-2 text-red-400">
              <X className="w-5 h-5" />
              <span>{error}</span>
            </div>
          </div>
        )}

        {ocrResult && !agentResponse && (
          <p className="text-xs text-textMuted/60 text-center">
            Review the extracted text above, then click "Process & Match" to run through the Time Agent pipeline
          </p>
        )}
      </CardContent>
    </Card>
  )
}