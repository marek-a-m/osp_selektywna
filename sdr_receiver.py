import numpy as np
from rtlsdr import RtlSdr
import signal
import sys
from typing import Optional, Callable
import logging

logger = logging.getLogger(__name__)

class SDRReceiver:
    def __init__(self, frequency: float, sample_rate: int = 250000, gain: float = 'auto'):
        self.frequency = frequency
        self.sample_rate = sample_rate
        self.gain = gain
        self.sdr: Optional[RtlSdr] = None
        self.running = False
        
    def initialize(self):
        try:
            self.sdr = RtlSdr()
            self.sdr.sample_rate = self.sample_rate
            self.sdr.center_freq = self.frequency
            self.sdr.gain = self.gain
            logger.info(f"SDR initialized: freq={self.frequency/1e6:.3f}MHz, rate={self.sample_rate/1000}kHz, gain={self.gain}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize SDR: {e}")
            return False
    
    def read_samples(self, num_samples: int = 256*1024):
        if not self.sdr:
            raise RuntimeError("SDR not initialized")
        return self.sdr.read_samples(num_samples)
    
    def stream_samples(self, callback: Callable, num_samples: int = 256*1024):
        if not self.sdr:
            raise RuntimeError("SDR not initialized")
        
        self.running = True
        logger.info("Starting sample stream...")
        
        def signal_handler(sig, frame):
            logger.info("Stopping stream...")
            self.running = False
            
        signal.signal(signal.SIGINT, signal_handler)
        
        while self.running:
            try:
                samples = self.read_samples(num_samples)
                callback(samples)
            except Exception as e:
                logger.error(f"Error reading samples: {e}")
                break
    
    def close(self):
        if self.sdr:
            self.sdr.close()
            logger.info("SDR closed")
            
    def __enter__(self):
        self.initialize()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()