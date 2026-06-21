import React, { useState } from 'react';
import { accountApi } from './accountApi';

const ResetPasswordPage = ({ token, onNavigate }) => {
    const [password, setPassword] = useState('');
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true); setError(''); setMessage('');
        try {
            const res = await accountApi.resetPassword({ token, new_password: password });
            setMessage(res.data.message);
        } catch (err) {
            setError(err.response?.data?.detail || 'Could not reset password');
        } finally {
            setLoading(false);
        }
    };

    if (!token) {
        return (
            <div className="auth-page">
                <div className="auth-card">
                    <h2 className="auth-title">Invalid Link</h2>
                    <p className="auth-subtitle">This reset link is missing its token.</p>
                    <div className="auth-links">
                        <button onClick={() => onNavigate('login')}>Back to login</button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="auth-page">
            <div className="auth-card">
                <h2 className="auth-title">Reset Password</h2>
                {error && <div className="auth-error">{error}</div>}
                {message ? (
                    <>
                        <div className="auth-success">{message}</div>
                        <button className="btn-primary" style={{ width: '100%' }} onClick={() => onNavigate('login')}>Go to Login</button>
                    </>
                ) : (
                    <form onSubmit={handleSubmit}>
                        <div className="input-group">
                            <label className="input-label">New Password</label>
                            <input type="password" className="input-field" value={password} onChange={e => setPassword(e.target.value)} required minLength={8} />
                        </div>
                        <button className="btn-primary" style={{ width: '100%' }} disabled={loading} type="submit">
                            {loading ? 'Saving...' : 'Set New Password'}
                        </button>
                    </form>
                )}
                <div className="auth-links">
                    <button onClick={() => onNavigate('login')}>Back to login</button>
                </div>
            </div>
        </div>
    );
};

export default ResetPasswordPage;
