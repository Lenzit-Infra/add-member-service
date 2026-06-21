import client from '../../api/client';

export const dashboardApi = {
    getSummary: () => client.get('/analytics/summary'),
    getCapacity: () => client.get('/analytics/capacity'),
};
