# coding=utf-8
"""月度利润核算 — 录入销售数据，自动计算当月盈亏"""

import streamlit as st
import pandas as pd
from datetime import date
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from finance.database import init_db, query, execute

init_db()


def show():
    st.header("📈 月度利润核算")

    tab1, tab2, tab3 = st.tabs(["📝 录入销售数据", "💸 录入费用", "📊 利润报告"])

    with tab1:
        _input_sales()
    with tab2:
        _input_expenses()
    with tab3:
        _profit_report()


def _input_sales():
    st.subheader("录入亚马逊销售数据")
    st.caption("从亚马逊卖家后台下载「结算报告」后手动填写，或上传报告文件")

    col1, col2 = st.columns(2)
    year_month = col1.text_input("月份", value=date.today().strftime("%Y-%m"), placeholder="2026-04")
    account = col2.selectbox("账号", ["F号", "N号"])

    # 获取该月已有数据
    existing = {r["sku"]: r for r in query(
        "SELECT * FROM amazon_sales WHERE year_month=? AND account=?",
        (year_month, account)
    )}

    skus = query("SELECT sku, product_name FROM product_costs ORDER BY sku")
    if not skus:
        st.warning("请先在「成本核算」页配置 SKU 成本")
        return

    with st.form("sales_input"):
        rows_data = []
        for s in skus:
            sku = s["sku"]
            prev = existing.get(sku, {})
            st.markdown(f"**{sku} — {s['product_name']}**")
            cols = st.columns(6)
            sold = cols[0].number_input("销量", value=int(prev.get("units_sold", 0)), step=1, key=f"sold_{sku}")
            returned = cols[1].number_input("退货", value=int(prev.get("units_returned", 0)), step=1, key=f"ret_{sku}")
            rev = cols[2].number_input("销售额($)", value=float(prev.get("revenue_usd", 0)), step=1.0, key=f"rev_{sku}", format="%.2f")
            fba = cols[3].number_input("FBA费($)", value=float(prev.get("fba_fees", 0)), step=1.0, key=f"fba_{sku}", format="%.2f")
            ref = cols[4].number_input("佣金($)", value=float(prev.get("referral", 0)), step=1.0, key=f"ref_{sku}", format="%.2f")
            net = cols[5].number_input("到账($)", value=float(prev.get("net_proceed", 0)), step=1.0, key=f"net_{sku}", format="%.2f")
            rows_data.append((sku, sold, returned, rev, fba, ref, net))

        ad_total = st.number_input("广告总费用($)", value=0.0, step=1.0, format="%.2f")
        exchange = st.number_input("当月汇率", value=7.2, step=0.01, format="%.2f")

        if st.form_submit_button("💾 保存销售数据", use_container_width=True, type="primary"):
            for r in rows_data:
                sku, sold, ret, rev, fba, ref, net = r
                # 按销量比例分摊广告费
                total_sold = sum(x[1] for x in rows_data) or 1
                ad_share = ad_total * (sold / total_sold)

                execute("""
                    INSERT INTO amazon_sales
                    (year_month, account, sku, units_sold, units_returned, revenue_usd, fba_fees, referral, ad_spend, net_proceed, exchange_rate)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(year_month, account, sku) DO UPDATE SET
                        units_sold=excluded.units_sold,
                        units_returned=excluded.units_returned,
                        revenue_usd=excluded.revenue_usd,
                        fba_fees=excluded.fba_fees,
                        referral=excluded.referral,
                        ad_spend=excluded.ad_spend,
                        net_proceed=excluded.net_proceed,
                        exchange_rate=excluded.exchange_rate
                """, (year_month, account, sku, sold, ret, rev, fba, ref, ad_share, net, exchange))
            st.success(f"✅ {year_month} {account} 销售数据已保存")
            st.rerun()


