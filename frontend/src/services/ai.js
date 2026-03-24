/**
 * ai.js — AI Assistant (Forky) API
 *
 * Wraps the /ai-assistant/* endpoints.
 *
 * Multi-turn conversation flow:
 *   1. First message: omit conversationId → backend creates a new DB conversation
 *      and returns a conversation_id in the response.
 *   2. Subsequent messages: pass the conversation_id from step 1 — the backend
 *      loads prior context and appends to the same conversation.
 *
 * Recommended pattern in components:
 *   const conversationIdRef = useRef(null)
 *
 *   const send = async (message) => {
 *     const data = await aiApi.chat({
 *       message,
 *       conversationId: conversationIdRef.current,
 *     })
 *     conversationIdRef.current = data.conversation_id   // persist across turns
 *   }
 *
 * Response shape (ChatResponse):
 *   {
 *     assistant_message:    string       — the reply to display
 *     recommendations:      Restaurant[] — ranked restaurants (may be empty)
 *     extracted_filters:    object       — filters the AI inferred from the message
 *     reasoning:            string       — AI's internal reasoning (debug)
 *     follow_up_question:   string|null  — suggested follow-up chip
 *     web_results_summary:  string|null  — web search snippet if used
 *     conversation_id:      string       — persist and pass on next turn
 *   }
 */
import api from './api'

export const aiApi = {
  /**
   * POST /ai-assistant/chat
   * Send a message to Forky.
   *
   * @param {{
   *   message:             string           — user's message text
   *   conversationId?:     string | null    — null on first turn
   *   conversationHistory?: { role: string, content: string }[]
   * }} options
   * @returns {Promise<ChatResponse>}
   */
  chat: ({ message, conversationId = null, conversationHistory = [] }) =>
    api.post('/ai-assistant/chat', {
      message,
      conversation_id:      conversationId,
      conversation_history: conversationHistory,
    }).then((r) => r.data),

  /**
   * GET /ai-assistant/conversations/:id
   * Load the full message history for a prior conversation.
   * Useful for a "resume chat" feature.
   *
   * @param {string} conversationId
   * @returns {Promise<{ id: string, messages: { role, content }[], created_at: string }>}
   */
  getConversation: (conversationId) =>
    api.get(`/ai-assistant/conversations/${conversationId}`).then((r) => r.data),

  /**
   * GET /ai-assistant/conversations
   * List the current user's saved conversations (most recent first).
   *
   * @param {{ limit?, offset? }} params
   * @returns {Promise<{ items: Conversation[], total: number }>}
   */
  listConversations: (params = {}) =>
    api.get('/ai-assistant/conversations', { params }).then((r) => r.data),
}
