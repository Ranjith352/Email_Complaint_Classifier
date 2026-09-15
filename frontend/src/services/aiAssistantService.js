import apiClient from './apiClient';

export const aiAssistantService = {
  askAssistant: async (message, complaintId = null, ticketNumber = null) => {
    const res = await apiClient.post('/ai/assistant', {
      message,
      complaint_id: complaintId,
      ticket_number: ticketNumber,
    });
    return res.data;
  },

  chat: async (message) => {
    const res = await apiClient.post('/ai/chat', { message });
    return res.data;
  },

  generateDraft: async (complaintId, tone = 'Empathetic & Professional') => {
    const res = await apiClient.post(`/complaints/${complaintId}/generate-response`, { tone });
    return res.data;
  },

  getLLMStatus: async () => {
    const res = await apiClient.get('/ai/llm/status');
    return res.data;
  },
};

export default aiAssistantService;
