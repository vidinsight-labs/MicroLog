"""
Test fixtures and utilities
"""

import pytest
import logging
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Geçici dizin oluşturur ve test sonunda temizler."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_log_file(temp_dir):
    """Geçici log dosyası yolu döndürür."""
    return str(temp_dir / "test.log")


@pytest.fixture
def clean_loggers():
    """Test öncesi ve sonrası logger'ları temizler."""
    # Test öncesi
    logging.root.handlers.clear()
    logging.root.setLevel(logging.WARNING)
    
    yield
    
    # Test sonrası
    logging.root.handlers.clear()
    logging.root.setLevel(logging.WARNING)
    
    # Tüm logger'ları temizle
    for name in list(logging.Logger.manager.loggerDict.keys()):
        if name.startswith('test_') or name.startswith('microlog'):
            logger = logging.getLogger(name)
            logger.handlers.clear()
            logger.setLevel(logging.NOTSET)


@pytest.fixture
def capture_logs(caplog):
    """Log kayıtlarını yakalar."""
    with caplog.at_level(logging.DEBUG):
        yield caplog

