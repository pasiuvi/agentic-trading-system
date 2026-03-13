# agents/risk_manager.py
# PURPOSE: Risk Management Agent — checks if a trade is safe before approving
# USAGE:   Imported by orchestrator.py

class RiskManager:
    """
    This agent enforces risk management rules.
    Even if the Decision Engine says BUY, the Risk Manager can block it
    if it violates safety rules.
    """

    def __init__(
        self,
        max_position_pct = 0.15,   # Max 15% of portfolio in one asset
        stop_loss_pct    = 0.05,   # Stop loss: sell if down 5%
        min_confidence   = 0.45,   # Reject trades with confidence below 45%
        max_daily_trades = 5,      # Max 5 trades per day
    ):
        self.max_position_pct = max_position_pct
        self.stop_loss_pct    = stop_loss_pct
        self.min_confidence   = min_confidence
        self.max_daily_trades = max_daily_trades
        self.daily_trades     = 0   # counter resets each day

    def approve(
        self,
        decision,          # 'BUY', 'SELL', or 'HOLD'
        confidence,        # 0.0 to 1.0 from DecisionEngine
        current_price,     # Latest close price
        portfolio_value,   # Total portfolio value in USD
        position_value,    # Current value held in this asset
        avg_buy_price=None # Average price we paid (for stop-loss)
    ):
        """
        Checks the proposed decision against all risk rules.
        Returns: dict with approved (bool), action, reason, and suggested trade size
        """
        # Default: approve the decision as-is
        result = {
            'approved':          True,
            'action':            decision,
            'reason':            'All risk checks passed',
            'suggested_size_usd': 0.0,
        }

        # ── Check 1: Confidence threshold ─────────────────────────────
        # If the AI is not confident enough, do not trade
        if confidence < self.min_confidence and decision != 'HOLD':
            result.update({
                'approved': False,
                'action':   'HOLD',
                'reason':   f'Confidence {confidence:.0%} below minimum {self.min_confidence:.0%}',
            })
            return result

        # ── Check 2: Daily trade limit ────────────────────────────────
        if self.daily_trades >= self.max_daily_trades and decision != 'HOLD':
            result.update({
                'approved': False,
                'action':   'HOLD',
                'reason':   f'Daily trade limit reached ({self.max_daily_trades})',
            })
            return result

        # ── Check 3: Position size limit ──────────────────────────────
        # Do not buy if already holding too much of this asset
        if decision == 'BUY':
            if portfolio_value > 0:
                current_pct = position_value / portfolio_value
                if current_pct >= self.max_position_pct:
                    result.update({
                        'approved': False,
                        'action':   'HOLD',
                        'reason':   f'Position {current_pct:.0%} already at max {self.max_position_pct:.0%}',
                    })
                    return result

            # Calculate how much to buy (10% of portfolio per trade)
            trade_size_usd = portfolio_value * 0.10
            result['suggested_size_usd'] = round(trade_size_usd, 2)

        # ── Check 4: Stop-loss (for SELL decisions) ───────────────────
        # If we are down more than stop_loss_pct, force a SELL
        if avg_buy_price and avg_buy_price > 0:
            loss_pct = (avg_buy_price - current_price) / avg_buy_price
            if loss_pct >= self.stop_loss_pct:
                result.update({
                    'approved': True,
                    'action':   'SELL',
                    'reason':   f'Stop-loss triggered: down {loss_pct:.1%} from avg buy price',
                })
                return result

        # Approved — increment trade counter
        if decision != 'HOLD':
            self.daily_trades += 1

        return result

    def reset_daily_counter(self):
        """Call this at the start of each trading day."""
        self.daily_trades = 0
