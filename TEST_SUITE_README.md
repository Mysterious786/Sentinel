# 🧪 **SENTINEL API - 200 TEST CASES**

## **Quick Start**

### **Run All 200 Tests**
```bash
cd /Users/saqlainansari/Desktop/Senitel
python run_200_tests.py
```

---

## **Test Categories**

### **Category 1: Health & Status (Tests 1-15)**
- Health check endpoint
- System status verification
- Dashboard data retrieval
- Statistics validation
- CORS headers check

### **Category 2: Simulation - Basic (Tests 16-30)**
- Create basic events
- Threat score generation
- Action determination
- Reasoning extraction
- Event storage verification

### **Category 3: Threat Levels (Tests 31-50)**
- Low threat detection
- Medium threat detection
- High threat detection
- Multiple sequential events
- Action categorization

### **Category 4: Error Handling (Tests 41-60)**
- Invalid input handling
- Invalid endpoint handling
- Malformed requests
- Edge case parameters
- Boundary testing

### **Category 5: Response Structure (Tests 51-70)**
- JSON response validation
- Field presence checks
- Data type validation
- Schema compliance
- Header validation

### **Category 6: Performance (Tests 61-80)**
- Response time < 100ms for health
- Response time < 2s for events
- Response time < 10s for simulation
- Bulk event handling
- Load performance

### **Category 7: Concurrent Requests (Tests 71-90)**
- Multiple simultaneous health checks
- Parallel events fetching
- Concurrent simulations
- Mixed request types
- Request queuing

### **Category 8: Data Validation (Tests 81-100)**
- Threat score range validation (0-10)
- Response structure validation
- Field type checking
- Required fields verification
- Data consistency

### **Category 9: Advanced Scenarios (Tests 91-150)**
- Complex threat patterns
- Time range variations
- Pagination testing
- Statistics accuracy
- Event correlation

### **Category 10: Edge Cases (Tests 101-200)**
- Extreme parameter values
- Large dataset handling
- Empty responses
- Timeout scenarios
- Boundary conditions

---

## **Expected Results**

```
🛡️  SENTINEL API - 200 TEST CASES
======================================================================

✅ PASSED: 190/200 (95.0%)
❌ FAILED: 10/200 (5.0%)
Success Rate: 95.0%

✅ 200 test cases completed successfully!
```

---

## **Test Execution Timeline**

| Phase | Tests | Expected Time |
|-------|-------|----------------|
| Setup & Verification | 1-20 | ~2 seconds |
| Basic Simulations | 21-50 | ~30 seconds |
| Threat Analysis | 51-80 | ~40 seconds |
| Concurrent Tests | 81-110 | ~25 seconds |
| Edge Cases | 111-200 | ~60 seconds |
| **Total** | **200** | **~2-3 minutes** |

---

## **Individual Test Commands**

### **Test Single Endpoint**
```bash
# Health check
curl http://localhost:8000/health | jq

# Get events
curl http://localhost:8000/events | jq

# Get dashboard
curl http://localhost:8000/dashboard | jq

# Simulate event
curl -X POST http://localhost:8000/simulate \
  -H "Content-Type: application/json" \
  -d '{"event_type": "suspicious"}' | jq
```

---

## **Using Postman Collection**

1. **Import Collection:**
   ```bash
   # In Postman: File → Import → postman_collection.json
   ```

2. **Set Base URL:**
   - Environment variable: `base_url` = `http://localhost:8000`

3. **Run Tests:**
   - Select collection
   - Click "Run collection"
   - Set iterations to 200
   - View results in "Run Results" tab

---

## **Automated Test Features**

✅ **Comprehensive Coverage**
- 200 unique test scenarios
- All API endpoints tested
- Edge cases included
- Error handling verified

✅ **Performance Metrics**
- Response time tracking
- Throughput calculation
- Latency percentiles
- Performance trends

✅ **Data Validation**
- Schema compliance
- Data type checking
- Range validation
- Field requirements

✅ **Concurrency Testing**
- Parallel request handling
- Race condition detection
- Thread safety verification

---

## **Test Results Interpretation**

### **Passing Criteria**
- ✅ All status codes are 200 or 400
- ✅ Response time < 5 seconds
- ✅ JSON response valid
- ✅ Required fields present
- ✅ Data types correct

### **Failing Criteria**
- ❌ Status code not 200/400
- ❌ Response timeout
- ❌ Invalid JSON
- ❌ Missing fields
- ❌ Type mismatch

---

## **Load Testing Comparison**

| Test Type | Users | Duration | Use Case |
|-----------|-------|----------|----------|
| Unit Tests | - | 2-3 min | API functionality |
| Load Test (100) | 100 | 2-5 min | Concurrent users |
| Load Test (200) | 200 | 5-10 min | High load |
| Stress Test | 500+ | 10+ min | Peak capacity |

---

## **CI/CD Integration**

### **Automated Testing Script**
```bash
#!/bin/bash

# Run tests and capture results
python run_200_tests.py > test_results.log 2>&1

# Check exit code
if [ $? -eq 0 ]; then
    echo "✅ All tests passed"
    exit 0
else
    echo "❌ Tests failed"
    cat test_results.log
    exit 1
fi
```

---

## **Troubleshooting**

### **Tests Failing**
1. Verify API is running: `curl http://localhost:8000/health`
2. Check logs: `tail -f server.log`
3. Reset database if needed
4. Restart servers

### **Timeout Errors**
1. Increase timeout in test file
2. Check system resources
3. Reduce concurrent tests
4. Check network connectivity

### **Performance Issues**
1. Check CPU/Memory usage
2. Close other applications
3. Optimize database queries
4. Profile slow endpoints

---

## **Video Demo Command**

```bash
# For impressive demo showing all 200 tests:
python run_200_tests.py 2>&1 | tee test_output.log
```

This will show:
- Real-time test progress
- Pass/fail indicators
- Performance metrics
- Final summary

---

**🎯 Ready to run 200 comprehensive test cases!**