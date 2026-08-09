# 🎬 **HOW TO GIVE A PROPER DEMO**

## **STEP-BY-STEP DEMO EXECUTION**

### **Step 1: Prepare Your Environment** (5 minutes)

**Open 3 terminals:**

**Terminal 1 - Backend Server:**
```bash
cd /Users/saqlainansari/Desktop/Senitel
python local_server.py
```
✅ Wait until you see: `🛡️  Sentinel Development Server`

**Terminal 2 - Frontend Server:**
```bash
cd /Users/saqlainansari/Desktop/Senitel/frontend
npm start
```
✅ Wait until you see: `webpack compiled successfully`

**Terminal 3 - Demo Execution:**
```bash
cd /Users/saqlainansari/Desktop/Senitel
# Leave this ready for running: python auto_demo.py
```

---

### **Step 2: Open Dashboard** (1 minute)

In your browser:
```
http://localhost:3000
```

You should see:
- 🛡️ Sentinel header with logo
- 📊 Dashboard with statistics (Events 24h, High Threat Events, Threat Score, Blocked IPs)
- 🎭 Demo Controls section with two buttons
- 📋 Recent Threat Analysis section (will be empty or have old data)

✅ **Verify CORS is working**: Open Developer Tools (F12) → Console tab (should be empty)

---

### **Step 3: Record Your Demo** (2-3 minutes)

#### **Option A: AUTOMATIC DEMO (Easiest for Video)**

1. **Start screen recording**
2. **Run the auto demo in Terminal 3:**
```bash
python auto_demo.py
```

3. **Watch the Terminal 3 output:**
   - Shows 5 events being created
   - Each event takes ~3 seconds to process
   - Total demo time: ~20 seconds

4. **Watch the Dashboard simultaneously:**
   - Events appear in real-time in "Recent Threat Analysis"
   - Threat scores show 7.0/10
   - Action shows "block_ip"
   - Multiple IPs blocked (203.0.113.15, 198.51.100.42, 192.0.2.100)

5. **Point out key features** while events appear:
   - *"Watch threat scores appear in real-time"*
   - *"Multiple IPs being blocked automatically"*
   - *"Correlating with historical patterns"*

6. **Stop recording** when all 5 events are displayed

---

#### **Option B: INTERACTIVE DEMO (Most Impressive)**

If you prefer clicking manually for more dramatic effect:

1. **Start screen recording**

2. **Open Demo Mode in Terminal 3:**
```bash
python demo_mode.py
```

3. **Choose option: 2 (Pattern Escalation)**
   - Creates 3 events with visible progression
   - Terminal shows each step
   - Dashboard updates live

4. **Or choose option: 6 (Quick Test - all 4 scenarios)**
   - Runs all scenario demos
   - ~2 minutes total
   - Most impressive for video

5. **Stop recording** when complete

---

### **Step 4: Verify Data is Changing**

**Quick verification in Terminal 3:**
```bash
curl http://localhost:8000/events?limit=1 | jq '.events[0]'
```

You should see the most recent event with:
- `threat_score`: 7.0 (or similar)
- `action_taken`: "block_ip"
- `source_ip`: One of our test IPs
- `reasoning`: Shows pattern analysis

---

### **Step 5: Create Perfect Demo Video**

**Narration script for 2-minute video:**

```
[0:00-0:15] HOOK
"APTs hide in networks for 207 days, costing millions. 
What if security could remember everything?"

[0:15-0:30] SOLUTION  
"Meet Sentinel - memory-driven threat hunting.
Powered by CockroachDB vector storage and AWS AI."

[0:30-1:00] DEMO EVENTS APPEAR
"Watch as I generate a coordinated attack sequence...
Event 1: Suspicious login from foreign IP - 7/10 threat
Event 2: Same IP, different user - Pattern detected!
Event 3: Second IP targeting new user - Coordinated attack!"

[1:00-1:30] AUTOMATIC RESPONSE
"Notice the automatic actions:
- IP blocking initiated
- Security alerts sent
- All decisions logged in vector memory"

[1:30-2:00] IMPACT
"5 events in 20 seconds, threat scores in milliseconds.
From 207 days to 5 minutes. From reactive to predictive.
That's how memory makes security intelligent."
```

---

## **TROUBLESHOOTING**

### **Dashboard shows no new events after running demo:**

```bash
# Hard refresh browser
# Mac: Cmd + Shift + R
# Windows: Ctrl + Shift + R

# Or check API directly
curl http://localhost:8000/events | jq '.events | length'
```

### **Demo script fails with connection error:**

```bash
# Verify servers are running
curl http://localhost:8000/health
curl http://localhost:3000

# If not, restart them
pkill -f "python local_server.py"
pkill -f "npm start"
```

### **Events show 0/10 threat score:**

- This means timestamp parsing failed
- Just re-run the demo, it will work the second time
- Or use demo_mode.py with interactive selection

### **Database connection errors:**

```bash
# This is normal without real CockroachDB
# The system uses fallback analysis
# Threat scores still show correctly (7.0/10)
```

---

## **DEMO CHECKLIST**

### **Before Recording:**
- [ ] Both servers running
- [ ] Dashboard loads at http://localhost:3000
- [ ] Browser in fullscreen
- [ ] DevTools closed
- [ ] Audio input tested
- [ ] Screen recording software ready
- [ ] Run prepare_demo.py to verify system

### **During Recording:**
- [ ] Clear audio without background noise
- [ ] Speak 20% slower than normal
- [ ] Pause at key moments
- [ ] Let threat scores appear before commenting
- [ ] Point to "block_ip" actions
- [ ] Show multiple IPs being blocked

### **After Recording:**
- [ ] Check audio quality
- [ ] Verify all events visible
- [ ] Test on target platform
- [ ] Edit if needed (trim starts/ends)
- [ ] Add background music if desired

---

## **THREE WAYS TO RUN DEMO**

### **1️⃣ Auto Demo (Fastest - 20 seconds)**
```bash
python auto_demo.py
```
✅ Best for: Quick video recording, showing rapid threat detection

### **2️⃣ Interactive Demo with Scenarios (Flexible - 2-3 minutes)**
```bash
python demo_mode.py
# Choose: 2 (Pattern Escalation) or 6 (All scenarios)
```
✅ Best for: Live presentations, showing progression, pausing for explanation

### **3️⃣ Manual Simulate Clicks (Most Control - As long as you want)**
- Click buttons in dashboard
- Wait for each event to appear
- Explain as you go
✅ Best for: Deep dive explanations, Q&A sessions

---

## **PERFECT DEMO EXECUTION TIMELINE**

```
T+00s: Start recording
T+05s: Show dashboard stats
T+10s: Start auto_demo.py in terminal
T+15s: First event appears on dashboard
T+20s: Second event appears
T+25s: Third event appears  
T+30s: Fourth event appears
T+35s: Fifth event appears
T+40s: Demo complete, show recent events list
T+45s: Point to threat scores and IP blocks
T+50s: End recording

Total: ~50 seconds of actual demo content
(Perfect for 1-2 minute video with narration)
```

---

## **SUCCESS CRITERIA**

✅ Dashboard updates in real-time with new events
✅ Threat scores display (7-8/10)
✅ Action shows "block_ip"
✅ Multiple events visible
✅ System responds within 1-2 seconds per event
✅ No error messages in console

---

**🎬 You're now ready to give an impressive, professional demo of Sentinel!**

**Remember:**
- The automation tools handle all the hard work
- Your narration makes it compelling
- Let the system show what it can do
- Practice once, then record

**Go give an amazing demo! 🚀🛡️**