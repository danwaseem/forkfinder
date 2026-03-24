/**
 * ErrorAlert
 *
 * Props:
 *   message    string              — text to display (renders nothing if falsy)
 *   variant    'error'|'warning'|'info'|'success'  — color scheme (default: 'error')
 *   title      string              — optional bold heading above the message
 *   onDismiss  () => void          — show an × button when provided
 *   className  string              — extra wrapper classes
 *   icon       ReactNode           — override the default icon
 */
export default function ErrorAlert({
  message,
  variant = 'error',
  title,
  onDismiss,
  className = '',
  icon,
}) {
  if (!message) return null

  const styles = {
    error:   { wrap: 'bg-red-50 border-red-200 text-red-800',   icon: 'text-red-500',   defaultIcon: '✕' },
    warning: { wrap: 'bg-amber-50 border-amber-200 text-amber-800', icon: 'text-amber-500', defaultIcon: '!' },
    info:    { wrap: 'bg-blue-50 border-blue-200 text-blue-800', icon: 'text-blue-500',  defaultIcon: 'i' },
    success: { wrap: 'bg-green-50 border-green-200 text-green-800', icon: 'text-green-600', defaultIcon: '✓' },
  }
  const s = styles[variant] || styles.error

  return (
    <div
      role="alert"
      className={`flex gap-3 p-4 rounded-xl border ${s.wrap} ${className}`}
    >
      {/* Icon */}
      <span className={`flex-shrink-0 font-bold text-sm leading-5 mt-0.5 ${s.icon}`} aria-hidden="true">
        {icon ?? s.defaultIcon}
      </span>

      {/* Content */}
      <div className="flex-1 min-w-0">
        {title && <p className="font-semibold text-sm mb-0.5">{title}</p>}
        <p className="text-sm leading-relaxed">{message}</p>
      </div>

      {/* Dismiss */}
      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          aria-label="Dismiss alert"
          className={`flex-shrink-0 p-1 rounded hover:bg-black/5 transition ${s.icon}`}
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
    </div>
  )
}
