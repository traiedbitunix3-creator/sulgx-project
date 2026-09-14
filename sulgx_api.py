"""
sulgx_api.py
=============
تنها نقطه‌ی ارتباط این پروژه با پنل SulgX (نسخه v1.1.0) که روی Railway اجرا
می‌شود (SULGX_BASE_URL). این نسخه مطابق مسیرهای واقعی تأییدشده‌ی API نوشته
شده و هیچ مفهوم قدیمی Inbound / create_client / delete_client در آن وجود
ندارد؛ پنل SulgX یک دامنه/سرور واحد است و هر «کانفیگ» صرفاً یک ردیف در
جدول `links` پنل است.

Endpointهای استفاده‌شده:

    POST   /api/login                -> body: {"password": "..."}
                                         کوکی HttpOnly به نام SulgX_session
                                         (JWT) روی session ست می‌شود.
    GET    /api/links                -> لیست همه‌ی لینک‌ها (کانفیگ‌ها)
    POST   /api/links                -> ساخت لینک جدید
    PATCH  /api/links/{uid}          -> ویرایش / تمدید یک لینک
    DELETE /api/links/{uid}          -> حذف یک لینک
    POST   /api/links/{uid}/new-uuid -> تغییر UUID یک لینک

⚠️ نکته‌ی مهم و صادقانه: لینک VLESS هرگز در این فایل به‌صورت محلی ساخته یا
حدس زده نمی‌شود. لینک همیشه مستقیماً از همان پاسخ JSON پنل SulgX خوانده
می‌شود (تابع `_extract_link`). چون ممکن است نام دقیق کلید این لینک در
پاسخ (مثلاً `link`, `vless_link`, `config_link`, ...) بین نسخه‌های مختلف
پنل شما کمی فرق داشته باشد، این نام از طریق متغیر محیطی SULGX_LINK_FIELD
قابل override است — یک‌بار با DevTools > Network روی پنل واقعی خودتان
پاسخ POST /api/links را چک کنید و اگر کلید پیش‌فرض `link` مطابقت نداشت،
همان‌جا در .env تنظیمش کنید؛ نیازی به تغییر کد نیست.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import settings

logger = logging.getLogger("sulgx_api")


# =====================================================================
# مسیرهای API (قابل override از طریق .env در صورت نیاز)
# =====================================================================
class SulgXEndpoints:
    LOGIN = os.getenv("SULGX_PATH_LOGIN", "/api/login")
    LOGOUT = os.getenv("SULGX_PATH_LOGOUT", "/api/logout")
    ME = os.getenv("SULGX_PATH_ME", "/api/me")

    LINKS = os.getenv("SULGX_PATH_LINKS", "/api/links")  # GET (list) + POST (create)
    LINK_DETAIL = os.getenv("SULGX_PATH_LINK_DETAIL", "/api/links/{uid}")  # PATCH + DELETE
    LINK_NEW_UUID = os.getenv("SULGX_PATH_LINK_NEW_UUID", "/api/links/{uid}/new-uuid")  # POST


# نام کلید(های) احتمالی لینک VLESS در پاسخ پنل. اولین موردی که در پاسخ
# پیدا شود استفاده می‌شود. مقدار اول از SULGX_LINK_FIELD (.env) می‌آید.
_LINK_FIELD_CANDIDATES = [
    f.strip()
    for f in (os.getenv("SULGX_LINK_FIELD", "link") + ",vless_link,config_link,subscription_link,url").split(",")
    if f.strip()
]


class SulgXAPIError(Exception):
    """خطای عمومی ارتباط با پنل SulgX."""

    def __init__(self, message: str, status_code: Optional[int] = None, payload: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class SulgXAuthError(SulgXAPIError):
    """خطای احراز هویت (لاگین ناموفق یا سشن منقضی)."""


@dataclass
class SulgXLink:
    """نمایش یک ردیف واقعی از جدول links در پنل SulgX (به‌همراه لینک واقعی)."""

    uid: str
    label: str
    limit_bytes: int
    used_bytes: int
    max_connections: int
    active: bool
    expires_at: Optional[str]
    link: str = ""  # لینک VLESS واقعی، مستقیماً از پاسخ پنل
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def limit_gb(self) -> float:
        return self.limit_bytes / (1024**3) if self.limit_bytes else 0.0

    @property
    def used_gb(self) -> float:
        return self.used_bytes / (1024**3)


class SulgXAPI:
    """
    کلاینت همگام (sync) برای ارتباط با SulgX Panel.
    از requests.Session با retry و کوکی JWT (SulgX_session) استفاده می‌کند.
    چون پروژه در بات/بک‌اند async است، این متدها باید با asyncio.to_thread
    فراخوانی شوند (همان‌طور که در backend/services/config_service.py انجام شده).
    """

    def __init__(
        self,
        base_url: str = settings.SULGX_BASE_URL,
        admin_password: str = settings.SULGX_ADMIN_PASSWORD,
        verify_ssl: bool = settings.SULGX_VERIFY_SSL,
        timeout: int = settings.SULGX_REQUEST_TIMEOUT,
    ):
        if not base_url:
            raise ValueError("SULGX_BASE_URL تنظیم نشده است (Environment Variables را در Railway بررسی کنید)")

        self.base_url = base_url.rstrip("/")
        self.admin_password = admin_password
        self.verify_ssl = verify_ssl
        self.timeout = timeout

        self.session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[502, 503, 504],
            allowed_methods=["GET", "POST", "PATCH", "DELETE"],
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        self._authenticated = False

    # ------------------------------------------------------------------
    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        auth_retry: bool = True,
    ) -> Any:
        if not self._authenticated:
            self.login()

        url = self._url(path)
        try:
            resp = self.session.request(
                method, url, json=json_body, params=params, timeout=self.timeout, verify=self.verify_ssl
            )
        except requests.RequestException as exc:
            logger.error("SulgX request failed: %s %s -> %s", method, url, exc)
            raise SulgXAPIError(f"خطا در اتصال به پنل SulgX: {exc}") from exc

        if resp.status_code in (401, 403):
            if auth_retry:
                logger.warning("SulgX session expired, re-authenticating...")
                self._authenticated = False
                self.login()
                return self._request(method, path, json_body=json_body, params=params, auth_retry=False)
            raise SulgXAuthError("احراز هویت با پنل SulgX ناموفق بود (سشن نامعتبر)", resp.status_code)

        if resp.status_code >= 400:
            try:
                payload = resp.json()
            except ValueError:
                payload = resp.text
            logger.error("SulgX API error %s %s -> %s: %s", method, url, resp.status_code, payload)
            raise SulgXAPIError(f"خطای پنل SulgX ({resp.status_code}) روی {path}", resp.status_code, payload)

        if not resp.content:
            return None
        try:
            return resp.json()
        except ValueError:
            return resp.text

    # ------------------------------------------------------------------
    # login / logout  — POST /api/login با body {"password": ...}
    # ------------------------------------------------------------------
    def login(self) -> bool:
        url = self._url(SulgXEndpoints.LOGIN)
        try:
            resp = self.session.post(
                url, json={"password": self.admin_password}, timeout=self.timeout, verify=self.verify_ssl
            )
        except requests.RequestException as exc:
            raise SulgXAPIError(f"عدم دسترسی به پنل SulgX هنگام لاگین: {exc}") from exc

        if resp.status_code >= 400:
            raise SulgXAuthError("پسورد ادمین پنل SulgX نادرست است یا پنل در دسترس نیست", resp.status_code)

        # کوکی HttpOnly به نام SulgX_session به‌صورت خودکار توسط requests.Session
        # ذخیره و در درخواست‌های بعدی ارسال می‌شود.
        self._authenticated = True
        logger.info("SulgX login OK (cookie SulgX_session set)")
        return True

    def logout(self) -> None:
        try:
            self._request("POST", SulgXEndpoints.LOGOUT, auth_retry=False)
        except SulgXAPIError:
            pass
        self._authenticated = False

    def check_connection(self) -> bool:
        """برای بررسی سریع سلامت اتصال (مثلاً از پنل ادمین بات)."""
        self._request("GET", SulgXEndpoints.ME)
        return True

    # ------------------------------------------------------------------
    # GET /api/links  — لیست همه‌ی لینک‌ها
    # ------------------------------------------------------------------
    def list_links(self) -> List[SulgXLink]:
        data = self._request("GET", SulgXEndpoints.LINKS)
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("links") or data.get("data") or data.get("items") or []
        else:
            items = []
        return [self._parse_link(item) for item in items if isinstance(item, dict)]

    def get_link(self, uid: str) -> Optional[SulgXLink]:
        """چون endpoint اختصاصی GET /api/links/{uid} در این نسخه استفاده نمی‌شود،
        از همان لیست کامل فیلتر می‌کنیم (endpointهای رسمی این پروژه فقط
        همان‌هایی هستند که در بالای فایل مستند شده‌اند)."""
        for link in self.list_links():
            if link.uid == str(uid):
                return link
        return None

    # ------------------------------------------------------------------
    # POST /api/links  — ساخت لینک جدید
    # ------------------------------------------------------------------
    def create_link(
        self,
        *,
        label: str,
        limit_bytes: int,
        max_connections: int,
        expiry_days: int,
        uid: Optional[str] = None,
        active: bool = True,
    ) -> SulgXLink:
        body: Dict[str, Any] = {
            "label": label,
            "limit_bytes": limit_bytes,
            "max_connections": max_connections,
            "expiry_days": expiry_days,
            "active": active,
        }
        if uid:
            body["uid"] = uid

        data = self._request("POST", SulgXEndpoints.LINKS, json_body=body)
        if not data:
            raise SulgXAPIError("پاسخ خالی از پنل SulgX هنگام ساخت لینک دریافت شد")
        return self._parse_link(data if isinstance(data, dict) else {})

    # ------------------------------------------------------------------
    # PATCH /api/links/{uid}  — ویرایش/تمدید یک لینک
    # ------------------------------------------------------------------
    def update_link(self, uid: str, **fields: Any) -> SulgXLink:
        path = SulgXEndpoints.LINK_DETAIL.format(uid=uid)
        body = {k: v for k, v in fields.items() if v is not None}

        data = self._request("PATCH", path, json_body=body)
        if not data:
            link = self.get_link(uid)
            if link is None:
                raise SulgXAPIError("لینک پس از بروزرسانی روی پنل پیدا نشد")
            return link
        return self._parse_link(data if isinstance(data, dict) else {})

    # ------------------------------------------------------------------
    # DELETE /api/links/{uid}  — حذف یک لینک
    # ------------------------------------------------------------------
    def delete_link(self, uid: str) -> bool:
        path = SulgXEndpoints.LINK_DETAIL.format(uid=uid)
        self._request("DELETE", path)
        return True

    # ------------------------------------------------------------------
    # POST /api/links/{uid}/new-uuid  — تغییر UUID یک لینک
    # ------------------------------------------------------------------
    def rotate_uuid(self, uid: str) -> SulgXLink:
        path = SulgXEndpoints.LINK_NEW_UUID.format(uid=uid)
        data = self._request("POST", path)
        if not data:
            raise SulgXAPIError("پاسخ خالی از پنل SulgX هنگام تغییر UUID دریافت شد")
        return self._parse_link(data if isinstance(data, dict) else {})

    # ------------------------------------------------------------------
    def _extract_link(self, data: Dict[str, Any]) -> str:
        for key in _LINK_FIELD_CANDIDATES:
            value = data.get(key)
            if isinstance(value, str) and value:
                return value
        nested = data.get("data") if isinstance(data.get("data"), dict) else None
        if nested:
            for key in _LINK_FIELD_CANDIDATES:
                value = nested.get(key)
                if isinstance(value, str) and value:
                    return value
        return ""

    def _parse_link(self, data: Dict[str, Any]) -> SulgXLink:
        return SulgXLink(
            uid=str(data.get("uid") or data.get("id") or ""),
            label=data.get("label", "") or "",
            limit_bytes=int(data.get("limit_bytes", 0) or 0),
            used_bytes=int(data.get("used_bytes", 0) or 0),
            max_connections=int(data.get("max_connections", 0) or 0),
            active=bool(data.get("active", True)),
            expires_at=data.get("expires_at") or data.get("expiry_date"),
            link=self._extract_link(data),
            raw=data,
        )


# نمونه‌ی singleton برای استفاده در سراسر پروژه
sulgx_client = SulgXAPI() if settings.SULGX_BASE_URL else None
