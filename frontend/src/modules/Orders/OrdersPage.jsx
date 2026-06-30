import React, { useState, useEffect, useCallback } from 'react';
import { ordersApi } from './api';
import CreateOrderModal from './components/CreateOrderModal';
import GenericListModal from '../../components/GenericListModal';
import ConfirmModal from '../../components/ConfirmModal';
import Pagination from '../../components/Pagination';
import IconSVG from '../../components/IconSVG';
import { useToast } from '../../context/ToastContext';

const PAGE_SIZE = 25;

const OrdersPage = () => {
    const showToast = useToast();
    const [data, setData] = useState({ items: [], total: 0, page: 1 });
    const [page, setPage] = useState(1);
    const [loading, setLoading] = useState(false);
    const [actionLoading, setActionLoading] = useState({});
    const [isCreateOpen, setCreateOpen] = useState(false);
    const [popupData, setPopupData] = useState({ isOpen: false, title: '', items: [], columns: [] });
    const [confirmState, setConfirmState] = useState({ isOpen: false, orderId: null });

    const fetchOrders = useCallback((p = page) => {
        setLoading(true);
        ordersApi.getAll({ page: p, page_size: PAGE_SIZE })
            .then(res => setData(res.data))
            .catch(() => showToast('Failed to load orders', 'error'))
            .finally(() => setLoading(false));
    }, [page]);

    useEffect(() => { fetchOrders(page); }, [page]);

    const handleAction = (id, type) => {
        setActionLoading(prev => ({ ...prev, [`${id}-${type}`]: true }));
        ordersApi.action(id, type)
            .then(() => { showToast(`Order ${type}d`, 'success'); fetchOrders(page); })
            .catch(err => showToast(err.response?.data?.detail || `Failed to ${type} order`, 'error'))
            .finally(() => setActionLoading(prev => ({ ...prev, [`${id}-${type}`]: false })));
    };

    const handleDelete = () => {
        const id = confirmState.orderId;
        setConfirmState({ isOpen: false, orderId: null });
        setActionLoading(prev => ({ ...prev, [`${id}-delete`]: true }));
        ordersApi.remove(id)
            .then(() => { showToast('Order deleted', 'success'); fetchOrders(page); })
            .catch(err => showToast(err.response?.data?.detail || 'Could not delete order', 'error'))
            .finally(() => setActionLoading(prev => ({ ...prev, [`${id}-delete`]: false })));
    };

    const totalPages = Math.ceil(data.total / PAGE_SIZE);

    return (
        <div className="table-wrapper">
            <div className="table-header-row">
                <div className="table-title">Orders Management</div>
                <button className="action-btn-primary" onClick={() => setCreateOpen(true)}>
                    <IconSVG name="Plus" /> Add Order
                </button>
            </div>

            {loading ? (
                <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-secondary)' }}>Loading...</div>
            ) : (
                <table>
                    <thead>
                        <tr><th>ID</th><th>Target</th><th>Sources</th><th>Progress</th><th>Status</th><th>Action</th></tr>
                    </thead>
                    <tbody>
                        {data.items.map(o => (
                            <tr key={o.id}>
                                <td>#{o.id}</td>
                                <td>{o.target_group}</td>
                                <td>
                                    <button className="link-text" onClick={() => setPopupData({ isOpen: true, title: `Sources for Order #${o.id}`, items: o.sources || [], columns: ['ID', 'Title', 'Link'] })}>
                                        {o.sources?.length || 0} Groups
                                    </button>
                                </td>
                                <td>
                                    <span className="progress-text">{o.current_count} / {o.desired_count} ({o.progress_percent ?? 0}%)</span>
                                    <div className="progress-container">
                                        <div className="progress-fill" style={{ width: `${Math.min(o.progress_percent ?? 0, 100)}%` }} />
                                    </div>
                                </td>
                                <td><span className={`badge badge-${o.status}`}>{o.status}</span></td>
                                <td>
                                    <div style={{ display: 'flex', gap: 6 }}>
                                        {o.status === 'in_progress' && (
                                            <button className="icon-btn-action pause" title="Pause" aria-label="Pause order"
                                                disabled={actionLoading[`${o.id}-pause`]}
                                                onClick={() => handleAction(o.id, 'pause')}>
                                                <IconSVG name={actionLoading[`${o.id}-pause`] ? 'Loader' : 'Pause'} size={14} />
                                            </button>
                                        )}
                                        {(o.status === 'paused' || o.status === 'pending_agent') && (
                                            <button className="icon-btn-action resume" title="Resume" aria-label="Resume order"
                                                disabled={actionLoading[`${o.id}-resume`]}
                                                onClick={() => handleAction(o.id, 'resume')}>
                                                <IconSVG name={actionLoading[`${o.id}-resume`] ? 'Loader' : 'Play'} size={14} />
                                            </button>
                                        )}
                                        {o.status !== 'cancelled' && o.status !== 'finished' && (
                                            <button className="icon-btn-action cancel" title="Cancel" aria-label="Cancel order"
                                                disabled={actionLoading[`${o.id}-cancel`]}
                                                onClick={() => handleAction(o.id, 'cancel')}>
                                                <IconSVG name={actionLoading[`${o.id}-cancel`] ? 'Loader' : 'Square'} size={14} />
                                            </button>
                                        )}
                                        {(o.status === 'cancelled' || o.status === 'finished') && (
                                            <button className="icon-btn-action delete" title="Delete" aria-label="Delete order"
                                                disabled={actionLoading[`${o.id}-delete`]}
                                                onClick={() => setConfirmState({ isOpen: true, orderId: o.id })}>
                                                <IconSVG name="Trash2" size={14} />
                                            </button>
                                        )}
                                    </div>
                                </td>
                            </tr>
                        ))}
                        {data.items.length === 0 && (
                            <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: 32 }}>No orders yet.</td></tr>
                        )}
                    </tbody>
                </table>
            )}

            <Pagination page={page} totalPages={totalPages} total={data.total} onPage={setPage} />

            <ConfirmModal
                isOpen={confirmState.isOpen}
                message={`Delete order #${confirmState.orderId}? This cannot be undone.`}
                confirmLabel="Delete"
                onConfirm={handleDelete}
                onCancel={() => setConfirmState({ isOpen: false, orderId: null })}
            />
            <GenericListModal isOpen={popupData.isOpen} onClose={() => setPopupData({ ...popupData, isOpen: false })} title={popupData.title} items={popupData.items} columns={popupData.columns} />
            <CreateOrderModal isOpen={isCreateOpen} onClose={() => setCreateOpen(false)} onRefresh={() => fetchOrders(page)} />
        </div>
    );
};
export default OrdersPage;
