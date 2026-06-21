import React, { useState } from 'react';
import { ordersApi } from '../api';

const CreateOrderModal = ({ isOpen, onClose, onRefresh }) => {
    const [target, setTarget] = useState("");
    const [sources, setSources] = useState("");
    const [count, setCount] = useState(100);

    const handleSubmit = async () => {
        try {
            await ordersApi.create({ target_link: target, source_links: sources.split(','), desired_count: count });
            onRefresh();
            onClose();
        } catch (error) {
            alert("Error creating order");
        }
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
export default CreateOrderModal;