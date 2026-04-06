"""MT5 GeoSignal Engine - Signal generation from geopolitical events."""

__version__ = "1.0.0"

# Export main classes for easy imports
from engine.worldmonitor import WorldMonitorClient

# Import other modules conditionally to support partial implementation
try:
    from engine.classifier import EventClassifier
except ImportError:
    pass

try:
    from engine.risk_gate import RiskGate
except ImportError:
    pass

try:
    from engine.router import SignalRouter
except ImportError:
    pass

__all__ = [
    "WorldMonitorClient",
]
