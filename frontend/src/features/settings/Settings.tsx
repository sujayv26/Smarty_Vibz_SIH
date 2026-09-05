import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '../../components/ui'
import { Button } from '../../components/ui/Button'
import { Badge } from '../../components/ui/Badge'
import { Input } from '../../components/ui/Input'
import { Select } from '../../components/ui/Select'
import { cn } from '../../lib/utils'
import { User, Bell, Shield, Palette, Key, Save } from 'lucide-react'
import { useState } from 'react'
import { useAuth } from '../auth/AuthContext'

export function Settings() {
  const { user } = useAuth()
  const [isSaving, setIsSaving] = useState(false)
  const [activeTab, setActiveTab] = useState<'profile' | 'notifications' | 'security' | 'appearance'>('profile')

  const handleSave = async () => {
    setIsSaving(true)
    await new Promise(r => setTimeout(r, 1000))
    setIsSaving(false)
  }

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold text-white">Settings</h1>
        <p className="text-textMuted mt-1">Manage your account preferences and preferences</p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border">
        {[
          { id: 'profile', label: 'Profile', icon: User },
          { id: 'notifications', label: 'Notifications', icon: Bell },
          { id: 'security', label: 'Security', icon: Shield },
          { id: 'appearance', label: 'Appearance', icon: Palette },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={cn(
              'flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors',
              activeTab === tab.id
                ? 'border-white text-white'
                : 'border-transparent text-textMuted hover:text-white hover:border-white/20'
            )}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Profile Tab */}
      {activeTab === 'profile' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="w-5 h-5" />
              Profile Information
            </CardTitle>
            <CardDescription>Update your personal information</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center gap-6">
              <div className="w-20 h-20 rounded-full bg-white/10 flex items-center justify-center">
                <span className="text-2xl font-bold text-white">
                  {user?.full_name?.split(' ').map(n => n[0]).join('').toUpperCase() || 'U'}
                </span>
              </div>
              <div>
                <p className="text-lg font-medium text-white">{user?.full_name}</p>
                <p className="text-textMuted">{user?.email}</p>
                <Badge variant="neutral" className="mt-2 capitalize">{user?.role?.toLowerCase().replace('_', ' ')}</Badge>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input label="Full Name" value={user?.full_name || ''} />
              <Input label="Email" type="email" value={user?.email || ''} />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Select
                label="Preferred Language"
                options={[
                  { value: 'en', label: 'English' },
                  { value: 'hi', label: 'Hindi (हिंदी)' },
                  { value: 'ta', label: 'Tamil (தமிழ்)' },
                  { value: 'te', label: 'Telugu (తెలుగు)' },
                ]}
                placeholder="Select language"
              />
              <Select
                label="Timezone"
                options={[
                  { value: 'UTC', label: 'UTC' },
                  { value: 'IST', label: 'IST (UTC+5:30)' },
                  { value: 'PST', label: 'PST (UTC-8)' },
                  { value: 'EST', label: 'EST (UTC-5)' },
                ]}
                placeholder="Select timezone"
              />
            </div>
            <div className="flex justify-end">
              <Button onClick={handleSave} loading={isSaving}>
                <Save className="w-4 h-4" />
                Save Changes
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Notifications Tab */}
      {activeTab === 'notifications' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="w-5 h-5" />
              Notification Preferences
            </CardTitle>
            <CardDescription>Choose how you want to be notified</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {[
              { title: 'Email Notifications', description: 'Receive email updates for important events', enabled: true },
              { title: 'Push Notifications', description: 'Browser push notifications for real-time alerts', enabled: true },
              { title: 'Daily Summary', description: 'End-of-day summary of project activity', enabled: false },
              { title: 'Delay Alerts', description: 'Immediate notifications for critical path delays', enabled: true },
              { title: 'Review Assignments', description: 'When items are assigned to your review queue', enabled: true },
              { title: 'Weekly Reports', description: 'Weekly productivity and progress reports', enabled: false },
            ].map((item) => (
              <div key={item.title} className="flex items-center justify-between p-4 rounded-lg bg-surfaceRaised border border-border">
                <div>
                  <p className="font-medium text-white">{item.title}</p>
                  <p className="text-sm text-textMuted">{item.description}</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" defaultChecked={item.enabled} className="sr-only peer" />
                  <div className="w-11 h-6 bg-surface border border-border peer-focus:ring-2 peer-focus:ring-white rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-border after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-white"></div>
                </label>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Security Tab */}
      {activeTab === 'security' && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Key className="w-5 h-5" />
                Password
              </CardTitle>
              <CardDescription>Change your password</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input label="Current Password" type="password" placeholder="••••••••" />
                <Input label="New Password" type="password" placeholder="••••••••" />
              </div>
              <Input label="Confirm New Password" type="password" placeholder="••••••••" />
              <div className="flex justify-end">
                <Button onClick={handleSave} loading={isSaving}>
                  <Save className="w-4 h-4" />
                  Update Password
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5" />
                Two-Factor Authentication
              </CardTitle>
              <CardDescription>Add an extra layer of security to your account</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-4 rounded-lg bg-surfaceRaised border border-border">
                <div>
                  <p className="font-medium text-white">Authenticator App</p>
                  <p className="text-sm text-textMuted">Use Google Authenticator, Authy, or similar</p>
                </div>
                <Button variant="secondary">Enable 2FA</Button>
              </div>
              <div className="flex items-center justify-between p-4 rounded-lg bg-surfaceRaised border border-border">
                <div>
                  <p className="font-medium text-white">Backup Codes</p>
                  <p className="text-sm text-textMuted">Generate one-time backup codes</p>
                </div>
                <Button variant="ghost">Generate Codes</Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Active Sessions</CardTitle>
              <CardDescription>Manage your active login sessions</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="p-4 rounded-lg bg-surfaceRaised border border-border flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center">
                    <span className="text-sm font-medium text-white">CU</span>
                  </div>
                  <div>
                    <p className="font-medium text-white">Current Session</p>
                    <p className="text-sm text-textMuted">Chrome on macOS • Active now</p>
                  </div>
                </div>
                <Badge variant="auto-commit" dot>Current</Badge>
              </div>
              <div className="p-4 rounded-lg bg-surfaceRaised border border-border flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center">
                    <span className="text-sm font-medium text-white">MB</span>
                  </div>
                  <div>
                    <p className="font-medium text-white">Mobile Browser</p>
                    <p className="text-sm text-textMuted">Safari on iOS • 2 hours ago</p>
                  </div>
                </div>
                <Button variant="ghost" size="sm">Revoke</Button>
              </div>
              <Button variant="ghost" className="w-full">Revoke All Other Sessions</Button>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Appearance Tab */}
      {activeTab === 'appearance' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Palette className="w-5 h-5" />
              Appearance
            </CardTitle>
            <CardDescription>Customize how ConSight looks</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <p className="text-sm font-medium text-white mb-4">Theme</p>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { id: 'dark', label: 'Dark', icon: '🌙' },
                  { id: 'light', label: 'Light', icon: '☀️' },
                  { id: 'system', label: 'System', icon: '💻' },
                ].map((theme) => (
                  <button
                    key={theme.id}
                    className={cn(
                      'p-4 rounded-lg border-2 transition-all',
                      activeTab === theme.id
                        ? 'border-white bg-white/10'
                        : 'border-border hover:border-white/20'
                    )}
                  >
                    <span className="text-3xl block mb-2">{theme.icon}</span>
                    <span className="font-medium text-white">{theme.label}</span>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <p className="text-sm font-medium text-white mb-4">Density</p>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { id: 'comfortable', label: 'Comfortable' },
                  { id: 'compact', label: 'Compact' },
                  { id: 'condensed', label: 'Condensed' },
                ].map((density) => (
                  <button
                    key={density.id}
                    className={cn(
                      'p-4 rounded-lg border-2 transition-all',
                      activeTab === density.id
                        ? 'border-white bg-white/10'
                        : 'border-border hover:border-white/20'
                    )}
                  >
                    <span className="font-medium text-white">{density.label}</span>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <p className="text-sm font-medium text-white mb-4">Reduced Motion</p>
              <label className="flex items-center gap-3 cursor-pointer">
                <input type="checkbox" className="w-4 h-4 rounded border-border bg-surfaceRaised text-white focus:ring-white" />
                <span className="text-white">Reduce animations and transitions</span>
              </label>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}