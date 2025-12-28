import React, { useState, useEffect } from 'react';
import './App.css'; 

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:4747/api/v1";
// --- ICONS ---
const IconSVG = ({ name, size = 18, className, style, color }) => {
    const icons = {
        LayoutDashboard: "M3 3h7v9H3zm11 0h7v5h-7zm0 9h7v9h-7zM3 16h7v5H3z",
        ListOrdered: "M10 6h11m-11 6h11m-11 6h11M4 6h1v4m-1 0h2m0 8H4c0-1 1-2 2-2V18c0-1-1-2-2-2h2",
        Zap: "M13 2L3 14h9l-1 8 10-12h-9l1-8z", 
        Settings: "M12.22 2h-.44a2 2 0 0 1-2 2.22l-.1.34a10 10 0 0 1-2.22 4.63l-.27.11a2 2 0 0 1-2.63-1L4.17 7.5a10 10 0 0 1 4.63-8.8l.22-.13a2 2 0 0 1 1-2.63L10.5 1.5",
        Users: "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M16 3.13a4 4 0 0 1 0 7.75M23 21v-2a4 4 0 0 0-3-3.87",
        Briefcase: "M20 7h-3a2 2 0 0 0-2-2h-6a2 2 0 0 0-2 2H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2zM9 7h6v2H9V7zm3 8h-2v-2h2v2z",
        Play: "M5 3l14 9-14 9V3z",
        Pause: "M6 4h4v16H6zm8 0h4v16h-4z",
        Square: "M5 5h14v14H5z",
        Plus: "M12 5v14M5 12h14",
        X: "M18 6L6 18M6 6l12 12",
        Search: "M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16zM21 21l-4.35-4.35",
        Info: "M12 22a10 10 0 1 0-10-10 10 10 0 0 0 10 10zm-1-11h2v6h-2zm0-4h2v2h-2z",
        CheckCircle: "M22 11.08V12a10 10 0 1 1-5.93-9.14M22 4L12 14.01l-3-3"
    };
    return (
        <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color || "currentColor"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} style={style}>
            <path d={icons[name] || "M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2z"} />
        </svg>
    );
};

// --- HELPER FUNCTIONS ---
const formatSeconds = (seconds) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    return `${h}h ${m}m`;
};

// --- MODALS ---

const GenericListModal = ({ isOpen, onClose, title, items, columns }) => {
    if (!isOpen) return null;
    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal modal-lg" onClick={e => e.stopPropagation()}>
                <div className="modal-header">
                    <h3 className="modal-title">{title}</h3>
                    <button onClick={onClose} className="icon-btn"><IconSVG name="X" /></button>
                </div>
                <div className="modal-body" style={{padding:0}}>
                    <table>
                        <thead>
                            <tr>{columns.map((c, i) => <th key={i}>{c}</th>)}</tr>
                        </thead>
                        <tbody>
                            {items.map((item, idx) => (
                                <tr key={idx}>
                                    {columns.map((col, i) => {
                                        const key = col.toLowerCase().replace(/ /g, '_');
                                        let val = item[key] || item[col.toLowerCase()] || '-';
                                        return <td key={i}>{val}</td>
                                    })}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

const CreateOrderModal = ({ isOpen, onClose, onRefresh }) => {
    const [target, setTarget] = useState("");
    const [sources, setSources] = useState("");
    const [count, setCount] = useState(100);

    const handleSubmit = () => {
        fetch(`${API_BASE_URL}/orders`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ target_link: target, source_links: sources, desired_count: count })
        }).then(() => { onRefresh(); onClose(); });
    };

    if (!isOpen) return null;
    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal" onClick={e => e.stopPropagation()}>
                <div className="modal-header"><h3>Add New Order</h3></div>
                <div className="modal-body">
                    <div className="input-group">
                        <label>Target Group Link</label>
                        <input className="input-field" value={target} onChange={e=>setTarget(e.target.value)} placeholder="https://t.me/target" />
                    </div>
                    <div className="input-group">
                        <label>Source Links (Comma separated)</label>
                        <textarea className="input-field" value={sources} onChange={e=>setSources(e.target.value)} placeholder="https://t.me/s1, https://t.me/s2" />
                    </div>
                    <div className="input-group">
                        <label>Desired Count</label>
                        <input type="number" className="input-field" value={count} onChange={e=>setCount(e.target.value)} />
                    </div>
                </div>
                <div className="modal-footer">
                    <button className="btn-primary" onClick={handleSubmit}>Create Order</button>
                </div>
            </div>
        </div>
    );
};

