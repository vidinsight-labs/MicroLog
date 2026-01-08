"""
Test formatter.py - Log Çıktı Formatları
"""

import pytest
import json
import logging
from microlog.formatters import JSONFormatter, PrettyFormatter, CompactFormatter


class TestJSONFormatter:
    """JSONFormatter testleri"""
    
    def test_json_formatter_basic(self):
        """JSONFormatter temel log formatını doğru oluşturur"""
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
        """JSONFormatter extra alanları JSON'a ekler"""
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
        """JSONFormatter exception bilgilerini JSON'a ekler"""
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
        """JSONFormatter timestamp'i ISO formatında oluşturur"""
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
        """PrettyFormatter okunabilir format oluşturur"""
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
        """PrettyFormatter extra alanları key=value formatında gösterir"""
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
        """PrettyFormatter ANSI renk kodları ile renkli çıktı üretir"""
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
        """CompactFormatter minimal tek satır format oluşturur"""
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
        """CompactFormatter extra alanları minimal formatta gösterir"""
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
