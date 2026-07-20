import { createContext, useContext, useEffect, useMemo, useState } from 'react'
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

  const restaurants = restaurantRes || []

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

  useEffect(() => {
    if (!restaurants.length) return
    const exists = restaurants.some((r) => r.id === restaurantId)
    if (!restaurantId || !exists) {
      const nextId = restaurants[0].id
      setRestaurantId(nextId)
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ restaurantId: nextId, branchId: null }))
    }
  }, [restaurants, restaurantId])

  const { data: branchRes, isFetching: branchesFetching } = useQuery({
    queryKey: ['branches', 'org-switcher', restaurantId],
    queryFn: async () =>
      (await listBranches({ restaurant_id: restaurantId, active_only: true })).data || [],
    enabled: Boolean(restaurantId),
    staleTime: 0,
    refetchOnMount: 'always',
  })

  const branches = branchRes || []
  const branchesLoading = (branchRes === undefined || branchesFetching) && Boolean(restaurantId)

  useEffect(() => {
    if (branchRes === undefined) return
    if (!branches.length) {
      if (branchId) {
        setBranchId(null)
        localStorage.setItem(
          STORAGE_KEY,
          JSON.stringify({ restaurantId, branchId: null }),
        )
      }
      return
    }
    const exists = branches.some((b) => b.id === branchId)
    if (!branchId || !exists) {
      const nextId = branches[0].id
      setBranchId(nextId)
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ restaurantId, branchId: nextId }),
      )
    }
  }, [branches, branchId, restaurantId, branchRes])

  const restaurant = restaurants.find((r) => r.id === restaurantId) || restaurants[0] || null
  const branch = branches.find((b) => b.id === branchId) || branches[0] || null

  const selectRestaurant = (id) => {
    setRestaurantId(id)
    setBranchId(null)
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ restaurantId: id, branchId: null }))
  }

  const selectBranch = (id) => {
    setBranchId(id)
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ restaurantId, branchId: id }))
  }

  const value = useMemo(
    () => ({
      restaurants,
      branches,
      restaurant,
      branch,
      restaurantId: restaurant?.id,
      branchId: branch?.id,
      branchesLoading,
      selectRestaurant,
      selectBranch,
    }),
    [restaurants, branches, restaurant, branch, branchesLoading],
  )

  return <OrgContext.Provider value={value}>{children}</OrgContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useOrg() {
  const ctx = useContext(OrgContext)
  if (!ctx) throw new Error('useOrg must be used within OrgProvider')
  return ctx
}
