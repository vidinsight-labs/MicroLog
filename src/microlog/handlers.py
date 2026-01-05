"""
handlers.py — Log Çıktı Hedefleri (Handlers)

Bu modül ne yapar?
- AsyncConsoleHandler:        Asenkron konsol çıktısı (stdout)
- AsyncRotatingFileHandler:   Asenkron dosya + otomatik döndürme + gzip
- AsyncSMTPHandler:           Asenkron email bildirimleri

Neden Asenkron?
- Log yazmak I/O işlemidir (disk, network)
- Senkron olsa ana thread bekler, uygulama yavaşlar
- Asenkron olunca log queue'ya atılır, arka planda yazılır

Mimari:
    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │ Ana Thread  │────▶│   Queue     │────▶│  Listener   │
    │ (log.info)  │     │ (buffer)    │     │ (arka plan) │
    └─────────────┘     └─────────────┘     └─────────────┘
         │                                        │
         │ Hemen döner                            │ Asenkron yazar
         ▼                                        ▼
    Uygulama devam                         Console/File/SMTP
"""

from __future__ import annotations

import sys
import gzip
import shutil
import logging
import smtplib
import atexit
import queue
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Any
from logging.handlers import QueueHandler, QueueListener


# ═══════════════════════════════════════════════════════════════════════════════
# BASE ASYNC HANDLER
# ═══════════════════════════════════════════════════════════════════════════════

