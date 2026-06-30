import client from '../../api/client';

export const ordersApi = {
    getAll: (params) => client.get('/orders', { params }),
    create: (data) => client.post('/orders', data),
    action: (id, type) => client.post(`/orders/${id}/action`, { type }),
    remove: (id) => client.delete(`/orders/${id}`),
};