#!/usr/bin/env python3

import sys
import time
import logging
import argparse
import yaml
from pathlib import Path
from datetime import datetime
import numpy as np
from typing import Optional

from sdr_receiver import SDRReceiver
from zvei_decoder import ZVEIDecoder
from signal_logger import SignalLogger

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ZVEIMonitor:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.setup_logging()
        
        self.receiver = SDRReceiver(
            frequency=self.config['sdr']['frequency'],
            sample_rate=self.config['sdr']['sample_rate'],
            gain=self.config['sdr']['gain']
        )
        
        self.decoder = ZVEIDecoder(
            sample_rate=self.config['decoder']['audio_sample_rate']
        )
        self.decoder.detection_threshold = self.config['decoder']['detection_threshold']
        
        self.signal_logger = SignalLogger(
            log_dir=self.config['logging']['log_dir'],
            frequency=self.config['sdr']['frequency']
        )
        
        self.last_display_time = time.time()
        self.samples_processed = 0
        
    def _load_config(self, config_path: str) -> dict:
        config_file = Path(config_path)
        if not config_file.exists():
            logger.error(f"Config file {config_path} not found")
            sys.exit(1)
            
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    
    def setup_logging(self):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, self.config['logging']['console_level']))
        
        log_dir = Path(self.config['logging']['log_dir'])
        log_dir.mkdir(exist_ok=True)
        
        file_handler = logging.FileHandler(
            log_dir / f"zvei_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        file_handler.setLevel(getattr(logging, self.config['logging']['file_level']))
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        root_logger.setLevel(logging.DEBUG)
    
    def process_samples(self, samples: np.ndarray):
        self.samples_processed += len(samples)
        
        decimation_factor = self.config['sdr']['sample_rate'] // self.config['decoder']['audio_sample_rate']
        if decimation_factor > 1:
            samples = samples[::decimation_factor]
        
        zvei_code = self.decoder.process_samples(samples)
        
        if zvei_code:
            print(f"\n{'='*50}")
            print(f"🔔 ZVEI DETECTED: {zvei_code}")
            print(f"Time: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
            print(f"{'='*50}\n")
            
            self.signal_logger.log_detection(zvei_code)
        
        current_time = time.time()
        if current_time - self.last_display_time > self.config['monitoring']['display_interval']:
            self.display_status()
            self.last_display_time = current_time
    
    def display_status(self):
        stats = self.signal_logger.get_statistics()
        print(f"\n--- Status Update ---")
        print(f"Frequency: {self.config['sdr']['frequency']/1e6:.3f} MHz")
        print(f"Samples processed: {self.samples_processed:,}")
        print(f"Total detections: {stats['total_detections']}")
        if 'unique_codes' in stats:
            print(f"Unique codes: {stats['unique_codes']}")
        if 'most_common' in stats:
            print(f"Most common: {stats['most_common']}")
        print(f"-------------------\n")
    
    def run(self):
        print(f"\n{'='*60}")
        print(f"ZVEI/CCIR Tone Monitor")
        print(f"{'='*60}")
        print(f"Frequency: {self.config['sdr']['frequency']/1e6:.3f} MHz")
        print(f"Sample Rate: {self.config['sdr']['sample_rate']/1000} kHz")
        print(f"Gain: {self.config['sdr']['gain']}")
        print(f"Device: Nooelec NESDR SMArt v5")
        print(f"Logs: {self.config['logging']['log_dir']}/")
        print(f"{'='*60}")
        print(f"Monitoring... Press Ctrl+C to stop\n")
        
        if not self.receiver.initialize():
            logger.error("Failed to initialize SDR receiver")
            return 1
        
        try:
            self.receiver.stream_samples(
                callback=self.process_samples,
                num_samples=self.config['monitoring']['buffer_size']
            )
        except KeyboardInterrupt:
            print("\n\nStopping monitor...")
        except Exception as e:
            logger.error(f"Error during monitoring: {e}")
            return 1
        finally:
            self.receiver.close()
            self.display_final_statistics()
            
        return 0
    
    def display_final_statistics(self):
        stats = self.signal_logger.get_statistics()
        print(f"\n{'='*60}")
        print(f"Session Summary")
        print(f"{'='*60}")
        print(f"Total detections: {stats['total_detections']}")
        if 'unique_codes' in stats:
            print(f"Unique codes detected: {stats['unique_codes']}")
        if 'most_common' in stats:
            print(f"Most common code: {stats['most_common']}")
        print(f"\nLog files saved:")
        for log_type, path in stats['log_files'].items():
            print(f"  {log_type.upper()}: {path}")
        print(f"{'='*60}\n")

def main():
    parser = argparse.ArgumentParser(description='ZVEI/CCIR Tone Monitor for RTL-SDR')
    parser.add_argument(
        '-c', '--config',
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    parser.add_argument(
        '-f', '--frequency',
        type=float,
        help='Override frequency in MHz'
    )
    parser.add_argument(
        '-g', '--gain',
        help='Override gain setting (auto or 0-50)'
    )
    
    args = parser.parse_args()
    
    monitor = ZVEIMonitor(args.config)
    
    if args.frequency:
        monitor.config['sdr']['frequency'] = args.frequency * 1e6
        monitor.receiver.frequency = args.frequency * 1e6
        
    if args.gain:
        try:
            gain = float(args.gain) if args.gain != 'auto' else 'auto'
            monitor.config['sdr']['gain'] = gain
            monitor.receiver.gain = gain
        except ValueError:
            logger.error(f"Invalid gain value: {args.gain}")
            sys.exit(1)
    
    sys.exit(monitor.run())

if __name__ == "__main__":
    main()