# Resource Testing Documentation

## Application Memory Footprint

### Development Environment
- Host System: Windows 10, 8GB RAM
- Python Version: 3.13.9

### Actual Application Usage
- Flask Process: ~150MB RAM
- System Monitoring: ~50MB RAM
- Total Footprint: ~200MB RAM

### Production Testing

#### Test 1: Docker Memory Constraint
```bash
docker run --memory="1g" 1gb-server
Result: ✓ Running stable for 24 hours
Peak Memory: 220MB
