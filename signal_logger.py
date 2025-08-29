import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import csv

logger = logging.getLogger(__name__)

class SignalLogger:
    def __init__(self, log_dir: str = "logs", frequency: float = 0):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.frequency = frequency
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        freq_mhz = int(frequency / 1e6) if frequency else 0
        
        self.json_file = self.log_dir / f"zvei_{freq_mhz}MHz_{timestamp}.json"
        self.csv_file = self.log_dir / f"zvei_{freq_mhz}MHz_{timestamp}.csv"
        self.text_file = self.log_dir / f"zvei_{freq_mhz}MHz_{timestamp}.txt"
        
        self._init_csv()
        self._init_text_log()
        
        self.detection_count = 0
        
    def _init_csv(self):
        with open(self.csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'date_time', 'zvei_code', 'frequency_mhz', 'signal_strength'])
            
    def _init_text_log(self):
        with open(self.text_file, 'w') as f:
            f.write(f"ZVEI/CCIR Signal Detection Log\n")
            f.write(f"Frequency: {self.frequency/1e6:.3f} MHz\n")
            f.write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*50 + "\n\n")
    
    def log_detection(self, zvei_code: str, signal_strength: Optional[float] = None):
        timestamp = datetime.now()
        self.detection_count += 1
        
        detection_data = {
            'timestamp': timestamp.timestamp(),
            'datetime': timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'zvei_code': zvei_code,
            'frequency_mhz': self.frequency / 1e6,
            'signal_strength': signal_strength,
            'detection_number': self.detection_count
        }
        
        self._log_json(detection_data)
        self._log_csv(detection_data)
        self._log_text(detection_data)
        
        logger.info(f"Logged ZVEI: {zvei_code} at {detection_data['datetime']}")
        
        return detection_data
    
    def _log_json(self, data: Dict[str, Any]):
        try:
            if self.json_file.exists():
                with open(self.json_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []
                
            logs.append(data)
            
            with open(self.json_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to write JSON log: {e}")
    
    def _log_csv(self, data: Dict[str, Any]):
        try:
            with open(self.csv_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    data['timestamp'],
                    data['datetime'],
                    data['zvei_code'],
                    data['frequency_mhz'],
                    data['signal_strength'] or ''
                ])
        except Exception as e:
            logger.error(f"Failed to write CSV log: {e}")
    
    def _log_text(self, data: Dict[str, Any]):
        try:
            with open(self.text_file, 'a') as f:
                f.write(f"[{data['datetime']}] ZVEI: {data['zvei_code']}")
                if data['signal_strength']:
                    f.write(f" (Signal: {data['signal_strength']:.1f}dB)")
                f.write("\n")
        except Exception as e:
            logger.error(f"Failed to write text log: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        stats = {
            'total_detections': self.detection_count,
            'log_files': {
                'json': str(self.json_file),
                'csv': str(self.csv_file),
                'text': str(self.text_file)
            },
            'frequency_mhz': self.frequency / 1e6
        }
        
        try:
            if self.json_file.exists():
                with open(self.json_file, 'r') as f:
                    logs = json.load(f)
                    if logs:
                        zvei_codes = [log['zvei_code'] for log in logs]
                        unique_codes = list(set(zvei_codes))
                        stats['unique_codes'] = len(unique_codes)
                        stats['most_common'] = max(set(zvei_codes), key=zvei_codes.count)
        except Exception as e:
            logger.error(f"Failed to calculate statistics: {e}")
            
        return stats