import apiClient from './client';

export const getSupportedDocumentTypes = async () => {
  const res = await apiClient.get('/knowledge/supported-types');
  return res.data;
};

export const getKnowledgeDocuments = async () => {
  const res = await apiClient.get('/knowledge/');
  return res.data;
};

export const getDocumentDetail = async (id) => {
  const res = await apiClient.get(`/knowledge/${id}`);
  return res.data;
};

export const createKnowledgeDocument = async (docData) => {
  const res = await apiClient.post('/knowledge/', docData);
  return res.data;
};

export const uploadDocumentFile = async (formData) => {
  const res = await apiClient.post('/knowledge/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
  return res.data;
};

export const queryKnowledgeRAG = async ({ question, document_type = null, limit = 4 }) => {
  const res = await apiClient.post('/knowledge/query', {
    question,
    document_type,
    limit
  });
  return res.data;
};

export const seedKnowledgeBase = async () => {
  const res = await apiClient.post('/knowledge/seed');
  return res.data;
};

export const deleteKnowledgeDocument = async (id) => {
  const res = await apiClient.delete(`/knowledge/${id}`);
  return res.data;
};
