import React, { useState, useEffect, useMemo } from 'react';
import { membersApi } from './api';
import IconSVG from '../../components/IconSVG';

const MembersPage = () => {
    const [members, setMembers] = useState([]);
    const [search, setSearch] = useState('');

    useEffect(() => {
        membersApi.getAll().then(res => setMembers(res.data)).catch(console.error);
    }, []);

    const filtered = useMemo(() => {
        if (!search.trim()) return members;
        const q = search.toLowerCase();
        return members.filter(m =>
            (m.username || '').toLowerCase().includes(q) ||
            (m.first_name || '').toLowerCase().includes(q) ||
            String(m.user_id).includes(q)
        );
    }, [members, search]);

    return (
        <div className="table-wrapper">
            <div className="table-header-row">
                <div className="table-title">Scraped Members ({filtered.length})</div>
                <div className="table-search">
                    <IconSVG name="Search" size={16} />
                    <input placeholder="Search username, name or ID..." value={search} onChange={e => setSearch(e.target.value)} />
                </div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>User ID</th><th>Username</th><th>First Name</th><th>Status</th><th>Quality Score</th><th>Flags</th>
                    </tr>
                </thead>
                <tbody>
                    {filtered.map(m => (
                        <tr key={m.user_id}>
                            <td>{m.user_id}</td>
                            <td>{m.username ? `@${m.username}` : '-'}</td>
                            <td>{m.first_name || '-'}</td>
                            <td><span className={`badge badge-${m.status === 'online' ? 'active' : 'inactive'}`}>{m.status}</span></td>
                            <td>
                                <span className="stat-val">{m.quality_score}</span>
                                <div className="progress-container" style={{ width: 70 }}>
                                    <div className="progress-fill" style={{ width: `${Math.min(m.quality_score, 100)}%` }} />
                                </div>
                            </td>
                            <td>
                                {m.is_premium && <span className="badge badge-active" style={{ marginRight: 4 }}>Premium</span>}
                                {m.is_bot && <span className="badge badge-banned">Bot</span>}
                            </td>
                        </tr>
                    ))}
                    {filtered.length === 0 && (
                        <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>No members scraped yet.</td></tr>
                    )}
                </tbody>
            </table>
        </div>
    );
};

export default MembersPage;
