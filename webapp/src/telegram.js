const tg = window.Telegram?.WebApp;

export function initTelegramApp() {
  if (!tg) return;
  tg.ready();
  tg.expand();
  tg.setHeaderColor("secondary_bg_color");
  tg.setBackgroundColor("#0f0f14");
  tg.enableClosingConfirmation();
}

export function getInitData() {
  return tg?.initData || "";
}

export function getThemeParams() {
  return tg?.themeParams || {};
}

export function hapticImpact(style = "light") {
  tg?.HapticFeedback?.impactOccurred(style);
}

export function showBackButton(onClick) {
  if (!tg) return;
  tg.BackButton.show();
  tg.BackButton.onClick(onClick);
}

export function hideBackButton() {
  tg?.BackButton.hide();
}

export function closeApp() {
  tg?.close();
}

export default tg;
