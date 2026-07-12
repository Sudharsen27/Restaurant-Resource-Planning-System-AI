import { useMemo, useState } from 'react'
import { Loader2, RefreshCw } from 'lucide-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import Card from '../components/ui/Card'
import EmptyState from '../components/ui/EmptyState'
import ManagerFeedbackHeader from '../components/feedback/ManagerFeedbackHeader'
import FeedbackSubmitForm from '../components/feedback/FeedbackSubmitForm'
import FeedbackResultPanel from '../components/feedback/FeedbackResultPanel'
import RecentFeedbackHistoryTable from '../components/feedback/RecentFeedbackHistoryTable'
import FeedbackErrorCard from '../components/feedback/FeedbackErrorCard'
import { useToast } from '../context/ToastContext'
import { useDashboardRefresh } from '../hooks/useDashboard'
import { submitFeedback, getFeedbackHistory } from '../services/feedbackService'
import {
  buildRecentFeedbackRows,
  getPendingPredictions,
  validateFeedbackForm,
} from '../utils/feedbackForm'

const HISTORY_QUERY_KEY = ['feedback-history']

export default function ManagerFeedback() {
  const toast = useToast()
  const refreshDashboard = useDashboardRefresh()
  const queryClient = useQueryClient()

  const [form, setForm] = useState({
    prediction_id: '',
    actual_customers: '',
    comments: '',
  })
  const [fieldErrors, setFieldErrors] = useState({})
  const [lastResult, setLastResult] = useState(null)

  const {
    data: history,
    isLoading: historyLoading,
    error: historyError,
    refetch: refetchHistory,
    isFetching,
  } = useQuery({
    queryKey: HISTORY_QUERY_KEY,
    queryFn: async () => (await getFeedbackHistory({ skip: 0, limit: 200 })).data,
    staleTime: 30_000,
    retry: 1,
  })

  const pendingPredictions = useMemo(() => getPendingPredictions(history), [history])

  const selectablePredictions = useMemo(() => {
    const pending = getPendingPredictions(history)
    if (pending.length) return pending
    return history || []
  }, [history])

  const recentFeedbackRows = useMemo(() => buildRecentFeedbackRows(history), [history])

  const selectedPrediction = useMemo(
    () => (history || []).find((p) => String(p.id) === String(form.prediction_id)),
    [history, form.prediction_id],
  )

  const submitMutation = useMutation({
    mutationFn: (payload) => submitFeedback(payload).then((r) => r.data),
    onSuccess: (data) => {
      setLastResult(data)
      setForm({ prediction_id: '', actual_customers: '', comments: '' })
      setFieldErrors({})
      toast.success('Feedback submitted successfully — model retrained')
      queryClient.invalidateQueries({ queryKey: HISTORY_QUERY_KEY })
      refreshDashboard()
    },
    onError: (err) => {
      const message =
        err.response?.data?.detail?.[0]?.msg ||
        err.response?.data?.detail ||
        err.message ||
        'Failed to submit feedback'
      toast.error(typeof message === 'string' ? message : 'Failed to submit feedback')
    },
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    const validation = validateFeedbackForm(form)
    if (!validation.valid) {
      setFieldErrors(validation.errors)
      return
    }
    setFieldErrors({})
    submitMutation.mutate({
      prediction_id: Number(form.prediction_id),
      actual_customers: Number(form.actual_customers),
      comments: form.comments.trim() || null,
    })
  }

  if (historyLoading) {
    return (
      <div className="space-y-8">
        <ManagerFeedbackHeader />
        <div className="flex min-h-[320px] items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <ManagerFeedbackHeader />
        <button
          type="button"
          onClick={() => refetchHistory()}
          disabled={isFetching}
          className="flex shrink-0 items-center gap-2 self-start rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900"
        >
          <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {historyError && (
        <FeedbackErrorCard
          title="Could not load predictions"
          message={historyError.message || 'Unable to reach the feedback history API.'}
          onRetry={() => refetchHistory()}
        />
      )}

      <div className="grid gap-6 xl:grid-cols-2">
        <Card
          title="Submit Feedback"
          subtitle="Select a prediction and record actual customer count"
        >
          {historyError ? (
            <EmptyState
              title="Predictions unavailable"
              description="Refresh to load prediction history before submitting feedback."
            />
          ) : (
            <>
              <FeedbackSubmitForm
                predictions={selectablePredictions}
                form={form}
                fieldErrors={fieldErrors}
                onChange={setForm}
                onSubmit={handleSubmit}
                submitting={submitMutation.isPending}
                selectedPrediction={selectedPrediction}
              />
              {pendingPredictions.length > 0 && (
                <p className="mt-4 text-xs text-slate-500">
                  {pendingPredictions.length} prediction(s) awaiting feedback
                </p>
              )}
            </>
          )}
        </Card>

        <Card title="Submission Result" subtitle="Shown after successful feedback">
          <FeedbackResultPanel
            result={lastResult}
            submitting={submitMutation.isPending}
          />
        </Card>
      </div>

      <Card title="Recent Feedback History" subtitle="Submitted corrections from managers">
        {recentFeedbackRows.length ? (
          <RecentFeedbackHistoryTable rows={recentFeedbackRows} />
        ) : (
          <EmptyState
            title="No feedback submitted yet"
            description="Submit manager feedback above to compare predictions vs actuals."
          />
        )}
      </Card>
    </div>
  )
}
