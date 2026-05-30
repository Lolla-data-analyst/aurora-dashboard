import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

st.set_page_config(page_title="Aurora Executive Dashboard", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #f0f4f8; }
    .main .block-container { padding-top: 1rem; }
    .kpi-card {
        background: white;
        border-radius: 10px;
        padding: 16px;
        box-shadow: 0 1px 6px rgba(0,0,0,0.08);
        border-top: 4px solid #1d4ed8;
        margin-bottom: 12px;
        min-height: 110px;
    }
    .kpi-label {
        font-size: 11px;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .kpi-value {
        font-size: 26px;
        font-weight: 800;
        color: #1e3a5f;
        margin: 6px 0 4px 0;
    }
    .kpi-sub { font-size: 11px; font-weight: 600; color: #16a34a; }
    .kpi-sub-red { font-size: 11px; font-weight: 600; color: #dc2626; }
    .header-banner {
        background: linear-gradient(120deg, #1e3a5f 0%, #1d4ed8 100%);
        padding: 20px 28px;
        border-radius: 12px;
        margin-bottom: 20px;
        color: white;
    }
    .section-title {
        font-size: 20px;
        font-weight: 800;
        color: #1e3a5f;
        padding: 10px 0 5px 0;
        border-left: 4px solid #1d4ed8;
        padding-left: 12px;
        margin: 10px 0;
    }
    .sub-title {
        font-size: 14px;
        font-weight: 700;
        color: #1e3a5f;
        margin: 8px 0;
    }
    [data-testid="stSidebar"] { background-color: #1e3a5f; }
    [data-testid="stSidebar"] * { color: white !important; }
    .stButton > button {
        background-color: #1d4ed8;
        color: white;
        font-weight: 700;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
    }
</style>
""", unsafe_allow_html=True)

C1 = "#1e3a5f"
C2 = "#1d4ed8"
C3 = "#93c5fd"

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
    df["month"] = df["transaction_date"].dt.strftime("%Y-%m")
    return df

df = load_data()

# Sidebar
st.sidebar.markdown("## 🏢 Aurora Analytics")
st.sidebar.markdown("---")
st.sidebar.markdown("### Filters")

regions  = ["All"] + sorted(df["region"].dropna().unique().tolist())
channels = ["All"] + sorted(df["channel"].dropna().unique().tolist())
segments = ["All"] + sorted(df["customer_segment"].dropna().unique().tolist())
months   = sorted(df["month"].unique().tolist())

sel_region  = st.sidebar.selectbox("🌍 Region", regions)
sel_channel = st.sidebar.selectbox("📡 Channel", channels)
sel_segment = st.sidebar.selectbox("👥 Segment", segments)
sel_dates   = st.sidebar.select_slider("📅 Month Range", options=months,
                                        value=(months[0], months[-1]))
st.sidebar.markdown("---")
st.sidebar.markdown("Powered by Groq AI")

# Filter data
dff = df.copy()
if sel_region  != "All": dff = dff[dff["region"] == sel_region]
if sel_channel != "All": dff = dff[dff["channel"] == sel_channel]
if sel_segment != "All": dff = dff[dff["customer_segment"] == sel_segment]
dff = dff[(dff["month"] >= sel_dates[0]) & (dff["month"] <= sel_dates[1])]

# Header
st.markdown("""
<div class="header-banner">
    <h1 style="margin:0;font-size:24px;font-weight:800;color:white;">🏢 Aurora Retail & Digital Services</h1>
    <p style="margin:5px 0 0 0;font-size:13px;opacity:0.85;color:white;">AI-Powered Executive Dashboard</p>
</div>""", unsafe_allow_html=True)

# KPIs
total_revenue   = dff["revenue"].sum()
total_profit    = dff["profit"].sum()
total_actual    = dff["actual_revenue"].sum()
total_budget    = dff["budgeted_revenue"].sum()
variance        = total_actual - total_budget
churn_rate      = (dff[dff["churn_flag"]=="Yes"]["customer_id"].nunique() /
                   dff["customer_id"].nunique() * 100) if dff["customer_id"].nunique() > 0 else 0
profit_margin   = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
total_customers = dff["customer_id"].nunique()

k1, k2, k3, k4, k5, k6 = st.columns(6)

with k1:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">💰 Total Revenue</div>
        <div class="kpi-value">{fmt(total_revenue)}</div>
        <div class="kpi-sub">All Regions</div>
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
    v_color = "kpi-sub" if variance >= 0 else "kpi-sub-red"
    v_text  = "▲ Over Budget" if variance >= 0 else "▼ Under Budget"
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">📊 Variance</div>
        <div class="kpi-value">{fmt(variance)}</div>
        <div class="{v_color}">{v_text}</div>
    </div>""", unsafe_allow_html=True)

with k5:
    c_color = "kpi-sub-red" if churn_rate > 20 else "kpi-sub"
    c_text  = "⚠ High Risk" if churn_rate > 20 else "✓ Acceptable"
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">⚠️ Churn Rate</div>
        <div class="kpi-value">{churn_rate:.1f}%</div>
        <div class="{c_color}">{c_text}</div>
    </div>""", unsafe_allow_html=True)

with k6:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-label">👥 Customers</div>
        <div class="kpi-value">{total_customers:,}</div>
        <div class="kpi-sub">Unique Customers</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Chart styles
FONT  = dict(family="Arial", size=12, color="#1e3a5f")
XAXIS = dict(tickfont=dict(size=11, color="#1e3a5f"), showgrid=False, tickangle=-30)
YAXIS = dict(tickfont=dict(size=11, color="#1e3a5f"), showgrid=True,
             gridcolor="#e2e8f0", tickformat="$,.0f")
MARG  = dict(t=50, b=60, l=50, r=20)

# Row 1
c1, c2 = st.columns(2)

with c1:
    region_rev = dff.groupby("region")["revenue"].sum().reset_index()
    region_rev = region_rev.sort_values("revenue", ascending=False)
    fig1 = px.bar(region_rev, x="region", y="revenue",
                  color_discrete_sequence=[C2],
                  text=[fmt(v) for v in region_rev["revenue"]],
                  title="📍 Revenue by Region")
    fig1.update_traces(textposition="outside",
                       textfont=dict(size=11, color="#1e3a5f", family="Arial Black"),
                       marker_line_width=0)
    fig1.update_layout(font=FONT, paper_bgcolor="white", plot_bgcolor="white",
                       title_font=dict(size=14, color="#1e3a5f", family="Arial Black"),
                       xaxis=XAXIS, yaxis=YAXIS, margin=MARG, height=380,
                       showlegend=False)
    st.plotly_chart(fig1, use_container_width=True)

with c2:
    channel_rev = dff.groupby("channel")["revenue"].sum().reset_index()
    fig2 = px.pie(channel_rev, names="channel", values="revenue",
                  color_discrete_sequence=[C1, C2, C3],
                  hole=0.45, title="📡 Revenue by Channel")
    fig2.update_traces(textfont=dict(size=12, color="white", family="Arial Black"),
                       textinfo="percent+label",
                       pull=[0.03] * len(channel_rev))
    fig2.update_layout(font=FONT, paper_bgcolor="white",
                       title_font=dict(size=14, color="#1e3a5f", family="Arial Black"),
                       legend=dict(font=dict(size=11, color="#1e3a5f")),
                       margin=dict(t=50, b=20, l=20, r=20), height=380)
    st.plotly_chart(fig2, use_container_width=True)

# Row 2
c3, c4 = st.columns(2)

with c3:
    dept = dff.groupby("department")[["budgeted_revenue", "actual_revenue"]].sum().reset_index()
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        name="Budgeted", x=dept["department"], y=dept["budgeted_revenue"],
        marker_color=C1,
        text=[fmt(v) for v in dept["budgeted_revenue"]],
        textposition="outside",
        textfont=dict(size=9, color="#1e3a5f", family="Arial Black")
    ))
    fig3.add_trace(go.Bar(
        name="Actual", x=dept["department"], y=dept["actual_revenue"],
        marker_color=C2,
        text=[fmt(v) for v in dept["actual_revenue"]],
        textposition="outside",
        textfont=dict(size=9, color="#1e3a5f", family="Arial Black")
    ))
    fig3.update_layout(
        barmode="group",
        title=dict(text="📊 Budget vs Actual by Department",
                   font=dict(size=14, color="#1e3a5f", family="Arial Black")),
        font=FONT, paper_bgcolor="white", plot_bgcolor="white",
        xaxis=XAXIS, yaxis=YAXIS, margin=MARG, height=380,
        legend=dict(font=dict(size=11, color="#1e3a5f")),
        bargap=0.2, bargroupgap=0.05
    )
    st.plotly_chart(fig3, use_container_width=True)

with c4:
    churn_seg = dff[dff["churn_flag"]=="Yes"].groupby("customer_segment")["customer_id"].nunique().reset_index()
    churn_seg.columns = ["segment", "churned"]
    fig4 = px.bar(churn_seg, x="segment", y="churned",
                  color_discrete_sequence=[C2],
                  text="churned", title="⚠️ Churn by Segment")
    fig4.update_traces(textposition="outside",
                       textfont=dict(size=12, color="#1e3a5f", family="Arial Black"),
                       marker_line_width=0)
    fig4.update_layout(
        font=FONT, paper_bgcolor="white", plot_bgcolor="white",
        title_font=dict(size=14, color="#1e3a5f", family="Arial Black"),
        xaxis=XAXIS,
        yaxis=dict(tickfont=dict(size=11, color="#1e3a5f"),
                   showgrid=True, gridcolor="#e2e8f0"),
        margin=MARG, height=380, showlegend=False
    )
    st.plotly_chart(fig4, use_container_width=True)

# Row 3
c5, c6 = st.columns(2)

with c5:
    monthly = dff.groupby("month")["profit"].sum().reset_index()
    monthly = monthly.sort_values("month")
    fig5 = go.Figure()
    fig5.add_trace(go.Scatter(
        x=monthly["month"], y=monthly["profit"],
        mode="lines+markers",
        line=dict(color=C2, width=2),
        marker=dict(color=C2, size=4),
        fill="tozeroy", fillcolor="rgba(29,78,216,0.1)"
    ))
    fig5.update_layout(
        title=dict(text="📅 Monthly Profit Trend",
                   font=dict(size=14, color="#1e3a5f", family="Arial Black")),
        font=FONT, paper_bgcolor="white", plot_bgcolor="white",
        xaxis=dict(tickfont=dict(size=10, color="#1e3a5f"),
                   showgrid=False, tickangle=-45, nticks=15),
        yaxis=YAXIS, margin=MARG, height=380
    )
    st.plotly_chart(fig5, use_container_width=True)

with c6:
    cat_rev = dff.groupby("category")["revenue"].sum().reset_index()
    cat_rev = cat_rev.sort_values("revenue", ascending=False)
    fig6 = px.bar(cat_rev, x="category", y="revenue",
                  color="category",
                  color_discrete_sequence=[C1, C2, C3],
                  text=[fmt(v) for v in cat_rev["revenue"]],
                  title="🛍️ Revenue by Category")
    fig6.update_traces(textposition="outside",
                       textfont=dict(size=12, color="#1e3a5f", family="Arial Black"),
                       marker_line_width=0)
    fig6.update_layout(
        font=FONT, paper_bgcolor="white", plot_bgcolor="white",
        title_font=dict(size=14, color="#1e3a5f", family="Arial Black"),
        xaxis=XAXIS, yaxis=YAXIS, margin=MARG, height=380, showlegend=False
    )
    st.plotly_chart(fig6, use_container_width=True)

st.markdown("---")

# AI Insights
st.markdown('<div class="section-title">🤖 AI-Generated Executive Insights</div>', unsafe_allow_html=True)

if st.button("✨ Generate AI Insights"):
    with st.spinner("Generating insights..."):
        prompt = (
            f"You are a business analyst. Write a short executive summary with 3 sections: "
            f"1. Performance Summary 2. Key Risks 3. Recommended Actions. "
            f"Data: Revenue={fmt(total_revenue)}, Profit={fmt(total_profit)}, "
            f"Variance={fmt(variance)}, Churn={churn_rate:.1f}%, "
            f"Top Region={region_rev.iloc[0]['region']}, "
            f"Top Channel={channel_rev.sort_values('revenue', ascending=False).iloc[0]['channel']}. "
            f"Be concise and professional."
        )
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}",
                     "Content-Type": "application/json"},
            json={"model": "llama-3.3-70b-versatile",
                  "messages": [{"role": "user", "content": prompt}]}
        ).json()
        if "choices" in res:
            st.markdown(res["choices"][0]["message"]["content"])
        else:
            st.error(f"API Error: {res}")

st.markdown("---")

# Task 2: Financial Narratives
st.markdown('<div class="section-title">📋 Automated Financial Narratives & Insights</div>', unsafe_allow_html=True)

dept["variance"]     = dept["actual_revenue"] - dept["budgeted_revenue"]
dept["variance_pct"] = (dept["variance"] / dept["budgeted_revenue"] * 100).round(2)
dept["status"]       = dept["variance"].apply(lambda x: "✅ Over" if x > 0 else "❌ Under")

st.markdown('<div class="sub-title">Budget vs Actual Revenue Analysis</div>', unsafe_allow_html=True)

dept_display = dept[["department","budgeted_revenue","actual_revenue","variance","variance_pct","status"]].copy()
dept_display["budgeted_revenue"] = dept_display["budgeted_revenue"].apply(fmt)
dept_display["actual_revenue"]   = dept_display["actual_revenue"].apply(fmt)
dept_display["variance"]         = dept_display["variance"].apply(fmt)
dept_display["variance_pct"]     = dept_display["variance_pct"].apply(lambda x: f"{x:.2f}%")
st.dataframe(dept_display, use_container_width=True)

monthly_fin = dff.groupby("month")[["budgeted_revenue", "actual_revenue"]].sum().reset_index()
monthly_fin = monthly_fin.sort_values("month")

fig7 = go.Figure()
fig7.add_trace(go.Scatter(x=monthly_fin["month"], y=monthly_fin["budgeted_revenue"],
                          name="Budgeted", line=dict(color=C1, dash="dash", width=2)))
fig7.add_trace(go.Scatter(x=monthly_fin["month"], y=monthly_fin["actual_revenue"],
                          name="Actual", line=dict(color=C2, width=2)))
fig7.update_layout(
    title=dict(text="📈 Monthly Budgeted vs Actual Revenue",
               font=dict(size=14, color="#1e3a5f", family="Arial Black")),
    font=FONT, paper_bgcolor="white", plot_bgcolor="white",
    xaxis=dict(tickfont=dict(size=10, color="#1e3a5f"),
               showgrid=False, tickangle=-45, nticks=15),
    yaxis=YAXIS, margin=MARG, height=380,
    legend=dict(font=dict(size=11, color="#1e3a5f"))
)
st.plotly_chart(fig7, use_container_width=True)

mean_var  = dept["variance_pct"].mean()
std_var   = dept["variance_pct"].std()
anomalies = dept[abs(dept["variance_pct"] - mean_var) > 1.5 * std_var]
if len(anomalies) > 0:
    st.warning(f"⚠️ Found {len(anomalies)} anomalies detected!")
    st.dataframe(anomalies[["department", "variance_pct", "status"]], use_container_width=True)
else:
    st.success("✅ No major anomalies detected!")

if st.button("📄 Generate Financial Report"):
    with st.spinner("Generating financial narrative..."):
        over  = dept[dept["variance"] > 0][["department", "variance_pct"]].to_string(index=False)
        under = dept[dept["variance"] < 0][["department", "variance_pct"]].to_string(index=False)
        fin_prompt = (
            f"Write a concise financial narrative with 4 sections: "
            f"1. Overall Performance 2. Over-performing departments "
            f"3. Under-performing departments 4. Recommendations. "
            f"Budgeted: {fmt(total_budget)}, Actual: {fmt(total_actual)}, "
            f"Variance: {fmt(variance)}. Over: {over}. Under: {under}."
        )
        fin_res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}",
                     "Content-Type": "application/json"},
            json={"model": "llama-3.3-70b-versatile",
                  "messages": [{"role": "user", "content": fin_prompt}]}
        ).json()
        if "choices" in fin_res:
            narrative = fin_res["choices"][0]["message"]["content"]
            st.markdown(narrative)
            st.download_button("📥 Download Report", narrative,
                               file_name="aurora_financial_report.txt")
        else:
            st.error(f"API Error: {fin_res}")
