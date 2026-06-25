import React, { useState, useEffect, useRef } from 'react';
import client from '../api/client';

const POLL_INTERVAL_MS = 10000;

const formatAge = (iso) => {
    if (!iso) return 'never';
    const seconds = Math.max(0, Math.floor((Date.now() - new Date(iso).getTime()) / 1000));
    if (seconds < 60) return `${seconds}s ago`;
    return `${Math.floor(seconds / 60)}m ago`;
};

const BackendStatus = () => {
    const [data, setData] = useState(null);
    const [reachError, setReachError] = useState(false);
    const timerRef = useRef(null);

    const poll = async () => {
        try {
            const res = await client.get('/health');
            setData(res.data);
            setReachError(false);
        } catch (e) {
            setReachError(true);
        }
    };

    useEffect(() => {
        poll();
        timerRef.current = setInterval(poll, POLL_INTERVAL_MS);
        return () => clearInterval(timerRef.current);
    }, []);

    let level = 'checking'; // checking | ok | degraded | down
    let label = 'Checking...';
    const issues = [];

    if (reachError) {
        level = 'down';
        label = 'Backend Offline';
    } else if (data) {
        if (data.database !== 'ok') issues.push('Database unreachable');
        if (data.worker !== 'ok') issues.push(`Worker ${data.worker}`);
        if (data.telegram_reachable === false) issues.push('Telegram unreachable from server');

        if (issues.length === 0) {
            level = 'ok';
            label = 'All Systems Online';
        } else {
            level = 'degraded';
            label = issues[0];
        }
    }

    const tooltip = data ? [
        `API: ok`,
        `Database: ${data.database}`,
        `Worker: ${data.worker} (heartbeat ${formatAge(data.worker_last_heartbeat)})`,
        `Telegram reachable: ${data.telegram_reachable === null ? 'unknown' : data.telegram_reachable} (checked ${formatAge(data.telegram_checked_at)})`,
    ].join('\n') : 'No response from backend';

    return (
        <div className={`backend-status backend-status-${level}`} title={tooltip}>
            <span className="backend-status-dot" />
            <span>{label}</span>
        </div>
    );
};

export default BackendStatus;
