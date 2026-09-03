import apiClient from './client';

export const analyzeComplaint = async (data) => {
  const res = await apiClient.post('/ai/analyze', data);
  return res.data;
};

export const classifyText = async (data) => {
  return analyzeComplaint(typeof data === 'string' ? { subject: 'Inquiry', body: data } : data);
};

export const chatWithAssistant = async (message) => {
  const res = await apiClient.post('/ai/chat', { message });
  return res.data;
};

export const summarizeComplaint = async (id) => {
  const res = await apiClient.post('/ai/analyze', { subject: 'Summary Request', body: `Ticket #${id}` });
  return res.data;
};

export const getResolutionRecommendations = async (id) => {
  const res = await apiClient.post('/ai/chat', { message: `Give resolution recommendations for ticket #${id}` });
  return res.data;
};

export const generateDraftResponse = async (id) => {
  const res = await apiClient.post('/ai/chat', { message: `Generate response draft for ticket #${id}` });
  return res.data;
};
