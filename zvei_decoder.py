import numpy as np
from scipy import signal as scipy_signal
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class ZVEIDecoder:
    ZVEI_TONES = {
        '0': 2400,
        '1': 1060,
        '2': 1160,
        '3': 1270,
        '4': 1400,
        '5': 1530,
        '6': 1670,
        '7': 1830,
        '8': 2000,
        '9': 2200,
        'A': 2800,
        'B': 810,
        'C': 970,
        'D': 885,
        'E': 2600,
        'F': 680,
        'REPEAT': 2400,
    }
    
    TONE_DURATION = 0.07  # 70ms per tone in ZVEI
    TONE_TOLERANCE = 20  # Hz tolerance for tone detection
    
    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate
        self.tone_map = {freq: digit for digit, freq in self.ZVEI_TONES.items()}
        self.last_detected = ""
        self.detection_threshold = 0.1
        
    def demodulate_fm(self, samples: np.ndarray) -> np.ndarray:
        analytic_signal = scipy_signal.hilbert(samples)
        phase = np.unwrap(np.angle(analytic_signal))
        demodulated = np.diff(phase) * self.sample_rate / (2 * np.pi)
        
        nyquist = self.sample_rate / 2
        cutoff = 3000  # Low-pass filter at 3kHz for ZVEI tones
        b, a = scipy_signal.butter(4, cutoff / nyquist, btype='low')
        filtered = scipy_signal.filtfilt(b, a, demodulated)
        
        return filtered
    
    def detect_tone(self, audio_segment: np.ndarray) -> Optional[str]:
        window = scipy_signal.windows.hamming(len(audio_segment))
        windowed = audio_segment * window
        
        fft = np.fft.rfft(windowed)
        freqs = np.fft.rfftfreq(len(windowed), 1/self.sample_rate)
        magnitude = np.abs(fft)
        
        magnitude = magnitude / np.max(magnitude) if np.max(magnitude) > 0 else magnitude
        
        peak_indices = scipy_signal.find_peaks(magnitude, height=self.detection_threshold)[0]
        
        if len(peak_indices) == 0:
            return None
            
        peak_idx = peak_indices[np.argmax(magnitude[peak_indices])]
        peak_freq = freqs[peak_idx]
        
        for digit, tone_freq in self.ZVEI_TONES.items():
            if abs(peak_freq - tone_freq) <= self.TONE_TOLERANCE:
                return digit
                
        return None
    
    def decode_sequence(self, audio_data: np.ndarray) -> List[Tuple[str, float]]:
        tone_samples = int(self.TONE_DURATION * self.sample_rate)
        hop_size = tone_samples // 2  # 50% overlap for better detection
        
        decoded_sequence = []
        timestamps = []
        
        for i in range(0, len(audio_data) - tone_samples, hop_size):
            segment = audio_data[i:i + tone_samples]
            detected_digit = self.detect_tone(segment)
            
            if detected_digit:
                timestamp = i / self.sample_rate
                
                if not decoded_sequence or (decoded_sequence[-1][0] != detected_digit or 
                                           timestamp - decoded_sequence[-1][1] > 0.1):
                    decoded_sequence.append((detected_digit, timestamp))
                    logger.debug(f"Detected tone: {detected_digit} at {timestamp:.3f}s")
        
        return self._clean_sequence(decoded_sequence)
    
    def _clean_sequence(self, sequence: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
        if not sequence:
            return []
            
        cleaned = []
        i = 0
        while i < len(sequence):
            digit, timestamp = sequence[i]
            
            if i + 1 < len(sequence) and sequence[i + 1][1] - timestamp < 0.05:
                i += 1
                continue
                
            cleaned.append((digit, timestamp))
            i += 1
            
        min_sequence_length = 5
        if len(cleaned) >= min_sequence_length:
            digits_only = ''.join([d for d, _ in cleaned])
            if digits_only != self.last_detected:
                self.last_detected = digits_only
                return cleaned
                
        return []
    
    def process_samples(self, iq_samples: np.ndarray) -> Optional[str]:
        try:
            audio = self.demodulate_fm(np.real(iq_samples))
            
            decoded = self.decode_sequence(audio)
            
            if decoded:
                zvei_code = ''.join([digit for digit, _ in decoded])
                return zvei_code
                
        except Exception as e:
            logger.error(f"Error processing samples: {e}")
            
        return None