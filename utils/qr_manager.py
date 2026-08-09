import qrcode
import os
import threading
import time
from typing import Optional

class QRManager:
    """
    Manages generation and expiry of QR codes.
    Demonstrates Multithreading (Concept #10) and File I/O (Concept #7).
    """
    def __init__(self, output_dir: str, expiry_seconds: int = 30):
        self.output_dir = output_dir
        self.expiry_seconds = expiry_seconds
        self.current_code: Optional[str] = None
        self._timer: Optional[threading.Timer] = None
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_qr(self, class_id: str) -> str:
        """Generates a new QR code and sets an expiry timer."""
        # Cancel existing timer if running
        if self._timer and self._timer.is_alive():
            self._timer.cancel()
            
        timestamp = int(time.time())
        self.current_code = f"ATT-{class_id}-{timestamp}"
        
        # Generator QR image using Pillow/qrcode (File I/O)
        img = qrcode.make(self.current_code)
        filename = f"qr_{class_id}.png"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'wb') as f:
            img.save(f)
            
        # Start background timer for expiry (Multithreading)
        self._timer = threading.Timer(self.expiry_seconds, self._expire_code)
        self._timer.start()
        
        return filename
        
    def _expire_code(self):
        """Callback run by background thread to invalidate the current code."""
        print(f"QR Code {self.current_code} has expired.")
        self.current_code = None
        
    def validate_code(self, code: str) -> bool:
        """Checks if a scanned code matches the currently active code."""
        if not self.current_code:
            return False
        return code == self.current_code
