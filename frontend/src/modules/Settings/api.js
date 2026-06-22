import client from '../../api/client';

export const settingsApi = {
    getAll: () => client.get('/analytics/settings'),
    update: (key, value) => client.post('/analytics/settings', { key, value }),
    getAdminEmails: () => client.get('/analytics/admin-emails'),
    addAdminEmail: (email) => client.post('/analytics/admin-emails', { email }),
    removeAdminEmail: (email) => client.delete(`/analytics/admin-emails/${encodeURIComponent(email)}`),
};
