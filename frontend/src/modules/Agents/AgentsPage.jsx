import React, { useState, useEffect, useCallback } from 'react';
import { agentsApi } from './api';
import IconSVG from '../../components/IconSVG';
import GenericListModal from '../../components/GenericListModal';
import ConfirmModal from '../../components/ConfirmModal';
import Pagination from '../../components/Pagination';
import LoginForm from '../Auth/components/LoginForm';
import { useToast } from '../../context/ToastContext';

const formatSeconds = (seconds) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    return `${h}h ${m}m`;
};

const STATE_LABEL = { available: 'Available', capacity_full: 'Capacity Full', cooldown: 'Flood-wait Cooldown', idle: 'Idle', banned: 'Banned' };
const STATE_BADGE = { available: 'active', capacity_full: 'pending', cooldown: 'pending', idle: 'inactive', banned: 'banned' };

const PAGE_SIZE = 25;

const AgentsPage = () => {
    const showToast = useToast();
    const [data, setData] = useState({ items: [], total: 0, page: 1 });
    const [page, setPage] = useState(1);
    const [loading, setLoading] = useState(false);
    const [actionLoading, setActionLoading] = useState({});
    const [showAddModal, setShowAddModal] = useState(false);
    const [historyModal, setHistoryModal] = useState({ isOpen: false, title: '', items: [] });
    const [confirmState, setConfirmState] = useState({ isOpen: false, agentId: null });

    const fetchAgents = useCallback((p = page) => {
        setLoading(true);
        agentsApi.getAll({ page: p, page_size: PAGE_SIZE })
            .then(res => setData(res.data))
            .catch(() => showToast('Failed to load agents', 'error'))
            .finally(() => setLoading(false));
    }, [page]);

    useEffect(() => { fetchAgents(page); }, [page]);

    const handleToggleActive = (id) => {
        setActionLoading(prev => ({ ...prev, [`active-${id}`]: true }));
        agentsApi.toggleActive(id)
            .then(() => { showToast('Agent status updated', 'success'); fetchAgents(page); })
            .catch(() => showToast('Failed to update agent', 'error'))
            .finally(() => setActionLoading(prev => ({ ...prev, [`active-${id}`]: false })));
    };

    const handleToggleBan = (id) => {
        setActionLoading(prev => ({ ...prev, [`ban-${id}`]: true }));
        agentsApi.toggleBan(id)
            .then(() => { showToast('Agent ban status updated', 'success'); fetchAgents(page); })
            .catch(() => showToast('Failed to update agent', 'error'))
            .finally(() => setActionLoading(prev => ({ ...prev, [`ban-${id}`]: false })));
    };

    const handleDelete = () => {
        const id = confirmState.agentId;
        setConfirmState({ isOpen: false, agentId: null });
        agentsApi.remove(id)
            .then(() => { showToast('Agent removed', 'success'); fetchAgents(page); })
            .catch(() => showToast('Failed to remove agent', 'error'));
    };

    const showHistory = (agent) => {
        agentsApi.getHistory(agent.id)
            .then(res => setHistoryModal({ isOpen: true, title: `History — ${agent.phone}`, items: res.data }))
            .catch(() => showToast('Failed to load history', 'error'));
    };

    const totalPages = Math.ceil(data.total / PAGE_SIZE);

    return (
        <div className="table-wrapper">
            <div className="table-header-row">
                <div className="table-title">Agents & Accounts</div>
                <button className="action-btn-primary" onClick={() => setShowAddModal(true)}>
                    <IconSVG name="Plus" size={14} /> Add Agent
                </button>
            </div>

            {loading ? (
                <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-secondary)' }}>Loading...</div>
            ) : (
                <table>
                    <thead>
                        <tr><th>ID</th><th>Phone</th><th>Status</th><th>Today's Adds</th><th>Active Time</th><th>Total Adds</th><th>Flags</th><th>Action</th></tr>
                    </thead>
                    <tbody>
                        {data.items.map(a => (
                            <tr key={a.id}>
                                <td>{a.id}</td>
                                <td>{a.phone}</td>
                                <td>
                                    <span className={`badge badge-${STATE_BADGE[a.state] || 'inactive'}`} title={a.pause_reason || ''}>
                                        {STATE_LABEL[a.state] || a.state}
                                    </span>
                                </td>
                                <td>{a.today_adds} / {a.daily_limit}</td>
                                <td>{formatSeconds(a.total_active_seconds || 0)}</td>
                                <td>{a.total_adds}</td>
                                <td>{a.needs_review && <span className="badge badge-banned">Needs Review</span>}</td>
                                <td>
                                    <div style={{ display: 'flex', gap: 6 }}>
                                        <button className="icon-btn-action" title="History" aria-label="View history" onClick={() => showHistory(a)}>
                                            <IconSVG name="ListOrdered" size={14} />
                                        </button>
                                        <button className="icon-btn-action" title={a.is_active ? 'Set Idle' : 'Set Active'} aria-label={a.is_active ? 'Set Idle' : 'Set Active'}
                                            disabled={actionLoading[`active-${a.id}`]}
                                            onClick={() => handleToggleActive(a.id)}>
                                            <IconSVG name={actionLoading[`active-${a.id}`] ? 'Loader' : 'Zap'} size={14} />
                                        </button>
                                        <button className="icon-btn-action ban" title={a.is_banned ? 'Unban' : 'Ban'} aria-label={a.is_banned ? 'Unban' : 'Ban'}
                                            disabled={actionLoading[`ban-${a.id}`]}
                                            onClick={() => handleToggleBan(a.id)}>
                                            <IconSVG name={actionLoading[`ban-${a.id}`] ? 'Loader' : 'Ban'} size={14} />
                                        </button>
                                        <button className="icon-btn-action delete" title="Remove" aria-label="Remove agent"
                                            onClick={() => setConfirmState({ isOpen: true, agentId: a.id })}>
                                            <IconSVG name="Trash2" size={14} />
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                        {data.items.length === 0 && (
                            <tr><td colSpan={8} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: 32 }}>No agents yet. Add one to get started.</td></tr>
                        )}
                    </tbody>
                </table>
            )}

            <Pagination page={page} totalPages={totalPages} total={data.total} onPage={setPage} />

            <ConfirmModal
                isOpen={confirmState.isOpen}
                message="Remove this agent permanently?"
                confirmLabel="Remove"
                onConfirm={handleDelete}
                onCancel={() => setConfirmState({ isOpen: false, agentId: null })}
            />

            {showAddModal && (
                <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3 className="modal-title">Add New Agent</h3>
                            <button className="icon-btn" aria-label="Close" onClick={() => setShowAddModal(false)}><IconSVG name="X" size={16} /></button>
                        </div>
                        <div className="modal-body">
                            <LoginForm onSuccess={() => { setShowAddModal(false); fetchAgents(page); }} />
                        </div>
                    </div>
                </div>
            )}

            <GenericListModal
                isOpen={historyModal.isOpen}
                onClose={() => setHistoryModal({ ...historyModal, isOpen: false })}
                title={historyModal.title}
                items={historyModal.items}
                columns={['Target Group', 'Username', 'Status', 'Fail Reason', 'Timestamp']}
            />
        </div>
    );
};
export default AgentsPage;
