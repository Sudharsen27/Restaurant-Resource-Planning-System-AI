import { useState } from 'react'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import { useAuth } from '../context/AuthContext'
import { changePassword } from '../services/authService'
import { useToast } from '../context/ToastContext'

export default function Profile() {
  const { user, refreshProfile } = useAuth()
  const { success, error } = useToast()
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
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

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-white">Profile</h1>
        <p className="text-sm text-slate-500">Account details and password management</p>
      </div>

      <Card title="Account">
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

      <Card title="Change password">
        <form onSubmit={onChangePassword} className="space-y-3">
          <input
            type="password"
            required
            minLength={8}
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            placeholder="Current password"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-950 dark:text-white"
          />
          <input
            type="password"
            required
            minLength={8}
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder="New password"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-950 dark:text-white"
          />
          <Button type="submit" disabled={loading}>
            {loading ? 'Updating…' : 'Update password'}
          </Button>
        </form>
      </Card>
    </div>
  )
}
