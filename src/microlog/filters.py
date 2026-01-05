"""
MicroLog Filters

Logging filtreleri: PII maskeleme, sampling, rate limiting.

Author: MicroLog Team
License: MIT
"""

import logging
import random
import re
from typing import Dict, List, Optional, Pattern


class PIIFilter(logging.Filter):
    """
    Personally Identifiable Information (PII) filtreleme.
    
    Loglarda bulunan hassas bilgileri (email, SSN, credit card, vb.) otomatik maskeler.
    GDPR, HIPAA gibi uyumluluk gereksinimleri için kritik.
    
    Example:
        >>> from microlog import setup_logger
        >>> from microlog.filters import PIIFilter
        >>> 
        >>> logger = setup_logger("app")
        >>> logger.addFilter(PIIFilter())
        >>> 
        >>> logger.info("User email: john@example.com")
        >>> # Output: "User email: [REDACTED_EMAIL]"
        >>> 
        >>> logger.info("Credit card: 4532-1234-5678-9010")
        >>> # Output: "Credit card: [REDACTED_CREDIT_CARD]"
    """
    
    # Default PII patterns
    DEFAULT_PATTERNS: Dict[str, str] = {
        "email": r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
        "phone_us": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        "phone_intl": r"\+\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}",
        "ipv4": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        "password": r"(?i)(password|passwd|pwd)[\s:=]+[\S]+",
        "api_key": r"(?i)(api[_-]?key|apikey|token)[\s:=]+[\S]+",
    }
    
    def __init__(
        self,
        patterns: Optional[Dict[str, str]] = None,
        replacement: str = "[REDACTED_{type}]",
        enabled_patterns: Optional[List[str]] = None
    ):
        """
        Args:
            patterns: Custom PII patterns (name -> regex)
            replacement: Replacement string ({type} yerine pattern adı konur)
            enabled_patterns: Sadece belirli pattern'leri etkinleştir (None = tümü)
        
        Example:
            >>> # Sadece email ve phone maskele
            >>> filter = PIIFilter(enabled_patterns=["email", "phone_us"])
            
            >>> # Custom pattern ekle
            >>> filter = PIIFilter(patterns={
            ...     "username": r"(?i)username[\s:=]+[\S]+",
            ...     "custom_id": r"ID-\d{6}"
            ... })
        """
        super().__init__()
        
        # Patterns: custom veya default
        self.patterns = patterns if patterns is not None else self.DEFAULT_PATTERNS.copy()
        self.replacement = replacement
        self.enabled_patterns = enabled_patterns
        
        # Compile regex patterns
        self._compiled_patterns: Dict[str, Pattern] = {}
        for name, pattern in self.patterns.items():
            # enabled_patterns varsa sadece onları compile et
            if self.enabled_patterns is None or name in self.enabled_patterns:
                try:
                    self._compiled_patterns[name] = re.compile(pattern)
                except re.error as e:
                    # Invalid regex - skip
                    pass
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        LogRecord'ı filtreler ve PII'ları maskeler.
        
        Args:
            record: LogRecord instance
            
        Returns:
            True (her zaman - filtre silmez, sadece maskeler)
        """
        # Message'ı maskele
        if hasattr(record, "msg") and isinstance(record.msg, str):
            record.msg = self._mask_pii(record.msg)
        
        # Args varsa onları da maskele (tuple olabilir)
        if hasattr(record, "args") and record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: self._mask_pii(str(v)) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, (tuple, list)):
                record.args = tuple(
                    self._mask_pii(str(arg)) if isinstance(arg, str) else arg
                    for arg in record.args
                )
        
        return True  # Her zaman pass - sadece maskele
    
    def _mask_pii(self, text: str) -> str:
        """Text'teki PII'ları maskeler."""
        masked_text = text
        
        for pattern_name, compiled_pattern in self._compiled_patterns.items():
            # Replacement string'de {type} varsa pattern adını koy
            replacement = self.replacement.replace("{type}", pattern_name.upper())
            masked_text = compiled_pattern.sub(replacement, masked_text)
        
        return masked_text


class SamplingFilter(logging.Filter):
    """
    Log sampling - yüksek volume'da log sayısını azaltır.
    
    Belirli bir sample rate'e göre logları filtreler.
    Production'da DEBUG log'ların %100'ünü yazmak yerine %10'unu yazabilirsiniz.
    
    Example:
        >>> from microlog import setup_logger
        >>> from microlog.filters import SamplingFilter
        >>> 
        >>> logger = setup_logger("app", level=logging.DEBUG)
        >>> 
        >>> # DEBUG logları %10 sample et, ERROR/CRITICAL tümünü yaz
        >>> logger.addFilter(SamplingFilter(
        ...     sample_rate=0.1,
        ...     level_overrides={
        ...         logging.ERROR: 1.0,
        ...         logging.CRITICAL: 1.0
        ...     }
        ... ))
        >>> 
        >>> # 100 DEBUG log → sadece ~10 tanesi yazılır
        >>> # 100 ERROR log → hepsi yazılır
    """
    
    def __init__(
        self,
        sample_rate: float = 1.0,
        level_overrides: Optional[Dict[int, float]] = None
    ):
        """
        Args:
            sample_rate: Default sample rate (0.0-1.0, 0=hiçbiri, 1=hepsi)
            level_overrides: Seviye bazında override (örn: {logging.ERROR: 1.0})
        
        Example:
            >>> # %50 sample, ama ERROR %100
            >>> filter = SamplingFilter(
            ...     sample_rate=0.5,
            ...     level_overrides={logging.ERROR: 1.0}
            ... )
        """
        super().__init__()
        
        if not 0.0 <= sample_rate <= 1.0:
            raise ValueError(f"sample_rate must be 0.0-1.0, got {sample_rate}")
        
        self.sample_rate = sample_rate
        self.level_overrides = level_overrides or {}
        
        # Validate level overrides
        for level, rate in self.level_overrides.items():
            if not 0.0 <= rate <= 1.0:
                raise ValueError(f"Override rate for level {level} must be 0.0-1.0, got {rate}")
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        LogRecord'ı sample eder.
        
        Args:
            record: LogRecord instance
            
        Returns:
            True (log geçer), False (log drop edilir)
        """
        # Seviye override var mı?
        rate = self.level_overrides.get(record.levelno, self.sample_rate)
        
        # Sample: random < rate ise geçer
        return random.random() < rate


