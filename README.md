# ZVEI/CCIR Tone Monitor for Raspberry Pi

SDR-based monitoring system for ZVEI/CCIR 5-tone signals using RTL-SDR on Raspberry Pi 4.

## Features

- Real-time ZVEI/CCIR tone detection and decoding
- Multiple logging formats (JSON, CSV, text)
- Configurable frequency and gain settings
- FM demodulation and tone detection
- Signal statistics and monitoring

## Hardware Requirements

- Raspberry Pi 4
- Nooelec NESDR SMArt v5 (or compatible RTL-SDR)
- Antenna suitable for your monitoring frequency

## Installation

1. Install system dependencies on Raspberry Pi:
```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-dev librtlsdr-dev rtl-sdr
```

2. Install Python packages:
```bash
pip3 install -r requirements.txt
```

3. Test RTL-SDR connection:
```bash
rtl_test
```

## Configuration

Edit `config.yaml` to set your monitoring parameters:

```yaml
sdr:
  frequency: 146500000  # Frequency in Hz
  sample_rate: 250000   # Sample rate in Hz
  gain: auto           # auto or 0-50 dB
```

## Usage

### Basic monitoring:
```bash
python3 zvei_monitor.py
```

### With custom frequency (MHz):
```bash
python3 zvei_monitor.py -f 146.5
```

### With custom gain:
```bash
python3 zvei_monitor.py -g 30
```

### With custom config file:
```bash
python3 zvei_monitor.py -c my_config.yaml
```

## Running on Raspberry Pi via SSH

1. SSH into your Raspberry Pi:
```bash
ssh pi@raspberry_ip
```

2. Navigate to project directory:
```bash
cd /path/to/selektywne
```

3. Run in background with nohup:
```bash
nohup python3 zvei_monitor.py > monitor.log 2>&1 &
```

4. Or use screen for persistent session:
```bash
screen -S zvei_monitor
python3 zvei_monitor.py
# Press Ctrl+A then D to detach
# Use 'screen -r zvei_monitor' to reattach
```

## Log Files

Logs are saved in the `logs/` directory:

- **JSON**: Structured data for processing
- **CSV**: For spreadsheet analysis
- **Text**: Human-readable log

## ZVEI/CCIR Tone Frequencies

| Digit | Frequency (Hz) |
|-------|---------------|
| 0     | 2400          |
| 1     | 1060          |
| 2     | 1160          |
| 3     | 1270          |
| 4     | 1400          |
| 5     | 1530          |
| 6     | 1670          |
| 7     | 1830          |
| 8     | 2000          |
| 9     | 2200          |
| A     | 2800          |
| B     | 810           |
| C     | 970           |
| D     | 885           |
| E     | 2600          |
| F     | 680           |

## Troubleshooting

### Permission denied for RTL-SDR:
```bash
sudo usermod -a -G plugdev $USER
# Log out and back in
```

### Device busy error:
```bash
sudo killall rtl_test rtl_fm rtl_sdr
```

### Check USB device:
```bash
lsusb | grep RTL
rtl_test -t
```

## Performance Tips

- Use a powered USB hub for better RTL-SDR stability
- Adjust gain for optimal signal (start with auto)
- Monitor CPU usage with `htop`
- Consider using a heatsink on Pi 4 for continuous operation

## License

MIT