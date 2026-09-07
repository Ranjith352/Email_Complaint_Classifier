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

export const summarizeComplaint = async (id, provider = null, model = null) => {
  const params = {};
  if (provider) params.provider = provider;
  if (model) params.model = model;
  const res = await apiClient.post(`/complaints/${id}/summarize`, null, { params });
  return res.data;
};

export const getLLMStatus = async () => {
  const res = await apiClient.get('/ai/llm/status');
  return res.data;
};

export const configureLLM = async (config) => {
  const res = await apiClient.post('/ai/llm/config', config);
  return res.data;
};

export const getOllamaModels = async () => {
  const res = await apiClient.get('/ai/llm/models');
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
