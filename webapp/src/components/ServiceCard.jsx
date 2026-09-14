import React from "react";
import ProgressBar from "./ProgressBar.jsx";

export default function ServiceCard({ config }) {
  const isActive = config.status === "active";
  const remaining = config.remaining_volume_gb;

  return (
    <div className="service-card fade-in">
      <div className="service-card-header">
        <span className={`status-badge ${isActive ? "active" : "inactive"}`}>
          {isActive ? "✅ فعال" : "❌ غیرفعال"}
        </span>
        <span className="service-name">👤 {config.name}</span>
      </div>

      <div className="service-info-grid">
        <div className="info-item">
          <span className="info-icon">🌍</span>
          <span>کشور سرور: —</span>
        </div>
        <div className="info-item">
          <span className="info-icon">🔋</span>
          <span>حجم کل: {config.volume_gb.toFixed(1)} GB</span>
        </div>
        <div className="info-item">
          <span className="info-icon">📥</span>
          <span>مصرف‌شده: {config.used_volume_gb.toFixed(1)} GB</span>
        </div>
        <div className="info-item">
          <span className="info-icon">💢</span>
          <span>باقی‌مانده: {remaining.toFixed(1)} GB</span>
        </div>
        <div className="info-item">
          <span className="info-icon">📅</span>
          <span>انقضا: {new Date(config.expire_date).toLocaleDateString("fa-IR")}</span>
        </div>
        <div className="info-item">
          <span className="info-icon">📶</span>
          <span>
            آخرین اتصال:{" "}
            {config.last_connection_at
              ? new Date(config.last_connection_at).toLocaleString("fa-IR")
              : "ثبت نشده"}
          </span>
        </div>
      </div>

      <ProgressBar used={config.used_volume_gb} total={config.volume_gb} />
    </div>
  );
}
