import React, { useState, useEffect, useCallback } from 'react';
import { groupsApi } from './api';
import GenericListModal from '../../components/GenericListModal';
import Pagination from '../../components/Pagination';
import IconSVG from '../../components/IconSVG';
import { useToast } from '../../context/ToastContext';

const PAGE_SIZE = 24;

const colorFor = (id) => {
    const palette = ['#f97316', '#3b82f6', '#10b981', '#8b5cf6', '#ef4444', '#06b6d4'];
    return palette[Math.abs(Number(id) % palette.length) || 0];
};

const GroupsPage = () => {
    const showToast = useToast();
    const [data, setData] = useState({ items: [], total: 0 });
    const [page, setPage] = useState(1);
    const [loading, setLoading] = useState(false);
    const [movements, setMovements] = useState({ isOpen: false, title: '', items: [] });

    const fetchGroups = useCallback((p) => {
        setLoading(true);
        groupsApi.getAll({ page: p, page_size: PAGE_SIZE })
            .then(res => setData(res.data))
            .catch(() => showToast('Failed to load groups', 'error'))
            .finally(() => setLoading(false));
    }, []);

    useEffect(() => { fetchGroups(page); }, [page]);

    const showMovements = (group) => {
        groupsApi.getMovements(group.id)
            .then(res => setMovements({ isOpen: true, title: `Member Movements — ${group.title}`, items: res.data }))
            .catch(() => showToast('Failed to load movements', 'error'));
    };

    const totalPages = Math.ceil(data.total / PAGE_SIZE);

    if (!loading && data.items.length === 0 && data.total === 0) {
        return <div className="empty-state">No groups tracked yet. Groups appear here once used as an Order target or source.</div>;
    }

    return (
        <div>
            {loading ? (
                <div style={{ textAlign: 'center', padding: 60, color: 'var(--text-secondary)' }}>Loading...</div>
            ) : (
                <div className="grid-container">
                    {data.items.map(g => (
                        <div className="group-card" key={g.id}>
                            <div className="group-icon-box" style={{ backgroundColor: colorFor(g.id) }}>
                                {(g.title || '?').charAt(0).toUpperCase()}
                            </div>
                            <h4 className="group-title">{g.title}</h4>
                            <div className="group-type">{g.type || 'group'}{g.is_lenzit_admin ? ' · Admin' : ''}</div>
                            <div className="group-stats">
                                <div className="stat-item">
                                    <span className="stat-val">{g.member_count ?? 0}</span>
                                    <span className="stat-lbl">Members</span>
                                </div>
                                <div className="stat-item">
                                    <span className="stat-val">{g.username ? `@${g.username}` : '-'}</span>
                                    <span className="stat-lbl">Username</span>
                                </div>
                            </div>
                            <button className="card-btn" onClick={() => showMovements(g)}>
                                <IconSVG name="RefreshCw" size={14} /> View Movements
                            </button>
                        </div>
                    ))}
                </div>
            )}

            <Pagination page={page} totalPages={totalPages} total={data.total} onPage={setPage} />

            <GenericListModal
                isOpen={movements.isOpen}
                onClose={() => setMovements({ ...movements, isOpen: false })}
                title={movements.title}
                items={movements.items}
                columns={['Username', 'Status', 'Joined At', 'Left At']}
            />
        </div>
    );
};
export default GroupsPage;
