# coding=utf-8
"""
亚马逊业务财务管理系统 — 主入口

功能模块：
  工厂账单  | 物流账单 | 成本核算 | 月度利润 | 广告分析
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from finance.database import init_db
from finance.modules import factory_bills, logistics_bills, cost_calculator, monthly_profit, ad_analysis

st.set_page_config(
    page_title="Ryan 亚马逊财务系统",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

# ─── 侧边栏导航 ─────────────────────────────────────────

with st.sidebar:
    st.markdown("## 💼 财务管理系统")
    st.caption("Ryan Yu · 亚马逊硅胶胸垫")
    st.divider()

    page = st.radio(
        "选择模块",
        options=["🏠 首页", "🏭 工厂账单", "🚚 物流账单", "💰 成本核算", "📈 月度利润", "📣 广告分析"],
        label_visibility="collapsed"
    )

    st.divider()
    st.caption("F号：B0G61JM8L6")
    st.caption("N号：B0CTFHB5J5")

# ─── 页面路由 ────────────────────────────────────────────

if page == "🏠 首页":
    st.title("💼 亚马逊业务财务管理系统")

    col1, col2, col3 = st.columns(3)

    from finance.database import query
    factory_total = query("SELECT COALESCE(SUM(amount+freight),0) as total FROM factory_bills WHERE pay_status!='已付款'")
    logistics_total = query("SELECT COALESCE(SUM(amount_cny),0) as total FROM logistics_bills WHERE pay_status='未付款'")
    months = query("SELECT COUNT(DISTINCT year_month) as cnt FROM amazon_sales")

    col1.metric("🔴 工厂未付款", f"¥{factory_total[0]['total']:,.0f}" if factory_total else "¥0")
    col2.metric("🟡 物流未付款", f"¥{logistics_total[0]['total']:,.0f}" if logistics_total else "¥0")
    col3.metric("📅 已录入月份", f"{months[0]['cnt']} 个月" if months else "0 个月")

    st.divider()
    st.markdown("""
    ### 快速操作
    | 模块 | 用途 | 频率 |
    |------|------|------|
    | 🏭 工厂账单 | 登记每次采购订单 | 每次进货时 |
    | 🚚 物流账单 | 记录发货到亚马逊仓库的运费 | 每次发货时 |
    | 💰 成本核算 | 设置各 SKU 的出厂价、FBA费等参数 | 成本变化时 |
    | 📈 月度利润 | 录入亚马逊结算数据，查看当月盈亏 | 每月底 |
    | 📣 广告分析 | 上传广告报告，分析 ACoS / ROAS | 每周 |
    """)

elif page == "🏭 工厂账单":
    factory_bills.show()

elif page == "🚚 物流账单":
    logistics_bills.show()

elif page == "💰 成本核算":
    cost_calculator.show()

elif page == "📈 月度利润":
    monthly_profit.show()

elif page == "📣 广告分析":
    ad_analysis.show()
