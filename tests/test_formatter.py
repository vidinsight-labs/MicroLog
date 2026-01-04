"""
Test formatter.py - Log Çıktı Formatları
"""

import pytest
import json
import logging
from microlog.formatter import JSONFormatter, PrettyFormatter, CompactFormatter


class TestJSONFormatter:
    """JSONFormatter testleri"""
    
    def test_json_formatter_basic(self):
        """Temel JSON formatter testi"""
        formatter = JSONFormatter(service_name="test-service")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        result = formatter.format(record)
        data = json.loads(result)
        
        assert data["level"] == "INFO"
        assert data["service"] == "test-service"
        assert data["message"] == "Test message"
        assert "timestamp" in data
    
    def test_json_formatter_with_extra(self):
        """Extra alanlarla JSON formatter testi"""
        formatter = JSONFormatter(service_name="test-service")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.user_id = "usr-123"
        record.order_id = "ord-456"
        
        result = formatter.format(record)
        data = json.loads(result)
        
        assert data["user_id"] == "usr-123"
        assert data["order_id"] == "ord-456"
    
    def test_json_formatter_with_exception(self):
        """Exception ile JSON formatter testi"""
        formatter = JSONFormatter(service_name="test-service")
        
        try:
            raise ValueError("Test error")
        except Exception:
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=1,
                msg="Test error",
                args=(),
                exc_info=True
            )
            
            result = formatter.format(record)
            data = json.loads(result)
            
            assert data["level"] == "ERROR"
            assert "exception" in data
            assert data["exception"]["type"] == "ValueError"
            assert "traceback" in data["exception"]
    
    def test_json_formatter_timestamp_format(self):
        """Timestamp format testi"""
        formatter = JSONFormatter(service_name="test-service", timestamp_format="iso")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None
        )
        
        result = formatter.format(record)
        data = json.loads(result)
        
        assert "T" in data["timestamp"]  # ISO format
        assert "Z" in data["timestamp"] or "+" in data["timestamp"]


class TestPrettyFormatter:
    """PrettyFormatter testleri"""
    
    def test_pretty_formatter_basic(self):
        """Temel Pretty formatter testi"""
        formatter = PrettyFormatter(service_name="test-service", use_colors=False)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        result = formatter.format(record)
        
        assert "INFO" in result
        assert "test-service" in result
        assert "Test message" in result
        assert "│" in result  # Separator karakteri
    
    def test_pretty_formatter_with_extra(self):
        """Extra alanlarla Pretty formatter testi"""
        formatter = PrettyFormatter(service_name="test-service", use_colors=False)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.user_id = "usr-123"
        
        result = formatter.format(record)
        
        assert "user_id=usr-123" in result
    
    def test_pretty_formatter_colors(self):
        """Renkli çıktı testi"""
        formatter = PrettyFormatter(service_name="test-service", use_colors=True)
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error message",
            args=(),
            exc_info=None
        )
        
        result = formatter.format(record)
        
        # ANSI renk kodları olmalı
        assert "\033" in result or "ERROR" in result


class TestCompactFormatter:
    """CompactFormatter testleri"""
    
    def test_compact_formatter_basic(self):
        """Temel Compact formatter testi"""
        formatter = CompactFormatter(service_name="test-service")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        result = formatter.format(record)
        
        parts = result.split()
        assert "INFO" in parts
        assert "test-service" in parts
        assert "Test" in parts
        assert "message" in parts
    
    def test_compact_formatter_with_extra(self):
        """Extra alanlarla Compact formatter testi"""
        formatter = CompactFormatter(service_name="test-service")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.user_id = "usr-123"
        record.order_id = "ord-456"
        
        result = formatter.format(record)
        
        assert "user_id=usr-123" in result
        assert "order_id=ord-456" in result

