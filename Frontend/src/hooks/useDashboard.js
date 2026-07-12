import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useCallback } from 'react'
import { fetchDashboardData, DASHBOARD_QUERY_KEY } from '../services/dashboardService'

export function useDashboard() {
  return useQuery({
    queryKey: DASHBOARD_QUERY_KEY,
    queryFn: () => fetchDashboardData(),
    staleTime: 30_000,
    refetchOnWindowFocus: true,
    retry: 1,
  })
}

export function useDashboardRefresh() {
  const queryClient = useQueryClient()

  return useCallback(() => {
    queryClient.invalidateQueries({ queryKey: DASHBOARD_QUERY_KEY })
    queryClient.invalidateQueries({ queryKey: ['feedback-history'] })
    queryClient.invalidateQueries({ queryKey: ['staff-latest'] })
    queryClient.invalidateQueries({ queryKey: ['inventory-latest'] })
    queryClient.invalidateQueries({ queryKey: ['model-analytics'] })
    queryClient.invalidateQueries({ queryKey: ['prediction-history-page'] })
  }, [queryClient])
}
