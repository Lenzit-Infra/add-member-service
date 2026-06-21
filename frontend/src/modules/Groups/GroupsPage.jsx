import React, { useState, useEffect } from 'react';
import { groupsApi } from './api';
import GenericListModal from '../../components/GenericListModal';
import IconSVG from '../../components/IconSVG';

const colorFor = (id) => {
    const palette = ['#f97316', '#3b82f6', '#10b981', '#8b5cf6', '#ef4444', '#06b6d4'];
    return palette[Math.abs(Number(id) % palette.length) || 0];
};

const GroupsPage = () => {
    const [groups, setGroups] = useState([]);
    const [movements, setMovements] = useState({ isOpen: false, title: '', items: [] });

    useEffect(() => {
        groupsApi.getAll().then(res => setGroups(res.data)).catch(console.error);
    }, []);

    const showMovements = (group) => {
        groupsApi.getMovements(group.id).then(res => {
            setMovements({
                isOpen: true,
                title: `Member Movements — ${group.title}`,
                items: res.data,
            });
        }).catch(console.error);
    };

    if (groups.length === 0) {
        return <div className="empty-state">No groups tracked yet. Groups appear here once used as an Order target or source.</div>;
    }

    return (
        <div>
            <div className="grid-container">
                {groups.map(g => (
                    <div className="group-card" key={g.id}>
                        <div className="group-icon-box" style={{ backgroundColor: colorFor(g.id) }}>
                            {(g.title || '?').charAt(0).toUpperCase()}
                        </div>
                        <h4 className="group-title">{g.title}</h4>
                        <div className="group-type">{g.type || 'group'}{g.is_lenzit_admin ? ' · Admin' : ''}</div>
                        <div className="group-stats">
                            <div className="stat-item">
                                <span className="stat-val">{g.member_count ?? 0}</span>
                                <span className="stat-lbl">Members</span>
                            </div>
                            <div className="stat-item">
                                <span className="stat-val">{g.username ? `@${g.username}` : '-'}</span>
                                <span className="stat-lbl">Username</span>
                            </div>
                        </div>
                        <button className="card-btn" onClick={() => showMovements(g)}>
                            <IconSVG name="RefreshCw" size={14} /> View Movements
                        </button>
                    </div>
                ))}
            </div>

            <GenericListModal
                isOpen={movements.isOpen}
                onClose={() => setMovements({ ...movements, isOpen: false })}
                title={movements.title}
                items={movements.items}
                columns={["Username", "Status", "Joined At", "Left At"]}
            />
        </div>
    );
};

export default GroupsPage;
