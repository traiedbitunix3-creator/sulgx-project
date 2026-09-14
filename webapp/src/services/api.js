import { getInitData } from "../telegram.js";

// اگر VITE_API_BASE_URL ست نشده باشد (حالت پیش‌فرض روی Railway)، رشته‌ی
// خالی یعنی درخواست‌ها به همان دامنه‌ای که WebApp از آن سرو شده ارسال
// می‌شوند (same-origin) — بک‌اند FastAPI همین دامنه را serve می‌کند.
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-Telegram-Init-Data": getInitData(),
      ...(options.headers || {}),
    },
  });

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new Error(data.detail || "خطای ارتباط با سرور");
  }
  return data;
}

export const api = {
  getProfile: () => request("/user/profile"),
  getConfigs: () => request("/user/configs"),
  createConfig: (payload) =>
    request("/config/create", { method: "POST", body: JSON.stringify(payload) }),
  renewConfig: (payload) =>
    request("/config/renew", { method: "POST", body: JSON.stringify(payload) }),
  resetLink: (payload) =>
    request("/config/reset-link", { method: "POST", body: JSON.stringify(payload) }),
  deleteConfig: (payload) =>
    request("/config/delete", { method: "POST", body: JSON.stringify(payload) }),
};
