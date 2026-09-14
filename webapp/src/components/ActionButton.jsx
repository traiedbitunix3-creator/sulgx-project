import React from "react";

export default function ActionButton({ icon, label, onClick, variant = "primary", disabled }) {
  return (
    <button
      className={`action-btn action-btn-${variant}`}
      onClick={onClick}
      disabled={disabled}
    >
      <span className="action-btn-icon">{icon}</span>
      <span>{label}</span>
    </button>
  );
}
