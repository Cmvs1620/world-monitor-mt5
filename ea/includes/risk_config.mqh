//+------------------------------------------------------------------+
//| Risk Configuration for GeoSignal Expert Advisor                 |
//| Defines risk parameters, instrument configs, and helper funcs   |
//+------------------------------------------------------------------+
#ifndef __RISK_CONFIG_MQH__
#define __RISK_CONFIG_MQH__

//+------------------------------------------------------------------+
//| Input Parameters (Configurable in MT5)                          |
//+------------------------------------------------------------------+

// Core EA control parameters
extern bool EA_ENABLED = true;
extern bool EA_TRADING_ENABLED = false;  // Separate from EA_ENABLED for testing
extern int POLL_INTERVAL_SECONDS = 5;
extern int BRIDGE_TIMEOUT_SECONDS = 30;

// Position management
extern int MAX_CONCURRENT_POSITIONS = 5;
extern double RISK_PER_TRADE_PERCENT = 2.0;  // Risk per trade as % of account
extern double MAX_DAILY_LOSS_PERCENT = 10.0; // Maximum daily loss threshold
extern double MAX_DRAWDOWN_PERCENT = 15.0;   // Maximum drawdown threshold

// File paths and debugging
extern string SIGNAL_FILE_PATH = "signal.json";
extern bool DEBUG_MODE = false;

//+------------------------------------------------------------------+
//| Instrument Configuration Structure                              |
//+------------------------------------------------------------------+
struct InstrumentConfig
{
    string symbol;           // Symbol name
    int stop_loss_pips;      // Stop loss in pips
    int take_profit_pips;    // Take profit in pips
};

//+------------------------------------------------------------------+
//| Instrument Configuration Array                                  |
//| Maps common forex and commodity pairs to SL/TP settings         |
//+------------------------------------------------------------------+
const InstrumentConfig INSTRUMENT_CONFIGS[] =
{
    {"XAUUSD",   15, 30},   // Gold:     SL=15, TP=30
    {"EURUSD",   20, 40},   // EUR/USD:  SL=20, TP=40
    {"GBPUSD",   20, 40},   // GBP/USD:  SL=20, TP=40
    {"USDJPY",   20, 40},   // USD/JPY:  SL=20, TP=40
    {"AUDUSD",   20, 40},   // AUD/USD:  SL=20, TP=40
    {"USDCAD",   20, 40},   // USD/CAD:  SL=20, TP=40
    {"NZDUSD",   20, 40},   // NZD/USD:  SL=20, TP=40
    {"USDCHF",   20, 40},   // USD/CHF:  SL=20, TP=40
    {"EURGBP",   20, 40},   // EUR/GBP:  SL=20, TP=40
    {"EURJPY",   25, 50},   // EUR/JPY:  SL=25, TP=50
    {"GBPJPY",   25, 50},   // GBP/JPY:  SL=25, TP=50
    {"WTIUSD",   15, 30},   // Crude Oil: SL=15, TP=30
    {"BRENTUSD", 15, 30},   // Brent Oil: SL=15, TP=30
    {"US30",     30, 60},   // US 30 (Dow): SL=30, TP=60
    {"SPX500",   30, 60},   // S&P 500:  SL=30, TP=60
    {"Germany40", 30, 60},  // DAX:      SL=30, TP=60
    {"UK100",    30, 60}    // FTSE 100: SL=30, TP=60
};

const int INSTRUMENT_CONFIGS_SIZE = ArraySize(INSTRUMENT_CONFIGS);

//+------------------------------------------------------------------+
//| Helper Function: GetInstrumentConfig()                          |
//| Retrieves SL/TP configuration for a given symbol                |
//| Returns: true if config found, false otherwise                  |
//+------------------------------------------------------------------+
bool GetInstrumentConfig(const string symbol, int &out_sl, int &out_tp)
{
    // Default values if not found
    out_sl = 20;
    out_tp = 40;

    // Search through configuration array
    for(int i = 0; i < INSTRUMENT_CONFIGS_SIZE; i++)
    {
        if(INSTRUMENT_CONFIGS[i].symbol == symbol)
        {
            out_sl = INSTRUMENT_CONFIGS[i].stop_loss_pips;
            out_tp = INSTRUMENT_CONFIGS[i].take_profit_pips;
            return true;
        }
    }

    // Symbol not found, return false but use defaults
    return false;
}

//+------------------------------------------------------------------+
//| Helper Function: CalculatePositionSize()                        |
//| Calculates position size based on risk management rules          |
//|
//| Parameters:                                                      |
//|   account_balance - Current account balance                     |
//|   risk_pips - Number of pips for stop loss                      |
//|   point_value - Value per pip for the symbol                    |
//|   risk_percent - Risk percentage per trade (default from config) |
//|                                                                  |
//| Returns: Position size in lots                                   |
//+------------------------------------------------------------------+
double CalculatePositionSize(double account_balance,
                             int risk_pips,
                             double point_value,
                             double risk_percent = -1.0)
{
    // Use default if not specified
    if(risk_percent < 0)
        risk_percent = RISK_PER_TRADE_PERCENT;

    // Validate inputs
    if(account_balance <= 0 || risk_pips <= 0 || point_value <= 0)
        return 0.0;

    // Calculate risk amount in account currency
    double risk_amount = account_balance * (risk_percent / 100.0);

    // Calculate position size
    // position_size (in lots) = risk_amount / (risk_pips * point_value * 100000)
    // The 100000 factor converts to standard lot (100,000 units)
    double position_size = risk_amount / (risk_pips * point_value * 100000);

    // Ensure minimum lot size (typically 0.01 for micro lots)
    if(position_size < 0.01)
        position_size = 0.01;

    // Round down to nearest 0.01 lot
    position_size = MathFloor(position_size * 100) / 100.0;

    return position_size;
}

//+------------------------------------------------------------------+
//| Helper Function: CheckRiskThresholds()                          |
//| Validates if current account state allows new trades             |
//|                                                                  |
//| Parameters:                                                      |
//|   account_equity - Current account equity                       |
//|   account_balance - Current account balance                     |
//|                                                                  |
//| Returns: true if thresholds are within limits, false otherwise  |
//+------------------------------------------------------------------+
bool CheckRiskThresholds(double account_equity, double account_balance)
{
    // Check daily loss threshold
    double daily_loss = account_balance - account_equity;
    double daily_loss_percent = (daily_loss / account_balance) * 100.0;

    if(daily_loss_percent > MAX_DAILY_LOSS_PERCENT)
    {
        if(DEBUG_MODE)
            Print("Risk threshold exceeded: Daily loss ", daily_loss_percent, "% exceeds limit ", MAX_DAILY_LOSS_PERCENT, "%");
        return false;
    }

    // Check drawdown threshold
    double drawdown_percent = daily_loss_percent;  // Simplified: use daily loss as proxy

    if(drawdown_percent > MAX_DRAWDOWN_PERCENT)
    {
        if(DEBUG_MODE)
            Print("Risk threshold exceeded: Drawdown ", drawdown_percent, "% exceeds limit ", MAX_DRAWDOWN_PERCENT, "%");
        return false;
    }

    return true;
}

#endif
