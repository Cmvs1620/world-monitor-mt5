//+------------------------------------------------------------------+
//| GeoSignal Expert Advisor                                        |
//| Main EA for executing trading signals from Python               |
//| Reads signals from signal.json and executes trades on MT5       |
//+------------------------------------------------------------------+
#property copyright "GeoSignal Trading System"
#property link      "https://geosignal.io"
#property version   "1.00"
#property strict
#property description "Executes trading signals from Python geopolitical event signals"

//+------------------------------------------------------------------+
//| Includes and Globals (Lines 1-30)                               |
//+------------------------------------------------------------------+

#include <Trade\Trade.mqh>
#include "includes/signal_struct.mqh"
#include "includes/risk_config.mqh"
#include <stdlib.mqh>
#include <stdio.mqh>

// Global objects and state tracking
CTrade trade;                           // Trade execution object
TradeSignal current_signal;             // Current signal being processed
ExecutionResult execution_result;       // Result of execution

// Tracking variables
datetime last_signal_check_time = 0;    // Timestamp of last signal poll
datetime last_execution_time = 0;       // Timestamp of last execution
string mt5_files_path = "";             // MT5 Files folder path
long last_executed_signal_id = 0;       // Event ID of last executed signal

// Logging file handle
int log_file_handle = INVALID_HANDLE;

//+------------------------------------------------------------------+
//| OnInit() - Expert Advisor Initialization (Lines 31-60)          |
//+------------------------------------------------------------------+
int OnInit()
{
    // Check if EA is enabled
    if(!EA_ENABLED)
    {
        Alert("GeoSignal EA is disabled via EA_ENABLED parameter");
        return INIT_PARAMETERS_INCORRECT;
    }

    // Get MT5 Files path
    string terminal_data_path = TerminalInfoString(TERMINAL_DATA_PATH);
    mt5_files_path = terminal_data_path + "\\MQL5\\Files";

    // Initialize CTrade object with magic number and slippage
    trade.SetExpertMagicNumber(123456);        // Magic number to identify EA orders
    trade.SetDeviationInPoints(10);             // 10-point slippage tolerance

    // Set up logging
    string log_file_name = "ea_execution.log";
    log_file_handle = FileOpen(log_file_name, FILE_WRITE | FILE_TXT);

    if(log_file_handle != INVALID_HANDLE)
    {
        LogMessage("==================================================");
        LogMessage("GeoSignal EA Started");
        LogMessage("EA Version: 1.00");
        LogMessage("Symbol: " + Symbol());
        LogMessage("Timeframe: " + EnumToString(Period()));
        LogMessage("Account: " + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)));
        LogMessage("==================================================");
    }
    else
    {
        Alert("Failed to open log file: " + log_file_name);
    }

    // Initialize signal and result structures
    InitSignal(current_signal);
    InitExecutionResult(execution_result);

    LogMessage("GeoSignal EA initialized successfully");
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| OnDeinit() - Expert Advisor Cleanup (Lines 61-65)               |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    LogMessage("GeoSignal EA stopped. Deinit reason: " + IntegerToString(reason));

    if(log_file_handle != INVALID_HANDLE)
    {
        FileClose(log_file_handle);
    }
}

//+------------------------------------------------------------------+
//| OnTick() - Main Expert Advisor Loop (Lines 66-100)              |
//+------------------------------------------------------------------+
void OnTick()
{
    // Check if it's time to poll for new signals
    datetime current_time = TimeCurrent();
    if((current_time - last_signal_check_time) < POLL_INTERVAL_SECONDS)
    {
        return;  // Not enough time has passed, skip this tick
    }

    last_signal_check_time = current_time;

    // Read signal from JSON file
    TradeSignal signal = ReadSignalFromJson();

    // Return early if action is HOLD or symbol is empty
    if(signal.action == "HOLD" || signal.symbol == "")
    {
        return;
    }

    // Check duplicate execution protection
    long signal_id = StringToInteger(signal.event_id);
    if(signal_id == last_executed_signal_id)
    {
        if(DEBUG_MODE)
            LogMessage("Duplicate signal detected, skipping. Signal ID: " + signal.event_id);
        return;
    }

    // Execute signal (validation and duplicate protection handled inside ExecuteSignal)
    // No timeout condition: rely on Python bridge to not send duplicate events
    // and event_id tracking to prevent re-execution of same signal
    ExecuteSignal(signal);
}

