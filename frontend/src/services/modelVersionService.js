import apiClient from './apiClient';

export const modelVersionService = {
  getActiveModels: async () => {
    const res = await apiClient.get('/models/active');
    return res.data;
  },

  getAllModelVersions: async () => {
    const res = await apiClient.get('/models');
    return res.data;
  },

  activateModel: async (modelId) => {
    const res = await apiClient.post(`/models/${modelId}/activate`);
    return res.data;
  },
};

export default modelVersionService;
