import apiClient from './client';

export const syncGmail = async () => {
  const response = await apiClient.post('/gmail/sync');
  return response.data;
};

export const getGmailStatus = async () => {
  const response = await apiClient.get('/gmail/status');
  return response.data;
};