//+------------------------------------------------------------------+
//| ReadSignalFromJson() - Read signal from JSON file (Lines 101-150)|
//+------------------------------------------------------------------+
TradeSignal ReadSignalFromJson()
{
    TradeSignal signal;
    InitSignal(signal);

    // Construct full file path
    string file_path = mt5_files_path + "\\" + SIGNAL_FILE_PATH;

    // Open file for reading
    int file_handle = FileOpen(SIGNAL_FILE_PATH, FILE_READ | FILE_TXT);

    if(file_handle == INVALID_HANDLE)
    {
        LogMessage("Warning: Could not open signal.json file");
        return signal;
    }

    // Read entire file content
    string file_content = "";
    while(!FileIsEnding(file_handle))
    {
        file_content += FileReadString(file_handle);
    }

    FileClose(file_handle);

    // Parse JSON and populate signal
    signal = ParseSignalJson(file_content);

    if(DEBUG_MODE && signal.symbol != "")
    {
        LogMessage("Signal read: " + signal.action + " " + signal.symbol +
                   " at confidence " + DoubleToString(signal.confidence, 2));
    }

    return signal;
}

//+------------------------------------------------------------------+
//| ParseSignalJson() - Parse JSON string (Lines 151-220)           |
//+------------------------------------------------------------------+
TradeSignal ParseSignalJson(const string json_content)
{
    TradeSignal signal;
    InitSignal(signal);

    // Parse "action" field
    int pos = StringFind(json_content, "\"action\"");
    if(pos >= 0)
    {
        int start = StringFind(json_content, "\"", pos + 8) + 1;
        int end = StringFind(json_content, "\"", start);
        signal.action = StringSubstr(json_content, start, end - start);
    }

    // Parse "symbol" field
    pos = StringFind(json_content, "\"symbol\"");
    if(pos >= 0)
    {
        int start = StringFind(json_content, "\"", pos + 8) + 1;
        int end = StringFind(json_content, "\"", start);
        signal.symbol = StringSubstr(json_content, start, end - start);
    }

    // Parse "confidence" field
    pos = StringFind(json_content, "\"confidence\"");
    if(pos >= 0)
    {
        int start = StringFind(json_content, ":", pos) + 1;
        int end = StringFind(json_content, ",", start);
        if(end < 0) end = StringFind(json_content, "}", start);
        string conf_str = StringSubstr(json_content, start, end - start);
        signal.confidence = StringToDouble(conf_str);
    }

    // Parse "volume" field
    pos = StringFind(json_content, "\"volume\"");
    if(pos >= 0)
    {
        int start = StringFind(json_content, ":", pos) + 1;
        int end = StringFind(json_content, ",", start);
        if(end < 0) end = StringFind(json_content, "}", start);
        string vol_str = StringSubstr(json_content, start, end - start);
        signal.volume = StringToDouble(vol_str);
    }

    // Parse "event_id" field
    pos = StringFind(json_content, "\"event_id\"");
    if(pos >= 0)
    {
        int start = StringFind(json_content, "\"", pos + 10) + 1;
        int end = StringFind(json_content, "\"", start);
        signal.event_id = StringSubstr(json_content, start, end - start);
    }

    // Parse "stop_loss" field
    pos = StringFind(json_content, "\"stop_loss\"");
    if(pos >= 0)
    {
        int start = StringFind(json_content, ":", pos) + 1;
        int end = StringFind(json_content, ",", start);
        if(end < 0) end = StringFind(json_content, "}", start);
        string sl_str = StringSubstr(json_content, start, end - start);
        signal.stop_loss = StringToDouble(sl_str);
    }

    // Parse "take_profit" field
    pos = StringFind(json_content, "\"take_profit\"");
    if(pos >= 0)
    {
        int start = StringFind(json_content, ":", pos) + 1;
        int end = StringFind(json_content, ",", start);
        if(end < 0) end = StringFind(json_content, "}", start);
        string tp_str = StringSubstr(json_content, start, end - start);
        signal.take_profit = StringToDouble(tp_str);
    }

    // Parse "rationale" field
    pos = StringFind(json_content, "\"rationale\"");
    if(pos >= 0)
    {
        int start = StringFind(json_content, "\"", pos + 11) + 1;
        int end = StringFind(json_content, "\"", start);
        signal.rationale = StringSubstr(json_content, start, end - start);
    }

    // Parse "timestamp" field
    pos = StringFind(json_content, "\"timestamp\"");
    if(pos >= 0)
    {
        int start = StringFind(json_content, "\"", pos + 11) + 1;
        int end = StringFind(json_content, "\"", start);
        signal.timestamp = StringSubstr(json_content, start, end - start);
    }

    return signal;
}

