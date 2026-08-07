/** Load Google Identity Services and request an ID token via One Tap / button flow. */

const GIS_SCRIPT_SRC = 'https://accounts.google.com/gsi/client'

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

/**
 * Opens Google's account chooser and resolves with a verified ID token string.
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
    const finish = (error, token) => {
      if (settled) return
      settled = true
      if (error) reject(error)
      else resolve(token)
    }

    google.accounts.id.initialize({
      client_id: clientId,
      callback: (response) => {
        if (!response?.credential) {
          finish(new Error('Google did not return an identity token'))
          return
        }
        finish(null, response.credential)
      },
      cancel_on_tap_outside: true,
      auto_select: false,
      use_fedcm_for_prompt: true,
    })

    google.accounts.id.prompt((notification) => {
      if (settled) return
      if (notification?.isNotDisplayed?.() || notification?.isSkippedMoment?.()) {
        // Fallback: open the official Google button popup via renderButton + click
        const host = document.createElement('div')
        host.style.position = 'fixed'
        host.style.left = '-9999px'
        document.body.appendChild(host)
        google.accounts.id.renderButton(host, {
          type: 'standard',
          theme: 'outline',
          size: 'large',
          text: 'continue_with',
          shape: 'rectangular',
          width: 320,
        })
        const button = host.querySelector('div[role="button"]')
        if (button) {
          button.click()
          window.setTimeout(() => host.remove(), 2000)
          return
        }
        host.remove()
        finish(new Error('Google sign-in was blocked by the browser. Allow third-party sign-in and try again.'))
      }
    })
  })
}
