import client from '../../api/client';

export const agentsApi = {
    getAll: () => client.get('/analytics/summary').then(res => ({ data: res.data.agents })), // با توجه به کنترلر بک اند
    toggleActive: (id) => client.patch(`/agents/${id}/toggle-active`),
    toggleBan: (id) => client.patch(`/agents/${id}/toggle-ban`),
    remove: (id) => client.delete(`/agents/${id}`),
    getHistory: (id) => client.get(`/agents/${id}/history`),
};