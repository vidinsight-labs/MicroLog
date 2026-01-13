<img width="1584" height="396" alt="LinkedIn Banner Design" src="https://github.com/user-attachments/assets/8692e053-14f7-4e7a-8320-24a518e275ba" />

# MicroLog - Modern Python Logging Library

MicroLog is a thread-safe, asynchronous Python logging library designed for production environments. It provides distributed tracing support, high performance, and ease of use.

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Asynchronous Logging** - Non-blocking, queue-based background processing
- **Distributed Tracing** - Built-in support for `trace_id`, `span_id`, `parent_span_id`
- **Multiple Formatters** - JSON, Pretty (colored), and Compact formats
- **File Rotation** - Size-based rotation with gzip compression
- **Email Notifications** - SMTP handler with rate limiting
- **Thread-Safe** - Safe for concurrent operations
- **High Performance** - 47,000+ logs per second
- **Production-Ready** - Validated with 159 tests

## Installation

```bash
# Clone the repository
git clone https://github.com/vidinsight-labs/MicroLog.git
cd MicroLog

# Install in development mode
pip install -e .

# Or use directly (add src directory to PYTHONPATH)
export PYTHONPATH=$(pwd)/src:$PYTHONPATH
```

## Quick Start

```python
from microlog import setup_logger, trace
import logging

# Create logger
logger = setup_logger("myapp", level=logging.INFO)

# Simple logging
logger.info("Application started")

# With trace context
with trace(trace_id="req-123"):
    logger.info("Processing request")
```

### Console Logger (Colored Output)

```python
from microlog import setup_console_logger

logger = setup_console_logger("myapp", service_name="api-service", use_colors=True)
logger.info("Request processed", extra={"user_id": "123", "duration_ms": 45})
```

### File Logger (JSON Format)

```python
from microlog import setup_file_logger

logger = setup_file_logger(
    name="myapp",
    filename="app.log",
    format_type="json",
    max_bytes=10 * 1024 * 1024,  # 10MB
    backup_count=5
)
logger.info("Event occurred", extra={"event_type": "user_action"})
```

### Distributed Tracing

```python
from microlog import setup_logger, trace

logger = setup_logger("myapp")

# Automatic trace context
with trace(correlation_id="req-123") as ctx:
    logger.info("Request received")
    logger.info("Processing", extra={"trace_id": ctx.trace_id})
```

### Decorator Support

```python
from microlog import setup_logger, with_trace

logger = setup_logger("myapp")

@with_trace(correlation_id="order-456")
def process_order(order_id: str):
    logger.info("Processing order", extra={"order_id": order_id})
```

## Documentation

- **[Quickstart Guide](docs/quickstart.md)** - Get started in minutes
- **[Trace Context](docs/trace-context.md)** - Distributed tracing guide
- **[Formatters](docs/formatters.md)** - JSON, Pretty, Compact formats
- **[Handlers](docs/handlers.md)** - Async handlers and configuration
- **[File Management](docs/file-management.md)** - Log rotation and compression

## Test Status

- **159 tests** - All tests passing (100%)
- **Thread safety** - Verified
- **Memory stability** - No leaks detected
- **Performance** - 47,000+ logs per second
- **Production ready** - Tested in API and microservice environments

## Examples

The project includes **35+ examples** organized in 8 categories:

- **Quickstart** - Minimal examples to get started
- **Basic** - Console and file logging
- **Trace** - Distributed tracing patterns
- **Advanced** - Custom handlers, thread safety
- **Web** - Flask, FastAPI, Django integrations
- **Async** - Async/await patterns
- **Microservices** - Service-to-service tracing
- **Production** - Production-ready configurations

Browse all examples: [examples/README.md](examples/README.md)

## Use Cases

### Microservices

```python
from microlog import setup_logger, trace

logger = setup_logger("api-gateway", service_name="gateway")

def handle_request(request):
    with trace(correlation_id=request.headers.get("X-Request-ID")):
        logger.info("Request received", extra={"path": request.path})
```

### Production Logging

```python
from microlog import setup_file_logger

logger = setup_file_logger(
    name="production-app",
    filename="/var/log/app.log",
    format_type="json",
    max_bytes=50 * 1024 * 1024,
    backup_count=10,
    compress=True
)
```

## Requirements

- Python 3.7+
- No external dependencies (uses only Python standard library)

## Contributing

Contributions are welcome! Please ensure all tests pass before opening an issue or submitting a PR.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

For questions, please open an issue or check the documentation.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Links

- **Repository**: [github.com/vidinsight-labs/MicroLog](https://github.com/vidinsight-labs/MicroLog)
- **Issues**: [GitHub Issues](https://github.com/vidinsight-labs/MicroLog/issues)
- **Documentation**: [docs/](docs/)

---

**MicroLog** - High-performance asynchronous logging library for Python
