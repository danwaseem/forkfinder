/**
 * ImageUpload — drag-and-drop / click-to-upload image field with preview.
 *
 * Props:
 *   preview     string            — current image URL (server path or Object URL)
 *   onFile      (File) => void    — called with a validated File
 *   label       string
 *   shape       'circle'|'square' — preview shape (default: 'circle')
 *   size        number            — preview dimension in px (default: 96)
 *   accept      string            — mime filter (default: 'image/*')
 *   uploading   boolean           — show spinner overlay while uploading
 *   disabled    boolean
 *   className   string
 *
 * Client-side validation:
 *   - Accepts only image/* MIME types
 *   - Rejects files > 5 MB with an inline error message
 */
import { useRef, useState } from 'react'

const MAX_SIZE_BYTES = 5 * 1024 * 1024   // 5 MB — mirrors backend limit

export default function ImageUpload({
  preview,
  onFile,
  label     = 'Upload photo',
  shape     = 'circle',
  size      = 96,
  accept    = 'image/*',
  uploading = false,
  disabled  = false,
  className = '',
}) {
  const inputRef           = useRef(null)
  const [dragging, setDragging]   = useState(false)
  const [clientError, setClientError] = useState('')

  const isCircle  = shape === 'circle'
  const shapeClass = isCircle ? 'rounded-full' : 'rounded-2xl'
  const isLocked   = disabled || uploading

  // ── Validate and forward the file ────────────────────────────────────────
  const handleFile = (file) => {
    if (!file || isLocked) return
    setClientError('')

    if (!file.type.startsWith('image/')) {
      setClientError('Please select an image file (JPEG, PNG, WEBP, or GIF).')
      return
    }
    if (file.size > MAX_SIZE_BYTES) {
      const mb = (file.size / (1024 * 1024)).toFixed(1)
      setClientError(`File is ${mb} MB — maximum is 5 MB.`)
      return
    }

    onFile?.(file)
  }

  const onInputChange = (e) => handleFile(e.target.files?.[0])

  const onDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    handleFile(e.dataTransfer.files?.[0])
  }

  return (
    <div className={`flex flex-col items-center gap-2 ${className}`}>
      {/* Drop zone / preview */}
      <div
        style={{ width: size, height: size }}
        onDragOver={(e)  => { e.preventDefault(); if (!isLocked) setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => !isLocked && inputRef.current?.click()}
        onKeyDown={(e) => e.key === 'Enter' && !isLocked && inputRef.current?.click()}
        role="button"
        tabIndex={isLocked ? -1 : 0}
        aria-label={label}
        aria-disabled={isLocked}
        className={[
          'relative overflow-hidden border-2 transition-all cursor-pointer select-none',
          shapeClass,
          dragging
            ? 'border-brand-500 bg-brand-50 scale-[1.03]'
            : clientError
              ? 'border-red-300 bg-red-50'
              : 'border-dashed border-gray-300 hover:border-brand-400 hover:bg-brand-50/40',
          isLocked ? 'opacity-60 cursor-not-allowed' : '',
        ].join(' ')}
      >
        {/* Current image */}
        {preview && (
          <img
            src={preview}
            alt="Preview"
            className={`w-full h-full object-cover ${shapeClass}`}
          />
        )}

        {/* Empty state */}
        {!preview && (
          <div className="w-full h-full flex flex-col items-center justify-center text-gray-400 gap-1 px-2">
            <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round"
                d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            {dragging && (
              <span className="text-[10px] text-brand-600 font-semibold">Drop here</span>
            )}
          </div>
        )}

        {/* Hover overlay (only when preview exists) */}
        {preview && !uploading && (
          <div className={`absolute inset-0 bg-black/40 flex items-center justify-center
                           opacity-0 hover:opacity-100 transition-opacity ${shapeClass}`}>
            <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round"
                d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
        )}

        {/* Uploading spinner overlay */}
        {uploading && (
          <div className={`absolute inset-0 bg-black/50 flex items-center justify-center ${shapeClass}`}>
            <div className="w-6 h-6 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          </div>
        )}
      </div>

      {/* Label + hint */}
      <div className="text-center">
        <button
          type="button"
          onClick={() => !isLocked && inputRef.current?.click()}
          disabled={isLocked}
          className="text-sm text-brand-600 hover:underline font-medium
                     disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {uploading ? 'Uploading…' : label}
        </button>
        <p className="text-xs text-gray-400 mt-0.5">JPEG · PNG · WEBP · GIF &nbsp;·&nbsp; Max 5 MB</p>
      </div>

      {/* Client-side error */}
      {clientError && (
        <p role="alert" className="text-xs text-red-600 text-center max-w-[160px] leading-tight">
          {clientError}
        </p>
      )}

      <input
        ref={inputRef}
        type="file"
        accept={accept}
        onChange={onInputChange}
        className="sr-only"
        aria-hidden="true"
        disabled={isLocked}
      />
    </div>
  )
}
