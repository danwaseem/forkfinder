/**
 * PhotoPicker — multi-photo selector with preview grid.
 *
 * Props:
 *   files         File[]           — controlled list of pending files
 *   onChange      (File[]) => void — called whenever the list changes
 *   existingUrls  string[]         — already-saved photo URLs (read-only display)
 *   maxFiles      number           — max total pending files (default: 10)
 *   disabled      boolean
 *   label         string
 *   hint          string
 *
 * Client-side validation per file:
 *   - Must be image/*
 *   - Must be ≤ 5 MB
 *
 * The component lets the parent manage state:
 *   const [photos, setPhotos] = useState([])
 *   <PhotoPicker files={photos} onChange={setPhotos} />
 */
import { useRef, useState } from 'react'
import { imgUrl } from '../../utils/format'

const MAX_FILE_SIZE = 5 * 1024 * 1024   // 5 MB

function validateFile(file) {
  if (!file.type.startsWith('image/')) {
    return `"${file.name}" is not an image.`
  }
  if (file.size > MAX_FILE_SIZE) {
    const mb = (file.size / (1024 * 1024)).toFixed(1)
    return `"${file.name}" is ${mb} MB — max 5 MB.`
  }
  return null
}

// ── Single pending-file thumbnail ─────────────────────────────────────────────
function PendingThumb({ file, onRemove }) {
  const [preview] = useState(() => URL.createObjectURL(file))
  return (
    <div className="relative w-24 h-24 group shrink-0">
      <img
        src={preview}
        alt={file.name}
        className="w-full h-full object-cover rounded-xl border border-gray-200"
      />
      <button
        type="button"
        onClick={onRemove}
        aria-label={`Remove ${file.name}`}
        className="absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full
                   bg-gray-900 text-white flex items-center justify-center
                   opacity-0 group-hover:opacity-100 transition-opacity
                   hover:bg-red-600 text-xs font-bold leading-none"
      >
        ×
      </button>
      <div className="absolute bottom-0 left-0 right-0 bg-black/50 text-white
                      text-[9px] px-1 py-0.5 rounded-b-xl truncate">
        {(file.size / 1024).toFixed(0)} KB
      </div>
    </div>
  )
}

// ── Existing-photo thumbnail (read-only) ─────────────────────────────────────
function ExistingThumb({ url }) {
  const src = imgUrl(url)
  return (
    <div className="relative w-24 h-24 shrink-0">
      {src ? (
        <img
          src={src}
          alt="Existing photo"
          className="w-full h-full object-cover rounded-xl border border-gray-200"
        />
      ) : (
        <div className="w-full h-full rounded-xl border border-gray-100 bg-gray-100 flex items-center justify-center text-2xl">
          🍽️
        </div>
      )}
      <span className="absolute bottom-0 left-0 right-0 bg-black/40 text-white
                       text-[9px] px-1 py-0.5 rounded-b-xl text-center">
        Saved
      </span>
    </div>
  )
}

// ── Add-more button ───────────────────────────────────────────────────────────
function AddButton({ onClick, disabled }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label="Add photos"
      className="w-24 h-24 rounded-xl border-2 border-dashed border-gray-300
                 flex flex-col items-center justify-center gap-1
                 text-gray-400 shrink-0
                 hover:border-brand-400 hover:text-brand-500 hover:bg-brand-50/40
                 disabled:opacity-40 disabled:cursor-not-allowed
                 transition-all duration-150"
    >
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
      </svg>
      <span className="text-[10px] font-medium">Add photo</span>
    </button>
  )
}

// ── Main component ────────────────────────────────────────────────────────────
export default function PhotoPicker({
  files        = [],
  onChange,
  existingUrls = [],
  maxFiles     = 10,
  disabled     = false,
  label        = 'Photos',
  hint,
}) {
  const inputRef               = useRef(null)
  const [errors, setErrors]    = useState([])
  const [dragging, setDragging] = useState(false)

  const totalCount = existingUrls.length + files.length
  const canAdd     = !disabled && totalCount < maxFiles

  const addFiles = (incoming) => {
    const newErrors = []
    const valid     = []

    for (const f of incoming) {
      const err = validateFile(f)
      if (err) {
        newErrors.push(err)
      } else {
        // De-duplicate by name + size
        const isDupe = files.some((x) => x.name === f.name && x.size === f.size)
        if (!isDupe) valid.push(f)
      }
    }

    setErrors(newErrors)
    if (valid.length === 0) return

    const capacity = maxFiles - existingUrls.length - files.length
    onChange?.([...files, ...valid.slice(0, capacity)])
  }

  const removeFile = (idx) => {
    const next = files.filter((_, i) => i !== idx)
    onChange?.(next)
    setErrors([])
  }

  const onInputChange = (e) => {
    addFiles(Array.from(e.target.files || []))
    // Reset input so the same file can be re-added after removal
    e.target.value = ''
  }

  const onDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    if (!canAdd) return
    addFiles(Array.from(e.dataTransfer.files || []))
  }

  const hasAny = existingUrls.length > 0 || files.length > 0

  return (
    <div className="space-y-3">
      {label && (
        <div className="flex items-center justify-between">
          <span className="label mb-0">{label}</span>
          <span className="text-xs text-gray-400">
            {totalCount} / {maxFiles}
          </span>
        </div>
      )}

      {/* Thumbnails + add button */}
      <div
        onDragOver={(e) => { e.preventDefault(); if (canAdd) setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={[
          'flex flex-wrap gap-3 p-4 rounded-2xl border-2 transition-all duration-150',
          dragging
            ? 'border-brand-400 bg-brand-50'
            : hasAny
              ? 'border-gray-200 bg-white'
              : 'border-dashed border-gray-300 bg-gray-50',
        ].join(' ')}
      >
        {/* Existing (saved) thumbnails */}
        {existingUrls.map((url) => (
          <ExistingThumb key={url} url={url} />
        ))}

        {/* Pending (new) thumbnails */}
        {files.map((file, i) => (
          <PendingThumb key={`${file.name}-${file.size}-${i}`} file={file} onRemove={() => removeFile(i)} />
        ))}

        {/* Add button */}
        {canAdd && (
          <AddButton onClick={() => inputRef.current?.click()} disabled={!canAdd} />
        )}

        {/* Empty placeholder */}
        {!hasAny && !canAdd && (
          <p className="text-sm text-gray-400 m-auto py-4">No photos yet.</p>
        )}
      </div>

      {/* Hint */}
      <p className="text-xs text-gray-400">
        {hint || `JPEG · PNG · WEBP · GIF · Max 5 MB each · Up to ${maxFiles} photos`}
      </p>

      {/* Errors */}
      {errors.length > 0 && (
        <ul role="alert" className="space-y-1">
          {errors.map((e, i) => (
            <li key={i} className="text-xs text-red-600 flex items-start gap-1.5">
              <svg className="w-3.5 h-3.5 mt-px shrink-0 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round"
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              {e}
            </li>
          ))}
        </ul>
      )}

      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        multiple
        onChange={onInputChange}
        className="sr-only"
        aria-hidden="true"
        disabled={!canAdd}
      />
    </div>
  )
}
