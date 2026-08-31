import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# 頁面配置
st.set_page_config(
    page_title="喵視角銷售分析儀表板",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# 資料載入函數 (使用 Streamlit 快取)
@st.cache_data
def load_data(file_path: str):
    xls = pd.ExcelFile(file_path)
    df_orders = pd.read_excel(xls, sheet_name="訂單")
    df_returns = pd.read_excel(xls, sheet_name="退貨")
    df_people = pd.read_excel(xls, sheet_name="人員")

    # 日期格式處理
    df_orders["訂單日期"] = pd.to_datetime(df_orders["訂單日期"])
    df_orders["年份"] = df_orders["訂單日期"].dt.year
    df_orders["年月"] = df_orders["訂單日期"].dt.to_period("M").astype(str)

    return df_orders, df_returns, df_people


# 載入資料
data_dir = os.path.join(os.path.dirname(__file__), "data")
excel_path = os.path.join(data_dir, "銷售分析表.xlsx")
logo_path = os.path.join(data_dir, "logo61ss.png")

if os.path.exists(excel_path):
    df_orders, df_returns, df_people = load_data(excel_path)
else:
    st.error(f"找不到資料檔案：{excel_path}，請確認檔案已放置於 data 資料夾中。")
    st.stop()

# 側邊欄設計
with st.sidebar:
    if os.path.exists(logo_path):
        st.image(logo_path, width="stretch")

    st.title("🔍 篩選條件")

    # 區域篩選
    all_regions = sorted(df_orders["區域"].unique().tolist())
    selected_regions = st.multiselect(
        "選擇區域", options=all_regions, default=all_regions
    )

    # 類別篩選
    all_categories = sorted(df_orders["類別"].unique().tolist())
    selected_categories = st.multiselect(
        "選擇產品類別", options=all_categories, default=all_categories
    )

    # 年份篩選
    all_years = sorted(df_orders["年份"].unique().tolist())
    selected_years = st.multiselect(
        "選擇年份", options=all_years, default=all_years
    )

# 資料過濾
filtered_df = df_orders[
    (df_orders["區域"].isin(selected_regions))
    & (df_orders["類別"].isin(selected_categories))
    & (df_orders["年份"].isin(selected_years))
]

# 主要區域標題
st.title("📈 喵視角銷售分析儀表板")
st.markdown("---")

# 關鍵指標 (KPI Cards)
col1, col2, col3, col4 = st.columns(4)

total_sales = filtered_df["銷售額"].sum()
total_profit = filtered_df["利潤"].sum()
total_orders = filtered_df["訂單ID"].nunique()
avg_discount = filtered_df["折扣"].mean() * 100

with col1:
    st.metric("總銷售額", f"${total_sales:,.2f}")
with col2:
    st.metric("總利潤", f"${total_profit:,.2f}")
with col3:
    st.metric("總訂單數", f"{total_orders:,} 筆")
with col4:
    st.metric("平均折扣", f"{avg_discount:.1f}%")

st.markdown("---")

# 圖表展示區 - 第一排
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("📅 月度銷售額與利潤趨勢")
    monthly_summary = (
        filtered_df.groupby("年月")[["銷售額", "利潤"]].sum().reset_index()
    )

    fig_trend = go.Figure()
    fig_trend.add_trace(
        go.Scatter(
            x=monthly_summary["年月"],
            y=monthly_summary["銷售額"],
            mode="lines+markers",
            name="銷售額",
            line=dict(color="#1f77b4", width=2),
        )
    )
    fig_trend.add_trace(
        go.Scatter(
            x=monthly_summary["年月"],
            y=monthly_summary["利潤"],
            mode="lines+markers",
            name="利潤",
            line=dict(color="#2ca02c", width=2),
        )
    )
    fig_trend.update_layout(
        xaxis_title="年月", yaxis_title="金額", hovermode="x unified"
    )
    st.plotly_chart(fig_trend, width="stretch")

with chart_col2:
    st.subheader("📦 各產品類別銷售佔比")
    cat_summary = filtered_df.groupby("類別")["銷售額"].sum().reset_index()
    fig_pie = px.pie(
        cat_summary,
        values="銷售額",
        names="類別",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig_pie.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig_pie, width="stretch")

# 圖表展示區 - 第二排
chart_col3, chart_col4 = st.columns(2)

with chart_col3:
    st.subheader("🗺️ 各區域銷售額比較")
    region_summary = (
        filtered_df.groupby("區域")["銷售額"].sum().reset_index()
    )
    region_summary = region_summary.sort_values(by="銷售額", ascending=True)
    fig_region = px.bar(
        region_summary,
        x="銷售額",
        y="區域",
        orientation="h",
        color="銷售額",
        color_continuous_scale="Viridis",
    )
    st.plotly_chart(fig_region, width="stretch")

with chart_col4:
    st.subheader("🏷️ 前 10 大熱銷產品子類別")
    subcat_summary = (
        filtered_df.groupby("子類別")["銷售額"]
        .sum()
        .nlargest(10)
        .reset_index()
    )
    fig_subcat = px.bar(
        subcat_summary,
        x="子類別",
        y="銷售額",
        color="銷售額",
        color_continuous_scale="Blues",
    )
    st.plotly_chart(fig_subcat, width="stretch")

# 明細資料表檢視
st.markdown("---")
st.subheader("📋 銷售明細資料夾")
with st.expander("點擊展開觀看詳細數據表"):
    st.dataframe(
        filtered_df[
            [
                "訂單ID",
                "訂單日期",
                "區域",
                "客戶名稱",
                "類別",
                "子類別",
                "產品名稱",
                "銷售額",
                "數量",
                "利潤",
            ]
        ],
        width="stretch",
    )