class AsyncHandler:
    """
    Asenkron handler base class.
    
    Queue kullanarak logları arka planda işler.
    Ana thread'i bloklamaz.
    
    Çalışma Mantığı:
        1. Logger, log.info() çağrılınca QueueHandler'a yazar
        2. QueueHandler, log'u queue'ya ekler (anında döner)
        3. QueueListener, queue'dan okur ve gerçek handler'a yazar
        4. Gerçek handler (console/file/smtp) I/O işlemini yapar
    """
    
    def __init__(self, handler: logging.Handler):
        """
        Args:
            handler: Sarmalanacak gerçek handler (Console, File, SMTP)
        """
        self._queue: queue.Queue = queue.Queue(-1)  # -1 = sınırsız boyut
        self._handler = handler
        self._listener: Optional[QueueListener] = None
        self._started = False
        self._lock = threading.Lock()  # Thread-safety için lock
        self._atexit_registered = False  # Atexit sadece bir kez register
    
    def start(self) -> None:
        """Asenkron listener'ı başlatır."""
        with self._lock:
            if not self._started:
                self._listener = QueueListener(
                    self._queue,
                    self._handler,
                    respect_handler_level=True
                )
                self._listener.start()
                self._started = True
                
                # Program kapanırken otomatik durdur (sadece bir kez register et)
                if not self._atexit_registered:
                    # Weak reference kullanarak circular reference'ı önle
                    import weakref
                    weak_self = weakref.ref(self)
                    
                    def cleanup():
                        strong_self = weak_self()
                        if strong_self is not None:
                            strong_self.stop()
                    
                    atexit.register(cleanup)
                    self._atexit_registered = True
    
    def stop(self) -> None:
        """
        Asenkron listener'ı durdurur ve kaynakları temizler.
        
        Queue'daki tüm pending mesajların flush edilmesini garantiler.
        Sentinel pattern ile %100 log flush garantisi.
        """
        with self._lock:
            # Eğer zaten durmuşsa hemen dön (idempotent)
            if not self._started or not self._listener:
                return
            
            if self._started and self._listener:
                import time
                import warnings
                
                initial_qsize = self._queue.qsize()
                
                # 1. Sentinel value (poison pill) gönder
                # None değeri queue'ya konur, listener bu değeri görünce dönecek
                self._queue.put(None)
                
                # 2. Queue'nun boşalması için makul bir süre bekle
                max_wait = 30.0  # Sentinel pattern ile daha uzun timeout güvenli
                wait_interval = 0.05
                total_waited = 0.0
                
                while self._queue.qsize() > 0 and total_waited < max_wait:
                    time.sleep(wait_interval)
                    total_waited += wait_interval
                
                final_qsize = self._queue.qsize()
                
                # 3. Listener'ı durdur (sentinel değerini işler)
                self._listener.stop()
                
                # 4. Listener thread'in terminate olmasını bekle
                if hasattr(self._listener, '_thread') and self._listener._thread:
                    self._listener._thread.join(timeout=5.0)
                
                self._started = False
                
                # 5. Handler'ı birden fazla kez flush (güvenlik için)
                if hasattr(self._handler, 'flush'):
                    for _ in range(3):  # 3 kez flush
                        try:
                            self._handler.flush()
                            time.sleep(0.05)  # Her flush arası mini delay
                        except Exception:
                            pass
                
                # 6. Dosyayı kapat
                if hasattr(self._handler, 'close'):
                    try:
                        self._handler.close()
                    except Exception:
                        pass  # close() hatalarını sessizce yoksay
                
                # 7. Debug info: Queue tam flush edilmedi mi?
                if final_qsize > 1:  # Sentinel (None) hariç
                    warnings.warn(
                        f"AsyncHandler.stop(): Queue not fully flushed - "
                        f"{final_qsize - 1} messages remaining out of {initial_qsize}",
                        RuntimeWarning,
                        stacklevel=2
                    )
    
    def __del__(self):
        """Destructor - GC sırasında temizlik."""
        try:
            self.stop()
        except Exception:
            pass  # Destructor'da hata fırlatma
    
    def __enter__(self):
        """Context manager entry - otomatik start."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - otomatik stop."""
        self.stop()
        return False  # Exception'ı propagate et
    
    async def __aenter__(self):
        """Async context manager entry - otomatik start."""
        self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - otomatik stop."""
        # stop() blocking olabilir, ama short-lived
        # Gerçek async impl için asyncio.to_thread kullanılabilir
        self.stop()
        return False  # Exception'ı propagate et
    
    def get_queue_handler(self) -> QueueHandler:
        """
        Logger'a eklenecek QueueHandler'ı döndürür.
        
        Returns:
            QueueHandler instance
        """
        # Thread-safe başlatma
        if not self._started:
            self.start()
        return QueueHandler(self._queue)
    
    @property
    def handler(self) -> logging.Handler:
        """
        Gerçek handler'ı döndürür.
        
        Formatter ayarlamak için kullanılır:
            async_handler.handler.setFormatter(JSONFormatter())
        """
        return self._handler


# ═══════════════════════════════════════════════════════════════════════════════
# ASYNC CONSOLE HANDLER
# ═══════════════════════════════════════════════════════════════════════════════

class AsyncConsoleHandler(AsyncHandler):
    """
    Asenkron konsol (stdout/stderr) handler.
    
    Özellikler:
    - Asenkron yazma (ana thread bloklanmaz)
    - İsteğe bağlı ERROR+ için stderr'e yönlendirme
    
    Kullanım:
        handler = AsyncConsoleHandler()
        handler.handler.setFormatter(JSONFormatter())
        logger.addHandler(handler.get_queue_handler())
    """
    
    def __init__(
        self,
        stream: Any = None,
        level: int = logging.DEBUG,
        error_stream: Any = None,
        split_errors: bool = False
    ):
        """
        Args:
            stream:       Çıktı stream'i (default: stdout)
            level:        Minimum log seviyesi
            error_stream: Error stream (default: stderr)
            split_errors: ERROR+ logları stderr'e yönlendir
        """
        if split_errors:
            # Error'ları ayrı stream'e yönlendir
            handler = _SplitStreamHandler(
                stdout=stream or sys.stdout,
                stderr=error_stream or sys.stderr
            )
        else:
            handler = logging.StreamHandler(stream or sys.stdout)
        
        handler.setLevel(level)
        super().__init__(handler)


class _SplitStreamHandler(logging.Handler):
    """
    ERROR ve üstü için stderr, diğerleri için stdout kullanır.
    
    Bu sayede:
    - Normal loglar stdout'a (pipeable)
    - Error loglar stderr'e (dikkat çeker)
    """
    
    def __init__(self, stdout=None, stderr=None):
        super().__init__()
        self.stdout = stdout or sys.stdout
        self.stderr = stderr or sys.stderr
    
    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            stream = self.stderr if record.levelno >= logging.ERROR else self.stdout
            stream.write(msg + "\n")
            stream.flush()
        except Exception:
            self.handleError(record)


# ═══════════════════════════════════════════════════════════════════════════════
# ASYNC ROTATING FILE HANDLER
# ═══════════════════════════════════════════════════════════════════════════════

class AsyncRotatingFileHandler(AsyncHandler):
    """
    Asenkron dönen (rotating) dosya handler.
    
    Özellikler:
    - Boyut bazlı döndürme (max_bytes aşılınca yeni dosya)
    - Gzip sıkıştırma (eski dosyalar küçülür)
    - Asenkron yazma (ana thread bloklanmaz)
    - Thread-safe (çoklu thread'den güvenli yazma)
    
    Dosya Yapısı:
        /var/log/myapp/
        ├── app.log          # Aktif log dosyası
        ├── app.log.1.gz     # En yeni backup (sıkıştırılmış)
        ├── app.log.2.gz     # Daha eski
        ├── app.log.3.gz     # Daha da eski
        └── app.log.4.gz     # En eski (backup_count'a göre silinir)
    
    Kullanım:
        handler = AsyncRotatingFileHandler(
            filename="/var/log/app.log",
            max_bytes=10*1024*1024,  # 10MB
            backup_count=5,
            compress=True
        )
        handler.handler.setFormatter(JSONFormatter())
        logger.addHandler(handler.get_queue_handler())
    """
    
    def __init__(
        self,
        filename: str,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB default
        backup_count: int = 5,
        compress: bool = True,
        encoding: str = "utf-8",
        level: int = logging.DEBUG
    ):
        """
        Args:
            filename:     Log dosyası yolu
            max_bytes:    Maksimum dosya boyutu (byte)
            backup_count: Saklanacak eski dosya sayısı
            compress:     Eski dosyaları gzip ile sıkıştır
            encoding:     Dosya encoding'i
            level:        Minimum log seviyesi
        """
        handler = _RotatingFileHandler(
            filename=filename,
            max_bytes=max_bytes,
            backup_count=backup_count,
            compress=compress,
            encoding=encoding
        )
        handler.setLevel(level)
        super().__init__(handler)
        
        # Public attributes (dışarıdan erişim için)
        self.filename = filename
        self.max_bytes = max_bytes
        self.backup_count = backup_count


class _RotatingFileHandler(logging.Handler):
    """
    Gerçek rotating file handler implementasyonu.
    
    Thread-safe ve gzip desteği ile.
    """
    
    def __init__(
        self,
        filename: str,
        max_bytes: int,
        backup_count: int,
        compress: bool,
        encoding: str
    ):
        super().__init__()
        self.filename = Path(filename)
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.compress = compress
        self.encoding = encoding
        
        # Thread safety için lock
        self._lock = threading.RLock()
        self._stream: Optional[Any] = None
        
        # Dosya dizinini oluştur (yoksa)
        self.filename.parent.mkdir(parents=True, exist_ok=True)
        
        # Dosyayı aç
        self._open()
    
    def _open(self) -> None:
        """Dosyayı açar."""
        self._stream = open(self.filename, "a", encoding=self.encoding)
    
    def _close(self) -> None:
        """Dosyayı kapatır."""
        if self._stream:
            self._stream.close()
            self._stream = None
    
    def emit(self, record: logging.LogRecord) -> None:
        """Log kaydını dosyaya yazar."""
        try:
            msg = self.format(record)
            
            with self._lock:
                # Rotation gerekli mi?
                if self._should_rotate():
                    self._rotate()
                
                # Dosyaya yaz
                if self._stream:
                    self._stream.write(msg + "\n")
                    self._stream.flush()
        except Exception:
            self.handleError(record)
    
    def _should_rotate(self) -> bool:
        """Dosya döndürülmeli mi kontrol eder."""
        if self.max_bytes <= 0:
            return False
        
        if not self.filename.exists():
            return False
        
        return self.filename.stat().st_size >= self.max_bytes
    
    def _rotate(self) -> None:
        """
        Dosyayı döndürür ve eski dosyaları yönetir.
        
        Algoritma:
        1. Mevcut dosyayı kapat
        2. Eski backup'ları bir kaydır (1→2, 2→3, ...)
        3. Mevcut dosyayı .1 yap (ve sıkıştır)
        4. Yeni boş dosya aç
        5. En eski backup'ı sil (limit aşıldıysa)
        """
        self._close()
        
        # Eski backup'ları kaydır
        for i in range(self.backup_count - 1, 0, -1):
            src = self._get_backup_name(i)
            dst = self._get_backup_name(i + 1)
            
            if src.exists():
                if dst.exists():
                    dst.unlink()
                src.rename(dst)
        
        # Mevcut dosyayı ilk backup yap
        if self.filename.exists():
            backup_path = self._get_backup_name(1)
            
            if self.compress:
                # Gzip ile sıkıştır
                with open(self.filename, "rb") as f_in:
                    with gzip.open(str(backup_path) + ".gz", "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                self.filename.unlink()
            else:
                self.filename.rename(backup_path)
        
        # En eski backup'ı sil (limit aşıldıysa)
        oldest = self._get_backup_name(self.backup_count)
        if oldest.exists():
            oldest.unlink()
        if Path(str(oldest) + ".gz").exists():
            Path(str(oldest) + ".gz").unlink()
        
        # Yeni dosya aç
        self._open()
    
    def _get_backup_name(self, index: int) -> Path:
        """Backup dosya adını döndürür."""
        return Path(f"{self.filename}.{index}")
    
    def close(self) -> None:
        """Handler'ı kapatır."""
        with self._lock:
            self._close()
        super().close()


# ═══════════════════════════════════════════════════════════════════════════════
# ASYNC SMTP HANDLER
# ═══════════════════════════════════════════════════════════════════════════════

class AsyncSMTPHandler(AsyncHandler):
    """
    Asenkron SMTP (email) handler.
    
    Kritik hatalar için email bildirimi gönderir.
    Rate limiting ile spam önleme.
    
    Özellikler:
    - Asenkron gönderim (ana thread bloklanmaz)
    - Rate limiting (aynı hata için minimum aralık)
    - HTML email desteği (güzel formatlanmış)
    - TLS desteği (güvenli bağlantı)
    
    Kullanım:
        handler = AsyncSMTPHandler(
            mailhost=("smtp.gmail.com", 587),
            fromaddr="alerts@mycompany.com",
            toaddrs=["oncall@mycompany.com"],
            subject="[ALERT] Service Error",
            credentials=("user", "password"),
            secure=True,
            level=logging.ERROR  # Sadece ERROR ve üstü
        )
        logger.addHandler(handler.get_queue_handler())
    """
    
    def __init__(
        self,
        mailhost: tuple,
        fromaddr: str,
        toaddrs: List[str],
        subject: str,
        credentials: Optional[tuple] = None,
        secure: bool = True,
        level: int = logging.ERROR,
        rate_limit: int = 60,
        include_trace: bool = True
    ):
        """
        Args:
            mailhost:      (host, port) tuple. Örn: ("smtp.gmail.com", 587)
            fromaddr:      Gönderen email adresi
            toaddrs:       Alıcı email adresleri listesi
            subject:       Email konusu
            credentials:   (username, password) tuple
            secure:        TLS kullan
            level:         Minimum log seviyesi (default: ERROR)
            rate_limit:    Aynı tip hata için minimum gönderim aralığı (saniye)
            include_trace: Traceback bilgisi ekle
        """
        handler = _SMTPHandler(
            mailhost=mailhost,
            fromaddr=fromaddr,
            toaddrs=toaddrs,
            subject=subject,
            credentials=credentials,
            secure=secure,
            rate_limit=rate_limit,
            include_trace=include_trace
        )
        handler.setLevel(level)
        super().__init__(handler)


class _SMTPHandler(logging.Handler):
    """
    Gerçek SMTP handler implementasyonu.
    
    Rate limiting ve HTML email desteği ile.
    LRU cache ile memory leak önlenir.
    """
    
    def __init__(
        self,
        mailhost: tuple,
        fromaddr: str,
        toaddrs: List[str],
        subject: str,
        credentials: Optional[tuple],
        secure: bool,
        rate_limit: int,
        include_trace: bool
    ):
        super().__init__()
        self.mailhost = mailhost
        self.fromaddr = fromaddr
        self.toaddrs = toaddrs
        self.subject = subject
        self.credentials = credentials
        self.secure = secure
        self.rate_limit = rate_limit
        self.include_trace = include_trace
        
        # Rate limiting için son gönderim zamanları (LRU cache)
        from collections import OrderedDict
        self._last_sent: OrderedDict = OrderedDict()
        self._max_cache_size = 1000  # Maximum 1000 unique error signatures
        self._lock = threading.Lock()
    
    def emit(self, record: logging.LogRecord) -> None:
        """Log kaydını email olarak gönderir."""
        try:
            # Rate limiting kontrolü
            if not self._should_send(record):
                return
            
            msg = self._build_email(record)
            self._send_email(msg)
            
        except Exception:
            self.handleError(record)
    
    def _should_send(self, record: logging.LogRecord) -> bool:
        """
        Rate limiting kontrolü.
        
        Aynı tip hata için minimum aralık bekler.
        Bu sayede aynı hata 1000 kez olsa bile 1000 email gitmez.
        LRU cache ile memory leak önlenir.
        """
        if self.rate_limit <= 0:
            return True
        
        # Hata imzası oluştur
        key = f"{record.name}:{record.levelname}:{record.getMessage()[:50]}"
        now = datetime.now().timestamp()
        
        with self._lock:
            last = self._last_sent.get(key, 0)
            if now - last < self.rate_limit:
                return False  # Çok erken, gönderme
            
            # Yeni entry ekle
            self._last_sent[key] = now
            
            # LRU cleanup: Cache boyutunu sınırla (memory leak önleme)
            if len(self._last_sent) > self._max_cache_size:
                # En eski entry'yi sil (FIFO)
                self._last_sent.popitem(last=False)
        
        return True
    
    def _build_email(self, record: logging.LogRecord) -> MIMEMultipart:
        """Email mesajını oluşturur (HTML + plain text)."""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"{self.subject} - {record.levelname}"
        msg["From"] = self.fromaddr
        msg["To"] = ", ".join(self.toaddrs)
        
        # Plain text versiyon
        text_content = self._format_text(record)
        msg.attach(MIMEText(text_content, "plain"))
        
        # HTML versiyon
        html_content = self._format_html(record)
        msg.attach(MIMEText(html_content, "html"))
        
        return msg
    
    def _format_text(self, record: logging.LogRecord) -> str:
        """Plain text email içeriği."""
        lines = [
            f"Level: {record.levelname}",
            f"Service: {record.name}",
            f"Time: {datetime.now().isoformat()}",
            f"Message: {record.getMessage()}",
            ""
        ]
        
        # Extra alanları ekle
        reserved = {
            "name", "msg", "args", "levelname", "levelno", "pathname",
            "filename", "module", "exc_info", "exc_text", "stack_info",
            "lineno", "funcName", "created", "msecs", "relativeCreated",
            "thread", "threadName", "processName", "process", "message", "taskName"
        }
        
        for key, value in record.__dict__.items():
            if not key.startswith("_") and key not in reserved:
                lines.append(f"{key}: {value}")
        
        # Traceback ekle
        if self.include_trace and record.exc_info:
            lines.append("")
            lines.append("Traceback:")
            lines.append(self.format(record))
        
        return "\n".join(lines)
    
    def _format_html(self, record: logging.LogRecord) -> str:
        """HTML email içeriği (güzel formatlanmış)."""
        
        # Level'a göre renk
        color = {
            "DEBUG": "#6c757d",
            "INFO": "#28a745",
            "WARNING": "#ffc107",
            "ERROR": "#dc3545",
            "CRITICAL": "#721c24"
        }.get(record.levelname, "#000000")
        
        # Extra alanları tablo satırları olarak
        reserved = {
            "name", "msg", "args", "levelname", "levelno", "pathname",
            "filename", "module", "exc_info", "exc_text", "stack_info",
            "lineno", "funcName", "created", "msecs", "relativeCreated",
            "thread", "threadName", "processName", "process", "message", "taskName"
        }
        
        extra_rows = ""
        for key, value in record.__dict__.items():
            if not key.startswith("_") and key not in reserved:
                extra_rows += f"<tr><td><strong>{key}</strong></td><td>{value}</td></tr>"
        
        # Traceback
        traceback_html = ""
        if self.include_trace and record.exc_info:
            tb = self.format(record) if record.exc_info else ""
            traceback_html = f"""
            <h3>Traceback</h3>
            <pre style="background: #f8f9fa; padding: 10px; overflow-x: auto;">{tb}</pre>
            """
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: {color}; color: white; padding: 15px; border-radius: 5px 5px 0 0;">
                <h2 style="margin: 0;">{record.levelname}</h2>
            </div>
            <div style="border: 1px solid #ddd; padding: 15px; border-radius: 0 0 5px 5px;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr><td><strong>Service</strong></td><td>{record.name}</td></tr>
                    <tr><td><strong>Time</strong></td><td>{datetime.now().isoformat()}</td></tr>
                    <tr><td><strong>Message</strong></td><td>{record.getMessage()}</td></tr>
                    {extra_rows}
                </table>
                {traceback_html}
            </div>
        </body>
        </html>
        """
    
    def _send_email(self, msg: MIMEMultipart) -> None:
        """Email'i gönderir."""
        host, port = self.mailhost
        
        with smtplib.SMTP(host, port) as server:
            if self.secure:
                server.starttls()
            
            if self.credentials:
                server.login(*self.credentials)
            
            server.sendmail(self.fromaddr, self.toaddrs, msg.as_string())