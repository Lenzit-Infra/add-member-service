import React from 'react';
import IconSVG from './IconSVG';

const GenericListModal = ({ isOpen, onClose, title, items, columns }) => {
    if (!isOpen) return null;
    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal modal-lg" onClick={e => e.stopPropagation()}>
                <div className="modal-header">
                    <h3 className="modal-title">{title}</h3>
                    <button onClick={onClose} className="icon-btn" aria-label="Close"><IconSVG name="X" /></button>
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
export default GenericListModal;