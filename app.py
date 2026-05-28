import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

st.set_page_config(page_title="Aurora Executive Dashboard", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #f4f6fb; }
    .main .block-container { padding-top: 1rem; }
    .kpi-card {
        background: white;
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        border-top: 4px solid #2563eb;
        margin-bottom: 12px;
    }
    .kpi-label {
        font-size: 12px;
        font-weight: 700;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .kpi-value {
        font-size: 30px;
        font-weight: 800;
        color: #1e3a8a;
        margin: 6px 0 4px 0;
    }
    .kpi-sub {
        font-size: 12px;
        font-weight: 600;
        color: #10b981;
    }
    .kpi-sub-red { color: #ef4444; }
    .header-banner {
        background: linear-gradient(120deg, #1e3a8a, #2563eb);
        padding: 22px 30px;
        border-radius: 14px;
        margin-bottom: 22px;
        color: white;
    }
    [data-testid="stSidebar"] { background-color: #1e3a8a; }
    [data-testid="stSidebar"] * { color: white !important; }
    [data-testid="stSidebar"] .stSelectbox > div > div { background-color: #1e40af; }
    .stButton > button {
        background-color: #2563eb;
        color: white;
        font-weight: 700;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        font-size: 14px;
    }
    .stButton > button:hover { background-color: #1d4ed8; }
</style>
""", unsafe_allow_html=True)

def fmt(n):
    if abs(n) >= 1_000_000_000:
        return f"${n/1_000_000_000:.1f}B"
    elif abs(n) >= 1_000_000:
        return f"${n/1_000_000:.1f}M"
    elif abs(n) >= 1_000:
        return f"${n/1_000:.1f}K"
    return f"${n:,.0f}"

@st.cache_data
def load_data():
    df = pd.read_excel("aurora_full_dataset.xlsx")
    df["transaction_date"] = pd.to_datetime(df["transaction_date"])
    df["month"] = df["transaction_date"].dt.to_period("M").astype(str)
    return df

df = load_data()

# Sidebar
st.sidebar.markdown("## 🏢 Aurora Analytics")
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Filters")

regions  = ["All"] + sorted(df["region"].dropna().unique().tolist())
channels = ["All"] + sorted(df["channel"].dropna().unique().tolist())
segments = ["All"] + sorted(df["customer_segment"].dropna().unique().tolist())
months   = sorted(df["month"].unique().tolist())

sel_region  = st.sidebar.selectbox("🌍 Region", regions)
sel_channel = st.sidebar.selectbox("📡 Channel", channels)
sel_segment = st.sidebar.selectbox("👥 Segment", segments)
sel_dates   = st.sidebar.select_slider("📅 Month Range", options=months, value=(months[0], months[-1]))

st.sidebar.markdown("---")
st.sidebar.markdown("Powered by Groq AI")

# Filter
dff = df.copy()
if sel_region  != "All": dff = dff[dff["region"] == sel_region]
if sel_channel != "All": dff = dff[dff["channel"] == sel_channel]
if sel_segment != "All": dff = dff[dff["customer_segment"] == sel_segment]
dff = dff[(dff["month"] >= sel_dates[0]) & (dff["month"] <= sel_dates[1])]

# Header
st.markdown("""
<div class="header-banner">
    <h1 style="margin:0; font-size:26px; font-weight:800;">🏢 Aurora Retail & Digital Services</h1>
    <p style="margin:6px 0 0 0; font-size:14px; opacity:0.85;">AI-Powered Executive Dashboard</p>
</div>""", unsafe_allow_html=True)

# KPIs
total_revenue    = dff["revenue"].sum()
total_profit     = dff["profit"].sum()
total_actual     = dff["actual_revenue"].sum()
total_budget     = dff["budgeted_revenue"].sum()
variance         = total_actual - total_budget
churn_rate       = (dff[dff["churn_flag"]=="Yes"]["customer_id"].nunique() / dff["customer_id"].nunique() * 100) if dff["customer_id"].nunique() > 0 else 0
profit_margin    = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
total_customers  = dff["customer_id"].nunique()

k1,k2,k3,k4,k5,k6 = st.columns(6)

with k1:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">💰 Total Revenue</div>
        <div class="kpi-value">{fmt(total_revenue)}</div>
        <div class="kpi-sub">All Regions & Channels</div>
    </div>""", unsafe_allow_html=True)

with k2:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">📈 Total Profit</div>
        <div class="kpi-value">{fmt(total_profit)}</div>
        <div class="kpi-sub">Margin: {profit_margin:.1f}%</div>
    </div>""", unsafe_allow_html=True)

with k3:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">🎯 Actual Revenue</div>
        <div class="kpi-value">{fmt(total_actual)}</div>
        <div class="kpi-sub">Budget: {fmt(total_budget)}</div>
    </div>""", unsafe_allow_html=True)

with k4:
    color = "kpi-sub" if variance >= 0 else "kpi-sub kpi-sub-red"
    sign  = "▲ Over Budget" if variance >= 0 else "▼ Under Budget"
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">📊 Variance</div>
        <div class="kpi-value">{fmt(variance)}</div>
        <div class="{color}">{sign}</div>
    </div>""", unsafe_allow_html=True)

with k5:
    c = "kpi-sub-red" if churn_rate > 20 else "kpi-sub"
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">⚠️ Churn Rate</div>
        <div class="kpi-value">{churn_rate:.1f}%</div>
        <div class="{c}">{'⚠ High Risk' if churn_rate > 20 else '✓ Acceptable'}</div>
    </div>""", unsafe_allow_html=True)

with k6:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">👥 Customers</div>
        <div class="kpi-value">{total_customers:,}</div>
        <div class="kpi-sub">Unique Customers</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Chart style
CLR  = ["#2563eb","#7c3aed","#0891b2","#059669","#dc2626","#d97706"]
FONT = dict(family="Arial", size=13, color="#1e3a8a")
AXIS = dict(tickfont=dict(size=12, color="#1e3a8a", family="Arial"),
            title_font=dict(size=13, color="#1e3a8a", family="Arial"),
            showgrid=True, gridcolor="#e5e7eb")
BASE = dict(paper_bgcolor="white", plot_bgcolor="white",
            font=FONT, title_font=dict(size=15, color="#1e3a8a", family="Arial Black"),
            margin=dict(t=50, b=40, l=40, r=20))

# Row 1
c1, c2 = st.columns(2)

with c1:
    region_rev = dff.groupby("region")["revenue"].sum().reset_index().sort_values("revenue", ascending=False)
    fig1 = px.bar(region_rev, x="region", y="revenue", color="region",
                  title="📍 Revenue by Region", color_discrete_sequence=CLR,
                  text=[fmt(v) for v in region_rev["revenue"]])
    fig1.update_traces(textposition="outside", textfont=dict(size=13, color="#1e3a8a", family="Arial Black"))
    fig1.update_layout(**BASE, showlegend=False, xaxis=AXIS, yaxis=dict(**AXIS, tickformat="$,.0f"))
    st.plotly_chart(fig1, use_container_width=True)

with c2:
    channel_rev = dff.groupby("channel")["revenue"].sum().reset_index()
    fig2 = px.pie(channel_rev, names="channel", values="revenue",
                  title="📡 Revenue by Channel", color_discrete_sequence=CLR, hole=0.45)
    fig2.update_traces(textfont=dict(size=13, color="white", family="Arial Black"),
                       textinfo="percent+label", pull=[0.03]*len(channel_rev))
    fig2.update_layout(paper_bgcolor="white", font=FONT,
                       title_font=dict(size=15, color="#1e3a8a", family="Arial Black"),
                       legend=dict(font=dict(size=12, color="#1e3a8a")),
                       margin=dict(t=50, b=20))
    st.plotly_chart(fig2, use_container_width=True)

# Row 2
c3, c4 = st.columns(2)

with c3:
    dept = dff.groupby("department")[["budgeted_revenue","actual_revenue"]].sum().reset_index()
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(name="Budgeted", x=dept["department"], y=dept["budgeted_revenue"],
                          marker_color="#2563eb",
                          text=[fmt(v) for v in dept["budgeted_revenue"]],
                          textposition="outside",
                          textfont=dict(size=12, color="#1e3a8a", family="Arial Black")))
    fig3.add_trace(go.Bar(name="Actual", x=dept["department"], y=dept["actual_revenue"],
                          marker_color="#059669",
                          text=[fmt(v) for v in dept["actual_revenue"]],
                          textposition="outside",
                          textfont=dict(size=12, color="#1e3a8a", family="Arial Black")))
    fig3.update_layout(barmode="group", title="📊 Budget vs Actual by Department",
                       **BASE, xaxis=AXIS, yaxis=dict(**AXIS, tickformat="$,.0f"),
                       legend=dict(font=dict(size=12, color="#1e3a8a")))
    st.plotly_chart(fig3, use_container_width=True)

with c4:
    churn_seg = dff[dff["churn_flag"]=="Yes"].groupby("customer_segment")["customer_id"].nunique().reset_index()
    churn_seg.columns = ["segment","churned"]
    fig4 = px.bar(churn_seg, x="segment", y="churned", color="segment",
                  title="⚠️ Churn by Segment", color_discrete_sequence=CLR,
                  text="churned")
    fig4.update_traces(textposition="outside", textfont=dict(size=13, color="#1e3a8a", family="Arial Black"))
    fig4.update_layout(**BASE, showlegend=False, xaxis=AXIS, yaxis=dict(**AXIS))
    st.plotly_chart(fig4, use_container_width=True)

# Row 3
c5, c6 = st.columns(2)

with c5:
    monthly = dff.groupby("month")["profit"].sum().reset_index()
    fig5 = px.area(monthly, x="month", y="profit", title="📅 Monthly Profit Trend",
                   color_discrete_sequence=["#2563eb"])
    fig5.update_layout(**BASE, xaxis=dict(**AXIS, tickangle=45),
                       yaxis=dict(**AXIS, tickformat="$,.0f"))
    st.plotly_chart(fig5, use_container_width=True)

with c6:
    cat_rev = dff.groupby("category")["revenue"].sum().reset_index().sort_values("revenue", ascending=False)
    fig6 = px.bar(cat_rev, x="category", y="revenue", color="category",
                  title="🛍️ Revenue by Category", color_discrete_sequence=CLR,
                  text=[fmt(v) for v in cat_rev["revenue"]])
    fig6.update_traces(textposition="outside", textfont=dict(size=13, color="#1e3a8a", family="Arial Black"))
    fig6.update_layout(**BASE, showlegend=False, xaxis=AXIS, yaxis=dict(**AXIS, tickformat="$,.0f"))
    st.plotly_chart(fig6, use_container_width=True)

st.markdown("---")

# AI Insights
st.markdown("### 🤖 AI-Generated Executive Insights")
if st.button("✨ Generate AI Insights"):
    with st.spinner("Generating insights..."):
        prompt = (
            f"You are a business analyst. Write a short executive summary with 3 sections: "
            f"1. Performance Summary 2. Key Risks 3. Recommended Actions. "
            f"Data: Revenue={fmt(total_revenue)}, Profit={fmt(total_profit)}, "
            f"Variance={fmt(variance)}, Churn={churn_rate:.1f}%, "
            f"Top Region={region_rev.iloc[0]['region']}, "
            f"Top Channel={channel_rev.sort_values('revenue',ascending=False).iloc[0]['channel']}. "
            f"Be concise and professional."
        )
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}", "Content-Type": "application/json"},
            json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}]}
        ).json()
        if "choices" in res:
            st.markdown(res["choices"][0]["message"]["content"])
        else:
            st.error(f"API Error: {res}")

