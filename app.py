import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Aurora Executive Dashboard", layout="wide")

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
total_revenue    = df["revenue"].sum()
total_profit     = df["profit"].sum()
total_actual_rev = df["actual_revenue"].sum()
total_budget_rev = df["budgeted_revenue"].sum()
revenue_variance = total_actual_rev - total_budget_rev
churn_rate       = (df[df["churn_flag"] == "Yes"]["customer_id"].nunique() /
                    df["customer_id"].nunique()) * 100

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("💰 Total Revenue",    f"${total_revenue:,.0f}")
col2.metric("📈 Total Profit",     f"${total_profit:,.0f}")
col3.metric("🎯 Actual Revenue",   f"${total_actual_rev:,.0f}")
col4.metric("📊 Revenue Variance", f"${revenue_variance:,.0f}",
            delta=f"{'Over' if revenue_variance > 0 else 'Under'} Budget")
col5.metric("⚠️ Churn Rate",      f"{churn_rate:.1f}%")

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

# ── Profit Trend ──────────────────────────────────────────────────────────────
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
        prompt = (
            f"You are a business analyst. Write a short executive summary with 3 sections: "
            f"1. Performance Summary 2. Key Risks 3. Recommended Actions. "
            f"Data: Revenue=${total_revenue:,.0f}, Profit=${total_profit:,.0f}, "
            f"Variance=${revenue_variance:,.0f}, Churn={churn_rate:.1f}%, "
            f"Top Region={region_rev.sort_values('revenue',ascending=False).iloc[0]['region']}, "
            f"Top Channel={channel_rev.sort_values('revenue',ascending=False).iloc[0]['channel']}. "
            f"Be concise and professional."
        )
        headers = {
            "Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}]
        }
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload
       )
        result = response.json()
        if "choices" in result:
            st.markdown(result["choices"][0]["message"]["content"])
        else:
            st.error(f"API Error: {result}")
    st.markdown("---")

# ── Task 2: Financial Narratives ──────────────────────────────────────────────
st.header("📋 Automated Financial Narratives & Insights")

# Variance Analysis
st.subheader("Budget vs Actual Revenue Analysis")
dept = df.groupby("department")[["budgeted_revenue", "actual_revenue"]].sum().reset_index()
dept["variance"] = dept["actual_revenue"] - dept["budgeted_revenue"]
dept["variance_pct"] = (dept["variance"] / dept["budgeted_revenue"] * 100).round(2)
dept["status"] = dept["variance"].apply(lambda x: "✅ Over" if x > 0 else "❌ Under")

st.dataframe(dept[["department", "budgeted_revenue", "actual_revenue", "variance", "variance_pct", "status"]], use_container_width=True)

# Monthly Analysis
st.subheader("Monthly Revenue Trend")
monthly_fin = df.groupby("month")[["budgeted_revenue", "actual_revenue"]].sum().reset_index()
monthly_fin["variance"] = monthly_fin["actual_revenue"] - monthly_fin["budgeted_revenue"]
fig6 = go.Figure()
fig6.add_trace(go.Scatter(x=monthly_fin["month"], y=monthly_fin["budgeted_revenue"], name="Budgeted", line=dict(color="blue")))
fig6.add_trace(go.Scatter(x=monthly_fin["month"], y=monthly_fin["actual_revenue"], name="Actual", line=dict(color="green")))
fig6.update_layout(title="Monthly Budgeted vs Actual Revenue")
st.plotly_chart(fig6, use_container_width=True)

# Anomaly Detection
st.subheader("⚠️ Anomaly Detection")
mean_var = dept["variance_pct"].mean()
std_var = dept["variance_pct"].std()
anomalies = dept[abs(dept["variance_pct"] - mean_var) > 1.5 * std_var]
if len(anomalies) > 0:
    st.warning(f"Found {len(anomalies)} anomalies in revenue performance!")
    st.dataframe(anomalies[["department", "variance_pct", "status"]], use_container_width=True)
else:
    st.success("No major anomalies detected!")

# AI Financial Narrative
st.subheader("🤖 AI-Generated Financial Narrative")
if st.button("Generate Financial Report"):
    with st.spinner("Generating financial narrative..."):
        over = dept[dept["variance"] > 0][["department", "variance_pct"]].to_string(index=False)
        under = dept[dept["variance"] < 0][["department", "variance_pct"]].to_string(index=False)
        fin_prompt = (
            f"You are a financial analyst. Write a concise financial narrative report with: "
            f"1. Overall Financial Performance 2. Over-performing departments 3. Under-performing departments 4. Recommendations. "
            f"Total Budgeted: ${total_budget_rev:,.0f}, Total Actual: ${total_actual_rev:,.0f}, "
            f"Variance: ${revenue_variance:,.0f}. "
            f"Over-performers: {over}. Under-performers: {under}. "
            f"Be professional and concise."
        )
        fin_headers = {
            "Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}",
            "Content-Type": "application/json"
        }
        fin_payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": fin_prompt}]
        }
        fin_response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=fin_headers,
            json=fin_payload
        )
        fin_result = fin_response.json()
        if "choices" in fin_result:
            narrative = fin_result["choices"][0]["message"]["content"]
            st.markdown(narrative)
            st.download_button("📥 Download Report", narrative, file_name="aurora_financial_report.txt")
