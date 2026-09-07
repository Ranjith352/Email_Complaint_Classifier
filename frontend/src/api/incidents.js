import apiClient from './client';

export const getActiveIncidents = async () => {
  const response = await apiClient.get('/incidents/active');
  return response.data;
};

export const detectIncidents = async (params = {}) => {
  const response = await apiClient.post('/incidents/detect', params);
  return response.data;
};

export const getIncidents = async (params = {}) => {
  const response = await apiClient.get('/incidents/', { params });
  return response.data;
};

export const getIncident = async (id) => {
  const response = await apiClient.get(`/incidents/${id}`);
  return response.data;
};

export const acknowledgeIncident = async (id, managerName = 'Operations Manager', notes = '') => {
  const response = await apiClient.post(`/incidents/${id}/acknowledge`, {
    manager_name: managerName,
    notes,
  });
  return response.data;
};

export const resolveIncident = async (id, managerName = 'Operations Manager', resolutionNotes = '') => {
  const response = await apiClient.post(`/incidents/${id}/resolve`, {
    manager_name: managerName,
    resolution_notes: resolutionNotes,
  });
  return response.data;
};
