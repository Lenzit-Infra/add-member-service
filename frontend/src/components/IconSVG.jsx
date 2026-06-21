import React from 'react';

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
        CheckCircle: "M22 11.08V12a10 10 0 1 1-5.93-9.14M22 4L12 14.01l-3-3",
        Trash2: "M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m3 0-1 14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2L4 6h16zM10 11v6M14 11v6",
        Ban: "M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zM4.93 4.93l14.14 14.14",
        TrendingUp: "M23 6l-9.5 9.5-5-5L1 18M17 6h6v6",
        RefreshCw: "M21 2v6h-6M3 22v-6h6M3.51 9a9 9 0 0 1 14.85-3.36L21 8M20.49 15a9 9 0 0 1-14.85 3.36L3 16"
    };
    return (
        <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color || "currentColor"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} style={style}>
            <path d={icons[name] || "M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2z"} />
        </svg>
    );
};
export default IconSVG;