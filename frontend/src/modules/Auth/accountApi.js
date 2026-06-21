// src/modules/Auth/accountApi.js
// Dashboard login/admin-claim/password-reset — distinct from authApi.js,
// which handles Telegram *agent* onboarding (/api/v1/auth), not dashboard login.
import client from '../../api/client';

export const accountApi = {
  login: (data) => client.post('/account/login', data),
  logout: () => client.post('/account/logout'),
  me: () => client.get('/account/me'),
  requestClaim: (email) => client.post('/account/claim-admin/request', { email }),
  completeClaim: (data) => client.post('/account/claim-admin/complete', data),
  forgotPassword: (email) => client.post('/account/forgot-password', { email }),
  resetPassword: (data) => client.post('/account/reset-password', data),
};
