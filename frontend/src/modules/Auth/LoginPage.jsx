import React, { useState } from 'react';
import { accountApi } from './accountApi';
import { useAuth } from './AuthContext';
import BackendStatus from '../../components/BackendStatus';

const LoginPage = ({ onNavigate }) => {
    const { login } = useAuth();
    const [form, setForm] = useState({ username_or_email: '', password: '' });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            const res = await accountApi.login(form);
            login(res.data.access_token, res.data.user);
        } catch (err) {
            setError(err.response?.data?.detail || 'Login failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-page">
            <div style={{ position: 'fixed', top: 16, right: 16 }}><BackendStatus /></div>
            <div className="auth-card">
                <h2 className="auth-title">Lenzit Panel</h2>
                <p className="auth-subtitle">Sign in to your dashboard account</p>
                {error && <div className="auth-error">{error}</div>}
                <form onSubmit={handleSubmit}>
                    <div className="input-group">
                        <label className="input-label">Username or Email</label>
                        <input
                            className="input-field"
                            value={form.username_or_email}
                            onChange={e => setForm({ ...form, username_or_email: e.target.value })}
                            required
                        />
                    </div>
                    <div className="input-group">
                        <label className="input-label">Password</label>
                        <input
                            type="password"
                            className="input-field"
                            value={form.password}
                            onChange={e => setForm({ ...form, password: e.target.value })}
                            required
                        />
                    </div>
                    <button className="btn-primary" style={{ width: '100%' }} disabled={loading} type="submit">
                        {loading ? 'Signing in...' : 'Sign In'}
                    </button>
                </form>
                <div className="auth-links">
                    <button onClick={() => onNavigate('forgot-password')}>Forgot password?</button>
                    <button onClick={() => onNavigate('claim-admin')}>Claim admin account</button>
                </div>
            </div>
        </div>
    );
};

export default LoginPage;
