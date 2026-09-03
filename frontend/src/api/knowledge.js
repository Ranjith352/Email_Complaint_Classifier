import apiClient from './client';

export const getKnowledgeDocuments = async () => {
  const res = await apiClient.get('/knowledge/');
  return res.data;
};

export const createKnowledgeDocument = async (docData) => {
  const res = await apiClient.post('/knowledge/', docData);
  return res.data;
};

export const queryKnowledgeRAG = async (question) => {
  const res = await apiClient.post('/knowledge/query', { question });
  return res.data;
};
