"""
Test decorators.py - Logging Decorators
"""

import pytest
from microlog.decorators import with_trace
from microlog.context import get_current_context


class TestWithTrace:
    """with_trace decorator testleri"""
    
    def test_with_trace_basic(self):
        """with_trace decorator fonksiyona trace context ekler"""
        @with_trace(correlation_id="test-123")
        def test_func():
            ctx = get_current_context()
            assert ctx is not None
            assert ctx.correlation_id == "test-123"
            return "success"
        
        result = test_func()
        assert result == "success"
    
    def test_with_trace_async(self):
        """with_trace async fonksiyonlarla çalışır"""
        import asyncio
        
        @with_trace(session_id="session-456")
        async def async_func():
            ctx = get_current_context()
            assert ctx is not None
            assert ctx.session_id == "session-456"
            return "async_success"
        
        result = asyncio.run(async_func())
        assert result == "async_success"
    
    def test_with_trace_nested(self):
        """with_trace iç içe kullanımda context yığını oluşturur"""
        @with_trace(correlation_id="outer")
        def outer_func():
            @with_trace(correlation_id="inner")
            def inner_func():
                ctx = get_current_context()
                assert ctx is not None
                assert ctx.correlation_id == "inner"
                return "inner"
            
            result = inner_func()
            ctx = get_current_context()
            assert ctx is not None
            assert ctx.correlation_id == "outer"
            return result
        
        result = outer_func()
        assert result == "inner"
