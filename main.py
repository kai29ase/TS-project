import streamlit as st
import numpy as np
import pandas as pd
import time
from datetime import datetime, timedelta, date
from supabase import create_client, Client
import plotly.express as px

# ================= 1. 系统配置区 =================
# ⚠️ 请填入您的 Supabase 真实信息，以便测试数据管理功能
SUPABASE_URL = "https://gcphgliusmlisuabnzip.supabase.co"
SUPABASE_KEY = "sb_publishable_sivoYyUISEUDMHcb9LNb2g_yBiUFESd"

st.set_page_config(
    page_title="Factory Monitor (Dev Mode)",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 工业 UI 风格定义 ---
st.markdown("""
<style>
    .stApp {background-color: #0b0f19;} /* 深空黑背景 */
    
    /* 顶部卡片样式 */
    div.css-1r6slb0 {background-color: #1f2937; border: 1px solid #374151; border-radius: 8px;}
    
    /* 关键指标大字 */
    div[data-testid="stMetricValue"] {
        font-family: 'Roboto Mono', monospace;
        font-size: 1.8rem;
        color: #60A5FA; /* 科技蓝 */
    }
    div[data-testid="stMetricLabel"] {color: #9CA3AF;}
    
    /* 自定义状态徽章 */
    .status-badge {
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .status-ok {background-color: #064E3B; color: #34D399;}
    .status-warn {background-color: #78350F; color: #FCD34D;}
    
    /* 侧边栏 */
    section[data-testid="stSidebar"] {background-color: #111827;}
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
    """生成一个模拟的热成像噪点图，无需真实相机"""
    # 生成 480x640 的随机热力图
    frame = np.random.rand(480, 640) * 255
    # 加上一些色块模拟"热源"
    cv2_sim = np.zeros((480, 640), dtype=np.uint8)
    # 模拟中心热源
    y, x = np.ogrid[:480, :640]
    mask = (x - 320)**2 + (y - 240)**2 <= 100**2
    frame[mask] += 100
    # 归一化并转为伪彩色 (模拟 OpenCV 的 colormap)
    # 这里为了不依赖 opencv 库导致报错，直接返回灰度图或简单的 RGB
    frame = np.clip(frame, 0, 255).astype(np.uint8)
    # 将单通道转为3通道以便 st.image 显示
    return np.stack((frame,)*3, axis=-1)

def get_mock_data():
    """生成模拟传感器读数"""
    # 基础温度 60度，随机波动 +/- 5度
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
st.sidebar.caption("Dev Mode V4.0 | No Hardware Req")

# 导航菜单
menu = st.sidebar.radio("系统模块", ["📊 总览仪表盘 (Dashboard)", "🔍 工艺详情 (Process Detail)", "💾 数据管理 (Data Admin)"])
st.sidebar.divider()

# 全局模拟器控制
st.sidebar.subheader("模拟器控制")
sim_active = st.sidebar.checkbox("启动虚拟产线", value=True)
auto_upload = st.sidebar.checkbox("自动上传数据 (每5秒)", value=False)

if auto_upload and sim_active:
    # 模拟后台自动上传任务
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
    
    # 获取一帧最新模拟数据
    live_data = get_mock_data()
    
    # 渲染4个工艺卡片
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
                # 取该工艺下的第一个指标作为主显
                main_metric = list(live_data[p_key].keys())[0]
                val = live_data[p_key][main_metric]['val']
                limit = live_data[p_key][main_metric]['limit']
                
                # 状态判定
                status_html = '<span class="status-badge status-ok">NORMAL</span>'
                if val > limit:
                    status_html = '<span class="status-badge status-warn">WARNING</span>'
                
                c_a, c_b = st.columns([2, 1])
                c_a.metric(main_metric, f"{val:.1f} °C")
                c_b.markdown(f"<br>{status_html}", unsafe_allow_html=True)
                
                # 迷你趋势图 (随机生成用于装饰 dashboard)
                st.line_chart(np.random.randn(20) + val, height=100)

# --- 模块 B: 工艺详情 (左视频 右数据) ---
elif menu == "🔍 工艺详情 (Process Detail)":
    # 顶部筛选
    target_process = st.selectbox("选择查看工艺", ["Pultrusion", "Encapsulation", "Conforming", "Stranding"])
    st.divider()
    
    col_video, col_data = st.columns([0.65, 0.35])
    
    # 获取数据
    live_data = get_mock_data()[target_process]
    
    with col_video:
        st.subheader("📹 实时热成像 (模拟信号)")
        if sim_active:
            # 显示虚拟热图
            mock_frame = get_mock_frame()
            # 在没有OpenCV的情况下，直接显示
            st.image(mock_frame, caption=f"Cam-01: {target_process} Station", use_container_width=True)
        else:
            st.info("模拟器已暂停")
            
    with col_data:
        st.subheader("📊 实时传感器阵列")
        # 遍历该工艺下的所有指标
        for m_name, info in live_data.items():
            unit = info.get("unit", "°C")
            delta_color = "inverse" if info['val'] > info['limit'] else "normal"
            
            with st.container(border=True):
                c1, c2 = st.columns([2, 1])
                c1.metric(m_name, f"{info['val']:.1f} {unit}", delta_color=delta_color)
                # 显示阈值
                c2.caption(f"Limit:\n{info['limit']} {unit}")

# --- 模块 C: 数据管理 (后台功能) ---
elif menu == "💾 数据管理 (Data Admin)":
    st.title("💾 数据库管理中心")
    st.markdown("直接与 Supabase 云端交互，进行数据审计和导出。")
    
    tab1, tab2 = st.tabs(["📉 历史数据查询", "🛠️ 数据库工具"])
    
    with tab1:
        c1, c2, c3 = st.columns(3)
        q_proc = c1.selectbox("工艺筛选", ["Pultrusion", "Encapsulation", "Conforming", "Stranding"], key="q_proc")
        # 简单处理：这里写死指标名，实际可联动
        q_metric = c2.text_input("指标名称 (如 Die Temp)", value="Die Temp")
        q_days = c3.slider("查询最近 N 天", 1, 30, 7)
        
        if st.button("🔍 执行云端查询"):
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
                        
                        # 图表
                        fig = px.area(df, x='LocalTime', y='value', title=f"{q_proc} - {q_metric} 趋势分析", template="plotly_dark")
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # 导出
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button("📥 导出查询结果 (CSV)", csv, "export_data.csv", "text/csv", type="primary")
                    else:
                        st.warning("未查询到数据。请尝试在侧边栏开启'自动上传数据'来生成一些测试记录。")

    with tab2:
        st.warning("⚠️ 危险操作区")
        if st.button("生成 100 条测试数据并写入云端"):
            if not supabase:
                st.error("无连接")
            else:
                progress_bar = st.progress(0)
                for i in range(10): # 分10批写入
                    mock_d = get_mock_data()
                    upload_data_batch(mock_d)
                    progress_bar.progress((i+1)*10)
                    time.sleep(0.1)
                st.success("100 条模拟数据写入完成！现在可以去'历史数据查询'查看了。")

# 自动刷新以维持实时感 (仅在 Dashboard 或 Detail 页面)
if menu != "💾 数据管理 (Data Admin)" and sim_active:
    time.sleep(0.5)
    st.experimental_rerun()