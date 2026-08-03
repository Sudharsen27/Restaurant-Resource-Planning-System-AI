/* global describe, it, expect */
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'
import AppModal from '../modals/AppModal'
import DataTable from '../tables/DataTable'
import { ThemeProvider } from '../../context/ThemeContext'

const login = vi.fn()

vi.mock('../../context/AuthContext', () => ({
  useAuth: () => ({ login, isAuthenticated: false, bootstrapping: false }),
}))

vi.mock('../../context/ToastContext', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn() }),
}))

describe('shared workflow components', () => {
  it('filters table rows through its accessible search field', () => {
    render(
      <DataTable
        columns={[{ key: 'name', label: 'Name' }]}
        rows={[
          { id: 1, name: 'Downtown' },
          { id: 2, name: 'Riverside' },
        ]}
      />,
    )

    fireEvent.change(screen.getByLabelText('Filter table rows'), { target: { value: 'river' } })

    expect(screen.getByText('Riverside')).toBeInTheDocument()
    expect(screen.queryByText('Downtown')).not.toBeInTheDocument()
  })

  it('moves focus into an open modal', async () => {
    render(
      <AppModal open title="Confirm order" onClose={vi.fn()} onConfirm={vi.fn()}>
        <input aria-label="Order note" />
      </AppModal>,
    )

    const dialog = screen.getByRole('dialog', { name: 'Confirm order' })
    expect(dialog).toBeInTheDocument()

    await waitFor(() => expect(dialog.contains(document.activeElement)).toBe(true))
  })
})

describe('login validation', () => {
  it('shows required-field messages without sending a login request', async () => {
    const { default: Login } = await import('../../pages/Login')
    login.mockClear()

    render(
      <ThemeProvider>
        <MemoryRouter>
          <Login />
        </MemoryRouter>
      </ThemeProvider>,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByText('Enter your email')).toBeInTheDocument()
    expect(screen.getByText('Enter your password')).toBeInTheDocument()
    expect(login).not.toHaveBeenCalled()
  })
})
