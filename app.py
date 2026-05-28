import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Aurora Executive Dashboard", layout="wide")

# ── Custom CSS (Power BI Style) ───────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #f0f2f6; }
    .main .block-container { padding-top: 1rem; }
    .kpi-box {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 5px solid #4f46e5;
        margin-bottom: 10px;
    }
    .kpi-label {
        font-size: 13px;
        color: #6b7280;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .kpi-value {
        font-size: 28px;
        font-weight: 700;
        color: #1e1b4b;
        margin: 5px 0;
    }
    .kpi-delta {
        font-size: 12px;
        color: #10b981;
        font-weight: 600;
    }
    .kpi-delta-red { color: #ef4444; }
    .dashboard-header {
        background: linear-gradient(135deg, #4f46e5, #7c3aed);
        padding: 20px 30px;
        border-radius: 12px;
        margin-bottom: 20px;
        color: white;
    }
    .section-header {
        background-color: white;
        padding: 10px 20px;
        border-radius: 8px;
        border-left: 4px solid #4f46e5;
        margin: 15px 0 10px 0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }
    .stButton>button {
        background-color: #4f46e5;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 8px 20px;
        font-weight: 600;
    }
    .stButton>button:hover { background-color: #4338ca; }
    [data-testid="stSidebar"] {
        background-color: #1e1b4b;
    }
    [data-testid="stSidebar"] * { color: white !important; }
    [data-testid="stSidebar"] .stSelectbox > div > div {
        background-color: #2d2a6e;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ── Helper: Format numbers ────────────────────────────────────────────────────
def fmt(n):
    if abs(n) >= 1_000_000_000:
        return f"${n/1_000_000_000:.1f}B"
    elif abs(n) >= 1_000_000:
        return f"${n/1_000_000:.1f}M"
    elif abs(n) >= 1_000:
        return f"${n/1_000:.1f}K"
    return f"${n:,.0f}"

# ── Load Data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_excel("aurora_full_dataset.xlsx")
    df["transaction_date"] = pd.to_datetime(df["transaction_date"])
    df["month"] = df["transaction_date"].dt.to_period("M").astype(str)
    return df

df = load_data()

# ── Sidebar Filters ───────────────────────────────────────────────────────────
st.sidebar.markdown("## 🏢 Aurora Analytics")
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Dashboard Filters")

regions  = ["All"] + sorted(df["region"].dropna().unique().tolist())
channels = ["All"] + sorted(df["channel"].dropna().unique().tolist())
segments = ["All"] + sorted(df["customer_segment"].dropna().unique().tolist())
months   = sorted(df["month"].unique().tolist())

selected_region  = st.sidebar.selectbox("🌍 Region", regions)
selected_channel = st.sidebar.selectbox("📡 Channel", channels)
selected_segment = st.sidebar.selectbox("👥 Customer Segment", segments)
selected_date    = st.sidebar.select_slider("📅 Month Range", options=months, value=(months[0], months[-1]))

st.sidebar.markdown("---")
st.sidebar.markdown("**AI-Powered Analytics**")
st.sidebar.markdown("Powered by Groq LLM")

# ── Apply Filters ─────────────────────────────────────────────────────────────
dff = df.copy()
if selected_region  != "All": dff = dff[dff["region"] == selected_region]
if selected_channel != "All": dff = dff[dff["channel"] == selected_channel]
if selected_segment != "All": dff = dff[dff["customer_segment"] == selected_segment]
dff = dff[(dff["month"] >= selected_date[0]) & (dff["month"] <= selected_date[1])]

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="dashboard-header">
    <h1 style="margin:0; font-size:26px;">🏢 Aurora Retail & Digital Services</h1>
    <p style="margin:5px 0 0 0; opacity:0.85; font-size:14px;">AI-Powered Executive Dashboard</p>
</div>
""", unsafe_allow_html=True)

# ── KPI Cards ─────────────────────────────────────────────────────────────────
total_revenue    = dff["revenue"].sum()
total_profit     = dff["profit"].sum()
total_actual_rev = dff["actual_revenue"].sum()
total_budget_rev = dff["budgeted_revenue"].sum()
revenue_variance = total_actual_rev - total_budget_rev
churn_rate       = (dff[dff["churn_flag"] == "Yes"]["customer_id"].nunique() /
                    dff["customer_id"].nunique() * 100) if dff["customer_id"].nunique() > 0 else 0
profit_margin    = (total_profit / total_revenue * 100) if total_revenue > 0 else 0

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.markdown(f"""<div class="kpi-box">
        <div class="kpi-label">💰 Total Revenue</div>
        <div class="kpi-value">{fmt(total_revenue)}</div>
        <div class="kpi-delta">All Channels</div>
    </div>""", unsafe_allow_html=True)

with col2:
    st.markdown(f"""<div class="kpi-box">
        <div class="kpi-label">📈 Total Profit</div>
        <div class="kpi-value">{fmt(total_profit)}</div>
        <div class="kpi-delta">Margin: {profit_margin:.1f}%</div>
    </div>""", unsafe_allow_html=True)

with col3:
    st.markdown(f"""<div class="kpi-box">
        <div class="kpi-label">🎯 Actual Revenue</div>
        <div class="kpi-value">{fmt(total_actual_rev)}</div>
        <div class="kpi-delta">vs Budget: {fmt(total_budget_rev)}</div>
    </div>""", unsafe_allow_html=True)

with col4:
    delta_color = "kpi-delta" if revenue_variance > 0 else "kpi-delta kpi-delta-red"
    delta_sign  = "▲ Over Budget" if revenue_variance > 0 else "▼ Under Budget"
    st.markdown(f"""<div class="kpi-box">
        <div class="kpi-label">📊 Revenue Variance</div>
        <div class="kpi-value">{fmt(revenue_variance)}</div>
        <div class="{delta_color}">{delta_sign}</div>
    </div>""", unsafe_allow_html=True)

with col5:
    churn_color = "kpi-delta-red" if churn_rate > 20 else "kpi-delta"
    st.markdown(f"""<div class="kpi-box">
        <div class="kpi-label">⚠️ Churn Rate</div>
        <div class="kpi-value">{churn_rate:.1f}%</div>
        <div class="kpi-delta {churn_color}">{'High Risk' if churn_rate > 20 else 'Acceptable'}</div>
    </div>""", unsafe_allow_html=True)

with col6:
    total_customers = dff["customer_id"].nunique()
    st.markdown(f"""<div class="kpi-box">
        <div class="kpi-label">👥 Total Customers</div>
        <div class="kpi-value">{total_customers:,}</div>
        <div class="kpi-delta">Unique Customers</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Chart colors ──────────────────────────────────────────────────────────────
COLORS = ["#4f46e5","#7c3aed","#a855f7","#ec4899","#f97316","#10b981"]

# ── Charts Row 1 ──────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    region_rev = dff.groupby("region")["revenue"].sum().reset_index()
    fig1 = px.bar(region_rev, x="region", y="revenue", color="region",
                  title="📍 Revenue by Region", color_discrete_sequence=COLORS)
    fig1.update_layout(paper_bgcolor="white", plot_bgcolor="white", showlegend=False)
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    channel_rev = dff.groupby("channel")["revenue"].sum().reset_index()
    fig2 = px.pie(channel_rev, names="channel", values="revenue",
                  title="📡 Revenue by Channel", color_discrete_sequence=COLORS, hole=0.4)
    fig2.update_layout(paper_bgcolor="white")
    st.plotly_chart(fig2, use_container_width=True)

# ── Charts Row 2 ──────────────────────────────────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    dept = dff.groupby("department")[["budgeted_revenue","actual_revenue"]].sum().reset_index()
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(name="Budgeted", x=dept["department"], y=dept["budgeted_revenue"], marker_color="#4f46e5"))
    fig3.add_trace(go.Bar(name="Actual",   x=dept["department"], y=dept["actual_revenue"],   marker_color="#10b981"))
    fig3.update_layout(barmode="group", title="📊 Budget vs Actual by Department",
                       paper_bgcolor="white", plot_bgcolor="white")
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    churn_seg = dff[dff["churn_flag"]=="Yes"].groupby("customer_segment")["customer_id"].nunique().reset_index()
    churn_seg.columns = ["segment","churned_customers"]
    fig4 = px.bar(churn_seg, x="segment", y="churned_customers", color="segment",
                  title="⚠️ Churn by Customer Segment", color_discrete_sequence=COLORS)
    fig4.update_layout(paper_bgcolor="white", plot_bgcolor="white", showlegend=False)
    st.plotly_chart(fig4, use_container_width=True)

# ── Charts Row 3 ──────────────────────────────────────────────────────────────
col5, col6 = st.columns(2)

with col5:
    monthly = dff.groupby("month")["profit"].sum().reset_index()
    fig5 = px.area(monthly, x="month", y="profit", title="📅 Monthly Profit Trend",
                   color_discrete_sequence=["#4f46e5"])
    fig5.update_layout(paper_bgcolor="white", plot_bgcolor="white")
    st.plotly_chart(fig5, use_container_width=True)

with col6:
    cat_rev = dff.groupby("category")["revenue"].sum().reset_index()
    fig7 = px.bar(cat_rev, x="category", y="revenue", color="category",
                  title="🛍️ Revenue by Category", color_discrete_sequence=COLORS)
    fig7.update_layout(paper_bgcolor="white", plot_bgcolor="white", showlegend=False)
    st.plotly_chart(fig7, use_container_width=True)

st.markdown("---")

# ── AI Insights ───────────────────────────────────────────────────────────────
st.markdown('<div class="section-header"><h3 style="margin:0;">🤖 AI-Generated Executive Insights</h3></div>', unsafe_allow_html=True)

if st.button("✨ Generate AI Insights"):
    with st.spinner("Generating insights..."):
        prompt = (
            f"You are a business analyst. Write a short executive summary with 3 sections: "
            f"1. Performance Summary 2. Key Risks 3. Recommended Actions. "
            f"Data: Revenue={fmt(total_revenue)}, Profit={fmt(total_profit)}, "
            f"Variance={fmt(revenue_variance)}, Churn={churn_rate:.1f}%, "
            f"Top Region={region_rev.sort_values('revenue',ascending=False).iloc[0]['region']}, "
            f"Top Channel={channel_rev.sort_values('revenue',ascending=False).iloc[0]['channel']}. "
            f"Be concise and professional."
        )
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}", "Content-Type": "application/json"},
            json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}]}
        )
        result = response.json()
        if "choices" in result:
            st.markdown(result["choices"][0]["message"]["content"])
        else:
            st.error(f"API Error: {result}")

