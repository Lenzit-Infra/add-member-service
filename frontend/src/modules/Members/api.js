import client from '../../api/client';

export const membersApi = {
    getAll: (params) => client.get('/analytics/members', { params }),
};
