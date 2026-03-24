import { useCallback, useEffect, useState } from 'react'
import { restaurantsApi } from '../services/restaurants'

/**
 * Fetch a paginated, filtered list of restaurants.
 * Pass `filters` object; call `setPage` or `setFilters` to trigger refetch.
 */
export function useRestaurants(initialFilters = {}) {
  const [filters, setFilters] = useState(initialFilters)
  const [page, setPage] = useState(1)
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [pages, setPages] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await restaurantsApi.list({ ...filters, page, limit: 12 })
      setItems(data.items || [])
      setTotal(data.total || 0)
      setPages(data.pages || 1)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load restaurants.')
    } finally {
      setLoading(false)
    }
  }, [filters, page])

  useEffect(() => { fetch() }, [fetch])

  const applyFilters = useCallback((newFilters) => {
    setFilters(newFilters)
    setPage(1)
  }, [])

  return { items, total, pages, page, setPage, loading, error, applyFilters, refetch: fetch }
}
