import React, { useState, useEffect } from 'react';
import { usersApi } from './usersApi';
import IconSVG from '../../components/IconSVG';

const formatDate = (iso) => iso ? new Date(iso).toLocaleString() : '—';

const AuditLogPanel = () => {
    const [entries, setEntries] = useState([]);

    const fetchLog = () => usersApi.getAuditLog().then(res => setEntries(res.data)).catch(console.error);
    useEffect(() => { fetchLog(); }, []);

    return (
        <div className="table-wrapper">
            <div className="table-header-row">
                <div className="table-title">Audit Log</div>
                <button className="icon-btn-action" title="Refresh" onClick={fetchLog}>
                    <IconSVG name="RefreshCw" size={14} />
                </button>
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
                        <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>No actions logged yet.</td></tr>
                    )}
                </tbody>
            </table>
        </div>
    );
};

export default AuditLogPanel;
