import apiClient from './client';

export const getDepartments = async () => {
  const res = await apiClient.get('/departments/');
  return res.data;
};

export const createDepartment = async (data) => {
  const res = await apiClient.post('/departments/', data);
  return res.data;
};
