import apiClient from './client';

export const getDashboardAnalytics = async (params = {}) => {
  const response = await apiClient.get('/analytics/dashboard', { params });
  return response.data;
};

export const getAIInsights = async (params = {}) => {
  const response = await apiClient.get('/analytics/insights', { params });
  return response.data;
};

export const getAnalyticsOverview = async (params = {}) => {
  const response = await apiClient.get('/analytics/overview', { params });
  return response.data;
};

export const getDepartmentAnalytics = async (params = {}) => {
  const response = await apiClient.get('/analytics/departments', { params });
  return response.data;
};

export const getCategoryAnalytics = async (params = {}) => {
  const response = await apiClient.get('/analytics/categories', { params });
  return response.data;
};

export const getSentimentAnalytics = async (params = {}) => {
  const response = await apiClient.get('/analytics/sentiment', { params });
  return response.data;
};

export const getEmotionAnalytics = async (params = {}) => {
  const response = await apiClient.get('/analytics/emotions', { params });
  return response.data;
};

export const getPriorityAnalytics = async (params = {}) => {
  const response = await apiClient.get('/analytics/priority', { params });
  return response.data;
};

export const getSLAAnalytics = async (params = {}) => {
  const response = await apiClient.get('/analytics/sla', { params });
  return response.data;
};

export const getAgentAnalytics = async (params = {}) => {
  const response = await apiClient.get('/analytics/agents', { params });
  return response.data;
};

export const getAIPerformanceAnalytics = async (params = {}) => {
  const response = await apiClient.get('/analytics/ai-performance', { params });
  return response.data;
};
