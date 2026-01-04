"""
Test decorators.py - Logging Decorators
"""

import pytest
import logging
import time
from microlog.decorators import (
    log_function,
    log_exception,
    log_performance,
    log_context,
)


class TestLogFunction:
    """log_function decorator testleri"""
    
    def test_log_function_basic(self, capture_logs):
        """Temel log_function testi"""
        logger = logging.getLogger("test_log_function")
        
        @log_function(logger=logger, level=logging.INFO)
        def test_func(x, y):
            return x + y
        
        result = test_func(2, 3)
        
        assert result == 5
        assert len(capture_logs.records) >= 1
        assert any("Calling" in r.message for r in capture_logs.records)
    
    def test_log_function_with_args(self, capture_logs):
        """log_function args loglama testi"""
        logger = logging.getLogger("test_log_args")
        
        @log_function(logger=logger, log_args=True)
        def test_func(name, age=25):
            return f"{name} is {age}"
        
        test_func("Alice", age=30)
        
        assert any("Calling" in r.message for r in capture_logs.records)
    
    def test_log_function_with_result(self, capture_logs):
        """log_function result loglama testi"""
        logger = logging.getLogger("test_log_result")
        
        @log_function(logger=logger, log_result=True)
        def test_func():
            return "success"
        
        test_func()
        
        assert any("completed" in r.message for r in capture_logs.records)
    
    def test_log_function_exception(self, capture_logs):
        """log_function exception yakalama testi"""
        logger = logging.getLogger("test_log_exception")
        
        @log_function(logger=logger)
        def test_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            test_func()
        
        assert any("failed" in r.message.lower() for r in capture_logs.records)


class TestLogException:
    """log_exception decorator testleri"""
    
    def test_log_exception_catch(self, capture_logs):
        """log_exception yakalama testi"""
        logger = logging.getLogger("test_log_exc")
        
        @log_exception(logger=logger, reraise=True)
        def test_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            test_func()
        
        assert any("Exception" in r.message for r in capture_logs.records)
    
    def test_log_exception_no_rerais(self, capture_logs):
        """log_exception reraise=False testi"""
        logger = logging.getLogger("test_log_exc_no_raise")
        
        @log_exception(logger=logger, reraise=False)
        def test_func():
            raise ValueError("Test error")
        
        result = test_func()
        
        assert result is None
        assert any("Exception" in r.message for r in capture_logs.records)
    
    def test_log_exception_no_error(self, capture_logs):
        """log_exception hata olmadan testi"""
        logger = logging.getLogger("test_log_exc_no_error")
        
        @log_exception(logger=logger)
        def test_func():
            return "success"
        
        result = test_func()
        
        assert result == "success"
        # Hata olmadığı için exception logu olmamalı
        assert not any("Exception" in r.message for r in capture_logs.records)


class TestLogPerformance:
    """log_performance decorator testleri"""
    
    def test_log_performance_basic(self, capture_logs):
        """Temel log_performance testi"""
        logger = logging.getLogger("test_perf")
        
        @log_performance(logger=logger, threshold=0.0)
        def test_func():
            time.sleep(0.01)
            return "done"
        
        result = test_func()
        
        assert result == "done"
        assert any("took" in r.message for r in capture_logs.records)
    
    def test_log_performance_threshold(self, capture_logs):
        """log_performance threshold testi"""
        logger = logging.getLogger("test_perf_threshold")
        
        @log_performance(logger=logger, threshold=0.1)  # 100ms threshold
        def fast_func():
            time.sleep(0.01)  # 10ms - threshold altında
            return "fast"
        
        @log_performance(logger=logger, threshold=0.1)
        def slow_func():
            time.sleep(0.15)  # 150ms - threshold üstünde
            return "slow"
        
        fast_func()
        slow_func()
        
        # Sadece slow_func loglanmalı
        perf_logs = [r for r in capture_logs.records if "took" in r.message]
        assert len(perf_logs) >= 1


class TestLogContext:
    """log_context context manager testleri"""
    
    def test_log_context_basic(self, capture_logs):
        """Temel log_context testi"""
        logger = logging.getLogger("test_ctx")
        
        with log_context("Test operation", logger=logger):
            pass
        
        assert any("started" in r.message for r in capture_logs.records)
        assert any("completed" in r.message for r in capture_logs.records)
    
    def test_log_context_with_exception(self, capture_logs):
        """log_context exception ile testi"""
        logger = logging.getLogger("test_ctx_exc")
        
        with pytest.raises(ValueError):
            with log_context("Test operation", logger=logger):
                raise ValueError("Test error")
        
        assert any("failed" in r.message.lower() for r in capture_logs.records)

