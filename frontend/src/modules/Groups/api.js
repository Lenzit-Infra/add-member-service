import client from '../../api/client';

export const groupsApi = {
    getAll: (params) => client.get('/analytics/groups', { params }),
    getMovements: (groupId) => client.get('/analytics/movements', { params: { group_id: groupId } }),
};
