//+------------------------------------------------------------------+
//| Signal Structures for GeoSignal Expert Advisor                  |
//| Defines shared data structures for signal processing            |
//+------------------------------------------------------------------+
#ifndef __SIGNAL_STRUCT_MQH__
#define __SIGNAL_STRUCT_MQH__

//+------------------------------------------------------------------+
//| TradeSignal Structure                                            |
//| Represents a trading signal read from signal.json               |
//+------------------------------------------------------------------+
struct TradeSignal
{
    string timestamp;        // ISO 8601 timestamp of signal generation
    string event_id;         // Unique event identifier
    string event_title;      // Event title/description
    string action;           // Trading action: "BUY", "SELL", "HOLD"
    string symbol;           // Trading symbol (e.g., "XAUUSD", "EURUSD")
    double confidence;       // Confidence level (0.0 to 1.0)
    double volume;           // Suggested trade volume/lot size
    double stop_loss;        // Stop loss price level
    double take_profit;      // Take profit price level
    string rationale;        // Trade rationale from signal source
};

//+------------------------------------------------------------------+
//| ExecutionResult Structure                                        |
//| Represents the result of signal execution, written to JSON      |
//+------------------------------------------------------------------+
struct ExecutionResult
{
    string timestamp;        // ISO 8601 timestamp of execution
    string signal_id;        // Reference to original signal
    bool executed;           // Whether order was successfully placed
    string status;           // Status: "success", "skipped", "error"
    ulong ticket;            // MT5 order ticket if successful (0 if failed)
    string error_reason;     // Error description if status is "error"
};

//+------------------------------------------------------------------+
//| Helper Functions                                                 |
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//| InitSignal() - Initialize TradeSignal structure                 |
//+------------------------------------------------------------------+
void InitSignal(TradeSignal &signal)
{
    signal.timestamp = "";
    signal.event_id = "";
    signal.event_title = "";
    signal.action = "HOLD";
    signal.symbol = "";
    signal.confidence = 0.0;
    signal.volume = 0.0;
    signal.stop_loss = 0.0;
    signal.take_profit = 0.0;
    signal.rationale = "";
}

//+------------------------------------------------------------------+
//| InitExecutionResult() - Initialize ExecutionResult structure    |
//+------------------------------------------------------------------+
void InitExecutionResult(ExecutionResult &result)
{
    result.timestamp = "";
    result.signal_id = "";
    result.executed = false;
    result.status = "error";
    result.ticket = 0;
    result.error_reason = "";
}

#endif
