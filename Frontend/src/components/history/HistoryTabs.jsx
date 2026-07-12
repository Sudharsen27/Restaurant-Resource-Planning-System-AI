import { HISTORY_TABS } from '../../utils/predictionHistory'

export default function HistoryTabs({ activeTab, onChange, counts }) {
  return (
    <div
      className="flex flex-wrap gap-2 border-b border-slate-200 pb-1 dark:border-slate-700"
      role="tablist"
      aria-label="History sections"
    >
      {HISTORY_TABS.map((tab) => {
        const active = activeTab === tab.id
        const count = counts?.[tab.id]
        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={active}
            aria-controls={`history-panel-${tab.id}`}
            id={`history-tab-${tab.id}`}
            onClick={() => onChange(tab.id)}
            className={`rounded-t-lg px-4 py-2.5 text-sm font-medium transition ${
              active
                ? 'border-b-2 border-indigo-600 text-indigo-600 dark:border-indigo-400 dark:text-indigo-400'
                : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
            }`}
          >
            {tab.label}
            {count != null && (
              <span
                className={`ml-2 rounded-full px-2 py-0.5 text-xs ${
                  active
                    ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-300'
                    : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'
                }`}
              >
                {count}
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}
