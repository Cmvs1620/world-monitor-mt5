# MT5 GeoSignal Expert Advisor

Automated forex trading system that monitors WorldMonitor geopolitical events, classifies them with Claude AI, and executes trades on MT5.

## Quick Start

### First Time Setup

1. Run the setup script to configure your environment:
```powershell
.\setup.ps1
```

2. Edit the `.env` file with your credentials:
```bash
# Add your MT5 path, API keys, and settings
```

3. Validate your configuration:
```bash
python validate.py
```

### Configuration

- **MT5 Files Path**: Update `MT5_INSTALLATION_PATH` in `.env` to point to your MetaTrader 5 directory
- **API Keys & Credentials**: Set `CLAUDE_API_KEY`, `WORLDMONITOR_API_KEY`, and MT5 account credentials in `.env`
- **Risk Settings**: Configure `RISK_PERCENTAGE`, `MAX_POSITION_SIZE`, and `STOP_LOSS_PIPS` in configuration files

### Running the System

1. Activate the virtual environment:
```bash
source venv/bin/activate  # macOS/Linux
# or
.\venv\Scripts\activate  # Windows
```

2. Start the system:
```bash
python run.py
```

## Architecture

- **engine/**: Core trading logic and strategy execution engine
- **bridge/**: MT5 connection handler and trade execution interface
- **ea/**: MetaTrader 5 Expert Advisor MQL5 source code
- **signals/**: Event classification and trade signal generation from geopolitical data
- **logs/**: System logs and trade history records

## Phases Checklist

- [x] Phase 0: Environment Setup
- [ ] Phase 1: WorldMonitor Integration
- [ ] Phase 2: Claude AI Classification
- [ ] Phase 3: Signal Generation
- [ ] Phase 4: MT5 Bridge & Trade Execution
- [ ] Phase 5: Testing & Deployment

## Support

For detailed documentation on development practices, see [CLAUDE.md](./CLAUDE.md).
