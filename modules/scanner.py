"""
Kiwiyd Antivirus Scanner Module (Python)
Multi-threaded scanner focused on MD5 hash detection from virus_hashes.json
Integrates with main app for directory selection, thread count configuration, and logging.
"""

import os
import json
import hashlib
import threading
from pathlib import Path
from datetime import datetime
from typing import Callable, List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from i18n import get_translator


@dataclass
class ScanResult:
    """Represents a scanned file result"""
    path: str
    name: str
    extension: str
    size: int
    md5: str
    threat_type: str
    threat_name: str


class VirusHashDatabase:
    """Database of known virus MD5 hashes loaded from virus_hashes.json"""
    
    def __init__(self):
        """Initialize virus hash database"""
        self.hashes: Dict[str, Dict[str, str]] = {}  # hash -> {name, type, severity}
        self.lock = threading.Lock()
        self.load_from_json()
    
    def load_from_json(self, filepath: str = "data/virus_hashes.json") -> bool:
        """Load virus hashes from JSON file
        
        Args:
            filepath: Path to virus_hashes.json
            
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            if not os.path.exists(filepath):
                return False
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if "hashes" in data:
                with self.lock:
                    for hash_val, info in data["hashes"].items():
                        hash_lower = hash_val.lower()
                        self.hashes[hash_lower] = {
                            "name": info.get("name", "Unknown"),
                            "type": info.get("type", "unknown"),
                            "severity": info.get("severity", "medium")
                        }
            return True
        except Exception as e:
            print(f"Warning: Could not load virus hash database: {e}")
            return False
    
    def check_hash(self, file_hash: str) -> Optional[Dict[str, str]]:
        """Check if file hash matches known virus
        
        Args:
            file_hash: MD5 hash to check
            
        Returns:
            Dict with threat info if found, None otherwise
        """
        if not file_hash:
            return None
        
        hash_lower = file_hash.lower()
        with self.lock:
            return self.hashes.get(hash_lower)
    
    def get_count(self) -> int:
        """Get total number of virus hashes"""
        with self.lock:
            return len(self.hashes)


class FileScanner:
    """Multi-threaded file scanner"""
    
    def __init__(self, 
                 virus_db: VirusHashDatabase,
                 thread_count: int = 4,
                 log_callback: Optional[Callable[[str], None]] = None):
        """Initialize scanner
        
        Args:
            virus_db: VirusHashDatabase instance
            thread_count: Number of threads to use for scanning
            log_callback: Optional callback function for logging (receives log message)
        """
        self.virus_db = virus_db
        self.thread_count = max(1, min(thread_count, os.cpu_count() or 4))
        self.log_callback = log_callback
        self.results: List[ScanResult] = []
        self.lock = threading.Lock()
        self.total_files_scanned = 0
        self.total_threats_found = 0
        self.translator = get_translator()  # Add translator reference
    
    def log(self, message: str):
        """Log a message
        
        Args:
            message: Message to log
        """
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)
    
    @staticmethod
    def calculate_md5(filepath: str, chunk_size: int = 65536) -> str:
        """Calculate MD5 hash of file
        
        Args:
            filepath: Path to file
            chunk_size: Chunk size for reading
            
        Returns:
            MD5 hash as hex string, or empty string on error
        """
        try:
            md5_hash = hashlib.md5()
            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    md5_hash.update(chunk)
            return md5_hash.hexdigest()
        except Exception:
            return ""
    
    def _process_file(self, filepath: str) -> Optional[ScanResult]:
        """Process a single file (calculate MD5 and check against database)
        
        Args:
            filepath: Path to file to scan
            
        Returns:
            ScanResult if threat found, None otherwise
        """
        try:
            if not os.path.isfile(filepath):
                return None
            
            # Get file info
            filename = os.path.basename(filepath)
            extension = Path(filename).suffix.lower()
            try:
                file_size = os.path.getsize(filepath)
            except Exception:
                file_size = 0
            
            # Calculate MD5
            file_md5 = self.calculate_md5(filepath)
            
            # Increment scan counter
            with self.lock:
                self.total_files_scanned += 1
            
            # Log file being scanned
            self.log(f"[*] Scanning: {filename}")
            
            # Check against virus database
            threat_info = self.virus_db.check_hash(file_md5)
            if threat_info:
                result = ScanResult(
                    path=filepath,
                    name=filename,
                    extension=extension,
                    size=file_size,
                    md5=file_md5,
                    threat_type=threat_info["type"],
                    threat_name=threat_info["name"]
                )
                
                with self.lock:
                    self.total_threats_found += 1
                
                self.log(f"[!] THREAT DETECTED: {filename}")
                self.log(f"    Type: {threat_info['type']}")
                self.log(f"    Name: {threat_info['name']}")
                self.log(f"    MD5: {file_md5}")
                self.log(f"    Severity: {threat_info['severity']}")
                
                return result
            
            return None
        
        except Exception as e:
            self.log(f"[ERROR] Error scanning {filepath}: {str(e)}")
            return None
    
    def scan_directory(self, directory: str, max_depth: int = 3) -> List[ScanResult]:
        """Scan directory for malware
        
        Args:
            directory: Directory path to scan
            max_depth: Maximum recursion depth
            
        Returns:
            List of ScanResult objects for detected threats
        """
        if not os.path.exists(directory):
            self.log(f"[ERROR] Directory not found: {directory}")
            return []
        
        self.results = []
        self.total_files_scanned = 0
        self.total_threats_found = 0
        
        # Collect all files to scan
        files_to_scan = []
        
        self.log(f"[*] Starting scan of: {directory}")
        self.log(f"[*] Using {self.thread_count} thread(s)")
        self.log(f"[*] Virus database: {self.virus_db.get_count()} signatures loaded")
        self.log("")
        
        try:
            for root, dirs, files in os.walk(directory):
                # Check depth
                depth = root.replace(directory, "").count(os.sep)
                if depth >= max_depth:
                    dirs.clear()
                    continue
                
                for filename in files:
                    filepath = os.path.join(root, filename)
                    files_to_scan.append(filepath)
        
        except Exception as e:
            self.log(f"[ERROR] Error traversing directory: {str(e)}")
            return []
        
        # Scan files using thread pool
        if files_to_scan:
            with ThreadPoolExecutor(max_workers=self.thread_count) as executor:
                futures = [executor.submit(self._process_file, f) for f in files_to_scan]
                
                for future in futures:
                    try:
                        result = future.result()
                        if result:
                            with self.lock:
                                self.results.append(result)
                    except Exception as e:
                        self.log(f"[ERROR] Thread error: {str(e)}")
        
        # Log summary
        self.log("")
        self.log(f"[OK] Scan completed")
        self.log(f"[OK] Files scanned: {self.total_files_scanned}")
        self.log(f"[OK] Threats found: {self.total_threats_found}")
        
        return self.results
    
    def scan_custom_directory(self, directory: str) -> str:
        """Scan custom directory and return JSON result
        
        Args:
            directory: Directory to scan
            
        Returns:
            JSON string with scan results
        """
        results = self.scan_directory(directory)
        
        result_dict = {
            "status": "completed",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "directory": directory,
            "files_scanned": self.total_files_scanned,
            "threats_found": self.total_threats_found,
            "database_entries": self.virus_db.get_count(),
            "threats": [
                {
                    "path": r.path,
                    "name": r.name,
                    "md5": r.md5,
                    "type": r.threat_type,
                    "threat": r.threat_name,
                    "size": r.size
                }
                for r in results
            ]
        }
        
        return json.dumps(result_dict, indent=2, ensure_ascii=False)


# Global scanner instance
_virus_db = VirusHashDatabase()
_scanner = None


def initialize_scanner(thread_count: int = 4, 
                      log_callback: Optional[Callable[[str], None]] = None) -> FileScanner:
    """Initialize global scanner instance
    
    Args:
        thread_count: Number of threads to use
        log_callback: Optional callback for logging
        
    Returns:
        FileScanner instance
    """
    global _scanner
    _scanner = FileScanner(_virus_db, thread_count=thread_count, log_callback=log_callback)
    return _scanner


def get_scanner() -> Optional[FileScanner]:
    """Get global scanner instance
    
    Returns:
        FileScanner instance or None if not initialized
    """
    return _scanner


def scan_directory(directory: str, 
                  thread_count: int = 4,
                  log_callback: Optional[Callable[[str], None]] = None) -> str:
    """Scan directory for malware
    
    Args:
        directory: Directory path to scan
        thread_count: Number of threads to use
        log_callback: Optional callback for logging
        
    Returns:
        JSON string with scan results
    """
    scanner = FileScanner(_virus_db, thread_count=thread_count, log_callback=log_callback)
    scanner.scan_directory(directory)
    return scanner.scan_custom_directory(directory)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        directory = sys.argv[1]
        threads = int(sys.argv[2]) if len(sys.argv) > 2 else 4
        
        print(scan_directory(directory, thread_count=threads))
    else:
        print("[ERROR] Usage: scanner.py <directory> [thread_count]")
