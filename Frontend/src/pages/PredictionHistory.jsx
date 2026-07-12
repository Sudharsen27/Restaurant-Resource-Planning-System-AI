import { useMemo, useState } from 'react'
import { Loader2, RefreshCw } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import Card from '../components/ui/Card'
import EmptyState from '../components/ui/EmptyState'
import PredictionHistoryHeader from '../components/history/PredictionHistoryHeader'
import HistoryTabs from '../components/history/HistoryTabs'
import HistoryToolbar from '../components/history/HistoryToolbar'
import HistoryPagination from '../components/history/HistoryPagination'
import ForecastHistoryTable from '../components/history/ForecastHistoryTable'
import FeedbackHistoryTable from '../components/history/FeedbackHistoryTable'
import ModelHistoryTable from '../components/history/ModelHistoryTable'
import HistoryErrorCard from '../components/history/HistoryErrorCard'
import { useToast } from '../context/ToastContext'
import {
  fetchPredictionHistoryData,
  PREDICTION_HISTORY_QUERY_KEY,
} from '../services/historyPageService'
import {
  buildFeedbackHistoryRows,
  buildForecastHistoryRows,
  buildModelHistoryRows,
  downloadCsv,
  feedbackHistoryToCsv,
  filterRows,
  forecastHistoryToCsv,
  modelHistoryToCsv,
  PAGE_SIZE_OPTIONS,
  paginateRows,
  sortRows,
} from '../utils/predictionHistory'

const TAB_CONFIG = {
  forecast: {
    defaultSort: 'createdAt',
    dateField: 'forecastDate',
    searchFields: [
      'predictionId',
      'forecastDate',
      'modelVersion',
      'predictedCustomers',
      'status',
    ],
    emptyTitle: 'No forecast history',
    emptyDescription: 'Generate forecasts to see prediction records here.',
    exportName: 'forecast-history.csv',
    toCsv: forecastHistoryToCsv,
  },
  feedback: {
    defaultSort: 'createdAt',
    dateField: 'createdAt',
    searchFields: ['predictionId', 'predicted', 'actual', 'comments'],
    emptyTitle: 'No feedback history',
    emptyDescription: 'Submit manager feedback to populate this tab.',
    exportName: 'feedback-history.csv',
    toCsv: feedbackHistoryToCsv,
  },
  model: {
    defaultSort: 'trainingDate',
    dateField: 'trainingDate',
    searchFields: ['version'],
    emptyTitle: 'No model history',
    emptyDescription: 'Model versions will appear after predictions are recorded.',
    exportName: 'model-history.csv',
    toCsv: modelHistoryToCsv,
  },
}

