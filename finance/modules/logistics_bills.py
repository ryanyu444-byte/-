# coding=utf-8
"""物流账单 — 登记发货记录和物流费用"""

import streamlit as st
import pandas as pd
from datetime import date
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from finance.database import init_db, query, execute, next_bill_no

init_db()

CARRIERS = ["安君快船", "快船国际", "UPS", "FedEx", "DHL", "其他"]
WAREHOUSES = ["HGR6", "ABE8", "FWA4", "ONT8", "LAX9", "BFI4", "其他"]


def show():
    st.header("🚚 物流账单")

    tab1, tab2 = st.tabs(["📝 登记发货", "📋 物流记录"])

    with tab1:
        _add_logistics_form()
    with tab2:
        _logistics_list()


def _add_logistics_form():
    with st.form("logistics_form"):
        col1, col2 = st.columns(2)

        with col1:
            bill_date = st.date_input("发货日期", value=date.today())
            carrier = st.selectbox("物流商", CARRIERS)
            tracking_no = st.text_input("运单号", placeholder="如：ANJU20260415001")
            warehouse = st.selectbox("目标仓库", WAREHOUSES)

        with col2:
            boxes = st.number_input("箱数", min_value=1, value=2, step=1)
            weight_kg = st.number_input("重量（kg）", min_value=0.0, value=20.0, step=0.5)
            amount_usd = st.number_input("物流费用（美元）", min_value=0.0, value=0.0, step=1.0)
            amount_cny = st.number_input("物流费用（人民币）", min_value=0.0, value=0.0, step=10.0)
            pay_status = st.selectbox("付款状态", ["未付款", "已付款"])

        note = st.text_input("备注（如：B0G61JM8L6 补货 6箱）")
        submitted = st.form_submit_button("✅ 登记发货", use_container_width=True, type="primary")

        if submitted:
            bill_no = next_bill_no("LOG")
            execute(
                """INSERT INTO logistics_bills
                   (bill_no, bill_date, carrier, tracking_no, warehouse, boxes, weight_kg,
                    amount_usd, amount_cny, pay_status, note)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (bill_no, str(bill_date), carrier, tracking_no, warehouse, boxes, weight_kg,
                 amount_usd, amount_cny, pay_status, note)
            )
            cost_str = f"${amount_usd:.2f}" if amount_usd else f"¥{amount_cny:.0f}"
            st.success(f"✅ {bill_no} 登记成功！{carrier} → {warehouse}，费用 {cost_str}")
            st.rerun()


def _logistics_list():
    rows = query("""
        SELECT bill_no, bill_date, carrier, tracking_no, warehouse, boxes, weight_kg,
               amount_usd, amount_cny, pay_status, note
        FROM logistics_bills ORDER BY bill_date DESC, id DESC
    """)

    if not rows:
        st.info("暂无物流记录")
        return

    df = pd.DataFrame(rows)
    df.columns = ["单号", "日期", "物流商", "运单号", "仓库", "箱数", "重量(kg)",
                  "费用(USD)", "费用(CNY)", "付款状态", "备注"]

    col1, col2, col3 = st.columns(3)
    col1.metric("发货次数", len(df))
    col2.metric("总费用(USD)", f"${df['费用(USD)'].sum():,.2f}")
    col3.metric("总费用(CNY)", f"¥{df['费用(CNY)'].sum():,.0f}")

    st.dataframe(df, use_container_width=True, hide_index=True)

    csv = df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button("📥 导出 CSV", csv, "物流账单.csv", "text/csv")
