import client from '../../api/client';

export const usersApi = {
    list: () => client.get('/account/users'),
    create: (data) => client.post('/account/users', data),
    update: (id, data) => client.patch(`/account/users/${id}`, data),
    remove: (id) => client.delete(`/account/users/${id}`),
    getRoles: () => client.get('/account/roles'),
    updateRolePermissions: (role, permissions) => client.post(`/account/roles/${role}/permissions`, { permissions }),
    getAuditLog: () => client.get('/account/audit-log'),
};
