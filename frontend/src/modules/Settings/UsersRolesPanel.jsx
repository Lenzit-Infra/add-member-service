import React, { useState, useEffect } from 'react';
import { usersApi } from './usersApi';
import IconSVG from '../../components/IconSVG';

const ROLE_OPTIONS = ['admin', 'operator', 'viewer'];

const formatDate = (iso) => iso ? new Date(iso).toLocaleString() : '—';

const UsersRolesPanel = () => {
    const [users, setUsers] = useState([]);
    const [rolesData, setRolesData] = useState(null); // { catalog, roles }
    const [pendingPerms, setPendingPerms] = useState({}); // role -> Set of permission keys (editable buffer)
    const [error, setError] = useState('');

    const [showAddModal, setShowAddModal] = useState(false);
    const [newUser, setNewUser] = useState({ username: '', email: '', password: '', role: 'operator' });

    const [resetModalUser, setResetModalUser] = useState(null);
    const [newPassword, setNewPassword] = useState('');

    const fetchUsers = () => usersApi.list().then(res => setUsers(res.data)).catch(console.error);
    const fetchRoles = () => usersApi.getRoles().then(res => {
        setRolesData(res.data);
        const buffer = {};
        Object.entries(res.data.roles).forEach(([role, info]) => { buffer[role] = new Set(info.permissions); });
        setPendingPerms(buffer);
    }).catch(console.error);

    useEffect(() => { fetchUsers(); fetchRoles(); }, []);

    const handleRoleChange = (user, role) => {
        usersApi.update(user.id, { role }).then(fetchUsers).catch(e => setError(e.response?.data?.detail || 'Failed to change role'));
    };

    const handleToggleActive = (user) => {
        usersApi.update(user.id, { is_active: !user.is_active }).then(fetchUsers).catch(e => setError(e.response?.data?.detail || 'Failed to update user'));
    };

    const handleDelete = (user) => {
        if (!window.confirm(`Delete user '${user.username}' permanently?`)) return;
        usersApi.remove(user.id).then(fetchUsers).catch(e => setError(e.response?.data?.detail || 'Failed to delete user'));
    };

    const handleAddUser = async () => {
        setError('');
        try {
            await usersApi.create(newUser);
            setShowAddModal(false);
            setNewUser({ username: '', email: '', password: '', role: 'operator' });
            fetchUsers();
        } catch (e) {
            setError(e.response?.data?.detail || 'Failed to create user');
        }
    };

    const handleResetPassword = async () => {
        setError('');
        try {
            await usersApi.update(resetModalUser.id, { new_password: newPassword });
            setResetModalUser(null);
            setNewPassword('');
        } catch (e) {
            setError(e.response?.data?.detail || 'Failed to reset password');
        }
    };

    const togglePerm = (role, key) => {
        setPendingPerms(prev => {
            const next = new Set(prev[role]);
            if (next.has(key)) next.delete(key); else next.add(key);
            return { ...prev, [role]: next };
        });
    };

    const handleSavePerms = (role) => {
        usersApi.updateRolePermissions(role, Array.from(pendingPerms[role] || [])).then(fetchRoles).catch(e => setError(e.response?.data?.detail || 'Failed to save permissions'));
    };

    return (
        <div>
            {error && <div className="auth-error" style={{ marginBottom: 16 }}>{error}</div>}

            <div className="table-wrapper" style={{ marginBottom: 28 }}>
                <div className="table-header-row">
                    <div className="table-title">Users</div>
                    <button className="action-btn-primary" onClick={() => setShowAddModal(true)}>
                        <IconSVG name="Plus" size={14} /> Add User
                    </button>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>Username</th><th>Email</th><th>Role</th><th>Status</th><th>Created</th><th>Last Login</th><th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {users.map(u => (
                            <tr key={u.id}>
                                <td>{u.username}</td>
                                <td>{u.email}</td>
                                <td>
                                    <select className="input-field" style={{ padding: '6px 8px' }} value={u.role} onChange={e => handleRoleChange(u, e.target.value)}>
                                        {ROLE_OPTIONS.map(r => <option key={r} value={r}>{r}</option>)}
                                    </select>
                                </td>
                                <td>
                                    <span className={`badge badge-${u.is_active ? 'active' : 'inactive'}`}>{u.is_active ? 'Active' : 'Disabled'}</span>
                                    {u.locked_until && <span className="badge badge-banned" style={{ marginLeft: 6 }}>Locked</span>}
                                </td>
                                <td style={{ fontSize: 12 }}>{formatDate(u.created_at)}</td>
                                <td style={{ fontSize: 12 }}>{formatDate(u.last_login_at)}{u.last_login_ip ? ` (${u.last_login_ip})` : ''}</td>
                                <td>
                                    <div style={{ display: 'flex', gap: 6 }}>
                                        <button className="icon-btn-action" title="Reset Password" onClick={() => { setResetModalUser(u); setNewPassword(''); }}>
                                            <IconSVG name="RefreshCw" size={14} />
                                        </button>
                                        <button className="icon-btn-action" title={u.is_active ? 'Disable' : 'Enable'} onClick={() => handleToggleActive(u)}>
                                            <IconSVG name="Zap" size={14} />
                                        </button>
                                        <button className="icon-btn-action delete" title="Delete" onClick={() => handleDelete(u)}>
                                            <IconSVG name="Trash2" size={14} />
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                        {users.length === 0 && (
                            <tr><td colSpan={7} style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>No users yet.</td></tr>
                        )}
                    </tbody>
                </table>
            </div>

            <div className="table-title" style={{ marginBottom: 12 }}>Role Permissions</div>
            <div className="settings-grid">
                <div className="settings-card">
                    <div className="input-label" style={{ marginBottom: 8 }}>admin</div>
                    <p className="settings-field-description">Always has full access to everything, including user management, roles, and the admin email allowlist. Not editable — this guarantees the system can never lock itself out.</p>
                </div>
                {['operator', 'viewer'].map(role => (
                    <div className="settings-card" key={role}>
                        <div className="input-label" style={{ marginBottom: 8 }}>{role}</div>
                        {(rolesData?.catalog || []).map(p => (
                            <label key={p.key} style={{ display: 'flex', alignItems: 'flex-start', gap: 8, marginBottom: 10, fontSize: 13, cursor: 'pointer' }}>
                                <input
                                    type="checkbox"
                                    checked={pendingPerms[role]?.has(p.key) || false}
                                    onChange={() => togglePerm(role, p.key)}
                                    style={{ marginTop: 2 }}
                                />
                                <span>
                                    <strong>{p.label}</strong>
                                    <br />
                                    <span style={{ color: 'var(--text-secondary)', fontSize: 12 }}>{p.description}</span>
                                </span>
                            </label>
                        ))}
                        <button className="btn-primary" style={{ marginTop: 4 }} onClick={() => handleSavePerms(role)}>Save</button>
                    </div>
                ))}
            </div>

            {showAddModal && (
                <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3 className="modal-title">Add User</h3>
                            <button className="icon-btn" onClick={() => setShowAddModal(false)}><IconSVG name="X" size={16} /></button>
                        </div>
                        <div className="modal-body">
                            <div className="input-group">
                                <label className="input-label">Username</label>
                                <input className="input-field" value={newUser.username} onChange={e => setNewUser({ ...newUser, username: e.target.value })} />
                            </div>
                            <div className="input-group">
                                <label className="input-label">Email</label>
                                <input className="input-field" type="email" value={newUser.email} onChange={e => setNewUser({ ...newUser, email: e.target.value })} />
                            </div>
                            <div className="input-group">
                                <label className="input-label">Password (min 8 characters)</label>
                                <input className="input-field" type="password" value={newUser.password} onChange={e => setNewUser({ ...newUser, password: e.target.value })} />
                            </div>
                            <div className="input-group">
                                <label className="input-label">Role</label>
                                <select className="input-field" value={newUser.role} onChange={e => setNewUser({ ...newUser, role: e.target.value })}>
                                    {ROLE_OPTIONS.map(r => <option key={r} value={r}>{r}</option>)}
                                </select>
                            </div>
                            <button className="btn-primary" style={{ width: '100%' }} onClick={handleAddUser}>Create</button>
                        </div>
                    </div>
                </div>
            )}

            {resetModalUser && (
                <div className="modal-overlay" onClick={() => setResetModalUser(null)}>
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3 className="modal-title">Reset Password — {resetModalUser.username}</h3>
                            <button className="icon-btn" onClick={() => setResetModalUser(null)}><IconSVG name="X" size={16} /></button>
                        </div>
                        <div className="modal-body">
                            <div className="input-group">
                                <label className="input-label">New password (min 8 characters)</label>
                                <input className="input-field" type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} />
                            </div>
                            <button className="btn-primary" style={{ width: '100%' }} onClick={handleResetPassword}>Update Password</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default UsersRolesPanel;
