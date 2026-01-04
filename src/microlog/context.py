"""
context.py — Trace ve Span ID Yönetimi

Bu modül ne yapar?
- Thread-safe context yönetimi (her thread kendi context'ini görür)
- Her request için benzersiz trace_id, span_id üretir
- Mikroservisler arası ID propagation sağlar

Kullanım:
    from microlog import trace
    
    with trace() as ctx:
        print(ctx.trace_id)      # "abc123..."
        print(ctx.headers())     # {"X-Trace-ID": "abc123...", ...}
"""

from __future__ import annotations

import uuid
import threading
from contextvars import ContextVar
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone


# ═══════════════════════════════════════════════════════════════════════════════
# YARDIMCI FONKSİYONLAR
# ═══════════════════════════════════════════════════════════════════════════════

def _generate_id() -> str:
    """
    Kısa ve benzersiz ID üretir.
    
    UUID'nin ilk 16 karakterini alır.
    Örnek: "a1b2c3d4e5f6g7h8"
    """
    return uuid.uuid4().hex[:16]


def _now_iso() -> str:
    """
    ISO 8601 formatında UTC timestamp döndürür.
    
    Örnek: "2024-01-15T14:32:01.123456+00:00"
    """
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


# ═══════════════════════════════════════════════════════════════════════════════
# TRACE CONTEXT SINIFI
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class TraceContext:
    """
    Bir request'in tüm trace bilgilerini tutar.
    
    Bu sınıf, mikroservis mimarisinde bir isteğin
    tüm servisler boyunca takip edilmesini sağlar.
    
    Attributes:
        trace_id:        Tüm servisler boyunca AYNI kalan ID
                         Bir kullanıcı isteğinin tüm yolculuğunu temsil eder
        
        span_id:         Bu OPERASYONA özgü ID
                         Her servis çağrısı yeni span_id alır
        
        parent_span_id:  Üst operasyonun span_id'si
                         "Bu operasyonu kim çağırdı?" sorusuna cevap
        
        correlation_id:  İş akışı bazlı gruplama ID'si
                         Örn: Bir sipariş sürecindeki tüm işlemler
        
        session_id:      Kullanıcı oturum ID'si
                         Login-logout arası tüm işlemler
        
        started_at:      Context'in oluşturulma zamanı
        
        extra:           Ek alanlar (user_id, tenant_id vs.)
    
    Örnek:
        ┌─────────────────────────────────────────────────────┐
        │ trace_id: "abc123"  (tüm servisler boyunca aynı)    │
        │                                                     │
        │  ┌─────────────────┐    ┌─────────────────┐         │
        │  │ Gateway         │───▶│ Auth            │         │
        │  │ span_id: "001"  │    │ span_id: "002"  │         │
        │  │ parent: null    │    │ parent: "001"   │         │
        │  └─────────────────┘    └─────────────────┘         │
        └─────────────────────────────────────────────────────┘
    """
    # Trace ID - tüm servisler boyunca aynı
    trace_id: str = field(default_factory=_generate_id)

    # Span ID - bu operasyona özgü
    span_id: str = field(default_factory=_generate_id)
    
    # Parent Span ID - kim çağırdı?
    parent_span_id: Optional[str] = None
    
    # Correlation ID - iş akışı bazlı
    correlation_id: Optional[str] = None
    
    # Session ID - kullanıcı oturumu
    session_id: Optional[str] = None
    
    # Başlangıç zamanı
    started_at: str = field(default_factory=_now_iso)
    
    # Ek alanlar
    extra: Dict[str, Any] = field(default_factory=dict)

    def child_span(self) -> TraceContext:
        """
        Bu context'ten yeni bir child span oluşturur.
        
        Child span:
        - Aynı trace_id'yi kullanır
        - Yeni span_id alır
        - Bu span'ın span_id'si, child'ın parent_span_id'si olur
        
        Kullanım:
            with trace() as parent:
                child = parent.child_span()
                # child.parent_span_id == parent.span_id
        
        Returns:
            Yeni TraceContext instance
        """
        return TraceContext(
            trace_id=self.trace_id,           # Aynı trace
            span_id=_generate_id(),           # Yeni span
            parent_span_id=self.span_id,      # Ben parent'ım
            correlation_id=self.correlation_id,
            session_id=self.session_id,
            extra=self.extra.copy()
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Context'i dict olarak döndürür.
        
        Bu dict, log kayıtlarına eklenir.
        
        Returns:
            {"trace_id": "...", "span_id": "...", ...}
        """
        result = {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
        }
        
        # Opsiyonel alanları sadece varsa ekle
        if self.parent_span_id:
            result["parent_span_id"] = self.parent_span_id
        if self.correlation_id:
            result["correlation_id"] = self.correlation_id
        if self.session_id:
            result["session_id"] = self.session_id
        
        # Extra alanları ekle
        result.update(self.extra)
        return result

    def headers(self) -> Dict[str, str]:
        """
        HTTP header'ları olarak döndürür.
        
        Servisler arası iletişimde bu header'lar
        request'e eklenir.
        
        Returns:
            {
                "X-Trace-ID": "abc123",
                "X-Span-ID": "span001",
                "X-Correlation-ID": "order-789",
                ...
            }
        
        Kullanım:
            with trace() as ctx:
                response = requests.post(
                    "http://other-service/api",
                    headers=ctx.headers()
                )
        """
        headers = {
            "X-Trace-ID": self.trace_id,
            "X-Span-ID": self.span_id,
        }
        
        if self.parent_span_id:
            headers["X-Parent-Span-ID"] = self.parent_span_id
        if self.correlation_id:
            headers["X-Correlation-ID"] = self.correlation_id
        if self.session_id:
            headers["X-Session-ID"] = self.session_id
        
        return headers

    @classmethod
    def from_headers(cls, headers: Dict[str, str]) -> TraceContext:
        """
        HTTP header'larından context oluşturur.
        
        Gelen request'in header'larından trace bilgilerini
        çıkarır ve yeni context oluşturur.
        
        Args:
            headers: HTTP request headers
        
        Returns:
            Yeni TraceContext instance
        
        Kullanım:
            # Flask/FastAPI handler'da
            ctx = TraceContext.from_headers(request.headers)
        """
        return cls(
            trace_id=headers.get("X-Trace-ID", _generate_id()),
            span_id=_generate_id(),  # Yeni span oluştur
            parent_span_id=headers.get("X-Span-ID"),  # Gelen span, bizim parent'ımız
            correlation_id=headers.get("X-Correlation-ID"),
            session_id=headers.get("X-Session-ID"),
        )


# ═══════════════════════════════════════════════════════════════════════════════
# CONTEXT STORAGE (Thread-Safe)
# ═══════════════════════════════════════════════════════════════════════════════

# ContextVar: Python 3.7+ ile gelen async-safe context storage
# Her asyncio task ve thread kendi değerini görür
_context_var: ContextVar[Optional[TraceContext]] = ContextVar(
    "trace_context", 
    default=None
)

# Thread-local fallback (eski Python veya özel durumlar için)
_thread_local = threading.local()

def get_current_context() -> Optional[TraceContext]:
    """
    Mevcut thread/task için aktif context'i döndürür.
    
    Logger bu fonksiyonu çağırarak trace bilgilerini alır.
    
    Returns:
        Aktif TraceContext veya None
    """
    # Önce ContextVar'ı dene (async-safe)
    ctx = _context_var.get()
    if ctx is not None:
        return ctx
    
    # Fallback: thread-local
    return getattr(_thread_local, "context", None)


def set_current_context(ctx: Optional[TraceContext]) -> None:
    """
    Mevcut thread/task için context'i ayarlar.
    
    Args:
        ctx: TraceContext instance veya None
    """
    _context_var.set(ctx)
    _thread_local.context = ctx

# ═══════════════════════════════════════════════════════════════════════════════
# TRACE CONTEXT MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class trace:
    """
    Trace context manager.
    
    `with` bloğu içinde trace context oluşturur ve yönetir.
    Blok bittiğinde önceki context'e geri döner.
    
    Kullanım Örnekleri:
    
        # 1. Yeni trace başlat
        with trace() as ctx:
            log.info("İstek alındı")  # trace_id otomatik eklenir
        
        # 2. Correlation ID ile
        with trace(correlation_id="order-123") as ctx:
            log.info("Sipariş işleniyor")
        
        # 3. Gelen request'ten devam et
        with trace(headers=request.headers) as ctx:
            log.info("Request işleniyor")
            # trace_id korunur, yeni span_id oluşur
        
        # 4. Parent context'ten child span
        with trace() as parent:
            with trace(parent=parent) as child:
                # child.parent_span_id == parent.span_id
        
        # 5. Extra alanlarla
        with trace(user_id="usr-456", tenant_id="acme") as ctx:
            log.info("User action")
            # user_id ve tenant_id loglara eklenir
    """
    
    def __init__(
        self,
        trace_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        session_id: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        parent: Optional[TraceContext] = None,
        **extra
    ):
        """
        Args:
            trace_id:       Belirli bir trace_id kullan (opsiyonel)
            correlation_id: İş akışı ID'si
            session_id:     Oturum ID'si
            headers:        HTTP header'larından context oluştur
            parent:         Parent context'ten child span oluştur
            **extra:        Ek alanlar (loglara eklenir)
        """
        self.previous_context: Optional[TraceContext] = None
        self.context: Optional[TraceContext] = None
        
        if headers:
            # HTTP header'larından oluştur
            self.context = TraceContext.from_headers(headers)
            if correlation_id:
                self.context.correlation_id = correlation_id
            if session_id:
                self.context.session_id = session_id
            self.context.extra.update(extra)
        
        elif parent:
            # Parent context'ten child span oluştur
            self.context = parent.child_span()
            if correlation_id:
                self.context.correlation_id = correlation_id
            if session_id:
                self.context.session_id = session_id
            self.context.extra.update(extra)
        
        else:
            # Yeni trace başlat
            self.context = TraceContext(
                trace_id=trace_id or _generate_id(),
                correlation_id=correlation_id,
                session_id=session_id,
                extra=extra
            )
    
    def __enter__(self) -> TraceContext:
        """
        Context manager giriş noktası.
        
        Mevcut context'i saklar ve yeni context'i aktif yapar.
        """
        self.previous_context = get_current_context()
        set_current_context(self.context)
        return self.context
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Context manager çıkış noktası.
        
        Önceki context'e geri döner.
        """
        set_current_context(self.previous_context)
        return None
    
    # ─────────────────────────────────────────────────────────────
    # Async context manager desteği
    # ─────────────────────────────────────────────────────────────
    
    async def __aenter__(self) -> TraceContext:
        """Async context manager giriş noktası."""
        return self.__enter__()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager çıkış noktası."""
        return self.__exit__(exc_type, exc_val, exc_tb)


# ═══════════════════════════════════════════════════════════════════════════════
# YARDIMCI FONKSİYONLAR
# ═══════════════════════════════════════════════════════════════════════════════

def create_trace(**kwargs) -> TraceContext:
    """
    Yeni bir TraceContext oluşturur (context manager olmadan).
    
    Context manager kullanmadan sadece context oluşturmak
    istediğinde kullan.
    
    Kullanım:
        ctx = create_trace(correlation_id="order-123")
        headers = ctx.headers()
    
    Returns:
        Yeni TraceContext instance
    """
    return TraceContext(**kwargs)