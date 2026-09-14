import React, { useEffect } from "react";
import { Route, Routes } from "react-router-dom";
import { initTelegramApp } from "./telegram.js";
import Dashboard from "./pages/Dashboard.jsx";
import ConfigPage from "./pages/ConfigPage.jsx";
import QRPage from "./pages/QRPage.jsx";

export default function App() {
  useEffect(() => {
    initTelegramApp();
  }, []);

  return (
    <div className="app-shell">
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/create" element={<ConfigPage />} />
        <Route path="/qr" element={<QRPage />} />
      </Routes>
    </div>
  );
}
