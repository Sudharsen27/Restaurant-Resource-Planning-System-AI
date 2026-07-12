import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { useTheme } from '../../context/ThemeContext'
import { getChartTheme } from '../../utils/format'

export default function FeatureImportanceVisual({ data, modelName }) {
  const { darkMode } = useTheme()
  const theme = getChartTheme(darkMode)

  if (!data?.length) {
    return (
      <div className="flex h-64 items-center justify-center rounded-xl border border-dashed border-slate-300 dark:border-slate-700">
        <p className="text-sm text-slate-500">No model metrics available</p>
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50/50 p-4 dark:border-slate-700 dark:bg-slate-900/50">
      {modelName && (
        <p className="mb-3 text-center text-xs text-slate-500">{modelName}</p>
      )}
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} layout="vertical" margin={{ left: 8, right: 24, top: 8, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={theme.grid} horizontal={false} />
          <XAxis
            type="number"
            tick={{ fill: theme.text, fontSize: 11 }}
            domain={[0, 100]}
            tickFormatter={(v) => `${v}%`}
          />
          <YAxis
            type="category"
            dataKey="feature"
            width={110}
            tick={{ fill: theme.text, fontSize: 11 }}
          />
          <Tooltip
            formatter={(value) => [`${Number(value).toFixed(2)}%`, 'Score']}
            contentStyle={{
              background: darkMode ? '#1e293b' : '#fff',
              border: `1px solid ${theme.grid}`,
              borderRadius: 8,
            }}
          />
          <Bar dataKey="importance" name="Importance" radius={[0, 4, 4, 0]}>
            {data.map((entry) => (
              <Cell key={entry.feature} fill={entry.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
