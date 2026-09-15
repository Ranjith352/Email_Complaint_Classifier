import apiClient from './apiClient';

export const departmentService = {
  getDepartments: async () => {
    const res = await apiClient.get('/departments');
    return res.data;
  },

  getDepartmentById: async (id) => {
    const res = await apiClient.get(`/departments/${id}`);
    return res.data;
  },

  getTeams: async (departmentId = null) => {
    const params = departmentId ? { department_id: departmentId } : {};
    const res = await apiClient.get('/teams', { params });
    return res.data;
  },

  getAgents: async (params = {}) => {
    const res = await apiClient.get('/agents', { params });
    return res.data;
  },
};

export default departmentService;
