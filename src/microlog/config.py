"""
MicroLog Configuration Support

Bu modül YAML/JSON configuration dosyalarından logger yapılandırma desteği sağlar.

Author: MicroLog Team
License: MIT
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .core import setup_logger
from .formatter import JSONFormatter, PrettyFormatter, CompactFormatter
from .handlers import AsyncConsoleHandler, AsyncRotatingFileHandler, AsyncSMTPHandler


def load_config(config_file: Union[str, Path]) -> Dict[str, Any]:
    """
    YAML veya JSON formatında configuration dosyası yükler.
    
    Args:
        config_file: Config dosyası path'i (.yaml, .yml, .json)
        
    Returns:
        Configuration dictionary
        
    Raises:
        FileNotFoundError: Dosya bulunamazsa
        ValueError: Dosya formatı desteklenmiyorsa veya parse edilemezse
        
    Example:
        >>> config = load_config("config.yaml")
        >>> logger = setup_from_config(config)
    """
    config_path = Path(config_file)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")
    
    suffix = config_path.suffix.lower()
    
    if suffix in (".yaml", ".yml"):
        try:
            import yaml
        except ImportError:
            raise ImportError(
                "PyYAML is required for YAML config files. "
                "Install it with: pip install pyyaml"
            )
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    
    elif suffix == ".json":
        import json
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    
    else:
        raise ValueError(
            f"Unsupported config file format: {suffix}. "
            "Supported formats: .yaml, .yml, .json"
        )
    
    if not isinstance(config, dict):
        raise ValueError(f"Config file must contain a dictionary, got {type(config)}")
    
    return config


def load_config_from_env(env_var: str = "MICROLOG_CONFIG") -> Optional[Dict[str, Any]]:
    """
    Environment variable'dan config dosyası path'i okuyup yükler.
    
    Args:
        env_var: Environment variable adı (default: MICROLOG_CONFIG)
        
    Returns:
        Configuration dictionary veya None (env var yoksa)
        
    Example:
        >>> os.environ["MICROLOG_CONFIG"] = "/path/to/config.yaml"
        >>> config = load_config_from_env()
    """
    config_path = os.getenv(env_var)
    if not config_path:
        return None
    
    return load_config(config_path)


def setup_from_config(
    config: Union[Dict[str, Any], str, Path],
    logger_name: Optional[str] = None
) -> logging.Logger:
    """
    Configuration dictionary veya dosyasından logger oluşturur.
    
    Args:
        config: Config dict veya config dosyası path'i
        logger_name: Logger adı (config'den override edilebilir)
        
    Returns:
        Configured Logger instance
        
    Config Format:
        ```yaml
        logging:
          name: myapp
          level: INFO
          service_name: myapp-service
          
          formatter:
            type: json  # json, pretty, compact
            service_name: myapp-service
            include_extra: true
          
          handlers:
            - type: console
              level: INFO
            
            - type: file
              filename: logs/app.log
              max_bytes: 10485760  # 10 MB
              backup_count: 5
              compress: true
              level: DEBUG
            
            - type: smtp
              mailhost: [smtp.example.com, 587]
              fromaddr: alerts@example.com
              toaddrs:
                - admin@example.com
              subject: Application Alert
              credentials: [user, password]
              secure: true
              rate_limit: 300
              level: ERROR
        ```
        
    Example:
        >>> # From dict
        >>> config = {"logging": {"name": "myapp", "level": "INFO"}}
        >>> logger = setup_from_config(config)
        
        >>> # From file
        >>> logger = setup_from_config("config.yaml")
        
        >>> # From environment variable
        >>> os.environ["MICROLOG_CONFIG"] = "config.yaml"
        >>> logger = setup_from_config(os.getenv("MICROLOG_CONFIG"))
    """
    # Config loading
    if isinstance(config, (str, Path)):
        config = load_config(config)
    
    if not isinstance(config, dict):
        raise ValueError(f"Config must be a dict or file path, got {type(config)}")
    
    # logging section
    log_config = config.get("logging", {})
    
    if not log_config:
        raise ValueError("Config must contain a 'logging' section")
    
    # Logger name
    name = logger_name or log_config.get("name", "root")
    
    # Log level
    level_str = log_config.get("level", "INFO")
    level = _parse_level(level_str)
    
    # Service name
    service_name = log_config.get("service_name")
    
    # Formatter
    formatter = _create_formatter(log_config.get("formatter", {}), service_name)
    
    # Logger oluştur
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()  # Mevcut handler'ları temizle
    
    # Handlers
    handlers_config = log_config.get("handlers", [])
    for handler_config in handlers_config:
        handler = _create_handler(handler_config, formatter)
        if handler:
            logger.addHandler(handler)
    
    return logger


def _parse_level(level: Union[str, int]) -> int:
    """Log level parse eder."""
    if isinstance(level, int):
        return level
    
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "WARN": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
        "FATAL": logging.CRITICAL,
    }
    
    level_upper = str(level).upper()
    if level_upper not in level_map:
        raise ValueError(
            f"Invalid log level: {level}. "
            f"Valid levels: {', '.join(level_map.keys())}"
        )
    
    return level_map[level_upper]


def _create_formatter(
    formatter_config: Dict[str, Any],
    default_service_name: Optional[str] = None
) -> logging.Formatter:
    """Config'den formatter oluşturur."""
    formatter_type = formatter_config.get("type", "compact").lower()
    service_name = formatter_config.get("service_name", default_service_name)
    include_extra = formatter_config.get("include_extra", True)
    
    if formatter_type == "json":
        return JSONFormatter(
            service_name=service_name,
            include_extra=include_extra
        )
    elif formatter_type == "pretty":
        return PrettyFormatter(
            service_name=service_name,
            include_extra=include_extra
        )
    elif formatter_type == "compact":
        return CompactFormatter(
            service_name=service_name
        )
    else:
        raise ValueError(
            f"Unknown formatter type: {formatter_type}. "
            "Valid types: json, pretty, compact"
        )


def _create_handler(
    handler_config: Dict[str, Any],
    formatter: logging.Formatter
) -> Optional[logging.Handler]:
    """Config'den handler oluşturur."""
    handler_type = handler_config.get("type", "").lower()
    level = _parse_level(handler_config.get("level", "INFO"))
    
    if handler_type == "console":
        handler = AsyncConsoleHandler()
        handler.get_queue_handler().setFormatter(formatter)
        handler.get_queue_handler().setLevel(level)
        handler.start()
        return handler.get_queue_handler()
    
    elif handler_type == "file":
        filename = handler_config.get("filename")
        if not filename:
            raise ValueError("File handler requires 'filename' parameter")
        
        max_bytes = handler_config.get("max_bytes", 10485760)  # 10 MB default
        backup_count = handler_config.get("backup_count", 5)
        compress = handler_config.get("compress", False)
        
        handler = AsyncRotatingFileHandler(
            filename=filename,
            max_bytes=max_bytes,
            backup_count=backup_count
        )
        handler.get_queue_handler().setFormatter(formatter)
        handler.get_queue_handler().setLevel(level)
        handler.start()
        return handler.get_queue_handler()
    
    elif handler_type == "smtp":
        mailhost = handler_config.get("mailhost")
        fromaddr = handler_config.get("fromaddr")
        toaddrs = handler_config.get("toaddrs")
        subject = handler_config.get("subject", "Application Log")
        
        if not all([mailhost, fromaddr, toaddrs]):
            raise ValueError(
                "SMTP handler requires 'mailhost', 'fromaddr', and 'toaddrs' parameters"
            )
        
        # mailhost: [host, port] veya "host:port"
        if isinstance(mailhost, str):
            if ":" in mailhost:
                host, port = mailhost.split(":")
                mailhost = (host, int(port))
            else:
                mailhost = (mailhost, 25)
        elif isinstance(mailhost, list):
            mailhost = tuple(mailhost)
        
        credentials = handler_config.get("credentials")
        if credentials and isinstance(credentials, list):
            credentials = tuple(credentials)
        
        secure = handler_config.get("secure", False)
        rate_limit = handler_config.get("rate_limit", 300)
        include_trace = handler_config.get("include_trace", True)
        
        handler = AsyncSMTPHandler(
            mailhost=mailhost,
            fromaddr=fromaddr,
            toaddrs=toaddrs,
            subject=subject,
            credentials=credentials,
            secure=secure,
            rate_limit=rate_limit,
            include_trace=include_trace
        )
        handler.get_queue_handler().setFormatter(formatter)
        handler.get_queue_handler().setLevel(level)
        handler.start()
        return handler.get_queue_handler()
    
    else:
        raise ValueError(
            f"Unknown handler type: {handler_type}. "
            "Valid types: console, file, smtp"
        )


__all__ = [
    "load_config",
    "load_config_from_env",
    "setup_from_config",
]

