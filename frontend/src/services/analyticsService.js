import apiClient from './apiClient';

export const analyticsService = {
  getOverview: async (days = 30) => {
    const res = await apiClient.get('/analytics/overview', { params: { days } });
    return res.data;
  },

  getDepartments: async () => {
    const res = await apiClient.get('/analytics/departments');
    return res.data;
  },

  getCategories: async () => {
    const res = await apiClient.get('/analytics/categories');
    return res.data;
  },

  getSentiment: async () => {
    const res = await apiClient.get('/analytics/sentiment');
    return res.data;
  },

  getPriority: async () => {
    const res = await apiClient.get('/analytics/priority');
    return res.data;
  },

  getSLA: async () => {
    const res = await apiClient.get('/analytics/sla');
    return res.data;
  },

  getAIPerformance: async () => {
    const res = await apiClient.get('/analytics/ai-performance');
    return res.data;
  },

  getAgents: async () => {
    const res = await apiClient.get('/analytics/agents');
    return res.data;
  },
};

export default analyticsService;
