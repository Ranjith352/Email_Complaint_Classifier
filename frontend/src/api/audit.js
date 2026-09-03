import apiClient from './client';

export const getAuditLogs = async (limit = 100) => {
  const res = await apiClient.get(`/audit/?limit=${limit}`);
  return res.data;
};
