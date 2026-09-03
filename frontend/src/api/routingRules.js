import client from './client';

/**
 * Configurable Routing Rules API Service
 * Rules are stored dynamically in PostgreSQL / Backend Database.
 * No hardcoded rules are used in the React frontend.
 */

export const getRoutingRules = async (isActive = null) => {
  const params = isActive !== null ? { is_active: isActive } : {};
  const response = await client.get('/routing-rules/', { params });
  return response.data;
};

export const createRoutingRule = async (ruleData) => {
  const response = await client.post('/routing-rules/', ruleData);
  return response.data;
};

export const getRoutingRuleById = async (id) => {
  const response = await client.get(`/routing-rules/${id}`);
  return response.data;
};

export const updateRoutingRule = async (id, ruleData) => {
  const response = await client.put(`/routing-rules/${id}`, ruleData);
  return response.data;
};

export const deleteRoutingRule = async (id) => {
  const response = await client.delete(`/routing-rules/${id}`);
  return response.data;
};
