import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { dashboardApi } from './api';
import { ordersApi } from '../Orders/api';
import { agentsApi } from '../Agents/api';
import IconSVG from '../../components/IconSVG';
import GenericListModal from '../../components/GenericListModal';

const KpiCard = ({ icon, color, bg, value, label }) => (
    <div className="kpi-card">
        <div className="kpi-icon" style={{ backgroundColor: bg, color: color }}>
            <IconSVG name={icon} size={22} />
        </div>
        <div>
            <div className="kpi-value">{value}</div>
            <div className="kpi-label">{label}</div>
        </div>
    </div>
);

const formatCountdown = (isoString) => {
    if (!isoString) return null;
    const diffMs = new Date(isoString) - new Date();
    if (diffMs <= 0) return 'now';
    const h = Math.floor(diffMs / 3600000);
    const m = Math.floor((diffMs % 3600000) / 60000);
    return `${h}h ${m}m`;
};

const AGENT_STATE_LABEL = {
    available: 'Available',
    capacity_full: 'Capacity Full',
    cooldown: 'Flood-wait Cooldown',
    idle: 'Idle',
    banned: 'Banned',
};
const AGENT_STATE_BADGE = {
    available: 'active',
    capacity_full: 'pending',
    cooldown: 'pending',
    idle: 'inactive',
    banned: 'banned',
};

