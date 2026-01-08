"""
Test core.py - Ana Logger Yapılandırması
"""

import pytest
import logging
from microlog.core import (
    setup_logger,
    configure_logger,
    setup_console_logger,
    setup_file_logger,
    TraceContextFilter,
    HandlerConfig,
)


class TestSetupLogger:
    """setup_logger testleri"""
    
    def test_setup_logger_basic(self, clean_loggers):
        """setup_logger temel kullanımını doğrular"""
        logger = setup_logger(name="test_logger", level=logging.DEBUG)
        
        assert logger.name == "test_logger"
        assert logger.level == logging.DEBUG
        assert len(logger.handlers) > 0
    
    def test_setup_logger_with_service_name(self, clean_loggers):
        """setup_logger service_name parametresi ile çalışır"""
        logger = setup_logger(
            name="test_service",
            service_name="order-service",
            level=logging.INFO
        )
        
        assert logger.name == "test_service"
        assert len(logger.handlers) > 0
    
    def test_setup_logger_with_custom_handler(self, clean_loggers):
        """setup_logger özel handler ve formatter ile çalışır"""
        from microlog.handlers import AsyncConsoleHandler
        from microlog.formatters import PrettyFormatter
        
        handler = AsyncConsoleHandler()
        
        logger = setup_logger(
            name="test_custom",
            handlers=[
                HandlerConfig(
                    handler=handler,
                    formatter=PrettyFormatter(service_name="test")
                )
            ]
        )
        
        assert len(logger.handlers) == 1
        handler.stop()


class TestSetupConsoleLogger:
    """setup_console_logger testleri"""
    
    def test_setup_console_logger_basic(self, clean_loggers):
        """setup_console_logger temel kullanımını doğrular"""
        logger = setup_console_logger(
            name="test_console",
            level=logging.INFO
        )
        
        assert logger.name == "test_console"
        assert logger.level == logging.INFO
        assert len(logger.handlers) > 0
    
    def test_setup_console_logger_with_colors(self, clean_loggers):
        """setup_console_logger renkli çıktı desteğini doğrular"""
        logger = setup_console_logger(
            name="test_colors",
            use_colors=True
        )
        
        assert len(logger.handlers) > 0


class TestSetupFileLogger:
    """setup_file_logger testleri"""
    
    def test_setup_file_logger_basic(self, clean_loggers, temp_log_file):
        """setup_file_logger temel kullanımını doğrular"""
        logger = setup_file_logger(
            name="test_file",
            filename=temp_log_file,
            format_type="json"
        )
        
        assert logger.name == "test_file"
        assert len(logger.handlers) > 0
        
        logger.info("Test message")
        
        # Handler'ları durdur
        for handler in logger.handlers:
            if hasattr(handler, 'stop'):
                handler.stop()
    
    def test_setup_file_logger_formats(self, clean_loggers, temp_log_file):
        """setup_file_logger tüm format tiplerini destekler (json, compact, pretty)"""
        for fmt_type in ["json", "compact", "pretty"]:
            log_file = temp_log_file.replace(".log", f"_{fmt_type}.log")
            logger = setup_file_logger(
                name=f"test_{fmt_type}",
                filename=log_file,
                format_type=fmt_type
            )
            
            assert len(logger.handlers) > 0
            
            # Handler'ları durdur
            for handler in logger.handlers:
                if hasattr(handler, 'stop'):
                    handler.stop()


class TestTraceContextFilter:
    """TraceContextFilter testleri"""
    
    def test_trace_context_filter(self, clean_loggers):
        """TraceContextFilter aktif context'ten trace bilgilerini log record'a ekler"""
        from microlog.context import TraceContext, set_current_context
        
        filter_obj = TraceContextFilter()
        
        # Context olmadan
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None
        )
        
        result = filter_obj.filter(record)
        assert result is True
        assert not hasattr(record, "trace_id")
        
        # Context ile
        ctx = TraceContext(trace_id="trace-123", span_id="span-456")
        set_current_context(ctx)
        
        record2 = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None
        )
        
        result2 = filter_obj.filter(record2)
        assert result2 is True
        assert record2.trace_id == "trace-123"
        assert record2.span_id == "span-456"
        
        set_current_context(None)
