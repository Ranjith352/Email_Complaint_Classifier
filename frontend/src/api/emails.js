import apiClient from './client';

export const syncGmail = async () => {
  const res = await apiClient.post('/emails/sync');
  return res.data;
};

export const getEmailStatus = async () => {
  const res = await apiClient.get('/emails/status');
  return res.data;
};
