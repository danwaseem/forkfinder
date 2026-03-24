/**
 * RestaurantGrid
 *
 * Renders a responsive grid (or list) of RestaurantCard components with
 * built-in loading skeletons and empty state.
 *
 * Props:
 *   restaurants     Restaurant[]    — data array
 *   loading         boolean         — show skeletons
 *   layout          'grid'|'list'   — display mode (default: 'grid')
 *   cols            2|3|4           — grid columns on large screens (default: 3)
 *   skeletonCount   number          — how many skeleton cards to show (default: 6)
 *   emptyIcon       string          — emoji for empty state
 *   emptyTitle      string          — heading for empty state
 *   emptyMessage    string          — body text for empty state
 *   emptyAction     { label, to, onClick }  — CTA in empty state
 *   onFavoriteToggle (id, state) => void  — bubble up from RestaurantCard
 *   className       string
 */
import RestaurantCard from './RestaurantCard'
import SkeletonLoader from '../common/SkeletonLoader'
import EmptyState from '../common/EmptyState'

const GRID_COLS = {
  2: 'sm:grid-cols-2',
  3: 'sm:grid-cols-2 lg:grid-cols-3',
  4: 'sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4',
}

export default function RestaurantGrid({
  restaurants = [],
  loading = false,
  layout = 'grid',
  cols = 3,
  skeletonCount = 6,
  emptyIcon = '🍽️',
  emptyTitle = 'No restaurants found',
  emptyMessage = 'Try adjusting your search or filters.',
  emptyAction,
  onFavoriteToggle,
  className = '',
}) {
  if (loading) {
    return (
      <SkeletonLoader
        variant={layout === 'list' ? 'list-item' : 'card'}
        count={skeletonCount}
        className={className}
      />
    )
  }

  if (!restaurants.length) {
    return (
      <EmptyState
        icon={emptyIcon}
        title={emptyTitle}
        message={emptyMessage}
        action={emptyAction}
        className={className}
      />
    )
  }

  if (layout === 'list') {
    return (
      <div className={`space-y-4 ${className}`}>
        {restaurants.map((r) => (
          <RestaurantCard
            key={r.id}
            restaurant={r}
            onFavoriteToggle={onFavoriteToggle}
            layout="list"
          />
        ))}
      </div>
    )
  }

  return (
    <div className={`grid grid-cols-1 ${GRID_COLS[cols] || GRID_COLS[3]} gap-6 ${className}`}>
      {restaurants.map((r) => (
        <RestaurantCard
          key={r.id}
          restaurant={r}
          onFavoriteToggle={onFavoriteToggle}
        />
      ))}
    </div>
  )
}
