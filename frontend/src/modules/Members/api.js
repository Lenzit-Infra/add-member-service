import client from '../../api/client';

export const membersApi = {
    getAll: () => client.get('/analytics/members'),
};
