/**
 * SearchBar
 *
 * Props:
 *   value        string         — controlled input value
 *   onChange     (val) => void  — called on every keystroke
 *   onSubmit     (val) => void  — called when the form is submitted
 *   placeholder  string         — input placeholder (default: "Search…")
 *   size         'sm'|'md'|'lg' — height / font size preset
 *   showButton   boolean        — show the search button (default: true)
 *   buttonLabel  string         — button text (default: "Search")
 *   className    string         — extra classes applied to the wrapper form
 *   autoFocus    boolean        — focus on mount
 */
export default function SearchBar({
  value = '',
  onChange,
  onSubmit,
  placeholder = 'Search restaurants, cuisines, or cities…',
  size = 'md',
  showButton = true,
  buttonLabel = 'Search',
  className = '',
  autoFocus = false,
}) {
  const sizes = {
    sm: { input: 'px-3.5 py-2 text-sm', button: 'px-4 py-2 text-sm', icon: 'w-4 h-4' },
    md: { input: 'px-4 py-3 text-sm',   button: 'px-5 py-3 text-sm', icon: 'w-4 h-4' },
    lg: { input: 'px-5 py-4 text-base', button: 'px-7 py-4 text-base', icon: 'w-5 h-5' },
  }
  const s = sizes[size] || sizes.md

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit?.(value)
  }

  return (
    <form
      onSubmit={handleSubmit}
      role="search"
      className={`flex gap-2 ${className}`}
    >
      <label htmlFor="search-input" className="sr-only">
        {placeholder}
      </label>

      <div className="relative flex-1">
        {/* Leading search icon */}
        <svg
          className={`absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none ${s.icon}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
        </svg>

        <input
          id="search-input"
          type="search"
          value={value}
          onChange={(e) => onChange?.(e.target.value)}
          placeholder={placeholder}
          autoFocus={autoFocus}
          className={`w-full ${s.input} pl-10 rounded-xl border border-gray-200 bg-white
            focus:outline-none focus:ring-2 focus:ring-brand-400 focus:border-transparent
            placeholder:text-gray-400 transition`}
        />

        {/* Clear button — only when there's text */}
        {value && (
          <button
            type="button"
            onClick={() => onChange?.('')}
            aria-label="Clear search"
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition"
          >
            <svg className={s.icon} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {showButton && (
        <button
          type="submit"
          className={`${s.button} rounded-xl bg-brand-600 text-white font-semibold
            hover:bg-brand-700 active:scale-[0.98] transition flex-shrink-0`}
        >
          {buttonLabel}
        </button>
      )}
    </form>
  )
}