// --- NEW AGENT WIZARD MODAL ---
const AddAgentModal = ({ isOpen, onClose, onRefresh }) => {
    const [step, setStep] = useState(1); // 1: Info, 2: Code, 3: 2FA, 4: Success
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    
    // Form Data
    const [phone, setPhone] = useState("");
    const [apiId, setApiId] = useState("");
    const [apiHash, setApiHash] = useState("");
    const [code, setCode] = useState("");
    const [password, setPassword] = useState("");
    const [phoneCodeHash, setPhoneCodeHash] = useState("");

    const reset = () => {
        setStep(1); setPhone(""); setApiId(""); setApiHash(""); setCode(""); setPassword(""); setError(""); setLoading(false);
    };

    const handleRequestCode = () => {
        setLoading(true); setError("");
        fetch(`${API_BASE_URL}/auth/request-code`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ phone, api_id: apiId, api_hash: apiHash })
        })
        .then(res => res.json())
        .then(data => {
            setLoading(false);
            if (data.status === 'success') {
                setPhoneCodeHash(data.phone_code_hash);
                setStep(2);
            } else {
                setError(data.message || "Failed to send code");
            }
        })
        .catch(err => { setLoading(false); setError("Network Error"); });
    };

    const handleVerifyCode = () => {
        setLoading(true); setError("");
        fetch(`${API_BASE_URL}/auth/verify-code`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ phone, code, phone_code_hash: phoneCodeHash })
        })
        .then(res => res.json())
        .then(data => {
            setLoading(false);
            if (data.status === 'success') {
                setStep(4); // Success
            } else if (data.status === '2fa_required') {
                setStep(3); // Go to Password
            } else {
                setError(data.message || "Invalid Code");
            }
        })
        .catch(err => { setLoading(false); setError("Network Error"); });
    };

    const handleVerifyPassword = () => {
        setLoading(true); setError("");
        fetch(`${API_BASE_URL}/auth/verify-password`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ phone, password })
        })
        .then(res => res.json())
        .then(data => {
            setLoading(false);
            if (data.status === 'success') {
                setStep(4);
            } else {
                setError(data.message || "Invalid Password");
            }
        })
        .catch(err => { setLoading(false); setError("Network Error"); });
    };

    const handleFinish = () => {
        onRefresh();
        onClose();
        reset();
    };

    if (!isOpen) return null;

    return (
        <div className="modal-overlay">
            <div className="modal" onClick={e => e.stopPropagation()}>
                <div className="modal-header">
                    <h3>Add Agent - Step {step}</h3>
                    <button onClick={onClose} className="icon-btn"><IconSVG name="X" /></button>
                </div>
                <div className="modal-body">
                    {/* STEP 1: INITIAL INFO */}
                    {step === 1 && (
                        <>
                            <div className="input-group">
                                <label>Phone Number (with +)</label>
                                <input className="input-field" value={phone} onChange={e=>setPhone(e.target.value)} placeholder="+989..." />
                            </div>
                            <div className="input-group">
                                <label>API ID</label>
                                <input className="input-field" value={apiId} onChange={e=>setApiId(e.target.value)} />
                            </div>
                            <div className="input-group">
                                <label>API Hash</label>
                                <input className="input-field" value={apiHash} onChange={e=>setApiHash(e.target.value)} />
                            </div>
                            <button className="btn-primary" style={{width:'100%'}} onClick={handleRequestCode} disabled={loading}>
                                {loading ? "Sending..." : "Send Code"}
                            </button>
                        </>
                    )}

                    {/* STEP 2: ENTER CODE */}
                    {step === 2 && (
                        <>
                            <p style={{marginBottom:10, fontSize:13}}>Code sent to {phone}. Check Telegram.</p>
                            <div className="input-group">
                                <label>Login Code</label>
                                <input className="input-field" value={code} onChange={e=>setCode(e.target.value)} placeholder="12345" />
                            </div>
                            <button className="btn-primary" style={{width:'100%'}} onClick={handleVerifyCode} disabled={loading}>
                                {loading ? "Verifying..." : "Verify Code"}
                            </button>
                        </>
                    )}

                    {/* STEP 3: 2FA PASSWORD */}
                    {step === 3 && (
                        <>
                            <p style={{marginBottom:10, fontSize:13}}>Two-Step Verification Enabled.</p>
                            <div className="input-group">
                                <label>Password</label>
                                <input className="input-field" type="password" value={password} onChange={e=>setPassword(e.target.value)} />
                            </div>
                            <button className="btn-primary" style={{width:'100%'}} onClick={handleVerifyPassword} disabled={loading}>
                                {loading ? "Checking..." : "Confirm Password"}
                            </button>
                        </>
                    )}

                    {/* STEP 4: SUCCESS */}
                    {step === 4 && (
                        <div style={{textAlign:'center', padding:20}}>
                            <IconSVG name="CheckCircle" size={48} color="green" style={{marginBottom:10}} />
                            <h3>Agent Added Successfully!</h3>
                            <button className="btn-primary" style={{width:'100%', marginTop:20}} onClick={handleFinish}>
                                Done
                            </button>
                        </div>
                    )}

                    {error && <div style={{color:'red', marginTop:10, fontSize:12}}>{error}</div>}
                </div>
            </div>
        </div>
    );
};

