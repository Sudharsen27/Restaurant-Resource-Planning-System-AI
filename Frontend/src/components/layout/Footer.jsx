export default function Footer() {
  return (
    <footer className="border-t border-stone-200 px-4 py-3 text-center text-xs text-stone-500 dark:border-white/10 dark:text-stone-500 lg:px-6">
      © {new Date().getFullYear()} RestoPlan · Restaurant operations workspace
    </footer>
  )
}
