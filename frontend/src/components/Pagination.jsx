import React from 'react';
import IconSVG from './IconSVG';

export default function Pagination({ page, totalPages, total, onPage }) {
    if (totalPages <= 1) return null;
    return (
        <div className="pagination-bar">
            <button className="icon-btn-action" onClick={() => onPage(page - 1)} disabled={page <= 1} aria-label="Previous page">
                <IconSVG name="ChevronLeft" size={15} />
            </button>
            <span className="pagination-info">Page {page} of {totalPages} — {total} total</span>
            <button className="icon-btn-action" onClick={() => onPage(page + 1)} disabled={page >= totalPages} aria-label="Next page">
                <IconSVG name="ChevronRight" size={15} />
            </button>
        </div>
    );
}
