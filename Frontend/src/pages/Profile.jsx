import { useState } from 'react'
import { Link } from 'react-router-dom'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import { Input, Switch } from '../components/forms/FormControls'
import { useAuth } from '../context/AuthContext'
import { changePassword } from '../services/authService'
import { useToast } from '../context/ToastContext'

export default function Profile() {
  const { user, refreshProfile } = useAuth()
  const { success, error } = useToast()
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [displayName, setDisplayName] = useState(user?.full_name || '')
  const [phone, setPhone] = useState('')
  const [emailAlerts, setEmailAlerts] = useState(true)
  const [pushAlerts, setPushAlerts] = useState(true)
  const [loading, setLoading] = useState(false)

  async function onChangePassword(e) {
    e.preventDefault()
    setLoading(true)
    try {
      await changePassword(currentPassword, newPassword)
      await refreshProfile()
      setCurrentPassword('')
      setNewPassword('')
      success('Password changed successfully')
    } catch (err) {
      error(err.message || 'Could not change password')
    } finally {
      setLoading(false)
    }
  }

  function onSaveProfile(e) {
    e.preventDefault()
    // API-ready: wire to PATCH /auth/me when available
    success('Profile preferences saved locally (API pending)')
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-white">Profile</h1>
        <p className="text-sm text-slate-500">Overview, security, sessions, and notification preferences</p>
      </div>

      <Card title="Overview">
        <dl className="grid gap-3 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-slate-500">Name</dt>
            <dd className="font-medium text-slate-900 dark:text-white">{user?.full_name}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Email</dt>
            <dd className="font-medium text-slate-900 dark:text-white">{user?.email}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Role</dt>
            <dd className="font-medium text-slate-900 dark:text-white">{user?.role}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Email verified</dt>
            <dd className="font-medium text-slate-900 dark:text-white">
              {user?.email_verified ? 'Yes' : 'Pending'}
            </dd>
          </div>
        </dl>
      </Card>

      <Card title="Edit profile">
        <form onSubmit={onSaveProfile} className="grid gap-3 sm:grid-cols-2">
          <Input label="Display name" value={displayName} onChange={(e) => setDisplayName(e.target.value)} />
          <Input label="Phone" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+91…" />
          <div className="sm:col-span-2">
            <Button type="submit">Save profile</Button>
          </div>
        </form>
      </Card>

      <Card title="Security">
        <form onSubmit={onChangePassword} className="space-y-3">
          <Input
            type="password"
            label="Current password"
            required
            minLength={8}
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
          />
          <Input
            type="password"
            label="New password"
            required
            minLength={8}
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
          />
          <Button type="submit" disabled={loading}>
            {loading ? 'Updating…' : 'Update password'}
          </Button>
        </form>
        <p className="mt-4 text-sm">
          <Link to="/sessions" className="text-blue-600 hover:underline">
            Manage active sessions →
          </Link>
        </p>
      </Card>

      <Card title="Notification preferences">
        <div className="space-y-4">
          <Switch label="Email alerts" checked={emailAlerts} onChange={setEmailAlerts} />
          <Switch label="Push / in-app alerts" checked={pushAlerts} onChange={setPushAlerts} />
        </div>
      </Card>
    </div>
  )
}
