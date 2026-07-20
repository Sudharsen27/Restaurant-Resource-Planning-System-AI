/**
 * Design tokens — single source for spacing, radius, motion, z-index.
 * Prefer Tailwind utilities in components; use these for JS-driven styles.
 */
export const tokens = {
  radius: {
    sm: '0.5rem',
    md: '0.75rem',
    lg: '1rem',
    xl: '1.25rem',
    '2xl': '1.5rem',
  },
  shadow: {
    card: '0 1px 2px rgb(0 0 0 / 0.04), 0 4px 16px rgb(0 0 0 / 0.04)',
    elevated: '0 8px 30px rgb(0 0 0 / 0.12)',
  },
  motion: {
    fast: '120ms',
    base: '200ms',
    slow: '320ms',
    ease: 'cubic-bezier(0.22, 1, 0.36, 1)',
  },
  z: {
    dropdown: 40,
    sidebar: 50,
    overlay: 55,
    modal: 60,
    toast: 70,
  },
  layout: {
    sidebarExpanded: 260,
    sidebarCollapsed: 72,
    navbar: 64,
  },
}

export const chartPalette = {
  primary: '#3b82f6',
  secondary: '#10b981',
  tertiary: '#f59e0b',
  danger: '#f43f5e',
  muted: '#71717a',
  grid: 'rgba(113, 113, 122, 0.15)',
}
