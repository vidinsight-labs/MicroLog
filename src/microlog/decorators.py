"""
decorators.py — Logging Decorators

Bu modül ne yapar?
- Fonksiyon ve metodları otomatik loglayan decorator'lar
- @log_function: Fonksiyon çağrılarını loglar
- @log_exception: Exception'ları otomatik yakalar ve loglar
- @log_performance: Fonksiyon süresini ölçer ve loglar
"""

from __future__ import annotations

import logging
import functools
import time
from typing import Callable, Any, Optional
from contextlib import contextmanager

from .context import get_current_context


# ═══════════════════════════════════════════════════════════════════════════════
# LOG FUNCTION DECORATOR
# ═══════════════════════════════════════════════════════════════════════════════

def log_function(
    logger: Optional[logging.Logger] = None,
    level: int = logging.DEBUG,
    log_args: bool = True,
    log_result: bool = False,
    log_trace: bool = True
):
    """
    Fonksiyon çağrılarını otomatik loglar.
    
    Args:
        logger:     Logger instance (default: fonksiyonun modülünden alınır)
        level:      Log seviyesi (default: DEBUG)
        log_args:   Fonksiyon argümanlarını logla
        log_result: Fonksiyon sonucunu logla
        log_trace:  Trace context bilgilerini ekle
    
    Kullanım:
        @log_function(log_args=True, log_result=True)
        def process_order(order_id: str, amount: float):
            return {"status": "processed"}
    """
    def decorator(func: Callable) -> Callable:
        nonlocal logger
        if logger is None:
            logger = logging.getLogger(func.__module__)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Trace context bilgilerini al
            ctx = get_current_context()
            trace_info = ctx.to_dict() if ctx else {}
            
            # Fonksiyon bilgileri
            func_name = f"{func.__module__}.{func.__qualname__}"
            
            # Log başlangıcı
            log_data = {
                "function": func_name,
                "event": "function_call",
                **trace_info
            }
            
            if log_args:
                log_data["func_args"] = str(args) if args else None
                log_data["func_kwargs"] = str(kwargs) if kwargs else None
            
            logger.log(level, f"Calling {func_name}", extra=log_data)
            
            try:
                # Fonksiyonu çalıştır
                result = func(*args, **kwargs)
                
                # Sonuç logla
                if log_result:
                    result_data = {
                        "function": func_name,
                        "event": "function_success",
                        "result": str(result)[:200],  # İlk 200 karakter
                        **trace_info
                    }
                    logger.log(level, f"{func_name} completed", extra=result_data)
                else:
                    logger.log(level, f"{func_name} completed", extra={
                        "function": func_name,
                        "event": "function_success",
                        **trace_info
                    })
                
                return result
            
            except Exception as e:
                # Exception logla
                logger.exception(
                    f"{func_name} failed: {e}",
                    extra={
                        "function": func_name,
                        "event": "function_error",
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        **trace_info
                    }
                )
                raise
        
        return wrapper
    return decorator


# ═══════════════════════════════════════════════════════════════════════════════
# LOG EXCEPTION DECORATOR
# ═══════════════════════════════════════════════════════════════════════════════

def log_exception(
    logger: Optional[logging.Logger] = None,
    level: int = logging.ERROR,
    reraise: bool = True,
    log_trace: bool = True
):
    """
    Exception'ları otomatik yakalar ve loglar.
    
    Args:
        logger:     Logger instance (default: fonksiyonun modülünden alınır)
        level:      Log seviyesi (default: ERROR)
        reraise:    Exception'ı tekrar fırlat (default: True)
        log_trace:  Trace context bilgilerini ekle
    
    Kullanım:
        @log_exception(reraise=False)
        def risky_operation():
            raise ValueError("Something went wrong")
    """
    def decorator(func: Callable) -> Callable:
        nonlocal logger
        if logger is None:
            logger = logging.getLogger(func.__module__)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Trace context bilgilerini al
                ctx = get_current_context()
                trace_info = ctx.to_dict() if ctx else {}
                
                func_name = f"{func.__module__}.{func.__qualname__}"
                
                logger.log(
                    level,
                    f"Exception in {func_name}: {type(e).__name__} - {e}",
                    exc_info=True,
                    extra={
                        "function": func_name,
                        "event": "exception",
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        **trace_info
                    }
                )
                
                if reraise:
                    raise
                return None
        
        return wrapper
    return decorator


