import React from 'react';

export default function ConfirmModal({ isOpen, message, confirmLabel = 'Delete', onConfirm, onCancel, danger = true }) {
    if (!isOpen) return null;
    return (
        <div className="modal-overlay" onClick={onCancel}>
            <div className="modal modal-sm" onClick={e => e.stopPropagation()}>
                <div className="modal-body" style={{ textAlign: 'center', padding: '28px 24px 20px' }}>
                    <p style={{ marginBottom: 24, fontSize: 15, lineHeight: 1.5 }}>{message}</p>
                    <div style={{ display: 'flex', gap: 10, justifyContent: 'center' }}>
                        <button className="btn-secondary" onClick={onCancel}>Cancel</button>
                        <button
                            className={danger ? 'btn-danger' : 'btn-primary'}
                            onClick={onConfirm}
                        >
                            {confirmLabel}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
