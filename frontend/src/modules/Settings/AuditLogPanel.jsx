import React, { useState, useEffect } from 'react';
import { usersApi } from './usersApi';
import IconSVG from '../../components/IconSVG';

const PAGE_SIZE = 25;
const formatDate = (iso) => iso ? new Date(iso).toLocaleString() : '—';

const AuditLogPanel = () => {
    const [entries, setEntries] = useState([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [actions, setActions] = useState([]);

    const [actorFilter, setActorFilter] = useState('');
    const [actionFilter, setActionFilter] = useState('');
    const [dateFrom, setDateFrom] = useState('');
    const [dateTo, setDateTo] = useState('');

    const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

    const fetchLog = (targetPage = page) => {
        usersApi.getAuditLog({
            actor: actorFilter || undefined,
            action: actionFilter || undefined,
            date_from: dateFrom || undefined,
            date_to: dateTo || undefined,
            page: targetPage,
            page_size: PAGE_SIZE,
        }).then(res => {
            setEntries(res.data.items);
            setTotal(res.data.total);
            setPage(targetPage);
        }).catch(console.error);
    };

    useEffect(() => {
        usersApi.getAuditLogActions().then(res => setActions(res.data.actions)).catch(console.error);
    }, []);

    useEffect(() => { fetchLog(1); }, []); // eslint-disable-line react-hooks/exhaustive-deps

    const handleApplyFilters = () => fetchLog(1);

    const handleClearFilters = () => {
        setActorFilter(''); setActionFilter(''); setDateFrom(''); setDateTo('');
        usersApi.getAuditLog({ page: 1, page_size: PAGE_SIZE }).then(res => {
            setEntries(res.data.items);
            setTotal(res.data.total);
            setPage(1);
        }).catch(console.error);
    };

    return (
        <div className="table-wrapper">
            <div className="table-header-row">
                <div className="table-title">Audit Log</div>
                <button className="icon-btn-action" title="Refresh" onClick={() => fetchLog(page)}>
                    <IconSVG name="RefreshCw" size={14} />
                </button>
            </div>

            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16, alignItems: 'flex-end' }}>
                <div className="input-group" style={{ marginBottom: 0 }}>
                    <label className="input-label">Actor</label>
                    <input className="input-field" placeholder="username" value={actorFilter} onChange={e => setActorFilter(e.target.value)} style={{ width: 140 }} />
                </div>
                <div className="input-group" style={{ marginBottom: 0 }}>
                    <label className="input-label">Action</label>
                    <select className="input-field" value={actionFilter} onChange={e => setActionFilter(e.target.value)} style={{ width: 170 }}>
                        <option value="">All actions</option>
                        {actions.map(a => <option key={a} value={a}>{a}</option>)}
                    </select>
                </div>
                <div className="input-group" style={{ marginBottom: 0 }}>
                    <label className="input-label">From</label>
                    <input className="input-field" type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)} />
                </div>
                <div className="input-group" style={{ marginBottom: 0 }}>
                    <label className="input-label">To</label>
                    <input className="input-field" type="date" value={dateTo} onChange={e => setDateTo(e.target.value)} />
                </div>
                <button className="action-btn-primary" onClick={handleApplyFilters}>Filter</button>
                <button className="icon-btn-action" onClick={handleClearFilters}>Clear</button>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>Timestamp</th><th>Actor</th><th>Action</th><th>Target</th><th>Details</th>
                    </tr>
                </thead>
                <tbody>
                    {entries.map(e => (
                        <tr key={e.id}>
                            <td style={{ fontSize: 12 }}>{formatDate(e.timestamp)}</td>
                            <td>{e.actor_username}</td>
                            <td>{e.action}</td>
                            <td>{e.target || '—'}</td>
                            <td style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{e.details || ''}</td>
                        </tr>
                    ))}
                    {entries.length === 0 && (
                        <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>No matching actions.</td></tr>
                    )}
                </tbody>
            </table>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 16 }}>
                <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                    {total === 0 ? '0 results' : `Page ${page} of ${totalPages} — ${total} total`}
                </span>
                <div style={{ display: 'flex', gap: 8 }}>
                    <button className="icon-btn-action" disabled={page <= 1} onClick={() => fetchLog(page - 1)}>
                        <IconSVG name="ChevronLeft" size={14} />
                    </button>
                    <button className="icon-btn-action" disabled={page >= totalPages} onClick={() => fetchLog(page + 1)}>
                        <IconSVG name="ChevronRight" size={14} />
                    </button>
                </div>
            </div>
        </div>
    );
};

export default AuditLogPanel;