st.markdown("---")

# Task 2: Financial Narratives
st.markdown("### 📋 Automated Financial Narratives & Insights")

dept["variance"]     = dept["actual_revenue"] - dept["budgeted_revenue"]
dept["variance_pct"] = (dept["variance"] / dept["budgeted_revenue"] * 100).round(2)
dept["status"]       = dept["variance"].apply(lambda x: "✅ Over" if x > 0 else "❌ Under")
st.dataframe(dept[["department","budgeted_revenue","actual_revenue","variance","variance_pct","status"]], use_container_width=True)

monthly_fin = dff.groupby("month")[["budgeted_revenue","actual_revenue"]].sum().reset_index()
fig7 = go.Figure()
fig7.add_trace(go.Scatter(x=monthly_fin["month"], y=monthly_fin["budgeted_revenue"],
                          name="Budgeted", line=dict(color="#2563eb", dash="dash", width=2)))
fig7.add_trace(go.Scatter(x=monthly_fin["month"], y=monthly_fin["actual_revenue"],
                          name="Actual", line=dict(color="#059669", width=2)))
fig7.update_layout(title="📈 Monthly Budgeted vs Actual Revenue", **BASE,
                   xaxis=dict(**AXIS, tickangle=45), yaxis=dict(**AXIS, tickformat="$,.0f"),
                   legend=dict(font=dict(size=12, color="#1e3a8a")))
st.plotly_chart(fig7, use_container_width=True)

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
        over  = dept[dept["variance"]>0][["department","variance_pct"]].to_string(index=False)
        under = dept[dept["variance"]<0][["department","variance_pct"]].to_string(index=False)
        fin_prompt = (
            f"You are a financial analyst. Write a concise financial narrative with: "
            f"1. Overall Financial Performance 2. Over-performing departments 3. Under-performing departments 4. Recommendations. "
            f"Budgeted: {fmt(total_budget)}, Actual: {fmt(total_actual)}, Variance: {fmt(variance)}. "
            f"Over: {over}. Under: {under}. Be professional and concise."
        )
        fin_res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}", "Content-Type": "application/json"},
            json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": fin_prompt}]}
        ).json()
        if "choices" in fin_res:
            narrative = fin_res["choices"][0]["message"]["content"]
            st.markdown(narrative)
            st.download_button("📥 Download Report", narrative, file_name="aurora_financial_report.txt")
        else:
            st.error(f"API Error: {fin_res}")
