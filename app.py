import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Aurora Executive Dashboard", layout="wide")

# ── API Setup ─────────────────────────────────────────────────────────────────
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.0-flash")

# ── Load Data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_excel("aurora_full_dataset.xlsx")
    df["transaction_date"] = pd.to_datetime(df["transaction_date"])
    return df

df = load_data()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🏢 Aurora Retail & Digital Services")
st.subheader("AI-Powered Executive Dashboard")
st.markdown("---")

# ── KPI Cards ─────────────────────────────────────────────────────────────────
total_revenue     = df["revenue"].sum()
total_profit      = df["profit"].sum()
total_actual_rev  = df["actual_revenue"].sum()
total_budget_rev  = df["budgeted_revenue"].sum()
revenue_variance  = total_actual_rev - total_budget_rev
churn_rate        = (df[df["churn_flag"] == "Yes"]["customer_id"].nunique() /
                     df["customer_id"].nunique()) * 100

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("💰 Total Revenue",      f"${total_revenue:,.0f}")
col2.metric("📈 Total Profit",       f"${total_profit:,.0f}")
col3.metric("🎯 Actual Revenue",     f"${total_actual_rev:,.0f}")
col4.metric("📊 Revenue Variance",   f"${revenue_variance:,.0f}",
            delta=f"{'Over' if revenue_variance > 0 else 'Under'} Budget")
col5.metric("⚠️ Churn Rate",        f"{churn_rate:.1f}%")

st.markdown("---")

# ── Charts Row 1 ──────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("Revenue by Region")
    region_rev = df.groupby("region")["revenue"].sum().reset_index()
    fig1 = px.bar(region_rev, x="region", y="revenue",
                  color="region", title="Total Revenue by Region")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Revenue by Channel")
    channel_rev = df.groupby("channel")["revenue"].sum().reset_index()
    fig2 = px.pie(channel_rev, names="channel", values="revenue",
                  title="Revenue Split by Channel")
    st.plotly_chart(fig2, use_container_width=True)

# ── Charts Row 2 ──────────────────────────────────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    st.subheader("Budget vs Actual Revenue by Department")
    dept = df.groupby("department")[["budgeted_revenue", "actual_revenue"]].sum().reset_index()
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(name="Budgeted", x=dept["department"], y=dept["budgeted_revenue"]))
    fig3.add_trace(go.Bar(name="Actual",   x=dept["department"], y=dept["actual_revenue"]))
    fig3.update_layout(barmode="group", title="Budget vs Actual by Department")
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.subheader("Churn by Customer Segment")
    churn_seg = df[df["churn_flag"] == "Yes"].groupby("customer_segment")["customer_id"].nunique().reset_index()
    churn_seg.columns = ["segment", "churned_customers"]
    fig4 = px.bar(churn_seg, x="segment", y="churned_customers",
                  color="segment", title="Churned Customers by Segment")
    st.plotly_chart(fig4, use_container_width=True)

# ── Profit Trend ───────────────────────────────────────────────────────────────
st.subheader("📅 Monthly Profit Trend")
df["month"] = df["transaction_date"].dt.to_period("M").astype(str)
monthly = df.groupby("month")["profit"].sum().reset_index()
fig5 = px.line(monthly, x="month", y="profit", title="Profit Over Time", markers=True)
st.plotly_chart(fig5, use_container_width=True)

st.markdown("---")

# ── AI Insights ───────────────────────────────────────────────────────────────
st.subheader("🤖 AI-Generated Executive Insights")

if st.button("Generate AI Insights"):
    with st.spinner("Generating insights..."):
        summary = f"""
        You are a senior business analyst. Based on this Aurora Retail data summary, 
        write a concise executive report with 3 sections:
        1. Performance Summary
        2. Key Risks & Opportunities  
        3. Recommended Executive Actions

        Data:
        - Total Revenue: ${total_revenue:,.0f}
        - Total Profit: ${total_profit:,.0f}
        - Actual vs Budget Revenue Variance: ${revenue_variance:,.0f}
        - Customer Churn Rate: {churn_rate:.1f}%
        - Top Region by Revenue: {region_rev.sort_values('revenue', ascending=False).iloc[0]['region']}
        - Top Channel by Revenue: {channel_rev.sort_values('revenue', ascending=False).iloc[0]['channel']}

        Write in professional, jargon-free language suitable for C-suite executives.
        """
        response = model.generate_content(summary)
        st.markdown(response.text)
