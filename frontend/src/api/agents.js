import apiClient from './client';

export const getAgents = async () => {
  const res = await apiClient.get('/agents/');
  return res.data;
};

export const createAgent = async (data) => {
  const res = await apiClient.post('/agents/', data);
  return res.data;
};
