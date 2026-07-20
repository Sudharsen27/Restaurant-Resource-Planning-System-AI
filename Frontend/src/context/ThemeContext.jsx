import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'

const ThemeContext = createContext(null)
const STORAGE_KEY = 'rrps-theme' // 'light' | 'dark' | 'system'

function getSystemDark() {
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

function resolveDark(preference) {
  if (preference === 'system') return getSystemDark()
  return preference === 'dark'
}

export function ThemeProvider({ children }) {
  const [preference, setPreference] = useState(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved === 'light' || saved === 'dark' || saved === 'system') return saved
    // migrate legacy boolean storage
    if (saved === 'true') return 'dark'
    if (saved === 'false') return 'light'
    return 'system'
  })

  const [darkMode, setDarkMode] = useState(() => resolveDark(preference))

  useEffect(() => {
    const apply = () => {
      const isDark = resolveDark(preference)
      setDarkMode(isDark)
      document.documentElement.classList.toggle('dark', isDark)
      localStorage.setItem(STORAGE_KEY, preference)
    }
    apply()

    if (preference !== 'system') return undefined
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const onChange = () => apply()
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [preference])

  const toggleTheme = useCallback(() => {
    setPreference((prev) => {
      const currentDark = resolveDark(prev)
      return currentDark ? 'light' : 'dark'
    })
  }, [])

  const setTheme = useCallback((value) => {
    if (value === 'light' || value === 'dark' || value === 'system') {
      setPreference(value)
    }
  }, [])

  const value = useMemo(
    () => ({
      darkMode,
      preference,
      theme: preference,
      toggleTheme,
      setTheme,
      setDarkMode: (v) => setPreference(v ? 'dark' : 'light'),
    }),
    [darkMode, preference, toggleTheme, setTheme],
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider')
  return ctx
}
