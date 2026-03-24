/**
 * EmptyState
 *
 * Props:
 *   icon      string | ReactNode  — emoji or element (default: '🍽️')
 *   title     string              — bold heading
 *   message   string              — sub-text (optional)
 *   action    { label, onClick, to }   — primary CTA (either onClick or react-router `to`)
 *   secondaryAction  { label, onClick, to }  — optional secondary CTA
 *   size      'sm'|'md'|'lg'      — controls padding / icon size
 *   className string
 */
import { Link } from 'react-router-dom'

export default function EmptyState({
  icon = '🍽️',
  title = 'Nothing here yet',
  message,
  action,
  secondaryAction,
  size = 'md',
  className = '',
}) {
  const sizes = {
    sm: { wrap: 'py-10', icon: 'text-4xl mb-2', title: 'text-base', msg: 'text-xs' },
    md: { wrap: 'py-16', icon: 'text-5xl mb-3', title: 'text-lg', msg: 'text-sm' },
    lg: { wrap: 'py-24', icon: 'text-7xl mb-4', title: 'text-2xl', msg: 'text-base' },
  }
  const s = sizes[size] || sizes.md

  function ActionButton({ action: a, primary }) {
    if (!a) return null
    const cls = primary
      ? 'btn-primary px-6 py-2.5 text-sm'
      : 'btn-secondary px-6 py-2.5 text-sm'
    if (a.to) return <Link to={a.to} className={cls}>{a.label}</Link>
    return <button type="button" onClick={a.onClick} className={cls}>{a.label}</button>
  }

  return (
    <div className={`text-center ${s.wrap} ${className}`}>
      <div className={s.icon} aria-hidden="true">{icon}</div>
      <p className={`font-semibold text-gray-700 ${s.title}`}>{title}</p>
      {message && <p className={`mt-1.5 text-gray-500 max-w-xs mx-auto ${s.msg}`}>{message}</p>}
      {(action || secondaryAction) && (
        <div className="mt-5 flex items-center justify-center gap-3 flex-wrap">
          <ActionButton action={action} primary />
          <ActionButton action={secondaryAction} />
        </div>
      )}
    </div>
  )
}
