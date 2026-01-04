"""
formatter.py — Log Çıktı Formatları

Bu modül ne yapar?
- Log kayıtlarını farklı formatlarda çıktılar
- JSONFormatter: Makineler için (Elasticsearch, Kibana, Loki)
- PrettyFormatter: Terminal için (renkli, okunabilir)
- CompactFormatter: Minimal (production)
"""


from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional
from datetime import datetime, timezone


# ═══════════════════════════════════════════════════════════════════════════════
# JSON FORMATTER
# ═══════════════════════════════════════════════════════════════════════════════

class JSONFormatter(logging.Formatter):
    # ─────────────────────────────────────────────────────────────
    # Python logging'in standart alanları
    # Bu alanlar JSON'a eklenmez (gereksiz/tekrar)
    # ─────────────────────────────────────────────────────────────
    RESERVED_ATTRS = frozenset({
        "name",           # Logger adı (service olarak ekliyoruz)
        "msg",            # Ham mesaj
        "args",           # Format argümanları
        "levelname",      # Level adı (level olarak ekliyoruz)
        "levelno",        # Level numarası
        "pathname",       # Dosya yolu
        "filename",       # Dosya adı
        "module",         # Modül adı
        "exc_info",       # Exception bilgisi
        "exc_text",       # Exception text
        "stack_info",     # Stack bilgisi
        "lineno",         # Satır numarası
        "funcName",       # Fonksiyon adı
        "created",        # Oluşturulma zamanı (float)
        "msecs",          # Milisaniye
        "relativeCreated",# Göreli zaman
        "thread",         # Thread ID
        "threadName",     # Thread adı
        "processName",    # Process adı
        "process",        # Process ID
        "message",        # Formatlanmış mesaj
        "taskName"        # Async task adı (Python 3.12+)
    })

    def __init__(
        self,
        service_name: Optional[str] = None,
        include_extra: bool = True,
        timestamp_format: str = "iso"
    ):
        super().__init__()
        self.service_name = service_name
        self.include_extra = include_extra
        self.timestamp_format = timestamp_format

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": self._get_timestamp(),
            "level": record.levelname,
            "service": self.service_name or record.name,
            "message": record.getMessage(),
        }

        if self.include_extra:
            for key, value in record.__dict__.items():
                if key not in self.RESERVED_ATTRS:
                    log_data[key] = self._serialize_value(value)

        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info)
            }

        return json.dumps(log_data, ensure_ascii=False, default=str)

    def _get_timestamp(self) -> str:
        now = datetime.now(timezone.utc)
        if self.timestamp_format == "unix":
            return str(now.timestamp())

        return now.isoformat(timespec="microseconds")

    def _serialize_value(self, value: Any) -> Any:
        if isinstance(value, (str, int, float, bool, type(None))):
            return value
        if isinstance(value, (list, tuple)):
            return [self._serialize_value(v) for v in value]
        if isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        # Diğer tipler string'e çevrilir
        return str(value)


# ═══════════════════════════════════════════════════════════════════════════════
# PRETTY FORMATTER (Renkli Terminal)
# ═══════════════════════════════════════════════════════════════════════════════

class PrettyFormatter(logging.Formatter):
    """
    Terminal için renkli ve okunabilir log formatı.
    
    Geliştirme ortamında kullanım için ideal.
    
    Örnek çıktı:
        14:32:01 │ INFO     │ order-service   │ Order created │ order_id=ORD-123
        14:32:02 │ ERROR    │ order-service   │ DB error      │ error_code=E001
    
    Renkler:
        DEBUG    → Cyan
        INFO     → Green
        WARNING  → Yellow
        ERROR    → Red
        CRITICAL → Magenta
    """
    
    # ANSI renk kodları
    COLORS = {
        "DEBUG":    "\033[36m",   # Cyan
        "INFO":     "\033[32m",   # Green
        "WARNING":  "\033[33m",   # Yellow
        "ERROR":    "\033[31m",   # Red
        "CRITICAL": "\033[35m",   # Magenta
    }
    RESET = "\033[0m"   # Rengi sıfırla
    DIM = "\033[2m"     # Soluk
    BOLD = "\033[1m"    # Kalın
    
    # Standart logging alanları
    RESERVED_ATTRS = frozenset({
        "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
        "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
        "created", "msecs", "relativeCreated", "thread", "threadName",
        "processName", "process", "message", "taskName"
    })
    
    def __init__(
        self,
        service_name: Optional[str] = None,
        use_colors: bool = True
    ):
        """
        Args:
            service_name: Servis adı (override)
            use_colors:   ANSI renkleri kullan
        """
        super().__init__()
        self.service_name = service_name
        self.use_colors = use_colors
    
    def format(self, record: logging.LogRecord) -> str:
        """Log kaydını okunabilir formata dönüştürür."""
        
        # Zaman (sadece saat:dakika:saniye)
        time_str = datetime.now().strftime("%H:%M:%S")
        
        # Level (renkli veya düz)
        level = record.levelname
        if self.use_colors:
            color = self.COLORS.get(level, "")
            level_str = f"{color}{level:8}{self.RESET}"
        else:
            level_str = f"{level:8}"
        
        # Servis adı
        service = self.service_name or record.name
        
        # Mesaj
        message = record.getMessage()
        
        # Extra alanlar (key=value formatında)
        extras = []
        for key, value in record.__dict__.items():
            if key not in self.RESERVED_ATTRS and not key.startswith("_"):
                if self.use_colors:
                    extras.append(f"{self.DIM}{key}={value}{self.RESET}")
                else:
                    extras.append(f"{key}={value}")
        
        extra_str = " ".join(extras)
        
        # Final format
        if self.use_colors:
            line = f"{self.DIM}{time_str}{self.RESET} │ {level_str} │ {self.BOLD}{service:15}{self.RESET} │ {message}"
        else:
            line = f"{time_str} │ {level_str} │ {service:15} │ {message}"
        
        # Extra alanları ekle
        if extra_str:
            line += f" │ {extra_str}"
        
        # Exception varsa ekle
        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)
        
        return line


# ═══════════════════════════════════════════════════════════════════════════════
# COMPACT FORMATTER (Minimal)
# ═══════════════════════════════════════════════════════════════════════════════

class CompactFormatter(logging.Formatter):
    """
    Minimal tek satır format.
    
    Production log aggregation için ideal.
    Dosya boyutunu küçük tutar.
    
    Örnek çıktı:
        INFO order-service Order created order_id=ORD-123 user_id=usr-456
    """
    
    RESERVED_ATTRS = frozenset({
        "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
        "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
        "created", "msecs", "relativeCreated", "thread", "threadName",
        "processName", "process", "message", "taskName"
    })
    
    def __init__(self, service_name: Optional[str] = None):
        """
        Args:
            service_name: Servis adı (override)
        """
        super().__init__()
        self.service_name = service_name
    
    def format(self, record: logging.LogRecord) -> str:
        """Log kaydını minimal formata dönüştürür."""
        service = self.service_name or record.name
        message = record.getMessage()
        
        # Parçaları birleştir
        parts = [record.levelname, service, message]
        
        # Extra alanları ekle
        for key, value in record.__dict__.items():
            if key not in self.RESERVED_ATTRS and not key.startswith("_"):
                parts.append(f"{key}={value}")
        
        return " ".join(parts)