class RateLimitFilter(logging.Filter):
    """
    Rate limiting - aynı mesajın çok sık loglanmasını önler.
    
    Belirli bir süre içinde aynı mesajdan sadece N tane yazdırır.
    Log storm'larını önlemek için kullanılır.
    
    Example:
        >>> from microlog import setup_logger
        >>> from microlog.filters import RateLimitFilter
        >>> 
        >>> logger = setup_logger("app")
        >>> 
        >>> # Her mesajdan 60 saniyede max 5 tane
        >>> logger.addFilter(RateLimitFilter(
        ...     max_per_interval=5,
        ...     interval_seconds=60
        ... ))
        >>> 
        >>> # Aynı hatayı 100 kez loglasanız bile sadece 5 tanesi yazılır
        >>> for i in range(100):
        ...     logger.error("Database connection failed")
    """
    
    def __init__(
        self,
        max_per_interval: int = 10,
        interval_seconds: float = 60.0,
        key_func: Optional[callable] = None
    ):
        """
        Args:
            max_per_interval: İnterval içinde max kaç log
            interval_seconds: Interval süresi (saniye)
            key_func: Log signature oluşturan fonksiyon (default: message + levelname)
        
        Example:
            >>> # Özel key func: sadece mesaj içeriğine göre
            >>> filter = RateLimitFilter(
            ...     max_per_interval=5,
            ...     key_func=lambda record: record.getMessage()
            ... )
        """
        super().__init__()
        
        if max_per_interval < 1:
            raise ValueError(f"max_per_interval must be >= 1, got {max_per_interval}")
        
        if interval_seconds <= 0:
            raise ValueError(f"interval_seconds must be > 0, got {interval_seconds}")
        
        self.max_per_interval = max_per_interval
        self.interval_seconds = interval_seconds
        self.key_func = key_func or self._default_key_func
        
        # Rate limit state (key -> list of timestamps)
        from collections import defaultdict, deque
        self._state: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_per_interval))
    
    def _default_key_func(self, record: logging.LogRecord) -> str:
        """Default key: levelname + message (first 50 chars)."""
        return f"{record.levelname}:{record.getMessage()[:50]}"
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Rate limit kontrolü.
        
        Args:
            record: LogRecord instance
            
        Returns:
            True (log geçer), False (rate limit aşıldı)
        """
        import time
        
        key = self.key_func(record)
        now = time.time()
        
        # Bu key için timestamp queue'sunu al
        timestamps = self._state[key]
        
        # Eski timestamp'leri temizle (interval dışındakiler)
        while timestamps and now - timestamps[0] > self.interval_seconds:
            timestamps.popleft()
        
        # Rate limit kontrolü
        if len(timestamps) >= self.max_per_interval:
            return False  # Rate limit aşıldı, log drop et
        
        # Yeni timestamp ekle
        timestamps.append(now)
        return True  # Log geçer


__all__ = [
    "PIIFilter",
    "SamplingFilter",
    "RateLimitFilter",
]

