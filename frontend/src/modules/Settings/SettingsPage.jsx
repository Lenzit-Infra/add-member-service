import React, { useState, useEffect } from 'react';
import { settingsApi } from './api';

const FIELDS = [
    { key: 'batch_size', label: 'Batch Size (users per cycle)' },
    { key: 'sleep_delay_min', label: 'Min Anti-Ban Delay (seconds)' },
    { key: 'sleep_delay_max', label: 'Max Anti-Ban Delay (seconds)' },
    { key: 'daily_limit_per_agent', label: 'Daily Limit per Agent' },
    { key: 'worker_check_interval', label: 'Worker Check Interval (seconds)' },
];

const SettingsPage = () => {
    const [values, setValues] = useState({});
    const [saving, setSaving] = useState(false);
    const [savedAt, setSavedAt] = useState(null);

    useEffect(() => {
        settingsApi.getAll().then(res => setValues(res.data)).catch(console.error);
    }, []);

    const handleChange = (key, val) => setValues(prev => ({ ...prev, [key]: val }));

    const handleSaveAll = async () => {
        setSaving(true);
        try {
            await Promise.all(FIELDS.map(f => settingsApi.update(f.key, String(values[f.key] ?? ''))));
            setSavedAt(new Date().toLocaleTimeString());
        } catch (e) {
            alert('Failed to save settings');
        } finally {
            setSaving(false);
        }
    };

    return (
        <div>
            <div className="settings-grid">
                {FIELDS.map(f => (
                    <div className="settings-card" key={f.key}>
                        <div className="input-group" style={{ marginBottom: 0 }}>
                            <label className="input-label">{f.label}</label>
                            <input
                                className="input-field"
                                type="number"
                                value={values[f.key] ?? ''}
                                onChange={e => handleChange(f.key, e.target.value)}
                            />
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
        </div>
    );
};

export default SettingsPage;
