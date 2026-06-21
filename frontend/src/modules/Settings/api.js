import client from '../../api/client';

export const settingsApi = {
    getAll: () => client.get('/analytics/settings'),
    update: (key, value) => client.post('/analytics/settings', { key, value }),
};
