import apiClient from './client';

export const getDepartments = async () => {
  const res = await apiClient.get('/departments/');
  return res.data;
};

export const getDepartmentById = async (id) => {
  const res = await apiClient.get(`/departments/${id}`);
  return res.data;
};

export const getDepartmentDashboard = async (id) => {
  const res = await apiClient.get(`/departments/${id}/dashboard`);
  return res.data;
};

export const createDepartment = async (data) => {
  const res = await apiClient.post('/departments/', data);
  return res.data;
};
