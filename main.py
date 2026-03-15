import streamlit as st
import pandas as pd
import time
import math
import random
from datetime import datetime
from threading import Thread
from dataclasses import dataclass, field
from typing import List

@dataclass
class MissionLogEntry:
    timestamp : str
    event : str
    coordinates : str

@dataclass
class MissionState:
    status: str = "IDLE"
    target_acquired: bool = False
    coords : List[int] = field(default_factory=lambda:[500, 500])
    history: List[dict] = field(default_factory=list)

# Persistent State

if 'state' not in st.session_state:
    st.session_state.state = MissionState()

# -- Mission Manager
def run_mission_logic():
    "OMS Sensor & MOSA Manager"
    angle = 0
    while True:
        # Network Failure
        if not st.session_state.get('network_active', True):
            time.sleep(1)
            continue

        # Sensor Logic: Calculate Circular Path
        x = int(500 + 200 * math.cos(angle))
        y = int(500 + 200 * math.sin(angle))

        # AI Logic: Target Acquisition Simulation
        target_found = random.random() > 0.92

        # Manager Logic: State Transition
        new_status = "TRACKING" if target_found else "Searching..."

        # Update Global State
        st.session_state.state.status = new_status
        st.session_state.state.target_acquired = target_found
        st.session_state.state.coords =[x,y]

        # Retain Path history
        st.session_state.state.history.append({"x": x, "y":y})
        if len(st.session_state.state.history) > 30:
            st.session_state.state.history.pop(0)
        
        angle += 0.15
        time.sleep(0.5)


if 'thread_started' not in st.session_state:
    thread = Thread(target=run_mission_logic, daemon=True)
    thread.start()
    st.session_state.thread_started = True

# --- HUMAN-SYSTEM INTERFACE (STREAMLIT UI) ---
st.set_page_config(page_title="UAV Digital Twin", layout="wide")

st.title("🛰️ UAV Mission Digital Twin")
st.caption("A MOSA-compliant architectural simulation for JADC2 environments.")

# Sidebar - Risk Management & HSI
st.sidebar.header("System Controls")
st.session_state.network_active = st.sidebar.toggle("Maintain Data Link", value=True)

# Metrics Row
col1, col2, col3 = st.columns(3)
if st.session_state.network_active:
    col1.metric("System Status", st.session_state.state.status)
    col2.metric("Link Latency", f"{random.randint(10, 45)}ms")
    col3.metric("UAV Coordinates", f"{st.session_state.state.coords[0]}, {st.session_state.state.coords[1]}")
else:
    col1.error("COMMS LOST")
    col2.metric("Link Latency", "N/A")
    col3.warning("GPS STALE")

# Tactical Visualization
st.subheader("Real-Time Mission Thread")
if st.session_state.network_active:
    df = pd.DataFrame(st.session_state.state.history)
    if not df.empty:
        st.scatter_chart(df, x="x", y="y", size=20)
    
    if st.session_state.state.target_acquired:
        st.toast("TARGET ACQUIRED", icon="🎯")
        st.success(f"Target locked at vector: {st.session_state.state.coords}")
else:
    st.info("System is in 'Autonomous Hold' mode. Re-establish link to resume telemetry.")

# Auto-refresh the UI
time.sleep(0.5)
st.rerun()


