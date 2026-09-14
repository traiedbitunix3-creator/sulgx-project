import React, { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api.js";
import { hapticImpact } from "../telegram.js";
import ServiceCard from "../components/ServiceCard.jsx";
import ActionButton from "../components/ActionButton.jsx";

export default function Dashboard() {
  const [configs, setConfigs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await api.getConfigs();
      setConfigs(data.configs || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const activeConfig = configs[0];

  const handleRefresh = async () => {
    hapticImpact("light");
    await load();
  };

  const handleRenew = async () => {
    if (!activeConfig) return;
    setBusy(true);
    try {
      await api.renewConfig({ config_uuid: activeConfig.uuid, extend_days: 30 });
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const handleResetLink = async () => {
    if (!activeConfig) return;
    setBusy(true);
    try {
      await api.resetLink({ config_uuid: activeConfig.uuid });
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const handleCopySubLink = async () => {
    if (!activeConfig) return;
    await navigator.clipboard.writeText(activeConfig.subscription_link || activeConfig.link);
    hapticImpact("medium");
  };

  return (
    <div className="page dashboard">
      <h1 className="page-title">📊 پنل من</h1>

      {loading && <div className="loader">در حال دریافت اطلاعات ...</div>}
      {error && <div className="error-box">{error}</div>}

      {!loading && !activeConfig && (
        <div className="empty-state">
          <p>هنوز سرویسی ندارید.</p>
          <ActionButton
            icon="🆕"
            label="دریافت کانفیگ رایگان"
            onClick={() => navigate("/create")}
          />
        </div>
      )}

      {activeConfig && (
        <>
          <ServiceCard config={activeConfig} />

          <div className="actions-grid">
            <ActionButton
              icon="📱"
              label="دریافت کانفیگ"
              onClick={() => navigate("/qr", { state: { link: activeConfig.link } })}
            />
            <ActionButton icon="🔗" label="لینک اشتراک" onClick={handleCopySubLink} />
            <ActionButton icon="🔄" label="بروزرسانی" onClick={handleRefresh} disabled={busy} />
            <ActionButton icon="⚙" label="تغییر لینک" onClick={handleResetLink} disabled={busy} variant="warning" />
            <ActionButton icon="💊" label="تمدید" onClick={handleRenew} disabled={busy} variant="success" />
          </div>
        </>
      )}
    </div>
  );
}
