import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { listRestaurants } from '../services/restaurantService'
import { listBranches } from '../services/branchService'

const OrgContext = createContext(null)
const STORAGE_KEY = 'rrps-org'

export function OrgProvider({ children }) {
  const { data: restaurantRes } = useQuery({
    queryKey: ['restaurants', 'org-switcher'],
    queryFn: async () => (await listRestaurants({ active_only: true })).data || [],
    staleTime: 60_000,
  })

  const restaurants = useMemo(() => restaurantRes || [], [restaurantRes])

  const [restaurantId, setRestaurantId] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}').restaurantId || null
    } catch {
      return null
    }
  })
  const [branchId, setBranchId] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}').branchId || null
    } catch {
      return null
    }
  })

  const restaurant = useMemo(
    () => restaurants.find((r) => r.id === restaurantId) || restaurants[0] || null,
    [restaurants, restaurantId],
  )
  const resolvedRestaurantId = restaurant?.id ?? null

  const { data: branchRes, isFetching: branchesFetching } = useQuery({
    queryKey: ['branches', 'org-switcher', resolvedRestaurantId],
    queryFn: async () =>
      (await listBranches({ restaurant_id: resolvedRestaurantId, active_only: true })).data || [],
    enabled: Boolean(resolvedRestaurantId),
    staleTime: 0,
    refetchOnMount: 'always',
  })

  const branches = useMemo(() => branchRes || [], [branchRes])
  const branchesLoading = (branchRes === undefined || branchesFetching) && Boolean(resolvedRestaurantId)

  const branch = useMemo(() => {
    if (branchRes === undefined) return null
    if (!branches.length) return null
    return branches.find((b) => b.id === branchId) || branches[0] || null
  }, [branches, branchId, branchRes])

  useEffect(() => {
    if (!resolvedRestaurantId || branchRes === undefined) return
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ restaurantId: resolvedRestaurantId, branchId: branch?.id ?? null }),
    )
  }, [resolvedRestaurantId, branch?.id, branchRes])

  const selectRestaurant = useCallback((id) => {
    setRestaurantId(id)
    setBranchId(null)
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ restaurantId: id, branchId: null }))
  }, [])

  const selectBranch = useCallback(
    (id) => {
      setBranchId(id)
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ restaurantId: resolvedRestaurantId, branchId: id }),
      )
    },
    [resolvedRestaurantId],
  )

  const value = useMemo(
    () => ({
      restaurants,
      branches,
      restaurant,
      branch,
      restaurantId: resolvedRestaurantId,
      branchId: branch?.id ?? null,
      branchesLoading,
      selectRestaurant,
      selectBranch,
    }),
    [restaurants, branches, restaurant, branch, resolvedRestaurantId, branchesLoading, selectRestaurant, selectBranch],
  )

  return <OrgContext.Provider value={value}>{children}</OrgContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useOrg() {
  const ctx = useContext(OrgContext)
  if (!ctx) throw new Error('useOrg must be used within OrgProvider')
  return ctx
}
