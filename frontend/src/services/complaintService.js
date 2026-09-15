import apiClient from './apiClient';

export const complaintService = {
  getComplaints: async (params = {}) => {
    const res = await apiClient.get('/complaints', { params });
    return res.data;
  },

  getComplaintById: async (id) => {
    const res = await apiClient.get(`/complaints/${id}`);
    return res.data;
  },

  createComplaint: async (data) => {
    const res = await apiClient.post('/complaints', data);
    return res.data;
  },

  updateDepartment: async (id, departmentId, reason, actor = 'Human Manager') => {
    const res = await apiClient.post(`/complaints/${id}/department`, {
      department_id: departmentId,
      reason,
      actor,
    });
    return res.data;
  },

  updateTeam: async (id, teamId, reason) => {
    const res = await apiClient.post(`/complaints/${id}/team`, {
      team_id: teamId,
      reason,
    });
    return res.data;
  },

  updatePriority: async (id, priority, reason) => {
    const res = await apiClient.post(`/complaints/${id}/priority`, {
      priority,
      reason,
    });
    return res.data;
  },

  assignAgent: async (id, agentId, notes) => {
    const res = await apiClient.post(`/complaints/${id}/assign`, {
      agent_id: agentId,
      notes,
    });
    return res.data;
  },

  updateStatus: async (id, status, notes) => {
    const res = await apiClient.post(`/complaints/${id}/status`, {
      status,
      notes,
    });
    return res.data;
  },

  getCustomerHistory: async (params = {}) => {
    const res = await apiClient.get('/ai/customer-history', { params });
    return res.data;
  },
};

export default complaintService;
