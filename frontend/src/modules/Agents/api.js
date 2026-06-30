import client from '../../api/client';

export const agentsApi = {
    getAll: (params) => client.get('/agents/', { params }),
    toggleActive: (id) => client.patch(`/agents/${id}/toggle-active`),
    toggleBan: (id) => client.patch(`/agents/${id}/toggle-ban`),
    remove: (id) => client.delete(`/agents/${id}`),
    getHistory: (id) => client.get(`/agents/${id}/history`),
};