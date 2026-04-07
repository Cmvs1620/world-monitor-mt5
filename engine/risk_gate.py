"""Pre-trade risk validation and position sizing module."""


class RiskGate:
    """Validates trade signals against hardcoded risk rules before execution.

    Enforces position sizing, confidence thresholds, concurrent position limits,
    duplicate symbol prevention, and drawdown constraints.
    """

    MIN_CONFIDENCE = 0.5
    MIN_VOLUME = 0.01
    MAX_VOLUME = 10.0

    def __init__(self, config):
        """Initialize RiskGate with risk configuration.

        Args:
            config (dict): Configuration with keys:
                - account_balance (float): Total account balance in USD
                - max_concurrent_positions (int): Maximum open trades allowed
                - risk_per_trade_percent (float): Max risk per trade (e.g., 1.0 for 1%)
                - max_drawdown_percent (float): Maximum allowed drawdown %
        """
        self.account_balance = config["account_balance"]
        self.max_concurrent_positions = config["max_concurrent_positions"]
        self.risk_per_trade_percent = config["risk_per_trade_percent"]
        self.max_drawdown_percent = config["max_drawdown_percent"]

    def validate(self, signal, current_positions, current_drawdown_percent=0.0):
        """Validate signal against all risk rules and calculate position size.

        Enforces validation rules in order:
        1. Action is not HOLD
        2. Confidence threshold >= 0.5
        3. No duplicate symbols
        4. Position limit not exceeded
        5. Drawdown limit not exceeded

        Args:
            signal (dict): Trade signal with keys:
                - action (str): "BUY", "SELL", or "HOLD"
                - symbol (str): Currency pair (e.g., "EURUSD")
                - confidence (float): Signal confidence [0.0, 1.0]
                - rationale (str): Description of signal
            current_positions (list): List of dicts with "symbol" and "volume" keys
            current_drawdown_percent (float): Current account drawdown %

        Returns:
            dict: Validation result with keys:
                - allowed (bool): Whether trade is allowed
                - reason (str): Explanation of decision
                - volume (float): Position size in lots (if allowed, else 0.0)
        """
        # Rule 1: Action must not be HOLD
        if signal.get("action") == "HOLD":
            return {
                "allowed": False,
                "reason": "HOLD action signals are not opened as trades",
                "volume": 0.0,
            }

        # Rule 2: Confidence threshold
        confidence = signal.get("confidence", 0.0)
        if confidence < self.MIN_CONFIDENCE:
            return {
                "allowed": False,
                "reason": f"Confidence {confidence:.2f} below minimum threshold {self.MIN_CONFIDENCE}",
                "volume": 0.0,
            }

        # Rule 3: Check for duplicate symbol
        symbol = signal.get("symbol", "")
        existing_symbols = [pos.get("symbol", "") for pos in current_positions]
        if symbol in existing_symbols:
            return {
                "allowed": False,
                "reason": f"Symbol {symbol} already has an open position",
                "volume": 0.0,
            }

        # Rule 4: Check position limit
        if len(current_positions) >= self.max_concurrent_positions:
            return {
                "allowed": False,
                "reason": f"Maximum concurrent positions ({self.max_concurrent_positions}) already reached",
                "volume": 0.0,
            }

        # Rule 5: Check drawdown limit
        if current_drawdown_percent > self.max_drawdown_percent:
            return {
                "allowed": False,
                "reason": f"Current drawdown {current_drawdown_percent:.2f}% exceeds limit {self.max_drawdown_percent}%",
                "volume": 0.0,
            }

        # All rules passed - calculate position size
        volume = self._calculate_volume(confidence)

        return {
            "allowed": True,
            "reason": f"Trade approved for {symbol} at {confidence:.2f} confidence",
            "volume": volume,
        }

    def _calculate_volume(self, confidence):
        """Calculate position size based on account and confidence.

        Risk amount = account_balance * min(confidence/100, risk_per_trade_percent/100)
        Volume = risk_amount / 100 (simplified conversion for forex)

        Then clamped between MIN_VOLUME and MAX_VOLUME.

        Args:
            confidence (float): Signal confidence [0.0, 1.0]

        Returns:
            float: Position size in lots
        """
        # Convert confidence to percentage for risk calculation
        # Scale risk by confidence (higher confidence = larger position)
        confidence_pct = confidence * 100.0

        # Use the minimum of confidence-scaled risk or absolute risk limit
        risk_pct = min(confidence_pct, self.risk_per_trade_percent)

        # Calculate risk amount in USD
        risk_amount = self.account_balance * (risk_pct / 100.0)

        # Convert risk amount to volume (1 lot of EURUSD at ~1.1000 = ~100 units)
        # Simplified: volume = risk_amount / 100
        volume = risk_amount / 100.0

        # Clamp between min and max volume
        volume = max(self.MIN_VOLUME, min(volume, self.MAX_VOLUME))

        return volume
