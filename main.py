import streamlit as st
import numpy as np
import pandas as pd
import time
from datetime import datetime, timedelta
from supabase import create_client, Client
import plotly.express as px

# ================= 1. 系统配置区 =================
# ⚠️ 请填入您的 Supabase 真实信息
SUPABASE_URL = "https://gcphgliusmlisuabnzip.supabase.co"
SUPABASE_KEY = "sb_publishable_sivoYyUISEUDMHcb9LNb2g_yBiUFESd"

st.set_page_config(
    page_title="Factory Monitor (Dev Mode)",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 工业 UI 风格定义 (亮色版) ---
st.markdown("""
<style>
    /* 全局背景：亮灰白色 */
    .stApp {
        background-color: #F8F9FA; 
        color: #1F2937;
    }
    
    /* 侧边栏：纯白带边框 */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E5E7EB;
    }
    
    /* 顶部卡片/容器样式：白色背景+轻微阴影 */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] > div {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        padding: 15px;
    }
    
    /* 关键指标数字：深蓝色，加粗 */
    div[data-testid="stMetricValue"] {
        font-family: 'Roboto Mono', monospace;
        font-size: 1.8rem;
        font-weight: 700;
        color: #2563EB; /* 科技蓝 (深色适配亮底) */
    }
    
    /* 指标标签颜色 */
    div[data-testid="stMetricLabel"] {
        color: #4B5563; /* 深灰 */
    }
    
    /* 自定义状态徽章 */
    .status-badge {
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .status-ok {background-color: #D1FAE5; color: #065F46;} /* 浅绿底深绿字 */
    .status-warn {background-color: #FEF3C7; color: #92400E;} /* 浅黄底深黄字 */
    
</style>
""", unsafe_allow_html=True)

# ================= 2. 后端逻辑 (云端 + 模拟) =================

@st.cache_resource
def init_supabase():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except:
        return None

supabase: Client = init_supabase()

# --- 核心：虚拟硬件层 (Mock Hardware) ---
def get_mock_frame():
    """生成一个模拟的热成像噪点图"""
    # 生成 480x640 的随机热力图
    frame = np.random.rand(480, 640) * 255
    # 模拟中心热源
    y, x = np.ogrid[:480, :640]
    mask = (x - 320)**2 + (y - 240)**2 <= 100**2
    frame[mask] += 100
    
    frame = np.clip(frame, 0, 255).astype(np.uint8)
    return np.stack((frame,)*3, axis=-1)

def get_mock_data():
    """生成模拟传感器读数"""
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
    """将一次快照上传到云端"""
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

# ================= 3. 前端 UI 逻辑 =================

st.sidebar.title("🏭 工业监控系统")
st.sidebar.caption("Dev Mode V4.0 | Bright Theme")

# 导航菜单 (已删除图标)
menu = st.sidebar.radio("系统模块", ["总览仪表盘 (Dashboard)", "工艺详情 (Process Detail)", "数据管理 (Data Admin)"])
st.sidebar.divider()

# 全局模拟器控制
st.sidebar.subheader("模拟器控制")
sim_active = st.sidebar.checkbox("启动虚拟产线", value=True)
auto_upload = st.sidebar.checkbox("自动上传数据 (每5秒)", value=False)

if auto_upload and sim_active:
    if 'last_upload' not in st.session_state: st.session_state.last_upload = time.time()
    if time.time() - st.session_state.last_upload > 5:
        mock_d = get_mock_data()
        if upload_data_batch(mock_d):
            st.toast("☁️ 模拟数据已自动上传云端", icon="✅")
        st.session_state.last_upload = time.time()

# --- 模块 A: Dashboard 总览 ---
if menu == "📊 总览仪表盘 (Dashboard)":
    st.title("🏭 全厂状态总览")
    st.markdown("实时监控各工艺环节核心指标 (模拟数据流)")
    
    live_data = get_mock_data()
    
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)
    layout = [
        (col1, "Pultrusion", "🟦 拉挤工艺"),
        (col2, "Encapsulation", "🟪 封装工艺"),
        (col3, "Conforming", "🟨 成型工艺"),
        (col4, "Stranding", "🟩 绞线工艺")
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

# --- 模块 B: 工艺详情 (左视频 右数据) ---
elif menu == "工艺详情 (Process Detail)":
    target_process = st.selectbox("选择查看工艺", ["Pultrusion", "Encapsulation", "Conforming", "Stranding"])
    st.divider()
    
    col_video, col_data = st.columns([0.65, 0.35])
    live_data = get_mock_data()[target_process]
    
    with col_video:
        st.subheader("📹 实时热成像 (模拟信号)")
        if sim_active:
            mock_frame = get_mock_frame()
            st.image(mock_frame, caption=f"Cam-01: {target_process} Station", use_container_width=True)
        else:
            st.info("模拟器已暂停")
            
    with col_data:
        st.subheader("📊 实时温度均值")
        for m_name, info in live_data.items():
            unit = info.get("unit", "°C")
            delta_color = "inverse" if info['val'] > info['limit'] else "normal"
            
            with st.container(border=True):
                c1, c2 = st.columns([2, 1])
                c1.metric(m_name, f"{info['val']:.1f} {unit}", delta_color=delta_color)
                c2.caption(f"Limit:\n{info['limit']} {unit}")

# --- 模块 C: 数据管理 (已删除图标) ---
elif menu == "数据管理 (Data Admin)":
    st.title("数据库管理中心") # 已删除图标
    st.markdown("直接与 Supabase 云端交互，进行数据审计和导出。")
    
    tab1, tab2 = st.tabs(["📉 历史数据查询", " 数据库工具"])
    
    with tab1:
        c1, c2, c3 = st.columns(3)
        q_proc = c1.selectbox("工艺筛选", ["Pultrusion", "Encapsulation", "Conforming", "Stranding"], key="q_proc")
        q_metric = c2.text_input("指标名称 (如 Die Temp)", value="Die Temp")
        q_days = c3.slider("查询最近 N 天", 1, 30, 7)
        
        if st.button("执行云端查询"):
            if not supabase:
                st.error("请先配置 Supabase 密钥！")
            else:
                with st.spinner("正在从 Supabase 拉取数据..."):
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
                        
                        st.success(f"查询成功！共找到 {len(df)} 条记录。")
                        
                        # 亮色主题图表 (template="plotly_white")
                        fig = px.area(df, x='LocalTime', y='value', title=f"{q_proc} - {q_metric} 趋势分析", template="plotly_white")
                        st.plotly_chart(fig, use_container_width=True)
                        
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button("📥 导出查询结果 (CSV)", csv, "export_data.csv", "text/csv", type="primary")
                    else:
                        st.warning("未查询到数据。")

    with tab2:
        st.warning("⚠️ 危险操作区")
        if st.button("生成 100 条测试数据并写入云端"):
            if not supabase:
                st.error("无连接")
            else:
                progress_bar = st.progress(0)
                for i in range(10): 
                    mock_d = get_mock_data()
                    upload_data_batch(mock_d)
                    progress_bar.progress((i+1)*10)
                    time.sleep(0.1)
                st.success("100 条模拟数据写入完成！")

# 自动刷新 (修复了 experimental_rerun 报错)
if menu != "数据管理 (Data Admin)" and sim_active:
    time.sleep(0.5)
    st.rerun()