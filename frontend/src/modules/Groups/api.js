import client from '../../api/client';

export const groupsApi = {
    getAll: () => client.get('/analytics/groups'),
    getMovements: (groupId) => client.get('/analytics/movements', { params: { group_id: groupId } }),
};
