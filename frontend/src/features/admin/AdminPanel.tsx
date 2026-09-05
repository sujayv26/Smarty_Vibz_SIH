import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui'
import { DataTable } from '../../components/ui/Table'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import { Select } from '../../components/ui/Select'
import { cn } from '../../lib/utils'
import { Users, Building2, Shield, Key, Plus } from 'lucide-react'
import { useState } from 'react'

const mockUsers = [
  { id: 1, email: 'admin@demo.com', name: 'System Admin', role: 'SYSTEM_ADMIN', org: 'Demo Construction Co.', status: 'Active' },
  { id: 2, email: 'contractor@demo.com', name: 'Contractor Admin', role: 'CONTRACTOR_ADMIN', org: 'Demo Construction Co.', status: 'Active' },
  { id: 3, email: 'controls@demo.com', name: 'Project Controls', role: 'PROJECT_CONTROLS', org: 'Demo Construction Co.', status: 'Active' },
  { id: 4, email: 'planner@demo.com', name: 'Discipline Planner', role: 'DISCIPLINE_PLANNER', org: 'Demo Construction Co.', status: 'Active' },
  { id: 5, email: 'supervisor@demo.com', name: 'Site Supervisor', role: 'SITE_SUPERVISOR', org: 'Demo Construction Co.', status: 'Active' },
]

const mockOrgs = [
  { id: 1, name: 'Demo Construction Co.', slug: 'demo', users: 5, projects: 2, status: 'Active' },
  { id: 2, name: 'Acme Infrastructure', slug: 'acme', users: 12, projects: 4, status: 'Active' },
  { id: 3, name: 'Global Builders Inc.', slug: 'global', users: 8, projects: 3, status: 'Active' },
]

const userColumns = [
  { key: 'name', header: 'Name', width: '180px' },
  { key: 'email', header: 'Email', width: '220px' },
  { key: 'role', header: 'Role', width: '180px' },
  { key: 'org', header: 'Organization', width: '200px' },
  { key: 'status', header: 'Status', width: '100px' },
  { key: 'actions', header: 'Actions', width: '120px' },
]

const orgColumns = [
  { key: 'name', header: 'Name', width: '200px' },
  { key: 'slug', header: 'Slug', width: '120px' },
  { key: 'users', header: 'Users', width: '80px' },
  { key: 'projects', header: 'Projects', width: '100px' },
  { key: 'status', header: 'Status', width: '100px' },
  { key: 'actions', header: 'Actions', width: '120px' },
]

export function AdminPanel() {
  const [activeTab, setActiveTab] = useState<'users' | 'organizations' | 'settings'>('users')
  const [showUserModal, setShowUserModal] = useState(false)
  const [editingUser, setEditingUser] = useState<any>(null)

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white">Administration</h1>
          <p className="text-textMuted mt-1">Manage users, organizations, and system settings</p>
        </div>
        {activeTab === 'users' && (
          <Button onClick={() => { setEditingUser(null); setShowUserModal(true); }}>
            <Plus className="w-4 h-4" />
            Add User
          </Button>
        )}
        {activeTab === 'organizations' && (
          <Button onClick={() => {}}>
            <Plus className="w-4 h-4" />
            Add Organization
          </Button>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border">
        {[
          { id: 'users', label: 'Users', icon: Users },
          { id: 'organizations', label: 'Organizations', icon: Building2 },
          { id: 'settings', label: 'System Settings', icon: Shield },
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

      {/* Users Tab */}
      {activeTab === 'users' && (
        <Card>
          <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <CardTitle>Users ({mockUsers.length})</CardTitle>
            <div className="flex items-center gap-2">
              <Input placeholder="Search users..." className="w-64" />
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <DataTable
              columns={userColumns}
              data={mockUsers}
              keyExtractor={(row) => String(row.id)}
              emptyMessage="No users found"
            />
          </CardContent>
        </Card>
      )}

      {/* Organizations Tab */}
      {activeTab === 'organizations' && (
        <Card>
          <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <CardTitle>Organizations ({mockOrgs.length})</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <DataTable
              columns={orgColumns}
              data={mockOrgs}
              keyExtractor={(row) => String(row.id)}
              emptyMessage="No organizations found"
            />
          </CardContent>
        </Card>
      )}

      {/* Settings Tab */}
      {activeTab === 'settings' && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Key className="w-5 h-5" />
                Security Settings
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input label="JWT Access Token Expiry (minutes)" value="15" />
                <Input label="JWT Refresh Token Expiry (days)" value="7" />
                <Input label="Max Login Attempts" value="5" />
                <Input label="Lockout Duration (minutes)" value="15" />
              </div>
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" className="w-4 h-4 rounded border-border bg-surfaceRaised text-white focus:ring-white" defaultChecked />
                  <span className="text-sm">Require 2FA for admin roles</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" className="w-4 h-4 rounded border-border bg-surfaceRaised text-white focus:ring-white" defaultChecked />
                  <span className="text-sm">Enforce password complexity</span>
                </label>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5" />
                CORS & API Settings
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Input label="Allowed Origins (comma-separated)" value="http://localhost:3000,http://localhost:5173" />
              <Input label="API Rate Limit (req/min)" value="1000" />
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" className="w-4 h-4 rounded border-border bg-surfaceRaised text-white focus:ring-white" defaultChecked />
                  <span className="text-sm">Enable API documentation (Swagger)</span>
                </label>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Building2 className="w-5 h-5" />
                Default Organization Settings
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Select
                  label="Default User Role"
                  options={[
                    { value: 'SITE_SUPERVISOR', label: 'Site Supervisor' },
                    { value: 'DISCIPLINE_PLANNER', label: 'Discipline Planner' },
                    { value: 'PROJECT_CONTROLS', label: 'Project Controls' },
                  ]}
                  placeholder="Select default role"
                />
                <Input label="Default Language" value="en" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* User Modal */}
      {showUserModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-md animate-scale-in">
            <CardHeader>
              <CardTitle>{editingUser ? 'Edit User' : 'Add User'}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Input label="Full Name" placeholder="John Doe" />
              <Input label="Email" type="email" placeholder="john@company.com" />
              <Input label="Password" type="password" placeholder="••••••••" />
              <Select
                label="Role"
                options={[
                  { value: 'SYSTEM_ADMIN', label: 'System Admin' },
                  { value: 'CONTRACTOR_ADMIN', label: 'Contractor Admin' },
                  { value: 'PROJECT_CONTROLS', label: 'Project Controls' },
                  { value: 'DISCIPLINE_PLANNER', label: 'Discipline Planner' },
                  { value: 'SITE_SUPERVISOR', label: 'Site Supervisor' },
                ]}
                placeholder="Select role"
              />
              <Select
                label="Organization"
                options={mockOrgs.map(o => ({ value: String(o.id), label: o.name }))}
                placeholder="Select organization"
              />
              <Select
                label="Discipline"
                options={[
                  { value: '', label: 'None' },
                  { value: 'Civil', label: 'Civil' },
                  { value: 'Piping', label: 'Piping' },
                  { value: 'Mechanical', label: 'Mechanical' },
                  { value: 'Electrical', label: 'Electrical' },
                ]}
                placeholder="Select discipline"
              />
              <div className="flex justify-end gap-3 pt-4">
                <Button variant="ghost" onClick={() => setShowUserModal(false)}>Cancel</Button>
                <Button onClick={() => setShowUserModal(false)}>Save</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}