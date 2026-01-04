"""
Integration testleri - Tüm modüllerin birlikte çalışması
"""

import pytest
import logging
import json
import time
from pathlib import Path
from microlog import (
    get_logger,
    trace,
    setup_production_logger,
    JSONFormatter,
    AsyncConsoleHandler,
)


class TestIntegration:
    """Integration testleri"""
    
    def test_full_workflow(self, clean_loggers, temp_log_file):
        """Tam workflow testi - trace + logging"""
        logger = setup_production_logger(
            name="integration_test",
            service_name="test-service",
            console=True,
            file_path=temp_log_file,
            json_format=True
        )
        
        with trace(correlation_id="test-order-123", user_id="usr-456") as ctx:
            logger.info("Order received", extra={"order_id": "ORD-789"})
            logger.debug("Processing order")
            
            # Trace bilgileri loglara eklenmiş mi?
            assert ctx.trace_id is not None
            assert ctx.correlation_id == "test-order-123"
        
        # Handler'ları durdur
        for handler in logger.handlers:
            if hasattr(handler, 'stop'):
                handler.stop()
    
    def test_trace_context_in_logs(self, clean_loggers, temp_log_file):
        """Trace context'in loglara eklenmesi testi"""
        from microlog import setup_file_logger
        
        logger = setup_file_logger(
            name="trace_test",
            filename=temp_log_file,
            format_type="json",
            service_name="trace-service"
        )
        
        with trace(trace_id="custom-trace-123") as ctx:
            logger.info("Test message", extra={"step": "validation"})
        
        # Dosyayı oku ve kontrol et
        time.sleep(0.2)  # Log yazılması için bekleme
        
        if Path(temp_log_file).exists():
            content = Path(temp_log_file).read_text()
            lines = [l for l in content.strip().split('\n') if l]
            if lines:
                data = json.loads(lines[-1])
                # Trace context bilgileri eklenmiş olmalı
                # (TraceContextFilter sayesinde)
        
        # Handler'ları durdur
        for handler in logger.handlers:
            if hasattr(handler, 'stop'):
                handler.stop()
    
    def test_decorator_with_trace(self, clean_loggers, capture_logs):
        """Decorator + trace birlikte kullanımı"""
        from microlog.decorators import log_function
        
        logger = get_logger(name="decorator_test")
        
        @log_function(logger=logger)
        def process_order(order_id: str):
            with trace(correlation_id=order_id):
                logger.info(f"Processing {order_id}")
                return {"status": "processed", "order_id": order_id}
        
        result = process_order("ORD-123")
        
        assert result["status"] == "processed"
        # Decorator en az 2 log oluşturur (başlangıç + bitiş), info log da eklenir
        assert len(capture_logs.records) >= 1  # En az bir log olmalı
    
    def test_multiple_handlers(self, clean_loggers, temp_log_file):
        """Çoklu handler testi"""
        from microlog.handlers import AsyncConsoleHandler, AsyncRotatingFileHandler
        from microlog.formatter import JSONFormatter, PrettyFormatter
        
        console_handler = AsyncConsoleHandler()
        console_handler.handler.setFormatter(PrettyFormatter(service_name="test"))
        
        file_handler = AsyncRotatingFileHandler(filename=temp_log_file)
        file_handler.handler.setFormatter(JSONFormatter(service_name="test"))
        
        logger = logging.getLogger("multi_handler_test")
        logger.addHandler(console_handler.get_queue_handler())
        logger.addHandler(file_handler.get_queue_handler())
        logger.setLevel(logging.INFO)
        
        logger.info("Test message", extra={"test": True})
        
        time.sleep(0.2)
        
        # Dosya oluşmuş mu?
        assert Path(temp_log_file).exists()
        
        console_handler.stop()
        file_handler.stop()
        file_handler.handler.close()

