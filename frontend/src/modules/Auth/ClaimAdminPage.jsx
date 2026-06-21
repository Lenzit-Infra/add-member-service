import React, { useState } from 'react';
import { accountApi } from './accountApi';
import { useAuth } from './AuthContext';

const ClaimAdminPage = ({ token, onNavigate }) => {
    const { login } = useAuth();
    const [email, setEmail] = useState('');
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleRequest = async (e) => {
        e.preventDefault();
        setLoading(true); setError(''); setMessage('');
        try {
            const res = await accountApi.requestClaim(email);
            setMessage(res.data.message);
        } catch (err) {
            setError(err.response?.data?.detail || 'Something went wrong');
        } finally {
            setLoading(false);
        }
    };

    const handleComplete = async (e) => {
        e.preventDefault();
        setLoading(true); setError('');
        try {
            const res = await accountApi.completeClaim({ token, username, password });
            login(res.data.access_token, res.data.user);
        } catch (err) {
            setError(err.response?.data?.detail || 'Could not complete claim');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-page">
            <div className="auth-card">
                <h2 className="auth-title">Claim Admin Account</h2>

                {!token ? (
                    <>
                        <p className="auth-subtitle">Enter the email your administrator allowlisted — we'll send you a claim link.</p>
                        {error && <div className="auth-error">{error}</div>}
                        {message && <div className="auth-success">{message}</div>}
                        <form onSubmit={handleRequest}>
                            <div className="input-group">
                                <label className="input-label">Email</label>
                                <input type="email" className="input-field" value={email} onChange={e => setEmail(e.target.value)} required />
                            </div>
                            <button className="btn-primary" style={{ width: '100%' }} disabled={loading} type="submit">
                                {loading ? 'Sending...' : 'Send Claim Link'}
                            </button>
                        </form>
                    </>
                ) : (
                    <>
                        <p className="auth-subtitle">Choose a username and password to finish setting up your admin account.</p>
                        {error && <div className="auth-error">{error}</div>}
                        <form onSubmit={handleComplete}>
                            <div className="input-group">
                                <label className="input-label">Username</label>
                                <input className="input-field" value={username} onChange={e => setUsername(e.target.value)} required />
                            </div>
                            <div className="input-group">
                                <label className="input-label">Password</label>
                                <input type="password" className="input-field" value={password} onChange={e => setPassword(e.target.value)} required minLength={8} />
                            </div>
                            <button className="btn-primary" style={{ width: '100%' }} disabled={loading} type="submit">
                                {loading ? 'Creating...' : 'Create Admin Account'}
                            </button>
                        </form>
                    </>
                )}

                <div className="auth-links">
                    <button onClick={() => onNavigate('login')}>Back to login</button>
                </div>
            </div>
        </div>
    );
};

export default ClaimAdminPage;
