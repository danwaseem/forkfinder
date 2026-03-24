/**
 * ChatMessageBubble
 *
 * A single message bubble for chat UIs.
 *
 * Props:
 *   role        'user'|'assistant'   — determines alignment & color
 *   content     string               — message text (newlines preserved)
 *   timestamp   string|Date          — optional ISO string or Date (shown as time)
 *   avatarUrl   string               — optional avatar image URL
 *   avatarFallback string            — single character shown when no avatarUrl
 *   isTyping    boolean              — show animated typing indicator instead of content
 *   className   string
 */
export default function ChatMessageBubble({
  role = 'assistant',
  content,
  timestamp,
  avatarUrl,
  avatarFallback,
  isTyping = false,
  className = '',
}) {
  const isUser = role === 'user'

  const timeStr = timestamp
    ? new Date(timestamp).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
    : null

  const Avatar = () => {
    if (isUser) return null
    if (avatarUrl) {
      return (
        <img
          src={avatarUrl}
          alt=""
          className="w-8 h-8 rounded-full object-cover flex-shrink-0 mt-0.5"
        />
      )
    }
    return (
      <div className="w-8 h-8 rounded-full bg-brand-100 text-brand-700 text-sm font-bold
                      flex items-center justify-center flex-shrink-0 mt-0.5">
        {avatarFallback ?? '🤖'}
      </div>
    )
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} gap-2 ${className}`}>
      <Avatar />

      <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} max-w-[82%]`}>
        <div
          className={`px-3.5 py-2.5 rounded-2xl text-sm leading-relaxed whitespace-pre-line
            ${isUser
              ? 'bg-brand-600 text-white rounded-br-sm'
              : 'bg-gray-100 text-gray-800 rounded-bl-sm'
            }`}
        >
          {isTyping ? (
            <span className="flex gap-1 items-center py-0.5 px-1">
              <span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce [animation-delay:0ms]" />
              <span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce [animation-delay:150ms]" />
              <span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce [animation-delay:300ms]" />
            </span>
          ) : (
            content
          )}
        </div>

        {timeStr && !isTyping && (
          <time className="text-[11px] text-gray-400 mt-1 px-1">{timeStr}</time>
        )}
      </div>
    </div>
  )
}
