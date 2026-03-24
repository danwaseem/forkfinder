/**
 * Lightweight className merger.
 * Joins truthy strings; filters falsy values.
 * Install clsx for full conditional support, or use this drop-in for simple cases.
 */
export function cn(...classes) {
  return classes.filter(Boolean).join(' ')
}
