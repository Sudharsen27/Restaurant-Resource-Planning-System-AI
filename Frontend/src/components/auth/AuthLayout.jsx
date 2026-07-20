import { BrandPanel, ThemeToggle } from './BrandPanel'

/**
 * Split-screen auth shell.
 * Mobile: compact brand + form. Tablet/desktop: branding | form.
 * Copyright sits with the form — no orphan dead space at the bottom.
 */
export default function AuthLayout({ children }) {
  return (
    <div className="auth-shell flex min-h-dvh flex-col bg-[#F7F8FA] dark:bg-black md:h-dvh md:flex-row md:overflow-hidden">
      <a
        href="#auth-main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-white focus:px-3 focus:py-2 focus:text-sm focus:font-medium focus:text-slate-900 focus:shadow-lg dark:focus:bg-zinc-900 dark:focus:text-white"
      >
        Skip to sign-in form
      </a>

      <div className="hidden md:contents">
        <BrandPanel />
      </div>
      <div className="md:hidden">
        <BrandPanel compact />
      </div>

      <main
        id="auth-main"
        className="relative flex min-h-0 flex-1 flex-col md:w-[54%] lg:w-[60%]"
      >
        <div className="absolute right-4 top-4 z-20 hidden md:block">
          <ThemeToggle />
        </div>

        <div className="flex flex-1 flex-col justify-center px-4 py-10 sm:px-8 sm:py-12 lg:px-14">
          <div className="relative z-10 mx-auto w-full max-w-[440px] auth-page-enter">
            {children}
            <p className="mt-8 text-center text-[11px] leading-none text-slate-400 dark:text-zinc-600">
              © {new Date().getFullYear()} RestoPlan · Encrypted sessions
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}
