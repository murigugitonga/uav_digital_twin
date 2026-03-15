import streamlit as st
import pandas as pd
import time
import math
import random
from datetime import datetime
from threading import Thread
from dataclasses import dataclass, field
from typing import List

# --- DATA MODELS ---
@dataclass
class MissionLogEntry:
    timestamp: str
    event: str
    coordinates: str

@dataclass
class MissionState:
    status: str = "IDLE"
    target_acquired: bool = False
    coords: List[int] = field(default_factory=lambda: [500, 500])
    history: List[dict] = field(default_factory=list)
    event_logs: List[MissionLogEntry] = field(default_factory=list)
    network_active: bool = True 

# --- 1. INITIALIZE STATE IMMEDIATELY ---
if 'state' not in st.session_state:
    st.session_state.state = MissionState()

# --- 2. THE THREAD-SAFE LOGIC ---
def run_uav_logic(state_ref):
    angle = 0
    while True:
        # Check the reference directly for thread safety
        if not state_ref.network_active:
            time.sleep(1)
            continue
            
        # Sensor Simulation
        x = int(500 + 200 * math.cos(angle))
        y = int(500 + 200 * math.sin(angle))
        
        # AI Detection Simulation
        target_found = random.random() > 0.94
        new_status = "TRACKING" if target_found else "SEARCHING"
        
        # Logic: Log unique target events
        if target_found and not state_ref.target_acquired:
            log = MissionLogEntry(
                timestamp=datetime.now().strftime("%H:%M:%S"),
                event="TARGET_ACQUIRED",
                coordinates=f"[{x}, {y}]"
            )
            state_ref.event_logs.insert(0, log)
            if len(state_ref.event_logs) > 10: state_ref.event_logs.pop()

        # Update State
        state_ref.status = new_status
        state_ref.target_acquired = target_found
        state_ref.coords = [x, y]
        state_ref.history.append({"x": x, "y": y})
        
        if len(state_ref.history) > 40: 
            state_ref.history.pop(0)
            
        angle += 0.12
        time.sleep(0.4)

# --- 3. START THREAD ---
if 'logic_thread' not in st.session_state:
    # Pass the actual state object to the thread so it bypasses st.session_state proxy
    thread = Thread(target=run_uav_logic, args=(st.session_state.state,), daemon=True)
    thread.start()
    st.session_state.logic_thread = True

# --- 4. HUMAN-SYSTEM INTERFACE (UI) ---
st.set_page_config(page_title="UAV Digital Twin", layout="wide")

st.title("UAV Mission Digital Twin")
st.markdown("**Architectural Model:** MOSA/JADC2 Simulation")

# Create a local reference for cleaner UI code
state = st.session_state.state

# Sidebar
st.sidebar.header("Command & Control")
state.network_active = st.sidebar.toggle("UAV Data Link", value=True)
st.sidebar.divider()
st.sidebar.info("Simulating a decoupled architecture where backend logic remains independent of the display layer.")

# Telemetry Metrics (Specify 3 columns)
m1, m2, m3 = st.columns(3)

if state.network_active:
    m1.metric("Mode", state.status)
    m2.metric("Link Latency", f"{random.randint(15, 55)}ms")
    m3.metric("Vector", f"{state.coords}")
else:
    m1.error("LINK LOST")
    m2.metric("Link Latency", "--")
    m3.warning("GPS STALE")

# Tactical Visualization & Logs (Specify 2 columns)
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Tactical Plot")
    if state.network_active and len(state.history) > 0:
        df = pd.DataFrame(state.history)
        st.scatter_chart(df, x="x", y="y", size=30)
    else:
        st.info("Awaiting telemetry synchronization...")

with col_right:
    st.subheader("Mission Traceability Log")
    if len(state.event_logs) > 0:
        log_df = pd.DataFrame([vars(l) for l in state.event_logs])
        st.table(log_df)
    else:
        st.write("No mission events recorded in current thread.")

# Auto-Refresh
time.sleep(0.5)

st.rerun()