//+------------------------------------------------------------------+
//| ValidateSignal() - Validate signal against risk rules (Lines 221-270)
//+------------------------------------------------------------------+
bool ValidateSignal(const TradeSignal &signal)
{
    // Rule 1: Check confidence threshold
    if(signal.confidence < 0.5)
    {
        LogMessage("Signal validation failed: Confidence " +
                   DoubleToString(signal.confidence, 2) + " below 0.5 threshold");
        return false;
    }

    // Rule 2: Check max concurrent positions
    int open_positions = CountOpenPositions();
    if(open_positions >= MAX_CONCURRENT_POSITIONS)
    {
        LogMessage("Signal validation failed: Max positions " +
                   IntegerToString(MAX_CONCURRENT_POSITIONS) + " already open. Current: " +
                   IntegerToString(open_positions));
        return false;
    }

    // Rule 3: Check no duplicate symbols
    if(PositionSelect(signal.symbol))
    {
        LogMessage("Signal validation failed: Position already open for " + signal.symbol);
        return false;
    }

    // Rule 4: Check daily loss limit
    double account_balance = AccountInfoDouble(ACCOUNT_BALANCE);
    double account_equity = AccountInfoDouble(ACCOUNT_EQUITY);
    double daily_profit = account_equity - account_balance;

    double max_loss_amount = (MAX_DAILY_LOSS_PERCENT / 100.0) * account_balance;
    if(daily_profit < -max_loss_amount)
    {
        LogMessage("Signal validation failed: Daily loss " +
                   DoubleToString(-daily_profit, 2) + " exceeds limit " +
                   DoubleToString(max_loss_amount, 2));
        return false;
    }

    // Rule 5: Check drawdown limit
    double equity_drawdown = (account_balance - account_equity) / account_balance * 100.0;
    if(equity_drawdown > MAX_DRAWDOWN_PERCENT)
    {
        LogMessage("Signal validation failed: Drawdown " +
                   DoubleToString(equity_drawdown, 2) + "% exceeds limit " +
                   DoubleToString(MAX_DRAWDOWN_PERCENT, 2) + "%");
        return false;
    }

    return true;
}

//+------------------------------------------------------------------+
//| ExecuteSignal() - Execute trade signal (Lines 271-350)          |
//+------------------------------------------------------------------+
bool ExecuteSignal(TradeSignal &signal)
{
    // Validate signal first
    if(!ValidateSignal(signal))
    {
        LogMessage("Signal execution aborted: Validation failed for " + signal.symbol);
        WriteHeartbeat(signal, false, "validation_failed");
        return false;
    }

    // Get current price for the symbol
    double current_price = SymbolInfoDouble(signal.symbol, SYMBOL_BID);
    if(current_price <= 0)
    {
        LogMessage("Error: Could not get price for symbol " + signal.symbol);
        WriteHeartbeat(signal, false, "price_error");
        return false;
    }

    // Get instrument configuration (SL/TP in pips)
    int sl_pips, tp_pips;
    GetInstrumentConfig(signal.symbol, sl_pips, tp_pips);

    // Get symbol point value
    double point_value = SymbolInfoDouble(signal.symbol, SYMBOL_POINT);
    int digits = (int)SymbolInfoInteger(signal.symbol, SYMBOL_DIGITS);

    // Calculate position size based on confidence and risk
    double position_size = CalculatePositionSize(AccountInfoDouble(ACCOUNT_BALANCE),
                                                 sl_pips,
                                                 point_value,
                                                 RISK_PER_TRADE_PERCENT);

    if(position_size <= 0)
    {
        LogMessage("Error: Calculated position size is invalid: " + DoubleToString(position_size, 2));
        WriteHeartbeat(signal, false, "position_size_error");
        return false;
    }

    // Calculate Stop Loss and Take Profit prices
    double sl_price, tp_price;

    if(signal.action == "BUY")
    {
        sl_price = current_price - (sl_pips * point_value);
        tp_price = current_price + (tp_pips * point_value);

        // Normalize prices to symbol precision
        sl_price = NormalizeDouble(sl_price, digits);
        tp_price = NormalizeDouble(tp_price, digits);
    }
    else if(signal.action == "SELL")
    {
        sl_price = current_price + (sl_pips * point_value);
        tp_price = current_price - (tp_pips * point_value);

        // Normalize prices to symbol precision
        sl_price = NormalizeDouble(sl_price, digits);
        tp_price = NormalizeDouble(tp_price, digits);
    }
    else
    {
        LogMessage("Error: Invalid action in signal: " + signal.action);
        WriteHeartbeat(signal, false, "invalid_action");
        return false;
    }

    // Place market order
    string order_comment = "GeoSignal:" + signal.event_id;
    bool success = false;

    if(signal.action == "BUY")
    {
        success = trade.Buy(position_size, signal.symbol, current_price, sl_price, tp_price, order_comment);
    }
    else
    {
        success = trade.Sell(position_size, signal.symbol, current_price, sl_price, tp_price, order_comment);
    }

    if(success)
    {
        ulong ticket = trade.ResultOrder();
        last_execution_time = TimeCurrent();
        last_executed_signal_id = StringToInteger(signal.event_id);

        LogMessage("Signal executed successfully: " + signal.action + " " +
                   DoubleToString(position_size, 2) + " " + signal.symbol +
                   " | Ticket: " + IntegerToString(ticket) +
                   " | SL: " + DoubleToString(sl_price, digits) +
                   " | TP: " + DoubleToString(tp_price, digits) +
                   " | Confidence: " + DoubleToString(signal.confidence, 2));

        WriteHeartbeat(signal, true, "success");
        return true;
    }
    else
    {
        string error_msg = trade.ResultRetcodeDescription();
        LogMessage("Signal execution failed: " + signal.symbol +
                   " | Error: " + error_msg);
        WriteHeartbeat(signal, false, error_msg);
        return false;
    }
}

