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

export const linkComplaint = async (id, targetComplaintId, notes = '') => {
  const response = await apiClient.post(`/complaints/${id}/duplicate/link`, {
    target_complaint_id: targetComplaintId,
    notes,
  });
  return response.data;
};

export const mergeComplaint = async (id, primaryComplaintId, reason = '') => {
  const response = await apiClient.post(`/complaints/${id}/duplicate/merge`, {
    primary_complaint_id: primaryComplaintId,
    reason,
  });
  return response.data;
};

export const ignoreDuplicateWarning = async (id, reason = '') => {
  const response = await apiClient.post(`/complaints/${id}/duplicate/ignore`, {
    reason,
  });
  return response.data;
};

export const getSimilarComplaints = async (id) => {
  const response = await apiClient.get(`/complaints/${id}/similar`);
  return response.data;
};

export const semanticSearchComplaints = async (query, limit = 10, threshold = 0.40) => {
  const response = await apiClient.get('/complaints/semantic-search', {
    params: { query, limit, threshold }
  });
  return response.data;
};

export const getComplaintsSimilarTo = async (id, limit = 10, threshold = 0.40) => {
  const response = await apiClient.get(`/complaints/${id}/find-similar`, {
    params: { limit, threshold }
  });
  return response.data;
};

export const summarizeComplaint = async (id, provider = null, model = null) => {
  const params = {};
  if (provider) params.provider = provider;
  if (model) params.model = model;
  const response = await apiClient.post(`/complaints/${id}/summarize`, null, { params });
  return response.data;
};

export const getComplaintSummary = async (id) => {
  const response = await apiClient.get(`/complaints/${id}/summary`);
  return response.data;
};

export const generateCustomerResponse = async (id, tone = "Empathetic & Professional") => {
  const response = await apiClient.post(`/complaints/${id}/generate-response`, { tone });
  return response.data;
};

export const editCustomerResponse = async (id, responseId, content) => {
  const response = await apiClient.put(`/complaints/${id}/edit-response`, {
    response_id: responseId,
    content
  });
  return response.data;
};

export const approveCustomerResponse = async (id, responseId, approvedBy = "Support Agent") => {
  const response = await apiClient.post(`/complaints/${id}/approve-response`, {
    response_id: responseId,
    approved_by: approvedBy
  });
  return response.data;
};

export const sendCustomerResponse = async (id, responseId, sender = "Support Agent") => {
  const response = await apiClient.post(`/complaints/${id}/send-response`, {
    response_id: responseId,
    sender
  });
  return response.data;
};



