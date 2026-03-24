/**
 * ChatWindow
 *
 * Headless-composable chat panel body — handles rendering the message thread,
 * recommendation cards, follow-up chips, typing indicator, suggestion chips,
 * and the text input. Layout/positioning is the parent's job.
 *
 * Props:
 *   messages        Message[]    — from useChat()
 *   loading         boolean      — from useChat()
 *   onSend          (text) => void
 *   onReset         () => void
 *   onNavigate      () => void   — called when user taps a rec card (e.g. close panel)
 *   suggestions     string[]     — initial prompt chips (shown on first turn)
 *   isFirstTurn     boolean      — from useChat()
 *   inputRef        ref          — optional, lets parent focus the input
 *   compact         boolean      — tighter padding for the FAB panel
 *   showHeader      boolean      — render the Forky header bar (default: false — parent handles it)
 *   className       string
 */
import { useEffect, useRef, useState } from 'react'
import ChatRecommendationCard from './ChatRecommendationCard'

const DEFAULT_SUGGESTIONS = [
  '🍝  Best Italian near me',
  '💸  Cheap eats under $$',
  '💑  Romantic dinner spots',
  '🥗  Great vegan options',
  '🎉  Good for groups',
  '🌮  Quick Mexican food',
]

// ── Typing dots ──────────────────────────────────────────────────────────────
function TypingIndicator() {
  return (
    <div className="flex items-start gap-2">
      <div className="w-7 h-7 rounded-full bg-brand-100 flex items-center justify-center text-sm flex-shrink-0">
        🍴
      </div>
      <div className="bg-gray-100 rounded-2xl rounded-bl-sm px-4 py-3 flex items-center gap-1">
        {[0, 150, 300].map((delay) => (
          <span
            key={delay}
            className="w-2 h-2 rounded-full bg-gray-400 animate-bounce"
            style={{ animationDelay: `${delay}ms` }}
          />
        ))}
      </div>
    </div>
  )
}

// ── Single message bubble + attached content ─────────────────────────────────
function MessageRow({ message, onNavigate, onSendFollowUp, compact }) {
  const isUser = message.role === 'user'
  const p      = compact ? 'px-3 py-2' : 'px-3.5 py-2.5'

  return (
    <div className="space-y-2">
      {/* Bubble */}
      <div className={`flex items-end gap-2 ${isUser ? 'justify-end' : 'justify-start'}`}>
        {/* Forky avatar — assistant only */}
        {!isUser && (
          <div className="w-7 h-7 rounded-full bg-brand-100 flex items-center justify-center text-sm flex-shrink-0 mb-0.5">
            🍴
          </div>
        )}

        <div
          className={`
            ${p} rounded-2xl text-sm leading-relaxed whitespace-pre-line max-w-[82%]
            ${isUser
              ? 'bg-brand-600 text-white rounded-br-sm'
              : message.isError
                ? 'bg-red-50 text-red-700 border border-red-200 rounded-bl-sm'
                : 'bg-gray-100 text-gray-800 rounded-bl-sm'
            }
          `}
        >
          {message.content}
        </div>
      </div>

      {/* Recommendation cards — only on assistant messages */}
      {!isUser && message.recommendations?.length > 0 && (
        <div className="ml-9 space-y-1.5">
          {message.recommendations.slice(0, 4).map((r) => (
            <ChatRecommendationCard
              key={r.id}
              restaurant={r}
              relevanceScore={r.relevance_score}
              onNavigate={onNavigate}
            />
          ))}
        </div>
      )}

      {/* Web summary note */}
      {!isUser && message.webSummary && (
        <div className="ml-9 flex items-start gap-1.5 text-[11px] text-gray-500 bg-gray-50 rounded-lg px-2.5 py-2">
          <span className="flex-shrink-0">🌐</span>
          <span className="leading-relaxed">{message.webSummary}</span>
        </div>
      )}

      {/* Follow-up chip */}
      {!isUser && message.followUp && (
        <div className="ml-9">
          <button
            type="button"
            onClick={() => onSendFollowUp(message.followUp)}
            className="text-xs bg-brand-50 text-brand-700 border border-brand-200 rounded-full
                       px-3 py-1.5 hover:bg-brand-100 transition text-left leading-tight"
          >
            💬 {message.followUp}
          </button>
        </div>
      )}
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────
export default function ChatWindow({
  messages,
  loading,
  onSend,
  onReset,
  onNavigate,
  suggestions = DEFAULT_SUGGESTIONS,
  isFirstTurn = true,
  inputRef: externalInputRef,
  compact = false,
  className = '',
}) {
  const [input, setInput]   = useState('')
  const bottomRef            = useRef(null)
  const internalInputRef     = useRef(null)
  const inputEl              = externalInputRef || internalInputRef

  // Auto-scroll on new messages or typing indicator
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const handleSubmit = (e) => {
    e.preventDefault()
    const text = input.trim()
    if (!text || loading) return
    setInput('')
    onSend(text)
  }

  const handleSuggestion = (s) => {
    // Strip leading emoji + spaces
    const clean = s.replace(/^[\p{Emoji}\s]+/u, '').trim()
    onSend(clean || s)
  }

  const pad = compact ? 'px-3' : 'px-4'

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* ── Message thread ─────────────────────────────────────────────────── */}
      <div className={`flex-1 overflow-y-auto ${pad} py-4 space-y-4`}>
        {messages.map((m) => (
          <MessageRow
            key={m.id}
            message={m}
            onNavigate={onNavigate}
            onSendFollowUp={(text) => {
              onSend(text)
            }}
            compact={compact}
          />
        ))}

        {loading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* ── Suggestion chips — only on first turn ──────────────────────────── */}
      {isFirstTurn && suggestions.length > 0 && (
        <div className={`${pad} pb-2 pt-1 flex gap-2 overflow-x-auto border-t border-gray-50`}
          style={{ scrollbarWidth: 'none' }}>
          {suggestions.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => handleSuggestion(s)}
              className="flex-shrink-0 text-xs px-3 py-1.5 bg-white border border-gray-200
                         rounded-full text-gray-600 hover:border-brand-300 hover:text-brand-700
                         hover:bg-brand-50 transition whitespace-nowrap"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* ── Input bar ──────────────────────────────────────────────────────── */}
      <div className={`${pad} pb-3 pt-2 border-t border-gray-100`}>
        <form onSubmit={handleSubmit} className="flex items-center gap-2">
          {/* New chat button */}
          {messages.length > 1 && (
            <button
              type="button"
              onClick={() => { onReset(); setInput('') }}
              title="Start new conversation"
              aria-label="Start new conversation"
              className="w-9 h-9 flex-shrink-0 rounded-xl border border-gray-200 text-gray-400
                         flex items-center justify-center hover:border-brand-300 hover:text-brand-500
                         transition"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M12 4v16m8-8H4" />
              </svg>
            </button>
          )}

          <input
            ref={inputEl}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask Forky anything…"
            aria-label="Message Forky"
            disabled={loading}
            className="flex-1 px-3.5 py-2.5 rounded-xl border border-gray-200 text-sm
                       focus:outline-none focus:ring-2 focus:ring-brand-400 focus:border-transparent
                       disabled:opacity-60 transition"
          />

          <button
            type="submit"
            disabled={!input.trim() || loading}
            aria-label="Send"
            className="w-9 h-9 flex-shrink-0 rounded-xl bg-brand-600 text-white
                       flex items-center justify-center hover:bg-brand-700
                       disabled:opacity-40 active:scale-95 transition"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </form>
      </div>
    </div>
  )
}
