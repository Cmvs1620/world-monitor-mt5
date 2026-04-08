# Integration Testing Suite - File Index

Complete end-to-end integration testing materials for Python Signal Engine → MT5 Expert Advisor pipeline.

**Total Files:** 12  
**Total Lines:** 4,700+  
**Test Coverage:** 6-part comprehensive flow with 15-point success criteria

---

## Quick Navigation

### Start Here
1. **README.md** - Overview and quick links
2. **QUICK_START.txt** - 5 commands to run full test (15 minutes)

### Setup & Planning
3. **INTEGRATION_SETUP.md** - Environment validation, prerequisites, configuration
4. **DATA_FLOW.md** - ASCII diagram showing complete signal pipeline with timestamps

### Execution & Testing
5. **E2E_TEST_PROCEDURE.md** - 6-part step-by-step test procedure (with detailed instructions)
6. **SUCCESS_CRITERIA.md** - 15 checkboxes for go/no-go decision

### Debugging & Reference
7. **TROUBLESHOOTING.md** - 40+ issues, root causes, fixes (comprehensive diagnostic guide)
8. **SIGNAL_PIPELINE_COMPARISON.md** - Risk rules consistency, data format validation

### Utilities & Automation
9. **sync_signal_to_mt5.py** - Auto-copy signal.json to MT5 Files folder with logging
10. **verify_trade_execution.py** - Validate signal→heartbeat mapping, generate report
11. **run_integration_test.py** - Main orchestrator for automated E2E test runs

### Results & Reporting
12. **TEST_RESULTS_TEMPLATE.md** - Template for recording test results

---

## File Descriptions

### Documentation (8 files)

| File | Purpose | Read Time | Key Sections |
|------|---------|-----------|--------------|
| README.md | Overview, quick links, file guide | 5 min | File structure, success criteria, troubleshooting overview |
| QUICK_START.txt | 5-step test execution guide | 3 min | 5 commands in order, expected outputs, success criteria |
| INTEGRATION_SETUP.md | Prerequisites and environment validation | 15 min | Checklist, validation steps, configuration files, troubleshooting setup |
| E2E_TEST_PROCEDURE.md | Complete 6-part test procedure | 20 min | Part 1-6 detailed steps, verification checklists, expected outputs |
| DATA_FLOW.md | Signal pipeline architecture diagram | 10 min | ASCII flow diagram, timeline, file paths, latency breakdown |
| SUCCESS_CRITERIA.md | 15-point go/no-go checklist | 10 min | 15 criteria with pass/fail conditions and test methods |
| TROUBLESHOOTING.md | Diagnostic guide for 40+ issues | 20 min | Issue matrix, root cause analysis, fixes, workflows |
| SIGNAL_PIPELINE_COMPARISON.md | Consistency validation matrix | 15 min | Risk rules, data formats, logging, tracing, timestamps |
| TEST_RESULTS_TEMPLATE.md | Results recording template | 5 min | Summary table, detailed results fields, sign-off |

### Python Utilities (3 files)

| File | Purpose | Usage | Key Features |
|------|---------|-------|--------------|
| sync_signal_to_mt5.py | Auto-sync signal.json to MT5 | `python sync_signal_to_mt5.py --mt5-path "..."` | Monitors for changes, copies with latency tracking, logs all operations |
| verify_trade_execution.py | Verify signal→heartbeat mapping | `python verify_trade_execution.py --csv logs/signals.csv` | Generates execution report with latency stats and validation |
| run_integration_test.py | Orchestrate full E2E test | `python run_integration_test.py --duration 600 --mt5-path "..."` | Background monitoring, progress reporting, summary statistics |

---

## Typical Workflow

### Scenario 1: First-Time Test (Complete)
1. Read **README.md** - Understand scope
2. Read **DATA_FLOW.md** - Understand architecture
3. Follow **INTEGRATION_SETUP.md** - Validate environment
4. Follow **E2E_TEST_PROCEDURE.md** - Run test
5. Check **SUCCESS_CRITERIA.md** - Verify pass
6. Use **TEST_RESULTS_TEMPLATE.md** - Record results

**Time:** ~60 minutes (including setup and test execution)

### Scenario 2: Quick Test (15 minutes)
1. Read **QUICK_START.txt** - Get 5 commands
2. Execute commands in order
3. Monitor outputs for expected patterns
4. Check **SUCCESS_CRITERIA.md** for pass/fail

**Time:** 15-20 minutes (no setup, assumes environment ready)

### Scenario 3: Debugging Failed Test
1. Review **TROUBLESHOOTING.md** - Find your issue
2. Follow diagnostic steps
3. Review **SIGNAL_PIPELINE_COMPARISON.md** - Check consistency
4. Re-run test with fixes
5. Check **DATA_FLOW.md** - Understand expected behavior

