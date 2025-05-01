# src/api/log_reader.py
import os
import re
from datetime import datetime
from typing import List, Optional, Dict, Iterator, Set
from core.logger import logger
from .api_models import LogEntry, LogFilter

class LogReader:
    """Log dosyalarını okuyup işleyen sınıf"""
    
    # Log satırı ayrıştırma için regex pattern
    LOG_PATTERN = re.compile(
        r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) \[(\w+)\] (?:\[([^:]+):(\d+)\] )?(.+)'
    )
    
    def __init__(self, log_dir: str = "logs"):
        """LogReader sınıfını başlatır"""
        self.log_dir = log_dir
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            logger.info(f"Log dizini oluşturuldu: {log_dir}")
    
    def get_available_log_files(self) -> List[str]:
        """Mevcut tüm log dosyalarını listeler"""
        try:
            return [f for f in os.listdir(self.log_dir) if f.endswith('.log')]
        except Exception as e:
            logger.error(f"Log dosyalarını listeleme hatası: {str(e)}")
            return []
    
    def parse_log_line(self, line: str) -> Optional[LogEntry]:
        """Bir log satırını ayrıştırır"""
        match = self.LOG_PATTERN.match(line)
        if not match:
            return None
        
        timestamp_str, level, source, line_number, message = match.groups()
        try:
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
            return LogEntry(
                timestamp=timestamp,
                level=level,
                message=message,
                source=source,
                line_number=int(line_number) if line_number else None
            )
        except Exception as e:
            logger.error(f"Log satırı ayrıştırma hatası: {str(e)}")
            return None
    
    def read_log_file(self, filename: str, filter_options: Optional[LogFilter] = None) -> List[LogEntry]:
        """Belirtilen log dosyasını okur ve filtreler"""
        try:
            file_path = os.path.join(self.log_dir, filename)
            if not os.path.exists(file_path):
                logger.warning(f"Log dosyası bulunamadı: {file_path}")
                return []
            
            # Filtreleme seçeneklerini ayarla
            filter_opts = filter_options or LogFilter()
            level_filter = filter_opts.level.upper() if filter_opts.level else None
            search_term = filter_opts.search_term.lower() if filter_opts.search_term else None
            source_file = filter_opts.source_file
            limit = filter_opts.limit
            
            # Dosyayı oku ve filtreleri uygula
            entries = []
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if not line:
                        continue
                    
                    entry = self.parse_log_line(line)
                    if not entry:
                        continue
                    
                    # Filtrelemeleri uygula
                    if level_filter and entry.level != level_filter:
                        continue
                    
                    if search_term and search_term not in entry.message.lower():
                        continue
                    
                    if source_file and (not entry.source or entry.source != source_file):
                        continue
                    
                    entries.append(entry)
                    
                    # Limit kontrolü
                    if len(entries) >= limit:
                        break
            
            return entries
        
        except Exception as e:
            logger.error(f"Log dosyası okuma hatası: {str(e)}")
            return []
    
    def tail_log_file(self, filename: str, n: int = 100) -> List[LogEntry]:
        """Bir log dosyasının son n satırını okur"""
        try:
            file_path = os.path.join(self.log_dir, filename)
            if not os.path.exists(file_path):
                logger.warning(f"Log dosyası bulunamadı: {file_path}")
                return []
            
            # Dosya boyutunu kontrol et
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return []
            
            # Son n satırı okumak için
            lines = []
            with open(file_path, 'r', encoding='utf-8') as file:
                # Başlangıçta tüm satırları alalım ve sondan başlayarak işleyelim
                all_lines = file.readlines()
                count = min(n, len(all_lines))
                
                for line in all_lines[-count:]:
                    line = line.strip()
                    if not line:
                        continue
                    
                    entry = self.parse_log_line(line)
                    if entry:
                        lines.append(entry)
            
            return lines
        
        except Exception as e:
            logger.error(f"Log dosyası tail hatası: {str(e)}")
            return []
    
    def get_available_log_levels(self) -> Set[str]:
        """Mevcut tüm log seviyelerini döndürür"""
        return {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
    
    def get_available_source_files(self) -> Set[str]:
        """Log kayıtlarında geçen kaynak dosyaları bulur"""
        try:
            source_files = set()
            
            for log_file in self.get_available_log_files():
                file_path = os.path.join(self.log_dir, log_file)
                with open(file_path, 'r', encoding='utf-8') as file:
                    for line in file:
                        match = self.LOG_PATTERN.match(line.strip())
                        if match and match.group(3):  # source file
                            source_files.add(match.group(3))
            
            return source_files
        except Exception as e:
            logger.error(f"Kaynak dosyaları alma hatası: {str(e)}")
            return set()
    
    def monitor_log_file(self, filename: str) -> Iterator[LogEntry]:
        """Log dosyasını gerçek zamanlı olarak izler (generator)"""
        try:
            file_path = os.path.join(self.log_dir, filename)
            if not os.path.exists(file_path):
                logger.warning(f"Log dosyası bulunamadı: {file_path}")
                return
            
            with open(file_path, 'r', encoding='utf-8') as file:
                # Dosyanın sonuna git
                file.seek(0, 2)
                
                while True:
                    line = file.readline()
                    if line:
                        line = line.strip()
                        entry = self.parse_log_line(line)
                        if entry:
                            yield entry
                    else:
                        # Yeni satır yoksa küçük bir bekleme yapabiliriz
                        # Bu örnekte bekleme yapmıyoruz çünkü WebSocket
                        # ile zaten polling yapılacak
                        break
        
        except Exception as e:
            logger.error(f"Log dosyası izleme hatası: {str(e)}")
            return


# Global log reader instance
log_reader = LogReader()

def get_log_reader() -> LogReader:
    """Global log reader nesnesini döndürür"""
    return log_reader 