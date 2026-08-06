/* global describe, it, expect, beforeEach */
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import { AuthProvider, useAuth } from './AuthContext'
import * as authService from '../services/authService'

vi.mock('../services/authService', () => ({
  fetchMe: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
}))

const user = { id: 'user-1', name: 'Asha', role: 'ADMIN' }

function AuthProbe() {
  const { bootstrapping, isAuthenticated, logout } = useAuth()

  return (
    <>
      <output aria-label="bootstrap-state">{bootstrapping ? 'loading' : 'ready'}</output>
      <output aria-label="authentication-state">{isAuthenticated ? 'authenticated' : 'logged-out'}</output>
      <button type="button" onClick={() => void logout().catch(() => {})}>
        Log out
      </button>
    </>
  )
}

function renderAuth() {
  return render(
    <AuthProvider>
      <AuthProbe />
    </AuthProvider>,
  )
}

function storeSession({ accessToken, storedUser } = {}) {
  if (accessToken) localStorage.setItem('rrps_access_token', accessToken)
  if (storedUser) localStorage.setItem('rrps_user', JSON.stringify(storedUser))
}

async function waitForBootstrap() {
  await waitFor(() => expect(screen.getByLabelText('bootstrap-state')).toHaveTextContent('ready'))
}

describe('AuthContext session validation', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
    authService.fetchMe.mockResolvedValue(user)
  })

  it('authenticates when both a user and access token are stored', async () => {
    storeSession({ accessToken: 'access-token', storedUser: user })

    renderAuth()
    await waitForBootstrap()

    expect(screen.getByLabelText('authentication-state')).toHaveTextContent('authenticated')
    expect(authService.fetchMe).toHaveBeenCalledOnce()
  })

  it('logs out a stored user when no access token exists', async () => {
    storeSession({ storedUser: user })

    renderAuth()
    await waitForBootstrap()

    expect(screen.getByLabelText('authentication-state')).toHaveTextContent('logged-out')
    expect(localStorage.getItem('rrps_user')).toBeNull()
  })

  it('logs out when an access token exists without a stored user', async () => {
    storeSession({ accessToken: 'access-token' })

    renderAuth()
    await waitForBootstrap()

    expect(screen.getByLabelText('authentication-state')).toHaveTextContent('logged-out')
    expect(localStorage.getItem('rrps_access_token')).toBeNull()
  })

  it('clears the in-memory user when the logout API fails', async () => {
    storeSession({ accessToken: 'access-token', storedUser: user })
    authService.logout.mockRejectedValue(new Error('Network unavailable'))

    renderAuth()
    await waitForBootstrap()
    fireEvent.click(screen.getByRole('button', { name: 'Log out' }))

    await waitFor(() =>
      expect(screen.getByLabelText('authentication-state')).toHaveTextContent('logged-out'),
    )
  })

  it('clears persisted authentication data during bootstrap without a token', async () => {
    storeSession({ storedUser: user })

    renderAuth()
    await waitForBootstrap()

    expect(localStorage.getItem('rrps_access_token')).toBeNull()
    expect(localStorage.getItem('rrps_refresh_token')).toBeNull()
    expect(localStorage.getItem('rrps_user')).toBeNull()
  })
})
