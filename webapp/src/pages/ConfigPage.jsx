import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api.js";
import { hapticImpact } from "../telegram.js";
import ActionButton from "../components/ActionButton.jsx";

const VOLUMES = [1, 5, 10, 20, 30, 55];
const DAYS = [7, 15, 30];
const DEVICES = [1, 2, 3];

export default function ConfigPage() {
  const [volume, setVolume] = useState(10);
  const [days, setDays] = useState(30);
  const [devices, setDevices] = useState(1);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleCreate = async () => {
    setBusy(true);
    setError("");
    try {
      const res = await api.createConfig({
        name: "My Free Config",
        volume_gb: volume,
        validity_days: days,
        max_connections: devices,
      });
      hapticImpact("heavy");
      navigate("/qr", { state: { link: res.config.link } });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page config-page">
      <h1 className="page-title">🆕 ساخت کانفیگ رایگان</h1>

      <section className="option-group">
        <h3>📦 حجم (GB)</h3>
        <div className="chip-row">
          {VOLUMES.map((v) => (
            <button
              key={v}
              className={`chip ${volume === v ? "chip-selected" : ""}`}
              onClick={() => setVolume(v)}
            >
              {v} GB
            </button>
          ))}
        </div>
      </section>

      <section className="option-group">
        <h3>⏳ مدت اعتبار</h3>
        <div className="chip-row">
          {DAYS.map((d) => (
            <button
              key={d}
              className={`chip ${days === d ? "chip-selected" : ""}`}
              onClick={() => setDays(d)}
            >
              {d} روز
            </button>
          ))}
        </div>
      </section>

      <section className="option-group">
        <h3>📱 تعداد دستگاه</h3>
        <div className="chip-row">
          {DEVICES.map((n) => (
            <button
              key={n}
              className={`chip ${devices === n ? "chip-selected" : ""}`}
              onClick={() => setDevices(n)}
            >
              {n} دستگاه
            </button>
          ))}
        </div>
      </section>

      {error && <div className="error-box">{error}</div>}

      <ActionButton
        icon="✅"
        label={busy ? "در حال ساخت ..." : "ساخت کانفیگ"}
        onClick={handleCreate}
        disabled={busy}
        variant="success"
      />
    </div>
  );
}
