import React, { useState, useEffect, useMemo } from 'react';
import { settingsApi } from './api';
import IconSVG from '../../components/IconSVG';
import UsersRolesPanel from './UsersRolesPanel';
import AuditLogPanel from './AuditLogPanel';

const ADMIN_ACCESS_TAB = 'Admin Access';
const USERS_ROLES_TAB = 'Users & Roles';
const AUDIT_LOG_TAB = 'Audit Log';

const SettingsPage = () => {
    const [schema, setSchema] = useState([]);
    const [values, setValues] = useState({});
    const [activeTab, setActiveTab] = useState(null);
    const [saving, setSaving] = useState(false);
    const [savedAt, setSavedAt] = useState(null);

    const [emails, setEmails] = useState([]);
    const [newEmail, setNewEmail] = useState('');
    const [emailError, setEmailError] = useState('');

    const fetchSettings = () => {
        settingsApi.getAll().then(res => {
            setSchema(res.data);
            const v = {};
            res.data.forEach(s => { v[s.key] = s.value; });
            setValues(v);
            if (!activeTab) setActiveTab(res.data[0]?.category || ADMIN_ACCESS_TAB);
        }).catch(console.error);
    };

    const fetchEmails = () => {
        settingsApi.getAdminEmails().then(res => setEmails(res.data.emails)).catch(console.error);
    };

    useEffect(() => { fetchSettings(); fetchEmails(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

    const categories = useMemo(() => {
        const seen = [];
        schema.forEach(s => { if (!seen.includes(s.category)) seen.push(s.category); });
        seen.push(ADMIN_ACCESS_TAB, USERS_ROLES_TAB, AUDIT_LOG_TAB);
        return seen;
    }, [schema]);

    const handleChange = (key, val) => setValues(prev => ({ ...prev, [key]: val }));

    const handleSaveAll = async () => {
        setSaving(true);
        try {
            await Promise.all(schema.map(s => settingsApi.update(s.key, String(values[s.key] ?? ''))));
            setSavedAt(new Date().toLocaleTimeString());
        } catch (e) {
            alert('Failed to save settings');
        } finally {
            setSaving(false);
        }
    };

    const handleAddEmail = async () => {
        const email = newEmail.trim().toLowerCase();
        if (!email) return;
        setEmailError('');
        try {
            const res = await settingsApi.addAdminEmail(email);
            setEmails(res.data.emails);
            setNewEmail('');
        } catch (e) {
            setEmailError(e.response?.data?.detail || 'Failed to add email');
        }
    };

    const handleRemoveEmail = async (email) => {
        if (!window.confirm(`Remove ${email} from the admin allowlist?`)) return;
        try {
            const res = await settingsApi.removeAdminEmail(email);
            setEmails(res.data.emails);
        } catch (e) {
            alert(e.response?.data?.detail || 'Failed to remove email');
        }
    };

    const fieldsForTab = schema.filter(s => s.category === activeTab);

    return (
        <div>
            <div className="settings-tabs">
                {categories.map(cat => (
                    <button
                        key={cat}
                        className={`settings-tab ${activeTab === cat ? 'active' : ''}`}
                        onClick={() => setActiveTab(cat)}
                    >
                        {cat}
                    </button>
                ))}
            </div>

            {activeTab === 'Anti-Ban / Telegram Safety' && (
                <div className="disclosure-banner">
                    <IconSVG name="Info" size={18} />
                    <span>
                        Telegram does not publish fixed flood-control thresholds, and its policy treats adding people
                        to groups/channels they didn't ask to join the same as spam. These settings reduce the
                        chance of an agent getting flagged — they cannot eliminate the risk entirely.
                    </span>
                </div>
            )}

            {activeTab === USERS_ROLES_TAB ? (
                <UsersRolesPanel />
            ) : activeTab === AUDIT_LOG_TAB ? (
                <AuditLogPanel />
            ) : activeTab === ADMIN_ACCESS_TAB ? (
                <div className="settings-card" style={{ maxWidth: 520 }}>
                    <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 0 }}>
                        Anyone on this list can claim a dashboard admin account at <code>/?view=claim-admin</code>.
                        Only existing admins can change this list.
                    </p>
                    <div className="admin-email-chips">
                        {emails.map(email => (
                            <span className="admin-email-chip" key={email}>
                                {email}
                                <button onClick={() => handleRemoveEmail(email)} title="Remove">
                                    <IconSVG name="X" size={12} />
                                </button>
                            </span>
                        ))}
                        {emails.length === 0 && <span style={{ color: 'var(--text-secondary)', fontSize: 13 }}>No admin emails yet.</span>}
                    </div>
                    <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
                        <input
                            className="input-field"
                            placeholder="new-admin@example.com"
                            value={newEmail}
                            onChange={e => setNewEmail(e.target.value)}
                            onKeyDown={e => e.key === 'Enter' && handleAddEmail()}
                        />
                        <button className="action-btn-primary" onClick={handleAddEmail}>
                            <IconSVG name="Plus" size={14} /> Add
                        </button>
                    </div>
                    {emailError && <div className="auth-error" style={{ marginTop: 10 }}>{emailError}</div>}
                </div>
            ) : (
                <>
                    <div className="settings-grid">
                        {fieldsForTab.map(f => (
                            <div className="settings-card" key={f.key}>
                                <div className="input-group" style={{ marginBottom: 0 }}>
                                    <label className="input-label">{f.label}</label>
                                    <input
                                        className="input-field"
                                        type="number"
                                        step={f.type === 'float' ? '0.05' : '1'}
                                        min={f.min}
                                        max={f.max}
                                        value={values[f.key] ?? ''}
                                        onChange={e => handleChange(f.key, e.target.value)}
                                    />
                                    <p className="settings-field-description">{f.description}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                    <div className="save-bar">
                        {savedAt && <span style={{ alignSelf: 'center', marginRight: 12, color: 'var(--text-secondary)', fontSize: 13 }}>Saved at {savedAt}</span>}
                        <button className="btn-primary" onClick={handleSaveAll} disabled={saving}>
                            {saving ? 'Saving...' : 'Save Settings'}
                        </button>
                    </div>
                </>
            )}
        </div>
    );
};

export default SettingsPage;
