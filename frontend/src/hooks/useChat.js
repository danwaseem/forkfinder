/**
 * useChat — centralized multi-turn AI conversation state
 *
 * Used by every chat surface (floating widget, inline panel, page).
 * Conversation ID is persisted in a ref so it survives re-renders
 * without causing unnecessary updates.
 *
 * Returned interface
 * ──────────────────
 *   messages      Message[]  — full thread including greeting
 *   loading       boolean    — true while waiting for the API
 *   send(text)    function   — append user msg, call API, append reply
 *   reset()       function   — start a fresh conversation
 *   isFirstTurn   boolean    — true before the user has sent anything
 *
 * Message shape
 * ─────────────
 *   { id, role, content, recommendations, followUp, webSummary, timestamp, isError }
 */
import { useCallback, useRef, useState } from 'react'
import { aiApi } from '../services/ai'
import { getErrorMessage } from '../utils/apiError'

const GREETING_TEXT =
  "Hi! I'm Forky, your AI dining guide. 🍴\n\nTell me what you're looking for — a cuisine, an occasion, a vibe, or a budget — and I'll find the perfect restaurant for you."

function msg(role, content, extras = {}) {
  return {
    id: Math.random().toString(36).slice(2),
    role,
    content,
    recommendations: [],
    followUp: null,
    webSummary: null,
    timestamp: new Date(),
    isError: false,
    ...extras,
  }
}

const GREETING = msg('assistant', GREETING_TEXT)

export function useChat() {
  const [messages, setMessages] = useState([GREETING])
  const [loading, setLoading]   = useState(false)
  const conversationIdRef        = useRef(null)

  const send = useCallback(async (text) => {
    const content = typeof text === 'string' ? text.trim() : ''
    if (!content || loading) return

    // Append the user's message immediately
    setMessages((prev) => [...prev, msg('user', content)])
    setLoading(true)

    try {
      const data = await aiApi.chat({
        message: content,
        conversationId: conversationIdRef.current,
      })

      // Persist conversation_id for all subsequent turns
      if (data.conversation_id) {
        conversationIdRef.current = data.conversation_id
      }

      setMessages((prev) => [
        ...prev,
        msg('assistant', data.assistant_message, {
          recommendations: data.recommendations   || [],
          followUp:        data.follow_up_question || null,
          webSummary:      data.web_results_summary || null,
        }),
      ])
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        msg('assistant', 'Sorry, I ran into a problem. Please try again.', {
          isError: true,
        }),
      ])
      // Error is displayed inline; no separate error state needed
      console.error('[useChat]', getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [loading])

  const reset = useCallback(() => {
    conversationIdRef.current = null
    setMessages([{ ...GREETING, id: Math.random().toString(36).slice(2) }])
    setLoading(false)
  }, [])

  return {
    messages,
    loading,
    send,
    reset,
    isFirstTurn: messages.length === 1,
  }
}
