import streamlit as st
import pandas as pd
import time
import math
import random
from datetime import datetime
from threading import Thread
from dataclasses import dataclass, field
from typing import List

# --- DATA MODELS & STATE MANAGEMENT ---
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

# Initialize Session State for Streamlit Persistence
if 'state' not in st.session_state:
    st.session_state.state = MissionState()

# --- BACKGROUND MISSION LOGIC (SENSORS & MANAGER) ---
def run_uav_logic():
    """Simulates the backend flight and target acquisition logic."""
    angle = 0
    while True:
        # Check if user 'cut' the network link via UI
        if not st.session_state.get('network_active', True):
            time.sleep(1)
            continue
            
        # 1. Sensor: Calculate Circular Flight Path
        x = int(500 + 200 * math.cos(angle))
        y = int(500 + 200 * math.sin(angle))
        
        # 2. AI: Simulated Target Acquisition (92% threshold)
        detection_chance = random.random()
        target_found = detection_chance > 0.92
        
        # 3. Manager: Update Status and Log Events (Traceability)
        new_status = "TRACKING" if target_found else "SEARCHING"
        
        if target_found and not st.session_state.state.target_acquired:
            # New target event
            log = MissionLogEntry(
                timestamp=datetime.now().strftime("%H:%M:%S"),
                event="TARGET_ACQUIRED",
                coordinates=f"[{x}, {y}]"
            )
            st.session_state.state.event_logs.insert(0, log)
            if len(st.session_state.state.event_logs) > 10: st.session_state.state.event_logs.pop()

        st.session_state.state.status = new_status
        st.session_state.state.target_acquired = target_found
        st.session_state.state.coords = [x, y]
        
        # Update Visual History
        st.session_state.state.history.append({"x": x, "y": y})
        if len(st.session_state.state.history) > 40: st.session_state.state.history.pop(0)
            
        angle += 0.12
        time.sleep(0.4)

# Start logic thread once
if 'logic_thread' not in st.session_state:
    thread = Thread(target=run_uav_logic, daemon=True)
    thread.start()
    st.session_state.logic_thread = True

# --- HUMAN-SYSTEM INTERFACE (UI) ---
st.set_page_config(page_title="UAV Digital Twin", layout="wide")

st.title("🛰️ UAV Mission Digital Twin")
st.markdown("**Architectural Model:** MOSA/JADC2 Simulation")

# Sidebar - Human Intervention
st.sidebar.header("Command & Control")
st.session_state.network_active = st.sidebar.toggle("UAV Data Link", value=True)
st.sidebar.divider()
st.sidebar.info("This dashboard simulates a Modular Open Systems Approach where the 'Brain' (Logic) is decoupled from the 'Interface' (Streamlit).")

# Telemetry Metrics
m1, m2, m3 = st.columns(3)
if st.session_state.network_active:
    m1.metric("Mode", st.session_state.state.status)
    m2.metric("Link Latency", f"{random.randint(15, 55)}ms")
    m3.metric("Vector", f"{st.session_state.state.coords}")
else:
    m1.error("LINK LOST")
    m2.metric("Link Latency", "--")
    m3.warning("GPS STALE")

# Tactical Visualization & Logs
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("Tactical Plot")
    if st.session_state.network_active:
        df = pd.DataFrame(st.session_state.state.history)
        if not df.empty:
            st.scatter_chart(df, x="x", y="y", size=30)
    else:
        st.info("Awaiting telemetry sync...")

with col_right:
    st.subheader("Mission Traceability Log")
    if st.session_state.state.event_logs:
        log_df = pd.DataFrame([vars(l) for l in st.session_state.state.event_logs])
        st.table(log_df)
    else:
        st.write("No combat events recorded.")

# Forced UI Refresh
time.sleep(0.5)

st.rerun()