//+------------------------------------------------------------------+
//| CountOpenPositions() - Count EA positions (Lines 351-365)       |
//+------------------------------------------------------------------+
int CountOpenPositions()
{
    int count = 0;
    int total_positions = PositionsTotal();

    for(int i = 0; i < total_positions; i++)
    {
        ulong ticket = PositionGetTicket(i);
        if(ticket > 0)
        {
            if(PositionGetInteger(POSITION_MAGIC) == 123456)
            {
                count++;
            }
        }
    }

    return count;
}

//+------------------------------------------------------------------+
//| LogMessage() - Write to log file (Lines 366-380)                |
//+------------------------------------------------------------------+
void LogMessage(const string message)
{
    if(log_file_handle == INVALID_HANDLE)
        return;

    // Format timestamp
    datetime now = TimeCurrent();
    string timestamp = TimeToString(now, TIME_DATE | TIME_MINUTES | TIME_SECONDS);

    // Write to file
    string log_line = "[" + timestamp + "] " + message;
    FileWrite(log_file_handle, log_line);

    // Also print to debug output
    if(DEBUG_MODE)
    {
        Print(log_line);
    }
}

//+------------------------------------------------------------------+
//| WriteHeartbeat() - Write execution result to JSON (Helper)      |
//+------------------------------------------------------------------+
void WriteHeartbeat(const TradeSignal &signal, bool executed, const string status)
{
    // Construct heartbeat JSON
    string heartbeat_json = "{";
    heartbeat_json += "\"timestamp\": \"" + TimeToString(TimeCurrent(), TIME_DATE | TIME_MINUTES | TIME_SECONDS) + "\", ";
    heartbeat_json += "\"signal_id\": \"" + signal.event_id + "\", ";
    heartbeat_json += "\"executed\": " + (executed ? "true" : "false") + ", ";
    heartbeat_json += "\"status\": \"" + status + "\", ";
    heartbeat_json += "\"ticket\": " + (executed ? IntegerToString(trade.ResultOrder()) : "0") + ", ";
    heartbeat_json += "\"error_reason\": \"" + (executed ? "" : trade.ResultRetcodeDescription()) + "\"";
    heartbeat_json += "}";

    // Write to heartbeat.json
    int hb_handle = FileOpen("heartbeat.json", FILE_WRITE | FILE_TXT);
    if(hb_handle != INVALID_HANDLE)
    {
        FileWrite(hb_handle, heartbeat_json);
        FileClose(hb_handle);
    }
}

//+------------------------------------------------------------------+
//| END OF GEOSIGNAL EA                                              |
//+------------------------------------------------------------------+