const DashboardPage = () => {
    const [summary, setSummary] = useState(null);
    const [capacity, setCapacity] = useState(null);
    const [loading, setLoading] = useState(true);
    const [historyModal, setHistoryModal] = useState({ isOpen: false, title: '', items: [] });

    const fetchAll = () => {
        Promise.all([dashboardApi.getSummary(), dashboardApi.getCapacity()])
            .then(([summaryRes, capacityRes]) => {
                setSummary(summaryRes.data);
                setCapacity(capacityRes.data);
            })
            .catch(console.error)
            .finally(() => setLoading(false));
    };

    useEffect(() => {
        fetchAll();
        const interval = setInterval(fetchAll, 15000); // live refresh every 15s
        return () => clearInterval(interval);
    }, []);

    const handleOrderAction = (id, type) => ordersApi.action(id, type).then(fetchAll);

    const showAgentHistory = (agent) => {
        agentsApi.getHistory(agent.id).then(res => {
            setHistoryModal({
                isOpen: true,
                title: `History — ${agent.phone}`,
                items: res.data,
            });
        }).catch(console.error);
    };

    if (loading) return <div className="empty-state">Loading dashboard...</div>;
    if (!summary || !capacity) return <div className="empty-state">Could not load dashboard data.</div>;

    const t = summary.totals || {};

    return (
        <div>
            <div className="kpi-grid">
                <KpiCard icon="Zap" color="var(--primary)" bg="var(--primary-light)" value={`${t.active_agents ?? 0}/${t.total_agents ?? 0}`} label="Active Agents" />
                <KpiCard icon="ListOrdered" color="var(--secondary)" bg="var(--secondary-light)" value={t.active_orders ?? 0} label="Active Orders" />
                <KpiCard icon="Users" color="var(--success)" bg="var(--success-bg)" value={t.total_members ?? 0} label="Members Scraped" />
                <KpiCard icon="TrendingUp" color="#b45309" bg="var(--warning-bg)" value={t.adds_today ?? 0} label="Adds Today" />
                <KpiCard icon="Briefcase" color="var(--text-secondary)" bg="var(--neutral-bg)" value={t.total_groups ?? 0} label="Groups Tracked" />
                <KpiCard icon="CheckCircle" color="var(--success)" bg="var(--success-bg)" value={t.finished_orders ?? 0} label="Orders Finished" />
            </div>

            {/* Q2: capacity planning */}
            <div className="chart-card">
                <h3 className="chart-card-title">Capacity Planning</h3>
                <div className="kpi-grid" style={{ marginBottom: 0 }}>
                    <KpiCard icon="Users" color="var(--secondary)" bg="var(--secondary-light)" value={capacity.eligible_agent_count} label="Agents Available Right Now" />
                    <KpiCard icon="ListOrdered" color="var(--primary)" bg="var(--primary-light)" value={capacity.total_remaining} label="Members Left To Add (All Orders)" />
                    <KpiCard icon="TrendingUp" color="#b45309" bg="var(--warning-bg)" value={capacity.agents_needed_for_one_day_clear} label="Agents Needed To Clear Backlog In 1 Day" />
                    <KpiCard icon="CheckCircle" color="var(--success)" bg="var(--success-bg)"
                        value={capacity.days_to_clear_with_current_agents === null ? '—' : `${capacity.days_to_clear_with_current_agents}d`}
                        label="ETA To Clear Backlog At Today's Pace" />
                </div>
            </div>

            {/* Q1: per-order status, blocker, ETA, quick actions */}
            <div className="table-wrapper" style={{ marginBottom: 28 }}>
                <div className="table-header-row">
                    <div className="table-title">Active Orders</div>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>ID</th><th>Target</th><th>Progress</th><th>Status</th><th>Blocking Reason</th><th>ETA (best/worst)</th><th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {capacity.orders.map(o => (
                            <tr key={o.id}>
                                <td>#{o.id}</td>
                                <td>{o.target_group}</td>
                                <td>
                                    <span className="progress-text">{o.current_count} / {o.desired_count} ({o.progress_percent}%)</span>
                                    <div className="progress-container">
                                        <div className="progress-fill" style={{ width: `${Math.min(o.progress_percent, 100)}%` }} />
                                    </div>
                                </td>
                                <td><span className={`badge badge-${o.status}`}>{o.status}</span></td>
                                <td style={{ fontSize: 12, color: o.blocking_reason === 'Running normally' ? 'var(--success)' : 'var(--text-secondary)' }}>{o.blocking_reason}</td>
                                <td>{o.best_case_days}d / {o.worst_case_days}d</td>
                                <td>
                                    <div style={{ display: 'flex', gap: 6 }}>
                                        {o.status === 'in_progress' && (
                                            <button className="icon-btn-action pause" title="Pause" onClick={() => handleOrderAction(o.id, 'pause')}><IconSVG name="Pause" size={14} /></button>
                                        )}
                                        {(o.status === 'paused' || o.status === 'pending_agent') && (
                                            <button className="icon-btn-action resume" title="Resume" onClick={() => handleOrderAction(o.id, 'resume')}><IconSVG name="Play" size={14} /></button>
                                        )}
                                        <button className="icon-btn-action cancel" title="Cancel" onClick={() => handleOrderAction(o.id, 'cancel')}><IconSVG name="Square" size={14} /></button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                        {capacity.orders.length === 0 && (
                            <tr><td colSpan={7} style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>No active orders right now.</td></tr>
                        )}
                    </tbody>
                </table>
            </div>

            {/* Q3: per-agent Telegram capacity */}
            <div className="table-wrapper" style={{ marginBottom: 28 }}>
                <div className="table-header-row">
                    <div className="table-title">Agent Capacity</div>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>Phone</th><th>Status</th><th>Today's Adds</th><th>Capacity Resets In</th><th>Flags</th><th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {(summary.agents || []).map(a => (
                            <tr key={a.id}>
                                <td>{a.phone}</td>
                                <td><span className={`badge badge-${AGENT_STATE_BADGE[a.state] || 'inactive'}`}>{AGENT_STATE_LABEL[a.state] || a.state}</span></td>
                                <td>{a.today_adds} / {a.daily_limit}</td>
                                <td>{a.resets_at ? formatCountdown(a.resets_at) : '—'}</td>
                                <td>{a.needs_review && <span className="badge badge-banned">Needs Review</span>}</td>
                                <td>
                                    <button className="icon-btn-action" title="History" onClick={() => showAgentHistory(a)}>
                                        <IconSVG name="ListOrdered" size={14} />
                                    </button>
                                </td>
                            </tr>
                        ))}
                        {(!summary.agents || summary.agents.length === 0) && (
                            <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>No agents yet.</td></tr>
                        )}
                    </tbody>
                </table>
            </div>

            <div className="chart-card">
                <h3 className="chart-card-title">Adds — Last 7 Days</h3>
                <ResponsiveContainer width="100%" height={260}>
                    <LineChart data={summary.trend || []}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                        <XAxis dataKey="date" tick={{ fontSize: 12, fill: 'var(--text-secondary)' }} />
                        <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: 'var(--text-secondary)' }} />
                        <Tooltip />
                        <Line type="monotone" dataKey="adds" stroke="var(--primary)" strokeWidth={2.5} dot={{ r: 3 }} />
                    </LineChart>
                </ResponsiveContainer>
            </div>

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

export default DashboardPage;