// --- PAGES ---

// 1. ORDERS PAGE
const OrdersPage = () => {
    const [orders, setOrders] = useState([]);
    const [isCreateOpen, setCreateOpen] = useState(false);
    const [popupData, setPopupData] = useState({ isOpen: false, title: "", items: [], columns: [] });

    const fetchOrders = () => {
        fetch(`${API_BASE_URL}/orders`).then(res=>res.json()).then(setOrders);
    };

    useEffect(() => fetchOrders(), []);

    const handleAction = (id, type) => {
        fetch(`${API_BASE_URL}/orders/${id}/action`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ type })
        }).then(fetchOrders);
    };

    const showSources = (order) => {
        setPopupData({
            isOpen: true,
            title: `Sources for Order #${order.id}`,
            items: order.sources,
            columns: ["ID", "Title", "Link", "Count"]
        });
    };

    const showAgents = (order) => {
        setPopupData({
            isOpen: true,
            title: `Agents for Order #${order.id}`,
            items: order.agents,
            columns: ["ID", "Phone", "Total Adds For Order"]
        });
    };

    return (
        <div className="table-wrapper">
            <div className="table-header-row">
                <div className="table-title">Orders Management</div>
                <button className="action-btn-primary" onClick={()=>setCreateOpen(true)}>
                    <IconSVG name="Plus" /> Add Order
                </button>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Target Group</th>
                        <th>Sources</th>
                        <th>Agents</th>
                        <th>Progress</th>
                        <th>Status</th>
                        <th>Created At</th>
                        <th>Ended At</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    {orders.map(o => (
                        <tr key={o.id}>
                            <td style={{fontFamily:'monospace'}}>#{o.id}</td>
                            <td style={{fontWeight:600}}>{o.target_group}</td>
                            <td>
                                <button className="link-text" onClick={()=>showSources(o)}>
                                    {o.sources.length} Groups
                                </button>
                            </td>
                            <td>
                                <button className="link-text" onClick={()=>showAgents(o)}>
                                    {o.agents.length} Agents
                                </button>
                            </td>
                            <td>{o.current_count} / {o.desired_count} ({o.progress_percent}%)</td>
                            <td><span className={`badge badge-${o.status}`}>{o.status.replace('_', ' ')}</span></td>
                            <td>{o.created_at}</td>
                            <td>{o.ended_at}</td>
                            <td>
                                <div style={{display:'flex', gap:6}}>
                                    {(o.status === 'in_progress' || o.status === 'pending_agent') && (
                                        <button className="icon-btn-action pause" title="Pause" onClick={()=>handleAction(o.id, 'pause')}>
                                            <IconSVG name="Pause" size={14}/>
                                        </button>
                                    )}
                                    {o.status === 'paused' && (
                                        <button className="icon-btn-action resume" title="Resume" onClick={()=>handleAction(o.id, 'resume')}>
                                            <IconSVG name="Play" size={14}/>
                                        </button>
                                    )}
                                    {(o.status !== 'cancelled' && o.status !== 'finished') && (
                                        <button className="icon-btn-action stop" title="Stop" onClick={()=>handleAction(o.id, 'stop')}>
                                            <IconSVG name="Square" size={14}/>
                                        </button>
                                    )}
                                </div>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
            
            <GenericListModal 
                isOpen={popupData.isOpen} 
                onClose={()=>setPopupData({...popupData, isOpen:false})} 
                title={popupData.title}
                items={popupData.items}
                columns={popupData.columns}
            />
            
            <CreateOrderModal isOpen={isCreateOpen} onClose={()=>setCreateOpen(false)} onRefresh={fetchOrders} />
        </div>
    );
};

// 2. AGENTS PAGE
const AgentsPage = () => {
    const [agents, setAgents] = useState([]);
    const [isAddOpen, setAddOpen] = useState(false);

    const fetchAgents = () => {
        fetch(`${API_BASE_URL}/agents`).then(res=>res.json()).then(setAgents);
    }

    useEffect(() => fetchAgents(), []);

    return (
        <div className="table-wrapper">
            <div className="table-header-row">
                <div className="table-title">Agents & Accounts</div>
                <button className="action-btn-primary" onClick={()=>setAddOpen(true)}>
                    <IconSVG name="Plus" /> Add Agent
                </button>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Phone</th>
                        <th>Status</th>
                        <th>Ban Info</th>
                        <th>Active Time</th>
                        <th>Daily Adds</th>
                        <th>Monthly</th>
                        <th>Total</th>
                        <th>Joined At</th>
                        <th>Last Active</th>
                    </tr>
                </thead>
                <tbody>
                    {agents.map(a => (
                        <tr key={a.id}>
                            <td>{a.id}</td>
                            <td>{a.phone}</td>
                            <td>
                                <span className={`badge badge-${a.is_active ? 'active' : 'inactive'}`}>
                                    {a.is_active ? 'Active' : 'Idle'}
                                </span>
                            </td>
                            <td>
                                {a.is_banned ? <span className="badge badge-banned" title={a.ban_reason}>BANNED</span> : '-'}
                            </td>
                            <td>{formatSeconds(a.total_active_seconds)}</td>
                            <td style={{fontWeight:600}}>{a.daily_adds}</td>
                            <td>{a.monthly_adds}</td>
                            <td>{a.total_adds}</td>
                            <td style={{fontSize:11}}>{a.first_joined_at}</td>
                            <td style={{fontSize:11}}>{a.last_active_at}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
            
            <AddAgentModal isOpen={isAddOpen} onClose={()=>setAddOpen(false)} onRefresh={fetchAgents} />
        </div>
    );
};

// 3. MEMBERS PAGE
const MembersPage = () => {
    const [members, setMembers] = useState([]);
    useEffect(() => { fetch(`${API_BASE_URL}/members`).then(res=>res.json()).then(setMembers); }, []);

    return (
        <div className="table-wrapper">
             <div className="table-header-row"><div className="table-title">Scraped Members DB</div></div>
             <table>
                <thead>
                    <tr>
                        <th>User ID</th>
                        <th>Username</th>
                        <th>Name</th>
                        <th>Quality Score</th>
                        <th>Status</th>
                        <th>Premium</th>
                        <th>Bot</th>
                    </tr>
                </thead>
                <tbody>
                    {members.map(m => (
                        <tr key={m.user_id}>
                            <td style={{fontFamily:'monospace'}}>{m.user_id}</td>
                            <td>{m.username || '-'}</td>
                            <td>{m.first_name}</td>
                            <td>
                                <span style={{fontWeight:700, color: m.quality_score > 50 ? 'green' : 'orange'}}>
                                    {m.quality_score}
                                </span>
                            </td>
                            <td><span className="badge badge-inactive">{m.status}</span></td>
                            <td>{m.is_premium ? 'YES' : '-'}</td>
                            <td>{m.is_bot ? 'YES' : '-'}</td>
                        </tr>
                    ))}
                </tbody>
             </table>
        </div>
    );
};

// 4. GROUPS PAGE
const GroupsPage = () => {
    const [groups, setGroups] = useState([]);
    useEffect(() => { fetch(`${API_BASE_URL}/groups`).then(res=>res.json()).then(setGroups); }, []);

    return (
        <div className="table-wrapper">
             <div className="table-header-row"><div className="table-title">All Groups</div></div>
             <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Title</th>
                        <th>Type</th>
                        <th>Link</th>
                        <th>Members</th>
                        <th>Lenzit Admin</th>
                    </tr>
                </thead>
                <tbody>
                    {groups.map(g => (
                        <tr key={g.id}>
                            <td>{g.id}</td>
                            <td style={{fontWeight:600}}>{g.title}</td>
                            <td>{g.type}</td>
                            <td style={{color:'blue'}}>{g.invite_link}</td>
                            <td>{g.member_count}</td>
                            <td>{g.is_lenzit_admin ? <span className="badge badge-active">YES</span> : 'NO'}</td>
                        </tr>
                    ))}
                </tbody>
             </table>
        </div>
    );
};

// --- APP LAYOUT ---
const App = () => {
    const [activePage, setActivePage] = useState('Agents');
    
    const menuItems = [
        { name: 'Orders', icon: 'ListOrdered' },
        { name: 'Agents', icon: 'Zap' },
        { name: 'Members', icon: 'Users' },
        { name: 'Groups', icon: 'Briefcase' },
        { name: 'Settings', icon: 'Settings' },
    ];

    const renderContent = () => {
        switch(activePage) {
            case 'Orders': return <OrdersPage />;
            case 'Agents': return <AgentsPage />;
            case 'Members': return <MembersPage />;
            case 'Groups': return <GroupsPage />;
            case 'Settings': return <div>Settings Component</div>;
            default: return <div>Page Not Found</div>;
        }
    };

    return (
        <div id="root">
            <div className="sidebar">
                <div className="user-profile">
                    <img src="https://placehold.co/100x100/3b82f6/white?text=A" className="avatar" alt="Admin" />
                    <div className="user-info"><h3>Admin Panel</h3><span>v3.0</span></div>
                </div>
                <div className="nav-menu">
                    {menuItems.map(item => (
                        <button key={item.name} className={`nav-item ${activePage === item.name ? 'active' : ''}`} onClick={() => setActivePage(item.name)}>
                            <IconSVG name={item.icon} size={18} /> {item.name}
                        </button>
                    ))}
                </div>
            </div>
            <div style={{flex:1, height:'100vh', overflow:'hidden', display:'flex', flexDirection:'column'}}>
                <div className="header"><div className="page-title">{activePage}</div></div>
                <div className="main-content">{renderContent()}</div>
            </div>
        </div>
    );
};

export default App;