# ═══════════════════════════════════════════════════════════════════════════════
# LOG PERFORMANCE DECORATOR
# ═══════════════════════════════════════════════════════════════════════════════

def log_performance(
    logger: Optional[logging.Logger] = None,
    level: int = logging.INFO,
    threshold: float = 0.0,
    log_trace: bool = True
):
    """
    Fonksiyon süresini ölçer ve loglar.
    
    Args:
        logger:     Logger instance (default: fonksiyonun modülünden alınır)
        level:      Log seviyesi (default: INFO)
        threshold:  Sadece bu süreyi aşan çağrıları logla (saniye)
        log_trace:  Trace context bilgilerini ekle
    
    Kullanım:
        @log_performance(threshold=1.0)  # 1 saniyeden uzun sürenleri logla
        def slow_operation():
            time.sleep(2)
    """
    def decorator(func: Callable) -> Callable:
        nonlocal logger
        if logger is None:
            logger = logging.getLogger(func.__module__)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = time.perf_counter() - start_time
                
                if elapsed >= threshold:
                    # Trace context bilgilerini al
                    ctx = get_current_context()
                    trace_info = ctx.to_dict() if ctx else {}
                    
                    func_name = f"{func.__module__}.{func.__qualname__}"
                    
                    logger.log(
                        level,
                        f"{func_name} took {elapsed:.4f}s",
                        extra={
                            "function": func_name,
                            "event": "performance",
                            "duration_seconds": elapsed,
                            "duration_ms": elapsed * 1000,
                            **trace_info
                        }
                    )
        
        return wrapper
    return decorator


# ═══════════════════════════════════════════════════════════════════════════════
# LOG CONTEXT MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

@contextmanager
def log_context(
    message: str,
    logger: Optional[logging.Logger] = None,
    level: int = logging.INFO,
    log_trace: bool = True
):
    """
    Context manager ile log başlangıç/bitiş logları.
    
    Args:
        message:    Log mesajı
        logger:     Logger instance
        level:      Log seviyesi
        log_trace:  Trace context bilgilerini ekle
    
    Kullanım:
        with log_context("Processing batch", logger):
            # İşlemler
            pass
    """
    if logger is None:
        import inspect
        frame = inspect.currentframe()
        if frame and frame.f_back:
            logger = logging.getLogger(frame.f_back.f_globals.get('__name__', 'root'))
        else:
            logger = logging.getLogger()
    
    # Trace context bilgilerini al
    ctx = get_current_context()
    trace_info = ctx.to_dict() if ctx and log_trace else {}
    
    start_time = time.perf_counter()
    
    logger.log(
        level,
        f"{message} - started",
        extra={
            "event": "context_start",
            "context_message": message,  # "message" rezerve alanıyla çakışmasın
            **trace_info
        }
    )
    
    try:
        yield
        elapsed = time.perf_counter() - start_time
        
        logger.log(
            level,
            f"{message} - completed in {elapsed:.4f}s",
            extra={
                "event": "context_end",
                "context_message": message,
                "duration_seconds": elapsed,
                "duration_ms": elapsed * 1000,
                **trace_info
            }
        )
    except Exception as e:
        elapsed = time.perf_counter() - start_time
        
        logger.exception(
            f"{message} - failed after {elapsed:.4f}s: {e}",
            extra={
                "event": "context_error",
                "context_message": message,
                "duration_seconds": elapsed,
                "duration_ms": elapsed * 1000,
                "error_type": type(e).__name__,
                "error_message": str(e),
                **trace_info
            }
        )
        raise
