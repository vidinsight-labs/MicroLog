"""
core.py — Ana Logger Yapılandırması

Bu modül ne yapar?
- Logger oluşturma ve yapılandırma
- Handler ve formatter kurulumu
- Trace context entegrasyonu
- Kolay kullanım için yardımcı fonksiyonlar
"""

from __future__ import annotations

import logging
import sys
from typing import Optional, List, Dict, Any
from logging import Logger

from .handlers import (
    AsyncConsoleHandler,
    AsyncRotatingFileHandler,
    AsyncSMTPHandler
)
from .formatter import (
    JSONFormatter,
    PrettyFormatter,
    CompactFormatter
)
from .context import get_current_context, TraceContext


# ═══════════════════════════════════════════════════════════════════════════════
# TRACE CONTEXT FILTER
# ═══════════════════════════════════════════════════════════════════════════════

class TraceContextFilter(logging.Filter):
    """
    Log kayıtlarına trace context bilgilerini ekler.
    
    Bu filter, her log kaydına aktif trace context'ten
    trace_id, span_id gibi bilgileri otomatik ekler.
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Log kaydını filtreler ve trace bilgilerini ekler."""
        ctx = get_current_context()
        
        if ctx:
            trace_data = ctx.to_dict()
            for key, value in trace_data.items():
                setattr(record, key, value)
        
        return True


# ═══════════════════════════════════════════════════════════════════════════════
# LOGGER CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

