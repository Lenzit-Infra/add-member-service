import React, { useState, useEffect } from 'react';
import { ordersApi } from './api';
import CreateOrderModal from './components/CreateOrderModal';
import GenericListModal from '../../components/GenericListModal';
import IconSVG from '../../components/IconSVG';

const OrdersPage = () => {
    const [orders, setOrders] = useState([]);
    const [isCreateOpen, setCreateOpen] = useState(false);
    const [popupData, setPopupData] = useState({ isOpen: false, title: "", items: [], columns: [] });

    const fetchOrders = () => {
        ordersApi.getAll().then(res => setOrders(res.data)).catch(console.error);
    };

    useEffect(() => fetchOrders(), []);

    const handleAction = (id, type) => {
        ordersApi.action(id, type).then(fetchOrders);
    };

    const handleDelete = (id) => {
        if (!window.confirm(`Delete order #${id}? This cannot be undone.`)) return;
        ordersApi.remove(id).then(fetchOrders).catch(err => alert(err.response?.data?.detail || 'Could not delete order'));
    };

    const showSources = (order) => {
        setPopupData({
            isOpen: true,
            title: `Sources for Order #${order.id}`,
            items: order.sources || [],
            columns: ["ID", "Title", "Link"]
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
                        <th>ID</th><th>Target</th><th>Sources</th><th>Progress</th><th>Status</th><th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    {orders.map(o => (
                        <tr key={o.id}>
                            <td>#{o.id}</td>
                            <td>{o.target_group}</td>
                            <td><button className="link-text" onClick={()=>showSources(o)}>{o.sources?.length || 0} Groups</button></td>
                            <td>
                                <span className="progress-text">{o.current_count} / {o.desired_count} ({o.progress_percent ?? 0}%)</span>
                                <div className="progress-container">
                                    <div className="progress-fill" style={{ width: `${Math.min(o.progress_percent ?? 0, 100)}%` }} />
                                </div>
                            </td>
                            <td><span className={`badge badge-${o.status}`}>{o.status}</span></td>
                            <td>
                                <div style={{display:'flex', gap:6}}>
                                    {o.status === 'in_progress' && (
                                        <button className="icon-btn-action pause" title="Pause" onClick={()=>handleAction(o.id, 'pause')}><IconSVG name="Pause" size={14}/></button>
                                    )}
                                    {(o.status === 'paused' || o.status === 'pending_agent') && (
                                        <button className="icon-btn-action resume" title="Resume" onClick={()=>handleAction(o.id, 'resume')}><IconSVG name="Play" size={14}/></button>
                                    )}
                                    {o.status !== 'cancelled' && o.status !== 'finished' && (
                                        <button className="icon-btn-action cancel" title="Cancel" onClick={()=>handleAction(o.id, 'cancel')}><IconSVG name="Square" size={14}/></button>
                                    )}
                                    {(o.status === 'cancelled' || o.status === 'finished') && (
                                        <button className="icon-btn-action delete" title="Delete" onClick={()=>handleDelete(o.id)}><IconSVG name="Trash2" size={14}/></button>
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
export default OrdersPage;