def _input_expenses():
    st.subheader("登记其他费用")

    with st.form("expense_form"):
        col1, col2 = st.columns(2)
        exp_date = col1.date_input("日期", value=date.today())
        account = col2.selectbox("账号", ["F号", "N号", "共用"])

        category = st.selectbox("费用类型", [
            "广告费", "FBA仓储费", "退款损失", "平台服务费",
            "头程物流", "采购货款", "包装材料", "认证/合规", "软件工具", "杂费"
        ])
        col3, col4 = st.columns(2)
        amount_usd = col3.number_input("金额（美元）", value=0.0, step=1.0, format="%.2f")
        amount_cny = col4.number_input("金额（人民币）", value=0.0, step=10.0, format="%.0f")
        note = st.text_input("备注")

        if st.form_submit_button("✅ 登记费用", use_container_width=True, type="primary"):
            execute(
                "INSERT INTO expenses (date, category, amount_usd, amount_cny, account, note) VALUES (?,?,?,?,?,?)",
                (str(exp_date), category, amount_usd, amount_cny, account, note)
            )
            st.success("费用已登记")
            st.rerun()

    # 近期费用
    recent = query("SELECT date, category, account, amount_usd, amount_cny, note FROM expenses ORDER BY date DESC LIMIT 20")
    if recent:
        st.dataframe(pd.DataFrame(recent), use_container_width=True, hide_index=True)


def _profit_report():
    st.subheader("月度利润报告")

    # 选择月份
    months = query("SELECT DISTINCT year_month FROM amazon_sales ORDER BY year_month DESC")
    if not months:
        st.info("请先录入销售数据")
        return

    month_options = [r["year_month"] for r in months]
    selected_month = st.selectbox("选择月份", month_options)
    exchange_rate = st.number_input("汇率（USD→CNY）", value=7.2, step=0.01)

    # 销售数据
    sales = query("SELECT * FROM amazon_sales WHERE year_month=?", (selected_month,))
    costs = {r["sku"]: r for r in query("SELECT * FROM product_costs")}

    if not sales:
        st.warning("该月暂无销售数据")
        return

    report_rows = []
    total_revenue = 0
    total_cogs_cny = 0
    total_net = 0
    total_ad = 0
    total_fba = 0
    total_ref = 0

    for s in sales:
        sku = s["sku"]
        c = costs.get(sku, {})
        units = s["units_sold"] - s["units_returned"]
        rev = s["revenue_usd"]
        net = s["net_proceed"]
        ad = s["ad_spend"]
        fba = s["fba_fees"]
        ref = s["referral"]

        # COGS
        fp = c.get("factory_price", 0)
        fpu = c.get("freight_per_unit", 0)
        cogs_per_unit = fp + fpu
        total_cogs = cogs_per_unit * units

        gross_profit_usd = net - (total_cogs / exchange_rate) - ad
        gross_profit_cny = gross_profit_usd * exchange_rate

        report_rows.append({
            "月份": selected_month,
            "账号": s["account"],
            "SKU": sku,
            "销量": units,
            "销售额($)": round(rev, 2),
            "到账($)": round(net, 2),
            "广告($)": round(ad, 2),
            "货款(¥)": round(total_cogs, 0),
            "毛利润(¥)": round(gross_profit_cny, 0),
        })

        total_revenue += rev
        total_cogs_cny += total_cogs
        total_net += net
        total_ad += ad
        total_fba += fba
        total_ref += ref

    df = pd.DataFrame(report_rows)

    # 关键指标
    total_profit_cny = (total_net - total_ad) * exchange_rate - total_cogs_cny

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("总销售额", f"${total_revenue:,.0f}")
    col2.metric("总到账", f"${total_net:,.0f}")
    col3.metric("广告费", f"${total_ad:,.0f}")
    col4.metric("🎯 净利润", f"¥{total_profit_cny:,.0f}",
                delta=f"{total_profit_cny/total_revenue/exchange_rate*100:.1f}% 利润率" if total_revenue else None)

    st.divider()

    # 成本拆解
    col1, col2, col3 = st.columns(3)
    col1.metric("货款(¥)", f"¥{total_cogs_cny:,.0f}")
    col2.metric("FBA费", f"${total_fba:,.0f}")
    col3.metric("平台佣金", f"${total_ref:,.0f}")

    st.dataframe(df, use_container_width=True, hide_index=True)

    # 费用汇总
    exp = query(
        "SELECT category, SUM(amount_usd) as usd, SUM(amount_cny) as cny FROM expenses "
        "WHERE date LIKE ? GROUP BY category",
        (f"{selected_month}%",)
    )
    if exp:
        st.subheader("其他费用明细")
        st.dataframe(pd.DataFrame(exp), use_container_width=True, hide_index=True)

    csv = df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button("📥 导出月度报告", csv, f"{selected_month}_利润报告.csv", "text/csv")
