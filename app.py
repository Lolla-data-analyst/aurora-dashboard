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
        padding: 16px 18px;
        box-shadow: 0 1px 6px rgba(0,0,0,0.08);
        border-top: 4px solid #1d4ed8;
        margin-bottom: 12px;
    }
    .kpi-label {
        font-size: 11px;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .kpi-value {
        font-size: 28px;
        font-weight: 800;
        color: #1e3a5f;
        margin: 4px 0;
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
    [data-testid="stSidebar"] { background-color: #1e3a5f; }
    [data-testid="stSidebar"] * { color: white !important; }
    [data-testid="stSidebar"] .stSelectbox > div > div { background-color: #1d4ed8; }
    .stButton > button {
        background-color: #1d4ed8;
        color: white;
        font-weight: 700;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
    }
    .stButton > button:hover { background-color: #1e40af; }
</style>
""", unsafe_allow_html=True)

# Professional 3-color palette: Navy, Blue, Steel
P1 = "#1e3a5f"  # Dark navy
P2 = "#1d4ed8"  # Royal blue
P3 = "#64b5f6"  # Light blue
COLORS = [P1, P2, P3]

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

# Filter
dff = df.copy()
if sel_region  != "All": dff = dff[dff["region"] == sel_region]
if sel_channel != "All": dff = dff[dff["channel"] == sel_channel]
if sel_segment != "All": dff = dff[dff["customer_segment"] == sel_segment]
dff = dff[(dff["month"] >= sel_dates[0]) & (dff["month"] <= sel_dates[1])]

# Header
st.markdown("""
<div class="header-banner">
    <h1 style="margin:0;font-size:24px;font-weight:800;">🏢 Aurora Retail & Digital Services</h1>
    <p style="margin:5px 0 0 0;font-size:13px;opacity:0.85;">AI-Powered Executive Dashboard</p>
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

k1,k2,k3,k4,k5,k6 = st.columns(6)
cards = [
    (k1, "💰 Total Revenue",   fmt(total_revenue),  "All Regions",          "kpi-sub"),
    (k2, "📈 Total Profit",    fmt(total_profit),   f"Margin: {profit_margin:.1f}%", "kpi-sub"),
    (k3, "🎯 Actual Revenue",  fmt(total_actual),   f"Budget: {fmt(total_budget)}", "kpi-sub"),
    (k4, "📊 Variance",        fmt(variance),
         "▲ Over Budget" if variance >= 0 else "▼ Under Budget",
         "kpi-sub" if variance >= 0 else "kpi-sub-red"),
    (k5, "⚠️ Churn Rate",     f"{churn_rate:.1f}%",
         "High Risk" if churn_rate > 20 else "Acceptable",
         "kpi-sub-red" if churn_rate > 20 else "kpi-sub"),
    (k6, "👥 Customers",       f"{total_customers:,}", "Unique Customers", "kpi-sub"),
]
for col, label, value, sub, sub_class in cards:
    with col:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="{sub_class}">{sub}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Base layout for all charts
def base_layout(title):
    return dict(
        title=dict(text=title, font=dict(size=14, color="#1e3a5f", family="Arial Black")),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family="Arial", size=12, color="#1e3a5f"),
        xaxis=dict(tickfont=dict(size=11, color="#1e3a5f"),
                   title_font=dict(size=12, color="#1e3a5f"),
                   showgrid=False, tickangle=-30),
        yaxis=dict(tickfont=dict(size=11, color="#1e3a5f"),
                   title_font=dict(size=12, color="#1e3a5f"),
                   showgrid=True, gridcolor="#e2e8f0",
                   tickformat="$,.0f"),
        margin=dict(t=50, b=60, l=50, r=20),
        height=380,
        legend=dict(font=dict(size=11, color="#1e3a5f"))
    )

# Row 1
c1, c2 = st.columns(2)
with c1:
    region_rev = dff.groupby("region")["revenue"].sum().reset_index().sort_values("revenue", ascending=False)
    fig1 = px.bar(region_rev, x="region", y="revenue", color_discrete_sequence=[P2],
                  text=[fmt(v) for v in region_rev["revenue"]])
    fig1.update_traces(textposition="outside", textfont=dict(size=11, color="#1e3a5f", family="Arial Black"),
                       marker_line_width=0)
fig1.update_layout(**base_layout("📍 Revenue by Region"))
with c2:
    channel_rev = dff.groupby("channel")["revenue"].sum().reset_index()
    fig2 = px.pie(channel_rev, names="channel", values="revenue",
                  color_discrete_sequence=[P1, P2, P3], hole=0.45)
    fig2.update_traces(textfont=dict(size=12, color="white", family="Arial Black"),
                       textinfo="percent+label", pull=[0.03]*len(channel_rev))
    fig2.update_layout(paper_bgcolor="white", height=380,
                       title=dict(text="📡 Revenue by Channel",
                                  font=dict(size=14, color="#1e3a5f", family="Arial Black")),
                       legend=dict(font=dict(size=11, color="#1e3a5f")),
                       margin=dict(t=50, b=20))
    st.plotly_chart(fig2, use_container_width=True)

# Row 2
c3, c4 = st.columns(2)
with c3:
    dept = dff.groupby("department")[["budgeted_revenue","actual_revenue"]].sum().reset_index()
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(name="Budgeted", x=dept["department"], y=dept["budgeted_revenue"],
                          marker_color=P1,
                          text=[fmt(v) for v in dept["budgeted_revenue"]],
                          textposition="outside",
                          textfont=dict(size=9, color="#1e3a5f", family="Arial Black")))
    fig3.add_trace(go.Bar(name="Actual", x=dept["department"], y=dept["actual_revenue"],
                          marker_color=P2,
                          text=[fmt(v) for v in dept["actual_revenue"]],
                          textposition="outside",
                          textfont=dict(size=9, color="#1e3a5f", family="Arial Black")))
    fig3.update_layout(barmode="group",
                       **base_layout("📊 Budget vs Actual by Department"),
                            legend=dict(font=dict(size=11, color="#1e3a5f")),
                       bargap=0.2, bargroupgap=0.05)
    st.plotly_chart(fig3, use_container_width=True)

with c4:
    churn_seg = dff[dff["churn_flag"]=="Yes"].groupby("customer_segment")["customer_id"].nunique().reset_index()
    churn_seg.columns = ["segment","churned"]
    fig4 = px.bar(churn_seg, x="segment", y="churned",
                  color_discrete_sequence=[P2],
                  text="churned")
    fig4.update_traces(textposition="outside",
                       textfont=dict(size=12, color="#1e3a5f", family="Arial Black"),
                       marker_line_width=0)
    fig4.update_layout(**base_layout("⚠️ Churn by Segment"))
    st.plotly_chart(fig4, use_container_width=True)

# Row 3
c5, c6 = st.columns(2)
with c5:
    monthly = dff.groupby("month")["profit"].sum().reset_index()
    monthly = monthly.sort_values("month")
    monthly["month_label"] = monthly["month"].str[:7]
    fig5 = go.Figure()
    fig5.add_trace(go.Scatter(x=monthly["month_label"], y=monthly["profit"],
                              mode="lines+markers", line=dict(color=P2, width=2),
                              marker=dict(color=P2, size=4),
                              fill="tozeroy", fillcolor="rgba(29,78,216,0.1)"))
    layout5 = base_layout("📅 Monthly Profit Trend")
    layout5["xaxis"]["tickangle"] = -45
    layout5["xaxis"]["nticks"] = 12
    layout5["yaxis"] = dict(tickfont=dict(size=11, color="#1e3a5f"),
                            showgrid=True, gridcolor="#e2e8f0", tickformat="$,.0f")
    fig5.update_layout(**layout5)
    st.plotly_chart(fig5, use_container_width=True)

with c6:
    cat_rev = dff.groupby("category")["revenue"].sum().reset_index().sort_values("revenue", ascending=False)
    fig6 = px.bar(cat_rev, x="category", y="revenue",
                  color_discrete_sequence=[P1, P2, P3],
                  color="category",
                  text=[fmt(v) for v in cat_rev["revenue"]])
    fig6.update_traces(textposition="outside",
                       textfont=dict(size=12, color="#1e3a5f", family="Arial Black"),
                       marker_line_width=0)
    fig6.update_layout(**base_layout("🛍️ Revenue by Category"),
                       showlegend=False,
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
st.markdown("### 📋 Automated Financial Narratives & Insights")

dept["variance"]     = dept["actual_revenue"] - dept["budgeted_revenue"]
dept["variance_pct"] = (dept["variance"] / dept["budgeted_revenue"] * 100).round(2)
dept["status"]       = dept["variance"].apply(lambda x: "✅ Over" if x > 0 else "❌ Under")
st.dataframe(dept[["department","budgeted_revenue","actual_revenue",
                    "variance","variance_pct","status"]], use_container_width=True)

monthly_fin = dff.groupby("month")[["budgeted_revenue","actual_revenue"]].sum().reset_index().sort_values("month")
monthly_fin["month_label"] = monthly_fin["month"].str[:7]
fig7 = go.Figure()
fig7.add_trace(go.Scatter(x=monthly_fin["month_label"], y=monthly_fin["budgeted_revenue"],
                          name="Budgeted", line=dict(color=P1, dash="dash", width=2)))
fig7.add_trace(go.Scatter(x=monthly_fin["month_label"], y=monthly_fin["actual_revenue"],
                          name="Actual", line=dict(color=P2, width=2)))
layout7 = base_layout("📈 Monthly Budgeted vs Actual Revenue")
layout7["xaxis"]["tickangle"] = -45
layout7["xaxis"]["nticks"] = 12
layout7["yaxis"] = dict(tickfont=dict(size=11, color="#1e3a5f"),
                        showgrid=True, gridcolor="#e2e8f0", tickformat="$,.0f")
layout7["legend"] = dict(font=dict(size=11, color="#1e3a5f"))
fig7.update_layout(**layout7)
st.plotly_chart(fig7, use_container_width=True)

mean_var  = dept["variance_pct"].mean()
std_var   = dept["variance_pct"].std()
anomalies = dept[abs(dept["variance_pct"] - mean_var) > 1.5 * std_var]
if len(anomalies) > 0:
    st.warning(f"⚠️ Found {len(anomalies)} anomalies detected!")
    st.dataframe(anomalies[["department","variance_pct","status"]], use_container_width=True)
else:
    st.success("✅ No major anomalies detected!")

if st.button("📄 Generate Financial Report"):
    with st.spinner("Generating financial narrative..."):
        over  = dept[dept["variance"]>0][["department","variance_pct"]].to_string(index=False)
        under = dept[dept["variance"]<0][["department","variance_pct"]].to_string(index=False)
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
