import { useState } from 'react';
import { aiAssistantService } from '../services';

export default function useAIAssistant() {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'assistant',
      text: 'Hello! I am your AI Copilot. Ask me questions like "Show unresolved critical Finance complaints", "Summarize CMP-10001", or "What policy applies to this refund complaint?".',
      timestamp: new Date().toISOString(),
    },
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const sendMessage = async (text, complaintId = null, ticketNumber = null) => {
    if (!text.trim()) return;

    const userMsg = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);
    setError(null);

    try {
      const res = await aiAssistantService.askAssistant(text, complaintId, ticketNumber);
      const assistantMsg = {
        id: `assistant-${Date.now()}`,
        sender: 'assistant',
        text: res.reply,
        toolCalled: res.tool_called,
        data: res.data,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
      return assistantMsg;
    } catch (err) {
      const errorMsg = {
        id: `error-${Date.now()}`,
        sender: 'assistant',
        text: 'Error processing request. Please try again or verify backend services.',
        isError: true,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const clearHistory = () => {
    setMessages([]);
  };

  return {
    messages,
    loading,
    error,
    sendMessage,
    clearHistory,
  };
}
