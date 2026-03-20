import streamlit as st
import pandas as pd
import numpy as np
import time
import plotly.graph_objects as go
import pydeck as pdk
from datetime import datetime
import pytz

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="ResiliNet | Network Sentinel",
    page_icon="⚡", # Professional favicon
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. PROFESSIONAL CSS & THEME ENGINEERING ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600&display=swap');

    /* GLOBAL THEME: Deep Matte Charcoal & Oxblood Red */
    .stApp { 
        background-color: #0a0a0a; 
        color: #e0e0e0; 
        font-family: 'Inter', sans-serif; 
    }
    
    /* REMOVE DEFAULT STREAMLIT PADDING & ADD BREATHING ROOM FOR LOGO */
    .block-container { 
        padding-top: 3rem; /* Increased to prevent top clipping */
        padding-bottom: 5rem;
    }

    /* CUSTOM DUAL-TONE LOGO - FIXED CLIPPING */
    .nav-logo {
        font-family: 'JetBrains Mono', monospace;
        font-size: 4rem; /* Slightly larger for impact */
        font-weight: 800;
        letter-spacing: -2px;
        text-align: center;
        margin-bottom: 30px;
        text-transform: uppercase;
        border-bottom: 2px solid #333;
        padding-bottom: 20px;
        padding-top: 10px; /* Added space for top of letters */
        line-height: 1.2; /* Fixes vertical cutting */
        position: relative;
        z-index: 1;
    }
    .logo-white { 
        color: #E6DCC3; 
        text-shadow: 0 0 20px rgba(230, 220, 195, 0.3); /* Soft beige glow */
    }
    .logo-red { 
        color: #800020; 
        text-shadow: 0 0 25px rgba(128, 0, 32, 0.8); /* Strong red glow */
    }

    /* PANEL DESIGN: INDUSTRIAL HUD */
    .tech-panel {
        background: #141414;
        border-left: 4px solid #800020; /* Red Accent */
        border-top: 1px solid #333;
        border-right: 1px solid #333;
        border-bottom: 1px solid #333;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* KPI METRIC CARDS */
    div[data-testid="stMetric"] {
        background-color: #141414;
        border: 1px solid #333;
        padding: 15px;
        border-radius: 0px;
        border-top: 2px solid #E6DCC3; /* Beige Accent */
    }
    div[data-testid="stMetricLabel"] { color: #888; font-size: 0.8em; font-family: 'JetBrains Mono', monospace; }
    div[data-testid="stMetricValue"] { color: #E6DCC3; font-weight: 600; }

    /* CUSTOM SLIDERS - Red Track */
    .stSlider > div > div > div > div { background-color: #800020 !important; }
    
    /* BUTTON STYLING OVERRIDE */
    button[kind="primary"] {
        background-color: #800020 !important;
        color: #E6DCC3 !important;
        border: 1px solid #E6DCC3 !important;
        border-radius: 0px !important;
        font-family: 'JetBrains Mono', monospace;
        text-transform: uppercase;
    }
    button[kind="secondary"] {
        background-color: transparent !important;
        color: #666 !important;
        border: 1px solid #333 !important;
        border-radius: 0px !important;
        font-family: 'JetBrains Mono', monospace;
        text-transform: uppercase;
    }

    /* DATAFRAME STYLING */
    div[data-testid="stDataFrame"] { border: 1px solid #333; }

    /* EXPANDER STYLING FOR FAQ */
    .stExpander {
        background-color: #111 !important;
        border: 1px solid #333 !important;
        margin-bottom: 5px !important;
    }
    .stExpander details summary {
        font-family: 'JetBrains Mono', monospace;
        color: #E6DCC3;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. GLOBAL STATE ---
if "page" not in st.session_state: st.session_state.page = "manual"
if "wallet_balance" not in st.session_state: st.session_state.wallet_balance = 1250.00 
if "manual_optimized" not in st.session_state: st.session_state.manual_optimized = False
if "staked_amount" not in st.session_state: st.session_state.staked_amount = 500.00
if "logs" not in st.session_state: st.session_state.logs = []

# --- 4. MAP HELPER (3D PYDECK) ---
def render_3d_map(status):
    # Professional Palette: 
    # Critical = Oxblood Red [128, 0, 32]
    # Optimized = Beige/Gold [218, 165, 32]
    # Normal = Slate Grey [47, 79, 79]
    
    if status == "CRITICAL FAILURE":
        h_color = [139, 0, 0, 220] # Deep Red
    elif status == "OPTIMIZED":
        h_color = [230, 220, 195, 200] # Beige
    else:
        h_color = [70, 70, 70, 180] # Dark Grey

    # VIT Vellore Coordinates
    VIT_LOCATIONS = [
        {"name": "HEALTH CENTRE [CRITICAL]", "lat": 12.9710, "lon": 79.1595, "color": h_color, "height": 300},
        {"name": "ACADEMIC BLOCK SJT", "lat": 12.9718, "lon": 79.1588, "color": [60, 60, 60, 100], "height": 150},
        {"name": "TECH TOWER", "lat": 12.9725, "lon": 79.1575, "color": [60, 60, 60, 100], "height": 150},
        {"name": "RESIDENTIAL ZONE", "lat": 12.9690, "lon": 79.1560, "color": [100, 100, 100, 150], "height": 120}
    ]
    map_data = pd.DataFrame(VIT_LOCATIONS)

    # 3D Column Layer (Buildings)
    layer_col = pdk.Layer(
        "ColumnLayer",
        map_data,
        get_position=["lon", "lat"],
        get_elevation="height",
        elevation_scale=1,
        radius=50,
        get_fill_color="color",
        pickable=True,
        auto_highlight=True,
    )
    
    # Arc Layer (Traffic Flow) - Beige Arcs
    arc_data = [{"source": [79.1560, 12.9690], "target": [79.1595, 12.9710]}]
    layer_arc = pdk.Layer(
        "ArcLayer",
        arc_data,
        get_source_position="source",
        get_target_position="target",
        get_width=4,
        get_source_color=[230, 220, 195], # Beige source
        get_target_color=h_color,
    )

    view_state = pdk.ViewState(latitude=12.9710, longitude=79.1580, zoom=15, pitch=50)
    st.pydeck_chart(pdk.Deck(layers=[layer_col, layer_arc], initial_view_state=view_state, tooltip={"text": "{name}"}))

# --- 5. NAVBAR (UPDATED) ---
# Custom Logo with Colors
st.markdown('<div class="nav-logo"><span class="logo-white">RESILI</span><span class="logo-red">NET</span></div>', unsafe_allow_html=True)

# Three-Button Navigation
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("MANUAL CONTROL", use_container_width=True, type="primary" if st.session_state.page == "manual" else "secondary"):
        st.session_state.page = "manual"
        st.rerun()
with c2:
    if st.button("AUTONOMOUS SENTINEL", use_container_width=True, type="primary" if st.session_state.page == "live" else "secondary"):
        st.session_state.page = "live"
        st.rerun()
with c3:
    if st.button("ABOUT PROTOCOL", use_container_width=True, type="primary" if st.session_state.page == "about" else "secondary"):
        st.session_state.page = "about"
        st.rerun()
st.markdown("---")

# ==============================================================================
# MODE 1: MANUAL SIMULATION
# ==============================================================================
if st.session_state.page == "manual":
    st.title("OPERATOR CONTROL TERMINAL")
    st.caption("SYSTEM ID: 6G-CORE | INJECT TRAFFIC & EXECUTE SLICING PROTOCOLS")

    col_ctrl, col_vis = st.columns([1, 2])

    with col_ctrl:
        # 1. WALLET PANEL
        # FIX: Removed indentation inside the HTML string to prevent code block rendering
        st.markdown(f"""
<div class="tech-panel">
    <h5 style="margin:0; color:#666; font-family:'JetBrains Mono';">NODE LIQUIDITY</h5>
    <h2 style="margin:0; color:#E6DCC3;">{st.session_state.wallet_balance:,.2f} RNET</h2>
    <small style="color:#800020;">CONNECTED: 0x71...9A2</small>
</div>
""", unsafe_allow_html=True)
        
        # 2. CONTROLS
        st.markdown("### TRAFFIC INJECTION")
        ent_load = st.slider("RESIDENTIAL BANDWIDTH LOAD", 0, 100, 45)
        crit_load = st.slider("CRITICAL INFRASTRUCTURE LOAD", 0, 100, 20)
        
        # LOGIC
        raw_load = ent_load + crit_load
        if st.session_state.manual_optimized:
            eff_load = (ent_load * 0.4) + crit_load
            status = "OPTIMIZED"
            latency = int(12 + (eff_load * 0.3))
            color = "#E6DCC3" # Beige
        else:
            eff_load = raw_load
            if eff_load > 85:
                status = "CRITICAL FAILURE"
                latency = int(150 + (eff_load * 2.5))
                color = "#800020" # Red
            else:
                status = "NOMINAL"
                latency = int(20 + (eff_load * 0.2))
                color = "#444" # Grey

        # 3. ACTION
        st.markdown(f"<div style='background:{color}; color:{'#fff' if status == 'CRITICAL FAILURE' else '#000'}; padding:10px; text-align:center; font-weight:bold; font-family:JetBrains Mono;'>STATUS: {status}</div>", unsafe_allow_html=True)
        st.write("") 

        if status == "CRITICAL FAILURE" and not st.session_state.manual_optimized:
            if st.button("EXECUTE SOCIAL SLICE PROTOCOL", type="primary", use_container_width=True):
                with st.spinner("ALLOCATING RESOURCES..."):
                    time.sleep(0.8)
                st.session_state.manual_optimized = True
                st.session_state.wallet_balance += 50
                st.rerun()
        
        if st.session_state.manual_optimized:
            if st.button("RESET SIMULATION SCENARIO", use_container_width=True):
                st.session_state.manual_optimized = False
                st.rerun()

    with col_vis:
        st.markdown("#### DIGITAL TWIN VISUALIZATION")
        render_3d_map(status)

        st.markdown("#### DEEP PACKET INSPECTION (DPI)")
        dpi_df = pd.DataFrame({
            'PROTOCOL': ['UDP (STREAM)', 'TCP (WEB)', 'DICOM (MED)', 'SYS_HEARTBEAT'],
            'THROUGHPUT': [f"{(ent_load * 0.4 if st.session_state.manual_optimized else ent_load) * 8} Mbps", f"{ent_load * 1.5} Mbps", f"{crit_load * 40} Mbps", "120 Mbps"],
            'QoS PRIORITY': ['LOW', 'MEDIUM', 'CRITICAL', 'HIGH']
        })
        st.dataframe(dpi_df, use_container_width=True, hide_index=True)


# ==============================================================================
# MODE 2: LIVE AI GUARDIAN
# ==============================================================================
elif st.session_state.page == "live":
    st.title("AUTONOMOUS NETWORK SENTINEL")
    st.caption("REAL-TIME MONITORING | SYNC: INDIAN STANDARD TIME (IST)")

    # TIME & PHYSICS
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_hour = now.hour
    
    # Physics Curve
    live_load = 30 + (max(0, 100 - abs(current_hour - 10) * 15)) + (max(0, 100 - abs(current_hour - 20) * 10)) + 15

    if live_load > 85:
        ai_status = "ACTIVE SLICING"
        live_latency = int(15 + (live_load * 0.4))
        jitter = "12ms"
        pkt_loss = "0.01%" 
    else:
        ai_status = "PASSIVE MONITORING"
        live_latency = int(20 + (live_load * 0.2))
        jitter = "2ms"
        pkt_loss = "0.00%"

    # --- TOP METRICS ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("SYSTEM CLOCK", now.strftime('%H:%M:%S'))
    m2.metric("SENTINEL STATE", ai_status)
    m3.metric("LATENCY", f"{live_latency} ms")
    m4.metric("JITTER / LOSS", f"{jitter} | {pkt_loss}")

    # --- MAIN CONTENT ---
    c_left, c_right = st.columns([2, 1])

    with c_left:
        st.markdown("#### PREDICTIVE LOAD MODEL (24H)")
        hours = list(range(24))
        y_vals = [30 + (max(0, 100 - abs(h - 10) * 15)) + (max(0, 100 - abs(h - 20) * 10)) for h in hours]
        
        # Plotly Theme Update
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hours, y=y_vals, 
            fill='tozeroy', 
            line=dict(color='#800020', width=2), # Red Line
            fillcolor='rgba(128, 0, 32, 0.2)', # Red Fill
            name='Traffic'
        ))
        fig.add_trace(go.Scatter(
            x=[current_hour], y=[live_load], 
            mode='markers', 
            marker=dict(color='#E6DCC3', size=10, line=dict(color='white', width=2)), # Beige Marker
            name='CURRENT'
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)', 
            font_color='#888',
            height=250, 
            margin=dict(l=0,r=0,t=0,b=0),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='#333')
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### REGIONAL STATUS MAP")
        render_3d_map("CRITICAL FAILURE" if live_load > 85 else "STABLE")

    with c_right:
        # FULL DEFI PANEL
        # FIX: Removed indentation inside the HTML string here as well
        st.markdown(f"""
<div class="tech-panel">
    <h3 style="margin:0; font-family:'JetBrains Mono'">DEFI LIQUIDITY</h3>
    <h1 style="color:#E6DCC3; margin:10px 0;">{st.session_state.staked_amount:,.2f}</h1>
    <small style="color:#888;">TOTAL STAKED (APY: 12%)</small>
    <hr style="border-color: #333;">
    <p style="color:#aaa;">AVAILABLE BALANCE: {st.session_state.wallet_balance:,.2f}</p>
</div>
""", unsafe_allow_html=True)

        # DEPOSIT / WITHDRAW TABS
        tab1, tab2 = st.tabs(["DEPOSIT STAKE", "WITHDRAW ASSETS"])
        with tab1:
            val = st.number_input("AMOUNT", 0.0, 1000.0, step=50.0, key="live_stake")
            if st.button("CONFIRM STAKE", use_container_width=True, type="primary"):
                st.session_state.wallet_balance -= val
                st.session_state.staked_amount += val
                st.rerun()
        with tab2:
            val2 = st.number_input("AMOUNT", 0.0, st.session_state.staked_amount, step=50.0, key="live_unstake")
            if st.button("CONFIRM WITHDRAWAL", use_container_width=True):
                st.session_state.wallet_balance += val2
                st.session_state.staked_amount -= val2
                st.rerun()
        
        st.markdown("---")
        st.markdown("#### SYSTEM LOGS")
        if live_load > 85:
            st.error(f"[{now.strftime('%H:%M:%S')}] CONGESTION DETECTED [NODE: TT]")
            st.success(f"[{now.strftime('%H:%M:%S')}] CONTRACT 0x8A...22 EXECUTED")
        else:
            st.info(f"[{now.strftime('%H:%M:%S')}] NETWORK STABLE | LATENCY < 30ms")

# ==============================================================================
# MODE 3: ABOUT PROTOCOL (FAQ)
# ==============================================================================
elif st.session_state.page == "about":
    st.title("PROTOCOL DOCUMENTATION")
    st.caption("RESILINET DECENTRALIZED INFRASTRUCTURE | KNOWLEDGE BASE")

    faq_data = [
        ("What is the ResiliNet Protocol?", "ResiliNet is a decentralized 6G network orchestration layer that uses blockchain-based smart contracts to dynamically allocate bandwidth and priority slices in real-time."),
        ("How does 'Social Slicing' work?", "Social Slicing deprioritizes non-essential traffic (like social media or background downloads) to guarantee 99.999% uptime for critical infrastructure during surges."),
        ("What is the role of the RNET token?", "RNET is the utility token used to pay for high-priority network slices and reward node operators for maintaining low-latency connections."),
        ("Is the network truly decentralized?", "Yes, the control plane is distributed across thousands of validator nodes, preventing any single point of failure in the 6G core."),
        ("How is AI used in the Sentinel mode?", "The Sentinel uses predictive Transformer models to forecast traffic spikes 15 minutes before they occur, preemptively adjusting slice depth."),
        ("What is Deep Packet Inspection (DPI)?", "DPI is the method used by our nodes to identify the protocol type (e.g., DICOM for medical imaging) to ensure it receives the correct QoS tag."),
        ("How do I earn rewards?", "By staking RNET tokens into regional liquidity pools, you provide the collateral necessary for node operators to bid on traffic routing tasks."),
        ("What are the latency targets for ResiliNet?", "We aim for sub-10ms end-to-end latency for URLLC (Ultra-Reliable Low-Latency Communications) applications."),
        ("Can this protocol run on existing 5G hardware?", "ResiliNet is designed as a software-defined layer that is backward compatible with 5G NR but optimized for 6G Terahertz frequencies."),
        ("How are 'Critical Failures' defined?", "A critical failure occurs when the combined load exceeds the node's physical capacity, causing packet drops in high-priority streams."),
        ("What is the 'Digital Twin'?", "It is a real-time 3D simulation of the physical network environment, allowing operators to visualize traffic flow and hardware health."),
        ("Is my data private on ResiliNet?", "Yes, ResiliNet uses Zero-Knowledge Proofs (ZKPs) to verify traffic priority without inspecting the actual content of the packets."),
        ("What happens if a node goes offline?", "The protocol's self-healing mesh architecture instantly reroutes traffic through the next most efficient path via the Arc-Layer."),
        ("What is the APY for staking?", "The current protocol-wide APY is 12%, funded by network transaction fees and slicing premiums."),
        ("How does the protocol handle Jitter?", "By using deterministic routing and time-sensitive networking (TSN) protocols integrated into the blockchain consensus."),
        ("What is the 'Oxblood' status?", "In our HUD, Oxblood Red indicates a critical congestion state where the Social Slice Protocol must be manually or autonomously triggered."),
        ("Who governs the protocol updates?", "Governance is handled by the ResiliNet DAO, where token holders vote on parameter changes like fee structures and slicing ratios."),
        ("How does 6G differ from 5G here?", "6G introduces native AI integration at the physical layer, which ResiliNet leverages for micro-second resource management."),
        ("Can I run a node on my own hardware?", "Any device meeting the minimum computational requirements (8-core CPU, 16GB RAM) can join as a 'Sentinel Node'."),
        ("Where is the first implementation located?", "The initial pilot is deployed across the VIT Vellore campus, monitoring academic and healthcare infrastructure.")
    ]

    st.markdown("### FREQUENTLY ASKED QUESTIONS")
    
    col_a, col_b = st.columns(2)
    
    # Split FAQ into two columns for better reading
    mid = len(faq_data) // 2
    
    with col_a:
        for q, a in faq_data[:mid]:
            with st.expander(q):
                st.markdown(f"<div style='color:#E6DCC3; border-left: 2px solid #800020; padding-left:15px;'>{a}</div>", unsafe_allow_html=True)

    with col_b:
        for q, a in faq_data[mid:]:
            with st.expander(q):
                st.markdown(f"<div style='color:#E6DCC3; border-left: 2px solid #800020; padding-left:15px;'>{a}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.info("Technical Whitepaper v2.4.0-Stable | Last Updated: Feb 2026 | Secured by AES-256")
    //ResiliNET Code
