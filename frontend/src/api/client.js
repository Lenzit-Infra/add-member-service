// src/api/client.js
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:4747/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // send/receive the httpOnly refresh-token cookie
});

let accessToken = null;
let onAuthFailure = () => {};

export const setAccessToken = (token) => { accessToken = token; };
export const setOnAuthFailure = (fn) => { onAuthFailure = fn; };

apiClient.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

let refreshPromise = null;

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { response, config } = error;
    const isAuthEndpoint = config?.url?.includes('/account/');

    if (response?.status === 401 && !isAuthEndpoint && !config._retried) {
      config._retried = true;
      try {
        if (!refreshPromise) {
          refreshPromise = axios
            .post(`${API_BASE_URL}/account/refresh`, {}, { withCredentials: true })
            .finally(() => { refreshPromise = null; });
        }
        const refreshRes = await refreshPromise;
        setAccessToken(refreshRes.data.access_token);
        config.headers.Authorization = `Bearer ${refreshRes.data.access_token}`;
        return apiClient.request(config);
      } catch (refreshError) {
        setAccessToken(null);
        onAuthFailure();
        return Promise.reject(error);
      }
    }

    console.error('API Error:', response?.data || error.message);
    return Promise.reject(error);
  }
);

export default apiClient;
