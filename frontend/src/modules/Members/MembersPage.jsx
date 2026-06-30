import React, { useState, useEffect, useCallback } from 'react';
import { membersApi } from './api';
import IconSVG from '../../components/IconSVG';
import Pagination from '../../components/Pagination';
import { useToast } from '../../context/ToastContext';

const PAGE_SIZE = 50;

const MembersPage = () => {
    const showToast = useToast();
    const [data, setData] = useState({ items: [], total: 0 });
    const [page, setPage] = useState(1);
    const [search, setSearch] = useState('');
    const [searchInput, setSearchInput] = useState('');
    const [loading, setLoading] = useState(false);

    const fetchMembers = useCallback((p, q) => {
        setLoading(true);
        membersApi.getAll({ page: p, page_size: PAGE_SIZE, search: q })
            .then(res => setData(res.data))
            .catch(() => showToast('Failed to load members', 'error'))
            .finally(() => setLoading(false));
    }, []);

    useEffect(() => { fetchMembers(page, search); }, [page, search]);

    const handleSearch = (e) => {
        e.preventDefault();
        setPage(1);
        setSearch(searchInput);
    };

    const totalPages = Math.ceil(data.total / PAGE_SIZE);

    return (
        <div className="table-wrapper">
            <div className="table-header-row">
                <div className="table-title">Scraped Members ({data.total})</div>
                <form className="table-search" onSubmit={handleSearch} style={{ display: 'flex', gap: 8 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <IconSVG name="Search" size={16} />
                        <input
                            placeholder="Search username or name…"
                            value={searchInput}
                            onChange={e => setSearchInput(e.target.value)}
                        />
                    </div>
                    <button type="submit" className="action-btn-primary" style={{ padding: '6px 12px' }}>Search</button>
                    {search && <button type="button" className="btn-secondary" style={{ padding: '6px 12px' }} onClick={() => { setSearchInput(''); setSearch(''); setPage(1); }}>Clear</button>}
                </form>
            </div>

            {loading ? (
                <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-secondary)' }}>Loading...</div>
            ) : (
                <table>
                    <thead>
                        <tr><th>User ID</th><th>Username</th><th>First Name</th><th>Status</th><th>Quality Score</th><th>Flags</th></tr>
                    </thead>
                    <tbody>
                        {data.items.map(m => (
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
                        {data.items.length === 0 && (
                            <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: 32 }}>No members found.</td></tr>
                        )}
                    </tbody>
                </table>
            )}

            <Pagination page={page} totalPages={totalPages} total={data.total} onPage={setPage} />
        </div>
    );
};
export default MembersPage;
