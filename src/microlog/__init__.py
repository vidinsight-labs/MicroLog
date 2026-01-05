"""
MicroLog — Modern Python Logging Kütüphanesi

MicroLog, mikroservis mimarileri için tasarlanmış, asenkron ve
trace-aware bir logging kütüphanesidir.

Özellikler:
- Asenkron log yazma (ana thread bloklanmaz)
- Trace context desteği (trace_id, span_id)
- Çoklu format desteği (JSON, Pretty, Compact)
- Çoklu handler desteği (Console, File, SMTP)
- Decorator'lar ile otomatik logging
- Thread-safe ve async-safe

Hızlı Başlangıç:
    from microlog import get_logger, trace
    
    logger = get_logger(service_name="my-service")
    
    with trace() as ctx:
        logger.info("Request received", extra={"user_id": "123"})
        logger.debug("Processing...", extra={"step": "validation"})
"""

from __future__ import annotations

__version__ = "0.1.0"
__author__ = "MicroLog Team"

# ═══════════════════════════════════════════════════════════════════════════════
# CORE - Logger Setup
# ═══════════════════════════════════════════════════════════════════════════════

from .core import (
    setup_logger,
    configure_logger,
    setup_console_logger,
    setup_file_logger,
    setup_production_logger,
    get_logger,
    TraceContextFilter,
)

# ═══════════════════════════════════════════════════════════════════════════════
# HANDLERS - Log Output Destinations
# ═══════════════════════════════════════════════════════════════════════════════

from .handlers import (
    AsyncHandler,
    AsyncConsoleHandler,
    AsyncRotatingFileHandler,
    AsyncSMTPHandler,
)

# ═══════════════════════════════════════════════════════════════════════════════
# FORMATTERS - Log Output Formats
# ═══════════════════════════════════════════════════════════════════════════════

from .formatter import (
    JSONFormatter,
    PrettyFormatter,
    CompactFormatter,
)

# ═══════════════════════════════════════════════════════════════════════════════
# CONTEXT - Trace and Span Management
# ═══════════════════════════════════════════════════════════════════════════════

from .context import (
    TraceContext,
    trace,
    create_trace,
    get_current_context,
    set_current_context,
)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIG - Configuration File Support
# ═══════════════════════════════════════════════════════════════════════════════

from .config import (
    load_config,
    load_config_from_env,
    setup_from_config,
)

# ═══════════════════════════════════════════════════════════════════════════════
# FILTERS - Logging Filters (PII, Sampling, Rate Limiting)
# ═══════════════════════════════════════════════════════════════════════════════

from .filters import (
    PIIFilter,
    SamplingFilter,
    RateLimitFilter,
)

# ═══════════════════════════════════════════════════════════════════════════════
# METRICS - Observability (Prometheus)
# ═══════════════════════════════════════════════════════════════════════════════

from .metrics import (
    MetricsHandler,
    QueueMetricsCollector,
    setup_metrics,
    PROMETHEUS_AVAILABLE,
)

# ═══════════════════════════════════════════════════════════════════════════════
# DECORATORS - Automatic Logging
# ═══════════════════════════════════════════════════════════════════════════════

from .decorators import (
    log_function,
    log_exception,
    log_performance,
    log_context,
)

# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

__all__ = [
    # Version
    "__version__",
    
    # Core
    "setup_logger",
    "configure_logger",
    "setup_console_logger",
    "setup_file_logger",
    "setup_production_logger",
    "get_logger",
    "TraceContextFilter",
    
    # Config
    "load_config",
    "load_config_from_env",
    "setup_from_config",
    
    # Filters
    "PIIFilter",
    "SamplingFilter",
    "RateLimitFilter",
    
    # Metrics
    "MetricsHandler",
    "QueueMetricsCollector",
    "setup_metrics",
    "PROMETHEUS_AVAILABLE",
    
    # Handlers
    "AsyncHandler",
    "AsyncConsoleHandler",
    "AsyncRotatingFileHandler",
    "AsyncSMTPHandler",
    
    # Formatters
    "JSONFormatter",
    "PrettyFormatter",
    "CompactFormatter",
    
    # Context
    "TraceContext",
    "trace",
    "create_trace",
    "get_current_context",
    "set_current_context",
    
    # Decorators
    "log_function",
    "log_exception",
    "log_performance",
    "log_context",
]

