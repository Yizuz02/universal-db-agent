import axios from 'axios';

const api = axios.create({
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const original = err.config;
    if (err.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refresh = localStorage.getItem('refresh_token');
      if (refresh) {
        try {
          const { data } = await axios.post('/api/token/refresh/', { refresh });
          localStorage.setItem('access_token', data.access);
          original.headers.Authorization = `Bearer ${data.access}`;
          return api(original);
        } catch {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(err);
  }
);

export default api;

// Auth
export const loginApi = (username, password) =>
  api.post('/api/token/', { username, password });

// Preferences
export const getPreferences = () =>
  api.get('/settings/api/preferences/');
export const updatePreferences = (data) =>
  api.put('/settings/api/preferences/', data);

// LLM Credentials
export const getCredentials = () =>
  api.get('/settings/api/credentials/');
export const createCredential = (data) =>
  api.post('/settings/api/credentials/', data);
export const updateCredential = (id, data) =>
  api.put(`/settings/api/credentials/${id}/`, data);
export const deleteCredential = (id) =>
  api.delete(`/settings/api/credentials/${id}/`);
export const activateCredential = (id) =>
  api.put('/settings/api/credentials/activate/', { credential_id: id });
export const getCredentialOptions = () =>
  api.get('/settings/api/credentials/options/');

// Conversations
export const getConversations = () =>
  api.get('/api/conversations/');
export const createConversation = (title) =>
  api.post('/api/conversations/', title ? { title } : {});
export const getConversation = (id) =>
  api.get(`/api/conversations/${id}/`);
export const sendMessage = (id, content) =>
  api.post(`/api/conversations/${id}/messages/`, { content });
export const updateConversationTitle = (id, title) =>
  api.patch(`/api/conversations/${id}/`, { title });
export const deleteConversation = (id) =>
  api.delete(`/api/conversations/${id}/`);

// Files
export const getFilePreview = (fileId) =>
  api.get(`/api/files/${fileId}/preview/`);

export const downloadFile = async (fileId) => {
  const token = localStorage.getItem('access_token');
  const response = await fetch(`/api/files/${fileId}/download/`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error('Download failed');
  const blob = await response.blob();
  const disposition = response.headers.get('Content-Disposition');
  let filename = 'download';
  if (disposition) {
    const match = disposition.match(/filename="?(.+?)"?$/);
    if (match) filename = match[1];
  }
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};
