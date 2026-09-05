import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui'
import { Button } from '../../components/ui/Button'
import { Badge } from '../../components/ui/Badge'
import { Upload, RotateCcw, ZoomIn, ZoomOut, Maximize, Layers, Box } from 'lucide-react'

export function BIMViewer() {
  return (
    <div className="space-y-6 animate-fade-in h-[calc(100vh-120px)]">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white">BIM / Digital Twin Viewer</h1>
          <p className="text-textMuted mt-1">3D model with progress visualization</p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="neutral">IFC Model: DEMO-001.ifc</Badge>
          <Button variant="secondary" size="sm">
            <Upload className="w-4 h-4" />
            Upload IFC
          </Button>
        </div>
      </div>

      {/* Viewer Area */}
      <div className="flex-1 flex flex-col min-h-0">
        <Card className="flex-1 flex flex-col min-h-0 p-0">
          <CardHeader className="flex flex-row items-center justify-between p-4 border-b border-border">
            <CardTitle className="flex items-center gap-2">
              <Box className="w-5 h-5" />
              3D Viewport
            </CardTitle>
            <div className="flex items-center gap-2">
              <Badge variant="auto-commit" dot>Live Progress Sync</Badge>
              <Button variant="ghost" size="sm">
                <Maximize className="w-4 h-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="flex-1 p-0 relative">
            {/* Placeholder for 3D viewer - would integrate with three.js / IFC.js */}
            <div className="w-full h-full bg-surfaceRaised flex items-center justify-center relative">
              <div className="text-center">
                <Box className="w-16 h-16 text-textMuted/50 mx-auto mb-4" />
                <p className="text-lg text-textMuted mb-2">3D BIM Viewer</p>
                <p className="text-sm text-textMuted/60 mb-6">
                  Integration with IFC.js / three.js would go here.<br />
                  Model elements colored by actual progress status from WBS nodes.
                </p>
                <div className="flex items-center justify-center gap-4 text-sm text-textMuted">
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded bg-green-400" />
                    <span>Complete</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded bg-amber-400" />
                    <span>In Progress</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded bg-textMuted/30" />
                    <span>Not Started</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded bg-red-400" />
                    <span>Delayed</span>
                  </div>
                </div>
              </div>

              {/* Viewer Controls Overlay */}
              <div className="absolute bottom-4 right-4 flex flex-col gap-2">
                <Button variant="secondary" size="sm" className="w-10 h-10 p-0">
                  <ZoomIn className="w-5 h-5" />
                </Button>
                <Button variant="secondary" size="sm" className="w-10 h-10 p-0">
                  <ZoomOut className="w-5 h-5" />
                </Button>
                <Button variant="secondary" size="sm" className="w-10 h-10 p-0">
                  <RotateCcw className="w-5 h-5" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Progress Legend / Model Tree */}
        <Card className="mt-4">
          <CardHeader className="flex flex-row items-center justify-between p-4 border-b border-border">
            <CardTitle className="flex items-center gap-2">
              <Layers className="w-5 h-5" />
              Model Tree / Progress
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {[
                { name: 'Piping Systems', complete: 65, inProgress: 20, notStarted: 15, delayed: 0 },
                { name: 'Civil Works', complete: 45, inProgress: 30, notStarted: 20, delayed: 5 },
                { name: 'Mechanical', complete: 30, inProgress: 40, notStarted: 25, delayed: 5 },
                { name: 'Electrical', complete: 55, inProgress: 25, notStarted: 20, delayed: 0 },
              ].map((item) => (
                <div key={item.name} className="p-4 rounded-lg bg-surfaceRaised border border-border">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-medium text-white">{item.name}</h4>
                    <Badge variant="neutral" className="text-xs">{item.complete + item.inProgress + item.notStarted + item.delayed} elements</Badge>
                  </div>
                  <div className="h-2 bg-surface rounded-full overflow-hidden mb-2">
                    <div
                      className="h-full bg-green-400 rounded-full"
                      style={{ width: `${item.complete}%` }}
                    />
                    <div
                      className="h-full bg-amber-400 rounded-full"
                      style={{ width: `${item.inProgress}%` }}
                    />
                    <div
                      className="h-full bg-textMuted/30 rounded-full"
                      style={{ width: `${item.notStarted}%` }}
                    />
                    {item.delayed > 0 && (
                      <div
                        className="h-full bg-red-400 rounded-full"
                        style={{ width: `${item.delayed}%` }}
                      />
                    )}
                  </div>
                  <div className="flex items-center justify-between text-xs text-textMuted">
                    <span className="text-green-400">Complete: {item.complete}%</span>
                    <span className="text-amber-400">In Progress: {item.inProgress}%</span>
                    <span>Not Started: {item.notStarted}%</span>
                    {item.delayed > 0 && <span className="text-red-400">Delayed: {item.delayed}%</span>}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}