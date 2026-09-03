import apiClient from './client';

export const getComplaints = async (params = {}) => {
  const response = await apiClient.get('/complaints/', { params });
  return response.data;
};

export const getComplaint = async (id) => {
  const response = await apiClient.get(`/complaints/${id}`);
  return response.data;
};

export const createComplaint = async (data) => {
  const response = await apiClient.post('/complaints/', data);
  return response.data;
};

export const updateComplaint = async (id, data) => {
  const response = await apiClient.put(`/complaints/${id}`, data);
  return response.data;
};

export const resolveComplaint = async (id, resolutionNotes, markAsKnowledgeBase = true) => {
  const response = await apiClient.post(`/complaints/${id}/resolve`, {
    resolution_notes: resolutionNotes,
    mark_as_knowledge_base: markAsKnowledgeBase,
  });
  return response.data;
};

export const reassignComplaint = async (id, department, subDepartment, reason) => {
  const response = await apiClient.post(`/complaints/${id}/reassign`, {
    department,
    sub_department: subDepartment,
    reason,
  });
  return response.data;
};

export const deleteComplaint = async (id) => {
  const response = await apiClient.delete(`/complaints/${id}`);
  return response.data;
};
