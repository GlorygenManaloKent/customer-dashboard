import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Customer Analytics Dashboard", layout="wide")

st.title("📊 Customer Analytics Dashboard (RFM + Churn)")

# -----------------------------
# Load dataset
# -----------------------------
@st.cache_data
def load_data():
    df = pd.read_excel("Online Retail CLEANED Data.xlsx")
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    return df

df = load_data()

# -----------------------------
# Build RFM table
# -----------------------------
reference_date = df['InvoiceDate'].max()

rfm = df.groupby('CustomerID').agg({
    'InvoiceDate': lambda x: (reference_date - x.max()).days,
    'InvoiceNo': 'nunique',
    'Revenue': 'sum'
}).reset_index()

rfm.columns = ['CustomerID', 'Recency', 'Frequency', 'Monetary']

# -----------------------------
# RFM scoring
# -----------------------------
def segment_customer(score):
    if score >= 13:
        return "Champions"
    elif score >= 10:
        return "Loyal"
    elif score >= 8:
        return "Potential Loyalist"
    elif score >= 6:
        return "Needs Attention"
    else:
        return "At Risk"

rfm['R_Score'] = pd.qcut(rfm['Recency'].rank(method='first'), 5, labels=[5,4,3,2,1]).astype(int)
rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 5, labels=[1,2,3,4,5]).astype(int)
rfm['M_Score'] = pd.qcut(rfm['Monetary'].rank(method='first'), 5, labels=[1,2,3,4,5]).astype(int)

rfm['RFM_Score'] = rfm['R_Score'] + rfm['F_Score'] + rfm['M_Score']
rfm['Segment'] = rfm['RFM_Score'].apply(segment_customer)

# -----------------------------
# Churn flag
# -----------------------------
rfm['Churn'] = (rfm['Recency'] > 90).astype(int)

# -----------------------------
# Sidebar filters
# -----------------------------
st.sidebar.header("Filters")

segment = st.sidebar.selectbox(
    "Segment",
    ['All'] + sorted(rfm['Segment'].unique())
)

churn = st.sidebar.selectbox(
    "Churn",
    ['All', 'Active', 'Churned']
)

# -----------------------------
# Apply filters
# -----------------------------
filtered = rfm.copy()

if segment != 'All':
    filtered = filtered[filtered['Segment'] == segment]

if churn == 'Active':
    filtered = filtered[filtered['Churn'] == 0]
elif churn == 'Churned':
    filtered = filtered[filtered['Churn'] == 1]

# -----------------------------
# Charts
# -----------------------------
st.subheader("Segment Distribution")
seg_counts = filtered['Segment'].value_counts().reset_index()
seg_counts.columns = ['Segment', 'Count']
st.plotly_chart(px.bar(seg_counts, x='Segment', y='Count'))

st.subheader("Churn Distribution")
churn_counts = filtered['Churn'].value_counts().reset_index()
churn_counts.columns = ['Churn', 'Count']
st.plotly_chart(px.bar(churn_counts, x='Churn', y='Count'))

st.subheader("Recency vs Monetary")
st.plotly_chart(px.scatter(
    filtered,
    x='Recency',
    y='Monetary',
    color='Segment',
    size='Frequency',
    hover_name='CustomerID'
))

st.subheader("Frequency Distribution")
st.plotly_chart(px.histogram(
    filtered,
    x='Frequency',
    nbins=20
))
