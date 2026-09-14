import React from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { QRCodeSVG } from "qrcode.react";
import { hapticImpact } from "../telegram.js";
import ActionButton from "../components/ActionButton.jsx";

export default function QRPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const link = location.state?.link;

  if (!link) {
    return (
      <div className="page qr-page">
        <p>لینکی برای نمایش وجود ندارد.</p>
        <ActionButton icon="⬅️" label="بازگشت" onClick={() => navigate("/")} />
      </div>
    );
  }

  const copyLink = async () => {
    await navigator.clipboard.writeText(link);
    hapticImpact("medium");
  };

  return (
    <div className="page qr-page">
      <h1 className="page-title">📶 کد QR کانفیگ</h1>

      <div className="qr-box fade-in">
        <QRCodeSVG value={link} size={220} bgColor="transparent" fgColor="#ffffff" />
      </div>

      <div className="link-box">{link}</div>

      <div className="actions-grid">
        <ActionButton icon="📋" label="کپی لینک" onClick={copyLink} />
        <ActionButton icon="⬅️" label="بازگشت به پنل" onClick={() => navigate("/")} />
      </div>
    </div>
  );
}
