import apiClient from './client';

export const getTeams = async () => {
  const res = await apiClient.get('/teams/');
  return res.data;
};

export const createTeam = async (data) => {
  const res = await apiClient.post('/teams/', data);
  return res.data;
};