def setup_logger(
    name: str = "root",
    level: int = logging.INFO,
    service_name: Optional[str] = None,
    handlers: Optional[List[logging.Handler]] = None,
    formatter: Optional[logging.Formatter] = None,
    add_trace_filter: bool = True
) -> Logger:
    """
    Logger oluşturur ve yapılandırır.
    
    Args:
        name:            Logger adı
        level:           Log seviyesi
        service_name:    Servis adı (formatter'lara geçilir)
        handlers:        Handler listesi (default: console handler)
        formatter:       Formatter (default: PrettyFormatter)
        add_trace_filter: Trace context filter ekle
    
    Returns:
        Yapılandırılmış Logger instance
    
    Kullanım:
        logger = setup_logger(
            name="myapp",
            level=logging.DEBUG,
            service_name="order-service"
        )
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Mevcut handler'ları temizle (tekrar kurulum için)
    logger.handlers.clear()
    
    # Handler'lar yoksa default console handler ekle
    if not handlers:
        console_handler = AsyncConsoleHandler(level=level)
        if formatter:
            console_handler.handler.setFormatter(formatter)
        else:
            # Default formatter
            fmt = PrettyFormatter(service_name=service_name or name)
            console_handler.handler.setFormatter(fmt)
        
        handlers = [console_handler.get_queue_handler()]
    
    # Handler'ları ekle
    for handler in handlers:
        logger.addHandler(handler)
    
    # Trace context filter ekle
    if add_trace_filter:
        trace_filter = TraceContextFilter()
        logger.addFilter(trace_filter)
    
    return logger


def configure_logger(
    logger: Logger,
    level: Optional[int] = None,
    service_name: Optional[str] = None,
    handlers: Optional[List[logging.Handler]] = None,
    formatter: Optional[logging.Formatter] = None,
    add_trace_filter: bool = True
) -> Logger:
    """
    Mevcut logger'ı yapılandırır.
    
    Args:
        logger:          Yapılandırılacak logger
        level:           Log seviyesi
        service_name:    Servis adı
        handlers:        Handler listesi
        formatter:       Formatter
        add_trace_filter: Trace context filter ekle
    
    Returns:
        Yapılandırılmış Logger instance
    """
    if level is not None:
        logger.setLevel(level)
    
    if handlers:
        logger.handlers.clear()
        for handler in handlers:
            logger.addHandler(handler)
    
    if formatter:
        for handler in logger.handlers:
            handler.setFormatter(formatter)
    
    if add_trace_filter:
        # Mevcut filter'ları kontrol et
        has_trace_filter = any(
            isinstance(f, TraceContextFilter) for f in logger.filters
        )
        if not has_trace_filter:
            logger.addFilter(TraceContextFilter())
    
    return logger


# ═══════════════════════════════════════════════════════════════════════════════
# QUICK SETUP FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def setup_console_logger(
    name: str = "root",
    level: int = logging.INFO,
    service_name: Optional[str] = None,
    use_colors: bool = True
) -> Logger:
    """
    Sadece console handler ile logger kurar.
    
    Args:
        name:         Logger adı
        level:        Log seviyesi
        service_name: Servis adı
        use_colors:   Renkli çıktı kullan
    
    Returns:
        Logger instance
    """
    handler = AsyncConsoleHandler(level=level)
    formatter = PrettyFormatter(
        service_name=service_name or name,
        use_colors=use_colors
    )
    handler.handler.setFormatter(formatter)
    
    return setup_logger(
        name=name,
        level=level,
        service_name=service_name,
        handlers=[handler.get_queue_handler()],
        formatter=formatter
    )


def setup_file_logger(
    name: str = "root",
    level: int = logging.INFO,
    service_name: Optional[str] = None,
    filename: str = "app.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    compress: bool = True,
    format_type: str = "json"  # "json", "compact", "pretty"
) -> Logger:
    """
    Sadece file handler ile logger kurar.
    
    Args:
        name:         Logger adı
        level:        Log seviyesi
        service_name: Servis adı
        filename:     Log dosyası yolu
        max_bytes:    Maksimum dosya boyutu
        backup_count: Backup dosya sayısı
        compress:     Sıkıştırma kullan
        format_type:  Format tipi ("json", "compact", "pretty")
    
    Returns:
        Logger instance
    """
    handler = AsyncRotatingFileHandler(
        filename=filename,
        max_bytes=max_bytes,
        backup_count=backup_count,
        compress=compress,
        level=level
    )
    
    if format_type == "json":
        formatter = JSONFormatter(service_name=service_name or name)
    elif format_type == "compact":
        formatter = CompactFormatter(service_name=service_name or name)
    else:
        formatter = PrettyFormatter(service_name=service_name or name, use_colors=False)
    
    handler.handler.setFormatter(formatter)
    
    return setup_logger(
        name=name,
        level=level,
        service_name=service_name,
        handlers=[handler.get_queue_handler()],
        formatter=formatter
    )


def setup_production_logger(
    name: str = "root",
    level: int = logging.INFO,
    service_name: Optional[str] = None,
    console: bool = True,
    file_path: Optional[str] = None,
    json_format: bool = True
) -> Logger:
    """
    Production ortamı için logger kurar (console + file).
    
    Args:
        name:         Logger adı
        level:        Log seviyesi
        service_name: Servis adı
        console:      Console handler ekle
        file_path:    File handler için dosya yolu
        json_format:  JSON format kullan (file için)
    
    Returns:
        Logger instance
    """
    handlers = []
    
    # Console handler
    if console:
        console_handler = AsyncConsoleHandler(level=level)
        console_formatter = CompactFormatter(service_name=service_name or name)
        console_handler.handler.setFormatter(console_formatter)
        handlers.append(console_handler.get_queue_handler())
    
    # File handler
    if file_path:
        file_handler = AsyncRotatingFileHandler(
            filename=file_path,
            level=level
        )
        if json_format:
            file_formatter = JSONFormatter(service_name=service_name or name)
        else:
            file_formatter = CompactFormatter(service_name=service_name or name)
        file_handler.handler.setFormatter(file_formatter)
        handlers.append(file_handler.get_queue_handler())
    
    return setup_logger(
        name=name,
        level=level,
        service_name=service_name,
        handlers=handlers
    )


# ═══════════════════════════════════════════════════════════════════════════════
# GET LOGGER HELPER
# ═══════════════════════════════════════════════════════════════════════════════

def get_logger(
    name: Optional[str] = None,
    service_name: Optional[str] = None
) -> Logger:
    """
    Logger alır veya oluşturur.
    
    Args:
        name:         Logger adı (default: çağıran modülün adı)
        service_name: Servis adı
    
    Returns:
        Logger instance
    
    Kullanım:
        logger = get_logger(service_name="order-service")
        logger.info("Order processed")
    """
    if name is None:
        import inspect
        frame = inspect.currentframe()
        if frame and frame.f_back:
            name = frame.f_back.f_globals.get('__name__', 'root')
        else:
            name = 'root'
    
    logger = logging.getLogger(name)
    
    # Eğer handler yoksa, default console handler ekle
    if not logger.handlers:
        setup_console_logger(
            name=name,
            service_name=service_name or name
        )
        logger = logging.getLogger(name)
    
    return logger