st.markdown("---")

# ── Task 2: Financial Narratives ──────────────────────────────────────────────
st.markdown('<div class="section-header"><h3 style="margin:0;">📋 Automated Financial Narratives & Insights</h3></div>', unsafe_allow_html=True)

dept["variance"]     = dept["actual_revenue"] - dept["budgeted_revenue"]
dept["variance_pct"] = (dept["variance"] / dept["budgeted_revenue"] * 100).round(2)
dept["status"]       = dept["variance"].apply(lambda x: "✅ Over" if x > 0 else "❌ Under")

st.markdown("**Budget vs Actual Revenue Analysis**")
st.dataframe(dept[["department","budgeted_revenue","actual_revenue","variance","variance_pct","status"]], use_container_width=True)

monthly_fin = dff.groupby("month")[["budgeted_revenue","actual_revenue"]].sum().reset_index()
fig6 = go.Figure()
fig6.add_trace(go.Scatter(x=monthly_fin["month"], y=monthly_fin["budgeted_revenue"], name="Budgeted", line=dict(color="#4f46e5", dash="dash")))
fig6.add_trace(go.Scatter(x=monthly_fin["month"], y=monthly_fin["actual_revenue"],   name="Actual",   line=dict(color="#10b981")))
fig6.update_layout(title="📈 Monthly Budgeted vs Actual Revenue", paper_bgcolor="white", plot_bgcolor="white")
st.plotly_chart(fig6, use_container_width=True)

