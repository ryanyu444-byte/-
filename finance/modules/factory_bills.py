# coding=utf-8
"""工厂账单 — 登记采购单、查看历史、标记付款"""

import streamlit as st
import pandas as pd
from datetime import date, datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from finance.database import init_db, query, execute, next_bill_no

init_db()


def show():
    st.header("🏭 工厂账单")

    tab1, tab2 = st.tabs(["📝 新增账单", "📋 账单列表"])

    with tab1:
        _add_bill_form()

    with tab2:
        _bill_list()


def _add_bill_form():
    with st.form("factory_bill_form"):
        col1, col2 = st.columns(2)

        with col1:
            bill_date = st.date_input("账单日期", value=date.today())
            factory = st.selectbox(
                "工厂名称",
                ["安君工厂", "其他工厂"],
                index=0
            )
            product = st.text_input("产品名称", placeholder="如：拷边按摩三角胸垫")
            sku = st.text_input("SKU", placeholder="如：F1102-S")

        with col2:
            qty = st.number_input("数量（件）", min_value=1, value=100, step=10)
            unit_price = st.number_input("单价（元）", min_value=0.0, value=2.42, step=0.01, format="%.2f")
            freight = st.number_input("国内运费（元）", min_value=0.0, value=0.0, step=10.0)
            pay_status = st.selectbox("付款状态", ["未付款", "已付款", "部分付款"])

        note = st.text_input("备注")
        submitted = st.form_submit_button("✅ 登记账单", use_container_width=True, type="primary")

        if submitted:
            if not product:
                st.error("请填写产品名称")
                return

            amount = qty * unit_price
            bill_no = next_bill_no("FAC")

            execute(
                """INSERT INTO factory_bills
                   (bill_no, bill_date, factory, product, sku, qty, unit_price, amount, freight, pay_status, note)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (bill_no, str(bill_date), factory, product, sku, qty, unit_price, amount, freight, pay_status, note)
            )
            st.success(f"✅ 账单 {bill_no} 登记成功！金额：¥{amount + freight:,.2f}")
            st.rerun()


def _bill_list():
    rows = query("""
        SELECT bill_no, bill_date, factory, product, sku, qty, unit_price, amount, freight,
               (amount + freight) AS total, pay_status, note
        FROM factory_bills ORDER BY bill_date DESC, id DESC
    """)

    if not rows:
        st.info("暂无账单记录")
        return

    df = pd.DataFrame(rows)
    df.columns = ["账单编号", "日期", "工厂", "产品", "SKU", "数量", "单价(¥)", "货款(¥)", "运费(¥)", "合计(¥)", "付款状态", "备注"]

    # 汇总
    col1, col2, col3 = st.columns(3)
    col1.metric("账单总数", len(df))
    col2.metric("总金额", f"¥{df['合计(¥)'].sum():,.0f}")
    col3.metric("未付款", f"¥{df[df['付款状态']=='未付款']['合计(¥)'].sum():,.0f}")

    # 付款状态颜色
    def highlight_status(val):
        colors = {"未付款": "background-color: #ffe0e0", "已付款": "background-color: #e0ffe0", "部分付款": "background-color: #fff3cd"}
        return colors.get(val, "")

    st.dataframe(
        df.style.applymap(highlight_status, subset=["付款状态"]),
        use_container_width=True,
        hide_index=True
    )

    # 标记付款
    st.divider()
    st.subheader("标记已付款")
    unpaid = [r["bill_no"] for r in rows if r["pay_status"] != "已付款"]
    if unpaid:
        selected = st.selectbox("选择账单", unpaid)
        if st.button("✅ 标记为已付款"):
            execute(
                "UPDATE factory_bills SET pay_status='已付款', pay_date=? WHERE bill_no=?",
                (str(date.today()), selected)
            )
            st.success(f"{selected} 已标记为已付款")
            st.rerun()

    # 导出
    csv = df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button("📥 导出 CSV", csv, "工厂账单.csv", "text/csv")
