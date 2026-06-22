import React, { useState, useEffect } from 'react';
import { agentsApi } from './api';
import IconSVG from '../../components/IconSVG';
import GenericListModal from '../../components/GenericListModal';
import LoginForm from '../Auth/components/LoginForm';

// تابع کمکی فرمت زمان
const formatSeconds = (seconds) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    return `${h}h ${m}m`;
};

const STATE_LABEL = {
    available: 'Available',
    capacity_full: 'Capacity Full',
    cooldown: 'Flood-wait Cooldown',
    idle: 'Idle',
    banned: 'Banned',
};
const STATE_BADGE = {
    available: 'active',
    capacity_full: 'pending',
    cooldown: 'pending',
    idle: 'inactive',
    banned: 'banned',
};

const AgentsPage = () => {
    const [agents, setAgents] = useState([]);
    const [showAddModal, setShowAddModal] = useState(false);
    const [historyModal, setHistoryModal] = useState({ isOpen: false, title: '', items: [] });

    const fetchAgents = () => {
        agentsApi.getAll().then(res => setAgents(res.data)).catch(console.error);
    };

    useEffect(() => fetchAgents(), []);

    const handleToggleActive = (id) => agentsApi.toggleActive(id).then(fetchAgents).catch(console.error);
    const handleToggleBan = (id) => agentsApi.toggleBan(id).then(fetchAgents).catch(console.error);
    const handleDelete = (id) => {
        if (!window.confirm('Remove this agent permanently?')) return;
        agentsApi.remove(id).then(fetchAgents).catch(console.error);
    };
    const showHistory = (agent) => {
        agentsApi.getHistory(agent.id).then(res => {
            setHistoryModal({ isOpen: true, title: `History — ${agent.phone}`, items: res.data });
        }).catch(console.error);
    };

    return (
        <div className="table-wrapper">
            <div className="table-header-row">
                <div className="table-title">Agents & Accounts</div>
                <button className="action-btn-primary" onClick={() => setShowAddModal(true)}>
                    <IconSVG name="Plus" size={14} /> Add Agent
                </button>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>ID</th><th>Phone</th><th>Status</th><th>Today's Adds</th><th>Active Time</th><th>Total Adds</th><th>Flags</th><th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    {agents.map(a => (
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
                                    <button className="icon-btn-action" title="History" onClick={() => showHistory(a)}>
                                        <IconSVG name="ListOrdered" size={14} />
                                    </button>
                                    <button className="icon-btn-action" title={a.is_active ? 'Set Idle' : 'Set Active'} onClick={() => handleToggleActive(a.id)}>
                                        <IconSVG name="Zap" size={14} />
                                    </button>
                                    <button className="icon-btn-action ban" title={a.is_banned ? 'Unban' : 'Ban'} onClick={() => handleToggleBan(a.id)}>
                                        <IconSVG name="Ban" size={14} />
                                    </button>
                                    <button className="icon-btn-action delete" title="Remove" onClick={() => handleDelete(a.id)}>
                                        <IconSVG name="Trash2" size={14} />
                                    </button>
                                </div>
                            </td>
                        </tr>
                    ))}
                    {agents.length === 0 && (
                        <tr><td colSpan={8} style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>No agents yet. Add one to get started.</td></tr>
                    )}
                </tbody>
            </table>

            {showAddModal && (
                <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3 className="modal-title">Add New Agent</h3>
                            <button className="icon-btn" onClick={() => setShowAddModal(false)}><IconSVG name="X" size={16} /></button>
                        </div>
                        <div className="modal-body">
                            <LoginForm onSuccess={() => { setShowAddModal(false); fetchAgents(); }} />
                        </div>
                    </div>
                </div>
            )}

            <GenericListModal
                isOpen={historyModal.isOpen}
                onClose={() => setHistoryModal({ ...historyModal, isOpen: false })}
                title={historyModal.title}
                items={historyModal.items}
                columns={["Target Group", "Username", "Status", "Fail Reason", "Timestamp"]}
            />
        </div>
    );
};
export default AgentsPage;
