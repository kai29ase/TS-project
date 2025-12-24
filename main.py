import streamlit as st
import numpy as np
import pandas as pd
import time
from datetime import datetime, timedelta
from supabase import create_client, Client
import plotly.express as px

# ================= 1. System Configuration =================
SUPABASE_URL = "https://gcphgliusmlisuabnzip.supabase.co"
SUPABASE_KEY = "sb_publishable_sivoYyUISEUDMHcb9LNb2g_yBiUFESd"

st.set_page_config(
    page_title="Factory Monitor (Dev Mode)",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Industrial UI Style (Bright Theme) ---
st.markdown("""
<style>
    .stApp { background-color: #F8F9FA; color: #1F2937; }
    section[data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E5E7EB; }
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] > div {
        background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); padding: 15px;
    }
    div[data-testid="stMetricValue"] { font-family: 'Roboto Mono', monospace; font-size: 1.8rem; font-weight: 700; color: #2563EB; }
    div[data-testid="stMetricLabel"] { color: #4B5563; }
    .status-badge { padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: bold; }
    .status-ok {background-color: #D1FAE5; color: #065F46;} 
    .status-warn {background-color: #FEF3C7; color: #92400E;} 
</style>
""", unsafe_allow_html=True)

# ================= 2. Backend Logic =================

@st.cache_resource
def init_supabase():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except:
        return None

supabase: Client = init_supabase()

def get_mock_frame():
    frame = np.random.rand(480, 640) * 255
    y, x = np.ogrid[:480, :640]
    mask = (x - 320)**2 + (y - 240)**2 <= 100**2
    frame[mask] += 100
    frame = np.clip(frame, 0, 255).astype(np.uint8)
    return np.stack((frame,)*3, axis=-1)

def get_mock_data():
    base = 60 + np.random.randn() * 2
    return {
        "Pultrusion": {
            "Die Temp": {"val": base * 1.2, "limit": 90},
            "Resin Temp": {"val": base * 0.8, "limit": 60},
            "Pull Speed": {"val": 5.5 + np.random.rand(), "limit": 10, "unit": "m/min"} 
        },
        "Encapsulation": {
            "Core Temp": {"val": base * 1.3, "limit": 85},
            "Power Unit": {"val": base * 0.9, "limit": 70}
        },
        "Conforming": {
            "Strand Temp": {"val": base * 1.05, "limit": 75},
        },
        "Stranding": {
            "Motor Temp": {"val": base * 1.15, "limit": 80},
            "RPM": {"val": 1200 + np.random.randn()*50, "limit": 1500, "unit": "rpm"}
        }
    }

def upload_data_batch(data_snapshot):
    if not supabase: return False
    try:
        rows = []
        for p_name, metrics in data_snapshot.items():
            for m_name, info in metrics.items():
                rows.append({
                    "process_name": p_name,
                    "metric_name": m_name,
                    "value": round(info['val'], 2)
                })
        supabase.table("sensor_data").insert(rows).execute()
        return True
    except:
        return False

# ================= 3. Frontend UI Logic =================

st.sidebar.title("Factory Monitoring System")
st.sidebar.caption("Dev Mode V4.1 | Fast Switch") # Updated version

# Navigation Menu
menu = st.sidebar.radio("System Modules", ["Dashboard", "Process Detail", "Data Admin"])
st.sidebar.divider()

# Simulator Controls
st.sidebar.subheader("Simulator Controls")
sim_active = st.sidebar.checkbox("Activate Virtual Line", value=True)
auto_upload = st.sidebar.checkbox("Auto Upload Data (5s interval)", value=False)

# Handle Auto Upload (Global Logic)
if auto_upload and sim_active:
    if 'last_upload' not in st.session_state: st.session_state.last_upload = time.time()
    if time.time() - st.session_state.last_upload > 5:
        mock_d = get_mock_data()
        if upload_data_batch(mock_d):
            st.toast("Simulated data uploaded to cloud")
        st.session_state.last_upload = time.time()

# --- Module A: Dashboard ---
if menu == "Dashboard":
    st.title("Plant Status Overview")
    st.markdown("Real-time monitoring of core metrics (Simulated Data)")
    
    # [关键修复] 使用 @st.fragment 让这个函数内部独立刷新，不阻塞侧边栏
    @st.fragment(run_every=0.5 if sim_active else None)
    def render_dashboard():
        live_data = get_mock_data()
        col1, col2 = st.columns(2)
        col3, col4 = st.columns(2)
        layout = [
            (col1, "Pultrusion", "Pultrusion"),
            (col2, "Encapsulation", "Encapsulation"),
            (col3, "Conforming", "Conforming"),
            (col4, "Stranding", "Stranding")
        ]
        
        for col, p_key, title in layout:
            with col:
                with st.container(border=True):
                    st.subheader(title)
                    main_metric = list(live_data[p_key].keys())[0]
                    val = live_data[p_key][main_metric]['val']
                    limit = live_data[p_key][main_metric]['limit']
                    
                    status_html = '<span class="status-badge status-ok">NORMAL</span>'
                    if val > limit:
                        status_html = '<span class="status-badge status-warn">WARNING</span>'
                    
                    c_a, c_b = st.columns([2, 1])
                    c_a.metric(main_metric, f"{val:.1f} °C")
                    c_b.markdown(f"<br>{status_html}", unsafe_allow_html=True)
                    st.line_chart(np.random.randn(20) + val, height=100)
    
    # 调用这个局部刷新的函数
    render_dashboard()

# --- Module B: Process Detail ---
elif menu == "Process Detail":
    target_process = st.selectbox("Select Process", ["Pultrusion", "Encapsulation", "Conforming", "Stranding"])
    st.divider()
    
    # [关键修复] 同样使用 fragment 隔离刷新
    @st.fragment(run_every=0.5 if sim_active else None)
    def render_detail_view(process_name):
        col_video, col_data = st.columns([0.65, 0.35])
        live_data = get_mock_data()[process_name]
        
        with col_video:
            st.subheader("Real-time Thermal Imaging")
            if sim_active:
                mock_frame = get_mock_frame()
                st.image(mock_frame, caption=f"Cam-01: {process_name} Station", use_container_width=True)
            else:
                st.info("Simulator Paused")
                
        with col_data:
            st.subheader("Real-time Sensor Array")
            for m_name, info in live_data.items():
                unit = info.get("unit", "°C")
                delta_color = "inverse" if info['val'] > info['limit'] else "normal"
                
                with st.container(border=True):
                    c1, c2 = st.columns([2, 1])
                    c1.metric(m_name, f"{info['val']:.1f} {unit}", delta_color=delta_color)
                    c2.caption(f"Limit:\n{info['limit']} {unit}")
    
    # 调用渲染
    render_detail_view(target_process)

# --- Module C: Data Admin ---
elif menu == "Data Admin":
    st.title("Database Admin Center")
    st.markdown("Interact directly with Supabase cloud.")
    
    tab1, tab2 = st.tabs(["Historical Data Query", "Database Tools"])
    
    with tab1:
        c1, c2, c3 = st.columns(3)
        q_proc = c1.selectbox("Filter Process", ["Pultrusion", "Encapsulation", "Conforming", "Stranding"], key="q_proc")
        q_metric = c2.text_input("Metric Name", value="Die Temp")
        q_days = c3.slider("Query last N days", 1, 30, 7)
        
        if st.button("Execute Cloud Query"):
            if not supabase:
                st.error("Please configure Supabase key first!")
            else:
                with st.spinner("Fetching data..."):
                    start_date = (datetime.utcnow() - timedelta(days=q_days)).isoformat()
                    res = supabase.table("sensor_data").select("*")\
                        .eq("process_name", q_proc)\
                        .eq("metric_name", q_metric)\
                        .gte("created_at", start_date)\
                        .order("created_at", desc=False).execute()
                    
                    df = pd.DataFrame(res.data)
                    
                    if not df.empty:
                        df['created_at'] = pd.to_datetime(df['created_at'])
                        df['LocalTime'] = df['created_at'] + timedelta(hours=8)
                        st.success(f"Found {len(df)} records.")
                        fig = px.area(df, x='LocalTime', y='value', title=f"{q_proc} - {q_metric} Trend", template="plotly_white")
                        st.plotly_chart(fig, use_container_width=True)
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button("Export (CSV)", csv, "export_data.csv", "text/csv", type="primary")
                    else:
                        st.warning("No data found.")

    with tab2:
        st.warning("⚠️ Danger Zone")
        if st.button("Generate & Upload 100 Test Records"):
            if not supabase:
                st.error("No Connection")
            else:
                progress_bar = st.progress(0)
                for i in range(10): 
                    mock_d = get_mock_data()
                    upload_data_batch(mock_d)
                    progress_bar.progress((i+1)*10)
                    time.sleep(0.1)
                st.success("Uploaded!")

# ⚠️ 注意：这里不再需要全局的 while True 或者 st.rerun() 了
# 刷新逻辑已经完全移交给具体的 @st.fragment 处理