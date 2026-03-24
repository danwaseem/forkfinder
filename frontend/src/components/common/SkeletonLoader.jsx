/**
 * SkeletonLoader
 *
 * Props:
 *   variant   'card'|'list-item'|'review'|'text'|'stat'   — shape preset
 *   count     number   — how many skeletons to render (default: 1)
 *   className string   — extra classes on the outer wrapper
 *
 * Usage:
 *   <SkeletonLoader variant="card" count={6} />
 *   <SkeletonLoader variant="review" count={3} />
 */

function Pulse({ className }) {
  return <div className={`animate-pulse rounded bg-gray-200 ${className}`} />
}

function CardSkeleton() {
  return (
    <div className="card overflow-hidden">
      {/* Image */}
      <Pulse className="h-44 rounded-none" />
      {/* Content */}
      <div className="p-4 space-y-3">
        <div className="flex justify-between gap-2">
          <Pulse className="h-4 w-3/5" />
          <Pulse className="h-5 w-10 rounded-full" />
        </div>
        <div className="flex gap-2">
          <Pulse className="h-5 w-16 rounded-full" />
          <Pulse className="h-5 w-20 rounded-full" />
        </div>
        <Pulse className="h-4 w-1/3" />
        <Pulse className="h-3 w-full" />
        <Pulse className="h-3 w-4/5" />
      </div>
    </div>
  )
}

function ListItemSkeleton() {
  return (
    <div className="card p-4 flex items-center gap-4">
      <Pulse className="w-16 h-16 rounded-xl flex-shrink-0" />
      <div className="flex-1 space-y-2">
        <Pulse className="h-4 w-2/5" />
        <Pulse className="h-3 w-3/5" />
        <Pulse className="h-3 w-1/4" />
      </div>
      <Pulse className="w-16 h-8 rounded-lg flex-shrink-0" />
    </div>
  )
}

function ReviewSkeleton() {
  return (
    <div className="border-b border-gray-100 py-5 last:border-0">
      <div className="flex gap-3">
        <Pulse className="w-10 h-10 rounded-full flex-shrink-0" />
        <div className="flex-1 space-y-2">
          <div className="flex justify-between">
            <Pulse className="h-3.5 w-28" />
            <Pulse className="h-3 w-20" />
          </div>
          <Pulse className="h-3.5 w-24" />
          <Pulse className="h-3 w-full" />
          <Pulse className="h-3 w-5/6" />
          <Pulse className="h-3 w-3/4" />
        </div>
      </div>
    </div>
  )
}

function TextSkeleton() {
  return (
    <div className="space-y-2">
      <Pulse className="h-4 w-full" />
      <Pulse className="h-4 w-5/6" />
      <Pulse className="h-4 w-4/5" />
      <Pulse className="h-4 w-2/3" />
    </div>
  )
}

function StatSkeleton() {
  return (
    <div className="card p-5 space-y-3">
      <div className="flex items-center gap-3">
        <Pulse className="w-10 h-10 rounded-xl flex-shrink-0" />
        <div className="flex-1 space-y-1.5">
          <Pulse className="h-6 w-16" />
          <Pulse className="h-3 w-24" />
        </div>
      </div>
    </div>
  )
}

const VARIANTS = {
  card: CardSkeleton,
  'list-item': ListItemSkeleton,
  review: ReviewSkeleton,
  text: TextSkeleton,
  stat: StatSkeleton,
}

const GRID_CLASSES = {
  card: 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6',
  'list-item': 'space-y-4',
  review: 'divide-y divide-gray-100',
  text: '',
  stat: 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4',
}

export default function SkeletonLoader({ variant = 'card', count = 1, className = '' }) {
  const Component = VARIANTS[variant] || CardSkeleton
  const gridClass = GRID_CLASSES[variant] || ''

  if (count === 1) return <Component />

  return (
    <div className={`${gridClass} ${className}`}>
      {Array.from({ length: count }).map((_, i) => (
        <Component key={i} />
      ))}
    </div>
  )
}