mean_var  = dept["variance_pct"].mean()
std_var   = dept["variance_pct"].std()
anomalies = dept[abs(dept["variance_pct"] - mean_var) > 1.5 * std_var]
if len(anomalies) > 0:
    st.warning(f"⚠️ Found {len(anomalies)} anomalies in revenue performance!")
    st.dataframe(anomalies[["department","variance_pct","status"]], use_container_width=True)
else:
    st.success("✅ No major anomalies detected!")

if st.button("📄 Generate Financial Report"):
    with st.spinner("Generating financial narrative..."):
        over  = dept[dept["variance"] > 0][["department","variance_pct"]].to_string(index=False)
        under = dept[dept["variance"] < 0][["department","variance_pct"]].to_string(index=False)
        fin_prompt = (
            f"You are a financial analyst. Write a concise financial narrative report with: "
            f"1. Overall Financial Performance 2. Over-performing departments 3. Under-performing departments 4. Recommendations. "
            f"Total Budgeted: {fmt(total_budget_rev)}, Total Actual: {fmt(total_actual_rev)}, Variance: {fmt(revenue_variance)}. "
            f"Over-performers: {over}. Under-performers: {under}. Be professional and concise."
        )
        fin_response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}", "Content-Type": "application/json"},
            json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": fin_prompt}]}
        )
        fin_result = fin_response.json()
        if "choices" in fin_result:
            narrative = fin_result["choices"][0]["message"]["content"]
            st.markdown(narrative)
            st.download_button("📥 Download Report", narrative, file_name="aurora_financial_report.txt")
        else:
            st.error(f"API Error: {fin_result}")
