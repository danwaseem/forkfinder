export default function LoadingSpinner({ fullPage = false, size = 'md', label = 'Loading…' }) {
  const sizes = { sm: 'w-5 h-5 border-2', md: 'w-9 h-9 border-[3px]', lg: 'w-14 h-14 border-4' }

  const spinner = (
    <div role="status" aria-label={label} className="flex flex-col items-center gap-3">
      <div className={`${sizes[size]} border-brand-100 border-t-brand-600 rounded-full animate-spin`} />
      {size !== 'sm' && (
        <span className="text-xs text-gray-400 font-medium">{label}</span>
      )}
    </div>
  )

  if (fullPage) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-white/80 backdrop-blur-sm z-50">
        {spinner}
      </div>
    )
  }

  return <div className="flex justify-center py-12">{spinner}</div>
}
