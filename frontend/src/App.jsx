import React, { useState } from 'react';
import './App.css';
import IconSVG from './components/IconSVG';
import BackendStatus from './components/BackendStatus';

// Import Pages from Modules
import DashboardPage from './modules/Dashboard/DashboardPage';
import OrdersPage from './modules/Orders/OrdersPage';
import AgentsPage from './modules/Agents/AgentsPage';
import MembersPage from './modules/Members/MembersPage';
import GroupsPage from './modules/Groups/GroupsPage';
import SettingsPage from './modules/Settings/SettingsPage';
import LoginForm from './modules/Auth/components/LoginForm';
import { AuthProvider, useAuth } from './modules/Auth/AuthContext';
import AuthGate from './modules/Auth/AuthGate';

const DashboardShell = () => {
    const { user, logout } = useAuth();
    const [activePage, setActivePage] = useState('Dashboard');

    const menuItems = [
        { name: 'Dashboard', icon: 'LayoutDashboard' },
        { name: 'Agents', icon: 'Zap' },
        { name: 'Orders', icon: 'ListOrdered' },
        { name: 'Add Account', icon: 'Plus' }, // میانبر به لاگین
        { name: 'Members', icon: 'Users' },
        { name: 'Groups', icon: 'Briefcase' },
        { name: 'Settings', icon: 'Settings' },
    ];

    const renderContent = () => {
        switch(activePage) {
            case 'Dashboard': return <DashboardPage />;
            case 'Orders': return <OrdersPage />;
            case 'Agents': return <AgentsPage />;
            case 'Add Account': return <div style={{maxWidth: 420}}><LoginForm /></div>;
            case 'Members': return <MembersPage />;
            case 'Groups': return <GroupsPage />;
            case 'Settings': return <SettingsPage />;
            default: return <div>Page Not Found</div>;
        }
    };

    return (
        <div id="root">
            <div className="sidebar">
                <div className="user-profile">
                    <img src="https://placehold.co/100x100/3b82f6/white?text=A" className="avatar" alt="Admin" />
                    <div className="user-info"><h3>{user?.username || 'Lenzit Panel'}</h3><span>Modular v4</span></div>
                </div>
                <div className="nav-menu">
                    {menuItems.map(item => (
                        <button key={item.name} className={`nav-item ${activePage === item.name ? 'active' : ''}`} onClick={() => setActivePage(item.name)}>
                            <IconSVG name={item.icon} size={18} /> {item.name}
                        </button>
                    ))}
                </div>
                <button className="exit-btn" onClick={logout}>
                    <IconSVG name="X" size={16} /> Logout
                </button>
            </div>
            <div style={{flex:1, height:'100vh', overflow:'hidden', display:'flex', flexDirection:'column'}}>
                <div className="header">
                    <div className="page-title">{activePage}</div>
                    <div className="header-right"><BackendStatus /></div>
                </div>
                <div className="main-content">{renderContent()}</div>
            </div>
        </div>
    );
};

const AppContent = () => {
    const { user, loading } = useAuth();
    if (loading) {
        return (
            <div className="auth-page">
                <div className="auth-card"><p className="auth-subtitle" style={{margin: 0}}>Loading...</p></div>
            </div>
        );
    }
    return user ? <DashboardShell /> : <AuthGate />;
};

const App = () => (
    <AuthProvider>
        <AppContent />
    </AuthProvider>
);

export default App;
