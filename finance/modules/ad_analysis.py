# coding=utf-8
"""广告分析 — 上传亚马逊广告报告，分析 ACoS / ROAS / 广告效率"""

import streamlit as st
import pandas as pd
import io
import sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from finance.database import init_db, query, execute

init_db()


def show():
    st.header("📣 广告分析")

    tab1, tab2 = st.tabs(["📤 上传广告报告", "📊 广告数据看板"])

    with tab1:
        _upload_ad_report()
    with tab2:
        _ad_dashboard()


def _upload_ad_report():
    st.subheader("上传亚马逊广告报告")
    st.caption("""
    **操作步骤：**
    1. 进入亚马逊广告后台 → Campaign Manager → 报告
    2. 下载「Sponsored Products Campaign报告」（CSV格式）
    3. 上传到这里
    """)

    account = st.selectbox("账号", ["F号", "N号"])
    uploaded = st.file_uploader("上传广告报告 CSV", type=["csv"])

    if uploaded:
        try:
            df = pd.read_csv(uploaded, encoding="utf-8-sig")
            st.write("**文件预览：**")
            st.dataframe(df.head(5))

            # 尝试自动识别列名（亚马逊报告格式）
            col_map = _detect_columns(df)

            if col_map:
                st.success(f"✅ 识别到 {len(df)} 行广告数据")

                if st.button("📥 导入数据库", type="primary"):
                    _import_ad_data(df, col_map, account)
                    st.success(f"✅ 广告数据导入成功！共 {len(df)} 条记录")
                    st.rerun()
            else:
                st.warning("无法自动识别列名，请检查报告格式是否为亚马逊标准广告报告")
                st.write("**当前列名：**", list(df.columns))

        except Exception as e:
            st.error(f"读取失败：{e}")

    # 手动录入单日广告数据
    st.divider()
    st.subheader("手动录入广告数据")

    with st.form("manual_ad"):
        col1, col2 = st.columns(2)
        ad_date = col1.date_input("日期", value=date.today())
        account2 = col2.selectbox("账号", ["F号", "N号"], key="acc2")

        cols = st.columns(4)
        impressions = cols[0].number_input("曝光量", value=0, step=100)
        clicks = cols[1].number_input("点击量", value=0, step=1)
        spend = cols[2].number_input("广告花费($)", value=0.0, step=0.1, format="%.2f")
        sales = cols[3].number_input("广告销售额($)", value=0.0, step=0.1, format="%.2f")
        orders = st.number_input("广告订单数", value=0, step=1)

        if st.form_submit_button("✅ 保存广告数据", type="primary"):
            acos = (spend / sales * 100) if sales else 0
            execute("""
                INSERT INTO ad_reports (date, account, impressions, clicks, spend_usd, sales_usd, orders, acos)
                VALUES (?,?,?,?,?,?,?,?)
            """, (str(ad_date), account2, impressions, clicks, spend, sales, orders, acos))
            st.success(f"✅ 广告数据已保存，ACoS = {acos:.1f}%")
            st.rerun()


def _detect_columns(df: pd.DataFrame) -> dict:
    """自动检测亚马逊广告报告的列名"""
    cols = {c.lower().strip(): c for c in df.columns}
    mapping = {}

    # 常见亚马逊报告列名变体
    checks = {
        "date": ["date", "日期", "start date"],
        "campaign": ["campaign name", "campaign", "活动名称"],
        "impressions": ["impressions", "曝光量"],
        "clicks": ["clicks", "点击量"],
        "spend": ["spend", "cost", "花费", "广告费"],
        "sales": ["7 day total sales", "sales", "14 day total sales", "销售额"],
        "orders": ["7 day total orders", "orders", "订单数"],
    }

    for key, variants in checks.items():
        for v in variants:
            if v.lower() in cols:
                mapping[key] = cols[v.lower()]
                break

    # 需要至少 spend 和 sales 才算识别成功
    return mapping if "spend" in mapping and "sales" in mapping else {}


def _import_ad_data(df: pd.DataFrame, col_map: dict, account: str):
    for _, row in df.iterrows():
        spend = float(row.get(col_map.get("spend", ""), 0) or 0)
        sales = float(row.get(col_map.get("sales", ""), 0) or 0)
        acos = (spend / sales * 100) if sales else 0

        execute("""
            INSERT INTO ad_reports (date, account, campaign, impressions, clicks, spend_usd, sales_usd, orders, acos)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            str(row.get(col_map.get("date", ""), "")),
            account,
            str(row.get(col_map.get("campaign", ""), "")),
            int(row.get(col_map.get("impressions", ""), 0) or 0),
            int(row.get(col_map.get("clicks", ""), 0) or 0),
            spend, sales,
            int(row.get(col_map.get("orders", ""), 0) or 0),
            acos,
        ))


def _ad_dashboard():
    st.subheader("广告数据看板")

    rows = query("""
        SELECT date, account, campaign, impressions, clicks, spend_usd, sales_usd, orders,
               CASE WHEN sales_usd > 0 THEN ROUND(spend_usd/sales_usd*100, 1) ELSE 0 END as acos,
               CASE WHEN spend_usd > 0 THEN ROUND(sales_usd/spend_usd, 2) ELSE 0 END as roas,
               CASE WHEN clicks > 0 THEN ROUND(spend_usd/clicks, 2) ELSE 0 END as cpc
        FROM ad_reports ORDER BY date DESC
    """)

    if not rows:
        st.info("暂无广告数据，请上传报告或手动录入")
        return

    df = pd.DataFrame(rows)

    # 汇总指标
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("总花费", f"${df['spend_usd'].sum():,.2f}")
    col2.metric("广告销售额", f"${df['sales_usd'].sum():,.2f}")
    total_acos = df['spend_usd'].sum() / df['sales_usd'].sum() * 100 if df['sales_usd'].sum() else 0
    col3.metric("整体 ACoS", f"{total_acos:.1f}%",
                delta="良好" if total_acos < 20 else "偏高",
                delta_color="normal" if total_acos < 20 else "inverse")
    col4.metric("总点击", f"{df['clicks'].sum():,}")
    avg_cpc = df['spend_usd'].sum() / df['clicks'].sum() if df['clicks'].sum() else 0
    col5.metric("平均CPC", f"${avg_cpc:.2f}")

    st.divider()

    # 按日期趋势
    if "date" in df.columns:
        daily = df.groupby("date").agg({
            "spend_usd": "sum",
            "sales_usd": "sum",
            "clicks": "sum"
        }).reset_index()
        daily["acos"] = daily["spend_usd"] / daily["sales_usd"].replace(0, 1) * 100
        st.line_chart(daily.set_index("date")[["spend_usd", "sales_usd"]])

    # 明细表
    df_display = df.rename(columns={
        "date": "日期", "account": "账号", "campaign": "广告活动",
        "impressions": "曝光", "clicks": "点击", "spend_usd": "花费($)",
        "sales_usd": "销售额($)", "orders": "订单", "acos": "ACoS%",
        "roas": "ROAS", "cpc": "CPC($)"
    })

    def color_acos(val):
        if isinstance(val, (int, float)):
            if val < 15: return "color: green"
            if val < 25: return "color: orange"
            return "color: red"
        return ""

    st.dataframe(
        df_display.style.applymap(color_acos, subset=["ACoS%"]),
        use_container_width=True,
        hide_index=True
    )

    csv = df_display.to_csv(index=False, encoding="utf-8-sig")
    st.download_button("📥 导出广告数据", csv, "广告分析.csv", "text/csv")
