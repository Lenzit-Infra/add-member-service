import React, { useState } from 'react';
import { accountApi } from './accountApi';

const ForgotPasswordPage = ({ onNavigate }) => {
    const [email, setEmail] = useState('');
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true); setError(''); setMessage('');
        try {
            const res = await accountApi.forgotPassword(email);
            setMessage(res.data.message);
        } catch (err) {
            setError(err.response?.data?.detail || 'Something went wrong');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-page">
            <div className="auth-card">
                <h2 className="auth-title">Forgot Password</h2>
                <p className="auth-subtitle">We'll email you a link to reset your password.</p>
                {error && <div className="auth-error">{error}</div>}
                {message && <div className="auth-success">{message}</div>}
                <form onSubmit={handleSubmit}>
                    <div className="input-group">
                        <label className="input-label">Email</label>
                        <input type="email" className="input-field" value={email} onChange={e => setEmail(e.target.value)} required />
                    </div>
                    <button className="btn-primary" style={{ width: '100%' }} disabled={loading} type="submit">
                        {loading ? 'Sending...' : 'Send Reset Link'}
                    </button>
                </form>
                <div className="auth-links">
                    <button onClick={() => onNavigate('login')}>Back to login</button>
                </div>
            </div>
        </div>
    );
};

export default ForgotPasswordPage;
