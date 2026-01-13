"""
Test context.py - Trace ve Span ID Yönetimi
"""

import pytest
from microlog.context import (
    TraceContext,
    trace,
    create_trace,
    get_current_context,
    set_current_context,
)


class TestTraceContext:
    """TraceContext sınıfı testleri"""
    
    def test_trace_context_creation(self):
        """TraceContext otomatik trace_id ve span_id oluşturur"""
        ctx = TraceContext()
        
        assert ctx.trace_id is not None
        assert len(ctx.trace_id) == 16
        assert ctx.span_id is not None
        assert len(ctx.span_id) == 16
        assert ctx.parent_span_id is None
        assert ctx.started_at is not None
    
    def test_trace_context_with_custom_values(self):
        """TraceContext özel değerlerle oluşturulabilir"""
        ctx = TraceContext(
            trace_id="custom-trace-123",
            span_id="custom-span-456",
            correlation_id="order-789",
            session_id="session-abc",
            extra={"user_id": "usr-123", "tenant_id": "acme"}
        )
        
        assert ctx.trace_id == "custom-trace-123"
        assert ctx.span_id == "custom-span-456"
        assert ctx.correlation_id == "order-789"
        assert ctx.session_id == "session-abc"
        assert ctx.extra["user_id"] == "usr-123"
        assert ctx.extra["tenant_id"] == "acme"
    
    def test_child_span_creation(self):
        """child_span() yeni span oluşturur ve parent ilişkisini kurar"""
        parent = TraceContext(trace_id="trace-123", span_id="span-456")
        child = parent.child_span()
        
        assert child.trace_id == "trace-123"  # Aynı trace_id
        assert child.span_id != "span-456"  # Yeni span_id
        assert child.parent_span_id == "span-456"  # Parent'ın span_id'si
        assert len(child.span_id) == 16
    
    def test_to_dict(self):
        """to_dict() context'i dict formatına dönüştürür"""
        ctx = TraceContext(
            trace_id="trace-123",
            span_id="span-456",
            correlation_id="order-789"
        )
        
        result = ctx.to_dict()
        
        assert result["trace_id"] == "trace-123"
        assert result["span_id"] == "span-456"
        assert result["correlation_id"] == "order-789"
        assert "parent_span_id" not in result  # None olduğu için eklenmez
    
    def test_to_dict_with_extra(self):
        """to_dict() extra alanları da dict'e ekler"""
        ctx = TraceContext(
            trace_id="trace-123",
            extra={"user_id": "usr-123", "order_id": "ord-456"}
        )
        
        result = ctx.to_dict()
        
        assert result["trace_id"] == "trace-123"
        assert result["user_id"] == "usr-123"
        assert result["order_id"] == "ord-456"
    
    def test_to_headers(self):
        """to_headers() context'i HTTP header formatına dönüştürür"""
        ctx = TraceContext(
            trace_id="trace-123",
            span_id="span-456",
            correlation_id="order-789",
            session_id="session-abc"
        )
        
        headers = ctx.to_headers()
        
        assert headers["X-Trace-Id"] == "trace-123"
        assert headers["X-Span-Id"] == "span-456"
        assert headers["X-Correlation-Id"] == "order-789"
        assert headers["X-Session-Id"] == "session-abc"
    
    def test_to_headers_without_optional(self):
        """to_headers() sadece mevcut alanları header'a ekler"""
        ctx = TraceContext(trace_id="trace-123", span_id="span-456")
        
        headers = ctx.to_headers()
        
        assert headers["X-Trace-Id"] == "trace-123"
        assert headers["X-Span-Id"] == "span-456"
        assert "X-Correlation-Id" not in headers
        assert "X-Session-Id" not in headers
    
    def test_from_headers(self):
        """from_headers() HTTP header'larından TraceContext oluşturur"""
        headers = {
            "X-Trace-ID": "trace-123",
            "X-Span-ID": "span-456",
            "X-Correlation-ID": "order-789",
            "X-Session-ID": "session-abc"
        }
        
        ctx = TraceContext.from_headers(headers)
        
        assert ctx.trace_id == "trace-123"
        assert ctx.span_id != "span-456"  # Yeni span oluşturulur
        assert ctx.parent_span_id == "span-456"  # Gelen span parent olur
        assert ctx.correlation_id == "order-789"
        assert ctx.session_id == "session-abc"
    
    def test_from_headers_missing(self):
        """from_headers() eksik header'larda otomatik ID'ler oluşturur"""
        headers = {}
        
        ctx = TraceContext.from_headers(headers)
        
        assert ctx.trace_id is not None
        assert ctx.span_id is not None
        assert ctx.parent_span_id is None


class TestTraceContextManager:
    """trace context manager testleri"""
    
    def test_trace_context_manager_basic(self):
        """trace() context manager context oluşturur ve temizler"""
        with trace() as ctx:
            assert ctx is not None
            assert ctx.trace_id is not None
            assert ctx.span_id is not None
            
            # Context aktif mi?
            current = get_current_context()
            assert current is not None
            assert current.trace_id == ctx.trace_id
        
        # Context temizlenmiş mi?
        current = get_current_context()
        assert current is None
    
    def test_trace_context_manager_with_params(self):
        """trace() parametrelerle özel context oluşturur"""
        with trace(
            trace_id="custom-trace",
            correlation_id="order-123",
            user_id="usr-456"
        ) as ctx:
            assert ctx.trace_id == "custom-trace"
            assert ctx.correlation_id == "order-123"
            assert ctx.extra["user_id"] == "usr-456"
    
    def test_trace_context_manager_nested(self):
        """trace() iç içe kullanımda parent-child ilişkisi kurar"""
        with trace(trace_id="parent-trace") as parent:
            parent_span_id = parent.span_id
            assert get_current_context().trace_id == "parent-trace"
            assert get_current_context().span_id == parent_span_id
            
            with trace(parent=parent) as child:
                assert get_current_context().trace_id == "parent-trace"
                assert get_current_context().span_id != parent_span_id
                assert get_current_context().parent_span_id == parent_span_id
            
            # Child'dan sonra parent'a dönmeli
            assert get_current_context().trace_id == "parent-trace"
            assert get_current_context().span_id == parent_span_id
    
    def test_trace_context_manager_from_headers(self):
        """trace() HTTP header'larından context oluşturur"""
        headers = {
            "X-Trace-ID": "trace-123",
            "X-Span-ID": "span-456",
            "X-Correlation-ID": "order-789"
        }
        
        with trace(headers=headers) as ctx:
            assert ctx.trace_id == "trace-123"
            assert ctx.parent_span_id == "span-456"
            assert ctx.correlation_id == "order-789"


class TestContextFunctions:
    """Context yardımcı fonksiyon testleri"""
    
    def test_get_current_context_none(self):
        """get_current_context() context yokken None döner"""
        set_current_context(None)
        assert get_current_context() is None
    
    def test_set_get_current_context(self):
        """set_current_context() ve get_current_context() birlikte çalışır"""
        ctx = TraceContext(trace_id="test-trace")
        
        set_current_context(ctx)
        assert get_current_context().trace_id == "test-trace"
        
        set_current_context(None)
        assert get_current_context() is None
    
    def test_create_trace(self):
        """create_trace() yeni TraceContext oluşturur"""
        ctx = create_trace(
            trace_id="trace-123",
            correlation_id="order-456"
        )
        
        assert ctx.trace_id == "trace-123"
        assert ctx.correlation_id == "order-456"
        assert isinstance(ctx, TraceContext)
