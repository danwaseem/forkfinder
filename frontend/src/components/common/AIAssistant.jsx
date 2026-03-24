/**
 * AIAssistant — floating AI chat widget
 *
 * Renders a fixed FAB button (bottom-right) that opens a full chat panel.
 * Only shown to authenticated users.
 *
 * Features
 * ────────
 *  · Multi-turn conversation via useChat()
 *  · Unread dot on FAB when panel is closed and Forky has replied
 *  · Smooth slide-up panel animation
 *  · Clear / new conversation button
 *  · Mobile: full-screen panel below 480 px
 *  · Accessibility: dialog role, focus trap on open, Escape to close
 */
import { useCallback, useEffect, useRef, useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import { useChat } from '../../hooks/useChat'
import ChatWindow from '../ai/ChatWindow'

// ─── FAB button ───────────────────────────────────────────────────────────────
function FAB({ open, hasUnread, onClick }) {
  return (
    <button
      onClick={onClick}
      aria-label={open ? 'Close AI assistant' : 'Open AI dining guide'}
      aria-expanded={open}
      className={`
        fixed bottom-6 right-6 z-50
        w-14 h-14 rounded-full shadow-xl
        flex items-center justify-center
        bg-gradient-to-br from-brand-500 to-brand-700 text-white
        hover:from-brand-600 hover:to-brand-800
        active:scale-95 transition-all duration-200
        focus:outline-none focus:ring-2 focus:ring-brand-400 focus:ring-offset-2
        ${open ? 'scale-90 opacity-0 pointer-events-none' : 'scale-100 opacity-100'}
      `}
    >
      <span className="text-2xl" aria-hidden="true">🍴</span>

      {/* Unread dot */}
      {hasUnread && !open && (
        <span
          className="absolute top-0.5 right-0.5 w-3.5 h-3.5 rounded-full bg-green-400
                     border-2 border-white animate-pulse"
          aria-hidden="true"
        />
      )}
    </button>
  )
}

// ─── Panel header ─────────────────────────────────────────────────────────────
function PanelHeader({ onReset, onClose, hasHistory }) {
  return (
    <div className="flex items-center justify-between px-4 py-3
                    bg-gradient-to-r from-brand-600 to-brand-700 text-white flex-shrink-0">
      <div className="flex items-center gap-2.5">
        <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center text-base">
          🍴
        </div>
        <div>
          <p className="font-semibold text-sm leading-tight">Forky</p>
          <p className="text-[11px] text-brand-200 leading-tight">AI Dining Guide · Always on</p>
        </div>
      </div>

      <div className="flex items-center gap-1">
        {/* Clear button — only when there's a real conversation */}
        {hasHistory && (
          <button
            type="button"
            onClick={onReset}
            aria-label="Start new conversation"
            title="New chat"
            className="p-2 rounded-lg hover:bg-white/10 transition text-white/80 hover:text-white"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
        )}

        {/* Close */}
        <button
          type="button"
          onClick={onClose}
          aria-label="Close chat"
          className="p-2 rounded-lg hover:bg-white/10 transition text-white/80 hover:text-white"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  )
}

// ─── Main component ───────────────────────────────────────────────────────────
export default function AIAssistant() {
  const { user } = useAuth()
  const { messages, loading, send, reset, isFirstTurn } = useChat()

  const [open, setOpen]         = useState(false)
  const [hasUnread, setHasUnread] = useState(false)
  const inputRef                 = useRef(null)
  const panelRef                 = useRef(null)

  // Track unread: a new assistant message arrived while panel was closed
  const lastMsgCount = useRef(1) // starts at 1 (greeting)
  useEffect(() => {
    const assistantAdded =
      messages.length > lastMsgCount.current &&
      messages[messages.length - 1]?.role === 'assistant'
    if (assistantAdded && !open) {
      setHasUnread(true)
    }
    lastMsgCount.current = messages.length
  }, [messages, open])

  // Clear unread when panel is opened
  const handleOpen = useCallback(() => {
    setOpen(true)
    setHasUnread(false)
    setTimeout(() => inputRef.current?.focus(), 100)
  }, [])

  const handleClose = useCallback(() => setOpen(false), [])

  // Close on Escape
  useEffect(() => {
    if (!open) return
    const onKey = (e) => { if (e.key === 'Escape') handleClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, handleClose])

  // Don't render for guests
  if (!user) return null

  return (
    <>
      {/* Backdrop — mobile only */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/20 sm:hidden"
          aria-hidden="true"
          onClick={handleClose}
        />
      )}

      {/* FAB */}
      <FAB open={open} hasUnread={hasUnread} onClick={handleOpen} />

      {/* ── Chat panel ─────────────────────────────────────────────────────── */}
      <div
        ref={panelRef}
        role="dialog"
        aria-label="Forky — AI dining assistant"
        aria-modal="true"
        className={`
          fixed z-50 bg-white border border-gray-200 shadow-2xl flex flex-col
          overflow-hidden transition-all duration-300 ease-out
          /* Mobile: slides up from bottom, full width */
          bottom-0 left-0 right-0 rounded-t-2xl
          sm:bottom-6 sm:right-6 sm:left-auto sm:rounded-2xl
          sm:w-[400px]
          /* Height */
          ${open
            ? 'h-[90vh] sm:h-[620px] translate-y-0 opacity-100'
            : 'h-[90vh] sm:h-[620px] translate-y-full sm:translate-y-8 opacity-0 pointer-events-none'
          }
        `}
      >
        <PanelHeader
          onClose={handleClose}
          onReset={reset}
          hasHistory={messages.length > 1}
        />

        <ChatWindow
          messages={messages}
          loading={loading}
          onSend={send}
          onReset={reset}
          onNavigate={handleClose}
          isFirstTurn={isFirstTurn}
          inputRef={inputRef}
          compact
        />
      </div>
    </>
  )
}