export default function PredictionHistory() {
  const toast = useToast()
  const [activeTab, setActiveTab] = useState('forecast')
  const [page, setPage] = useState(0)
  const [pageSize, setPageSize] = useState(PAGE_SIZE_OPTIONS[0])
  const [search, setSearch] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [sortKey, setSortKey] = useState(TAB_CONFIG.forecast.defaultSort)
  const [sortDir, setSortDir] = useState('desc')

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: PREDICTION_HISTORY_QUERY_KEY,
    queryFn: fetchPredictionHistoryData,
    staleTime: 30_000,
    retry: 1,
  })

  const forecastRows = useMemo(
    () => buildForecastHistoryRows(data?.feedbackHistory, data?.latestForecast),
    [data],
  )
  const feedbackRows = useMemo(
    () => buildFeedbackHistoryRows(data?.feedbackHistory),
    [data],
  )
  const modelRows = useMemo(
    () => buildModelHistoryRows(data?.feedbackHistory, data?.latestDashboard, data?.latestForecast),
    [data],
  )

  const tabRows = useMemo(() => {
    if (activeTab === 'feedback') return feedbackRows
    if (activeTab === 'model') return modelRows
    return forecastRows
  }, [activeTab, forecastRows, feedbackRows, modelRows])

  const config = TAB_CONFIG[activeTab]

  const processed = useMemo(() => {
    const filtered = filterRows(tabRows, {
      search,
      dateFrom,
      dateTo,
      searchFields: config.searchFields,
      dateField: config.dateField,
    })
    return sortRows(filtered, sortKey, sortDir)
  }, [tabRows, search, dateFrom, dateTo, sortKey, sortDir, config])

  const pagination = useMemo(
    () => paginateRows(processed, page, pageSize),
    [processed, page, pageSize],
  )

  const handleTabChange = (tab) => {
    setActiveTab(tab)
    setPage(0)
    setSortKey(TAB_CONFIG[tab].defaultSort)
    setSortDir('desc')
    setSearch('')
    setDateFrom('')
    setDateTo('')
  }

  const handleSort = (field) => {
    if (sortKey === field) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(field)
      setSortDir('desc')
    }
  }

  const handleExport = () => {
    if (!processed.length) {
      toast.error('No records to export')
      return
    }
    downloadCsv(config.exportName, config.toCsv(processed))
    toast.success('CSV exported')
  }

  const counts = {
    forecast: forecastRows.length,
    feedback: feedbackRows.length,
    model: modelRows.length,
  }

  if (isLoading) {
    return (
      <div className="space-y-8">
        <PredictionHistoryHeader />
        <div className="flex min-h-[320px] items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
        </div>
      </div>
    )
  }

  if (isError && !data?.feedbackHistory?.length) {
    return (
      <div className="space-y-8">
        <PredictionHistoryHeader />
        <HistoryErrorCard
          title="Unable to load prediction history"
          message={error?.message || 'Could not reach the history APIs.'}
          onRetry={() => refetch()}
        />
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <PredictionHistoryHeader />
        <button
          type="button"
          onClick={() => refetch()}
          disabled={isFetching}
          className="flex shrink-0 items-center gap-2 self-start rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900"
        >
          <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {data?.errors?.length > 0 && (
        <HistoryErrorCard
          title="Partial data loaded"
          message={Array.isArray(data.errors) ? data.errors.join(' · ') : String(data.errors)}
          onRetry={() => refetch()}
        />
      )}

      <Card>
        <HistoryTabs activeTab={activeTab} onChange={handleTabChange} counts={counts} />

        <div className="mt-4" role="tabpanel" id={`history-panel-${activeTab}`} aria-labelledby={`history-tab-${activeTab}`}>
          <HistoryToolbar
            search={search}
            onSearchChange={(v) => {
              setSearch(v)
              setPage(0)
            }}
            dateFrom={dateFrom}
            onDateFromChange={(v) => {
              setDateFrom(v)
              setPage(0)
            }}
            dateTo={dateTo}
            onDateToChange={(v) => {
              setDateTo(v)
              setPage(0)
            }}
            pageSize={pageSize}
            onPageSizeChange={(v) => {
              setPageSize(v)
              setPage(0)
            }}
            filteredCount={processed.length}
            totalCount={tabRows.length}
            onExport={handleExport}
            exportDisabled={!processed.length}
          />

          {!pagination.rows.length ? (
            <EmptyState title={config.emptyTitle} description={config.emptyDescription} />
          ) : (
            <>
              {activeTab === 'forecast' && (
                <ForecastHistoryTable
                  rows={pagination.rows}
                  sortKey={sortKey}
                  sortDir={sortDir}
                  onSort={handleSort}
                />
              )}
              {activeTab === 'feedback' && (
                <FeedbackHistoryTable
                  rows={pagination.rows}
                  sortKey={sortKey}
                  sortDir={sortDir}
                  onSort={handleSort}
                />
              )}
              {activeTab === 'model' && (
                <ModelHistoryTable
                  rows={pagination.rows}
                  sortKey={sortKey}
                  sortDir={sortDir}
                  onSort={handleSort}
                />
              )}

              <HistoryPagination
                safePage={pagination.safePage}
                totalPages={pagination.totalPages}
                start={pagination.start}
                end={pagination.end}
                total={pagination.total}
                onPageChange={setPage}
              />
            </>
          )}
        </div>
      </Card>
    </div>
  )
}
