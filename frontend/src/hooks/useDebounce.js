import { useEffect, useState } from 'react'

/**
 * Debounce a value by `delay` ms.
 * Useful for search inputs so we don't fire an API call on every keystroke.
 */
export function useDebounce(value, delay = 400) {
  const [debounced, setDebounced] = useState(value)

  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(id)
  }, [value, delay])

  return debounced
}
