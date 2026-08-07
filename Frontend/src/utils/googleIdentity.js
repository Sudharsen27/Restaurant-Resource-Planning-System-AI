/** Google Identity Services — reliable Continue-with-Google via official button. */

const GIS_SCRIPT_SRC = 'https://accounts.google.com/gsi/client'
const GOOGLE_SIGNIN_TIMEOUT_MS = 90_000

let scriptPromise = null

function loadGoogleScript() {
  if (typeof window === 'undefined') {
    return Promise.reject(new Error('Google sign-in is only available in the browser'))
  }
  if (window.google?.accounts?.id) {
    return Promise.resolve(window.google)
  }
  if (scriptPromise) return scriptPromise

  scriptPromise = new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[src="${GIS_SCRIPT_SRC}"]`)
    if (existing) {
      existing.addEventListener('load', () => resolve(window.google))
      existing.addEventListener('error', () => reject(new Error('Failed to load Google Identity Services')))
      return
    }

    const script = document.createElement('script')
    script.src = GIS_SCRIPT_SRC
    script.async = true
    script.defer = true
    script.onload = () => resolve(window.google)
    script.onerror = () => {
      scriptPromise = null
      reject(new Error('Failed to load Google Identity Services'))
    }
    document.head.appendChild(script)
  })

  return scriptPromise
}

function createGoogleChooserOverlay() {
  const overlay = document.createElement('div')
  overlay.setAttribute('role', 'dialog')
  overlay.setAttribute('aria-modal', 'true')
  overlay.setAttribute('aria-label', 'Continue with Google')
  overlay.style.cssText = [
    'position:fixed',
    'inset:0',
    'z-index:99999',
    'display:flex',
    'align-items:center',
    'justify-content:center',
    'background:rgba(15,23,42,0.55)',
    'padding:16px',
  ].join(';')

  const panel = document.createElement('div')
  panel.style.cssText = [
    'width:min(100%,360px)',
    'border-radius:16px',
    'background:#fff',
    'padding:24px',
    'box-shadow:0 20px 45px rgba(0,0,0,0.25)',
    'font-family:system-ui,sans-serif',
  ].join(';')

  const title = document.createElement('h2')
  title.textContent = 'Continue with Google'
  title.style.cssText = 'margin:0 0 8px;font-size:18px;font-weight:700;color:#0f172a;'

  const help = document.createElement('p')
  help.textContent = 'Choose your Google account to sign in securely.'
  help.style.cssText = 'margin:0 0 20px;font-size:14px;line-height:1.45;color:#64748b;'

  const buttonHost = document.createElement('div')
  buttonHost.style.cssText = 'display:flex;justify-content:center;min-height:44px;'

  const cancel = document.createElement('button')
  cancel.type = 'button'
  cancel.textContent = 'Cancel'
  cancel.style.cssText = [
    'margin-top:16px',
    'width:100%',
    'height:40px',
    'border-radius:10px',
    'border:1px solid #cbd5e1',
    'background:#fff',
    'color:#334155',
    'font-size:14px',
    'font-weight:600',
    'cursor:pointer',
  ].join(';')

  panel.append(title, help, buttonHost, cancel)
  overlay.appendChild(panel)
  document.body.appendChild(overlay)

  return { overlay, buttonHost, cancel }
}

/**
 * Shows Google's official sign-in button and resolves with an ID token.
 * Avoids FedCM One Tap skipped_moment hangs from programmatic prompt().
 */
export async function requestGoogleIdToken(clientId) {
  if (!clientId) {
    throw new Error('Google sign-in is not configured')
  }

  const google = await loadGoogleScript()
  if (!google?.accounts?.id) {
    throw new Error('Google Identity Services is unavailable')
  }

  return new Promise((resolve, reject) => {
    let settled = false
    const { overlay, buttonHost, cancel } = createGoogleChooserOverlay()

    const cleanup = () => {
      overlay.remove()
      window.clearTimeout(timeoutId)
      document.removeEventListener('keydown', onKeyDown)
    }

    const finish = (error, token) => {
      if (settled) return
      settled = true
      cleanup()
      if (error) reject(error)
      else resolve(token)
    }

    const onKeyDown = (event) => {
      if (event.key === 'Escape') {
        finish(new Error('Google sign-in was cancelled'))
      }
    }

    const timeoutId = window.setTimeout(() => {
      finish(new Error('Google sign-in timed out. Please try again.'))
    }, GOOGLE_SIGNIN_TIMEOUT_MS)

    cancel.addEventListener('click', () => {
      finish(new Error('Google sign-in was cancelled'))
    })
    document.addEventListener('keydown', onKeyDown)

    google.accounts.id.initialize({
      client_id: clientId,
      callback: (response) => {
        if (!response?.credential) {
          finish(new Error('Google did not return an identity token'))
          return
        }
        finish(null, response.credential)
      },
      // One Tap/FedCM prompt is unreliable for custom buttons; use the official button instead.
      auto_select: false,
      cancel_on_tap_outside: true,
      use_fedcm_for_prompt: false,
    })

    google.accounts.id.renderButton(buttonHost, {
      type: 'standard',
      theme: 'outline',
      size: 'large',
      text: 'continue_with',
      shape: 'rectangular',
      logo_alignment: 'left',
      width: 320,
    })
  })
}