**Time:** 30-45 minutes (depends on issue complexity)

### Scenario 4: Automating Tests
1. Use **run_integration_test.py** - Main orchestrator
2. Configure with `--duration`, `--mt5-path`, `--verbose` flags
3. Let it run with background monitoring
4. Review generated report

**Time:** 30 minutes (fully automated execution)

---

## Key Metrics & Targets

| Metric | Target | Pass | Fail |
|--------|--------|------|------|
| Success Criteria | ≥14/15 | ✓ | ✗ |
| Execution Ratio | ≥30% | Execute signal | Risk gate blocks |
| Latency (Avg) | <5 min | Signal → Trade | Timeout |
| Signal Updates | Every 10s | Continuous | Stalled |
| File Sync | <60s | On time | Late/missing |
| Risk Gates | 100% valid | All checked | Skipped |
| Tickets | All > 0 | Valid | Zero/negative |
| Heartbeat Match | 100% | signal_id = event_id | Mismatch |

---

## Prerequisites Summary

Before running any test, ensure:
- Python 3.8+ with anthropic, requests modules
- ANTHROPIC_API_KEY set and valid
- WorldMonitor API accessible (curl test)
- config/settings.json configured with MT5 Files path
- MT5 with GeoSignal EA deployed and running
- SMB share mounted or manual copy method ready
- Account balance > $1000
- signals/ and logs/ directories exist

See **INTEGRATION_SETUP.md** Part 1 for complete validation checklist.

---

## File Sizes

```
README.md                         ~2.5 KB
QUICK_START.txt                   ~3.0 KB
INTEGRATION_SETUP.md              ~8.0 KB
E2E_TEST_PROCEDURE.md             ~10.0 KB
DATA_FLOW.md                       ~8.0 KB
SUCCESS_CRITERIA.md                ~9.0 KB
TROUBLESHOOTING.md                ~15.0 KB
SIGNAL_PIPELINE_COMPARISON.md      ~10.0 KB
TEST_RESULTS_TEMPLATE.md           ~5.0 KB
sync_signal_to_mt5.py              ~6.0 KB
verify_trade_execution.py          ~5.0 KB
run_integration_test.py             ~7.0 KB
────────────────────────────────────────
Total                             ~88.0 KB
```

---

## Git Commit Info

```
Commit: Phase 3 Task 6: Test Python-EA Integration
Message: test(integration): add end-to-end python-ea integration test suite with monitoring utilities

Files Added:
  - 12 files, 4,698 lines
  - Comprehensive E2E test documentation
  - 3 Python utility scripts
  - 8 detailed markdown guides
  - Full diagnostics and troubleshooting

Coverage:
  - Signal generation to trade execution
  - File synchronization and network latency
  - Risk gate validation
  - Heartbeat response verification
  - End-to-end latency measurement
  - Execution report generation
```

---

## Next Steps

After successful integration test:
1. Review **SUCCESS_CRITERIA.md** - Confirm all 15 items pass
2. Complete **TEST_RESULTS_TEMPLATE.md** - Record official results
3. Archive logs to `results/test_YYYY-MM-DD/` directory
4. For production:
   - Change POLL_INTERVAL_SECONDS to 300 (from 10)
   - Increase trading parameters as appropriate
   - Run final verification test
   - Deploy to live trading

---

## Support & Diagnostics

**If test fails:**
1. Check **TROUBLESHOOTING.md** for your symptom
2. Follow diagnostic steps (curl tests, file checks, log inspection)
3. Review **DATA_FLOW.md** to understand expected behavior
4. Validate **SIGNAL_PIPELINE_COMPARISON.md** for consistency issues
5. Check **E2E_TEST_PROCEDURE.md** Part 8 for general cleanup

**If uncertain:**
1. Read the relevant section in **E2E_TEST_PROCEDURE.md**
2. Check **INTEGRATION_SETUP.md** Part 6 pre-test checklist
3. Review **QUICK_START.txt** for quick commands
4. Consult **DATA_FLOW.md** for understanding pipeline

---

## Statistics

- **Total Files:** 12
- **Total Lines:** 4,698
- **Documentation:** 3,500+ lines
- **Code:** 1,200+ lines
- **Test Procedures:** 150+ steps across 6 parts
- **Success Criteria:** 15 checkboxes
- **Troubleshooting Issues:** 40+
- **Diagnostic Workflows:** 6
- **Sample Commands:** 30+
- **Success Criteria Explanation:** 8,000+ words

---

## Maintenance

These integration test materials should be updated when:
- Risk gate parameters change
- Signal format changes
- EA properties change
- File paths change
- New issues discovered during testing
- Performance targets change

Keep **TROUBLESHOOTING.md** current with new issues found in production testing.

---

**Last Updated:** 2026-04-07  
**Version:** 1.0 (Initial Release)  
**Status:** Ready for Production Testing
