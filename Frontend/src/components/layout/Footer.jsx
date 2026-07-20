export default function Footer() {
  return (
    <footer className="border-t border-slate-200 px-4 py-3 text-center text-xs text-slate-500 dark:border-zinc-800 dark:text-zinc-500 lg:px-6">
      © {new Date().getFullYear()} Restaurant Resource Planning System · Enterprise ERP UI
    </footer>
  )
}
