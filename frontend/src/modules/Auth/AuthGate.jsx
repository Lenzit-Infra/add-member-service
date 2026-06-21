import React, { useState } from 'react';
import LoginPage from './LoginPage';
import ClaimAdminPage from './ClaimAdminPage';
import ForgotPasswordPage from './ForgotPasswordPage';
import ResetPasswordPage from './ResetPasswordPage';

const VALID_VIEWS = ['claim-admin', 'reset-password', 'forgot-password', 'login'];

const AuthGate = () => {
    const params = new URLSearchParams(window.location.search);
    const initialView = VALID_VIEWS.includes(params.get('view')) ? params.get('view') : 'login';
    const initialToken = params.get('token') || '';

    const [view, setView] = useState(initialView);

    const navigate = (next) => {
        setView(next);
        // Clean the URL so a refresh doesn't keep re-triggering the emailed-link flow.
        window.history.replaceState({}, '', window.location.pathname);
    };

    switch (view) {
        case 'claim-admin':
            return <ClaimAdminPage token={initialToken} onNavigate={navigate} />;
        case 'reset-password':
            return <ResetPasswordPage token={initialToken} onNavigate={navigate} />;
        case 'forgot-password':
            return <ForgotPasswordPage onNavigate={navigate} />;
        default:
            return <LoginPage onNavigate={navigate} />;
    }
};

export default AuthGate;
