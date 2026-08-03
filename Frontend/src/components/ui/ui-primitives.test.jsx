/* global describe, it, expect */
import { fireEvent, render, screen } from '@testing-library/react'
import Button from './Button'
import EmptyState from './EmptyState'
import LoadingSpinner from './LoadingSpinner'
import { Input, Switch } from '../forms/FormControls'

describe('shared UI primitives', () => {
  it('renders an accessible primary action', () => {
    render(<Button>Save changes</Button>)

    expect(screen.getByRole('button', { name: 'Save changes' })).toHaveClass('bg-emerald-600')
  })

  it('connects an input label to its field', () => {
    render(<Input id="restaurant-name" label="Restaurant name" />)

    expect(screen.getByLabelText('Restaurant name')).toBeInTheDocument()
  })

  it('reports loading status to assistive technologies', () => {
    render(<LoadingSpinner label="Loading orders" />)

    expect(screen.getByRole('status')).toHaveTextContent('Loading orders')
  })

  it('toggles a switch with its control state', () => {
    let checked = false
    const onChange = (next) => {
      checked = next
    }
    const { rerender } = render(<Switch label="Auto refresh" checked={checked} onChange={onChange} />)

    fireEvent.click(screen.getByRole('switch', { name: 'Auto refresh' }))
    expect(checked).toBe(true)

    rerender(<Switch label="Auto refresh" checked={checked} onChange={onChange} />)
    expect(screen.getByRole('switch', { name: 'Auto refresh' })).toHaveAttribute('aria-checked', 'true')
  })

  it('exposes empty-state feedback as a live status', () => {
    render(<EmptyState title="No orders" description="Create an order to get started." />)

    expect(screen.getByRole('status')).toHaveTextContent('No orders')
  })
})
