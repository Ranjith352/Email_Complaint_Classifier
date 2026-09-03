import apiClient from './client';

export const getNotifications = async (unreadOnly = false) => {
  const res = await apiClient.get(`/notifications/?unread_only=${unreadOnly}`);
  return res.data;
};

export const markNotificationAsRead = async (id) => {
  const res = await apiClient.post(`/notifications/${id}/read`);
  return res.data;
};
