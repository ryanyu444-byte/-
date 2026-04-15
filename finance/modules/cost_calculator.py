# coding=utf-8
"""产品成本核算 — 每个SKU的完整成本拆解和利润预测"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from finance.database import init_db, query, execute

init_db()

# 默认SKU列表（基于现有产品）
DEFAULT_SKUS = [
    {"sku": "F1101-S", "name": "6对不分小码"},
    {"sku": "F1101-L", "name": "6对不分大码"},
    {"sku": "F1102-S", "name": "3对不分小码"},
    {"sku": "F1102-L", "name": "3对不分大码"},
    {"sku": "F1103-S", "name": "3对分小码"},
    {"sku": "F1103-L", "name": "3对分大码"},
    {"sku": "F1104-S", "name": "6对分小码"},
    {"sku": "F1104-L", "name": "6对分大码"},
    {"sku": "F1105-S", "name": "3对防水小码"},
    {"sku": "F1105-L", "name": "3对防水大码"},
]


def show():
    st.header("💰 产品成本核算")

    tab1, tab2 = st.tabs(["⚙️ 成本配置", "📊 利润分析"])

    with tab1:
        _cost_config()
    with tab2:
        _profit_analysis()


def _cost_config():
    st.subheader("设置各 SKU 成本参数")

    existing = {r["sku"]: r for r in query("SELECT * FROM product_costs")}

    with st.form("cost_config_form"):
        st.markdown("**汇率设置**")
        exchange_rate = st.number_input("USD/CNY 汇率", value=7.2, step=0.01, format="%.2f")

        st.divider()
        st.markdown("**SKU 成本参数**")

        rows_data = []
        for item in DEFAULT_SKUS:
            sku = item["sku"]
            prev = existing.get(sku, {})
            st.markdown(f"**{sku} — {item['name']}**")
            cols = st.columns(5)
            fp = cols[0].number_input(f"出厂价(¥)", value=float(prev.get("factory_price", 2.42)), step=0.01, key=f"fp_{sku}", format="%.2f")
            fpu = cols[1].number_input(f"头程摊销(¥)", value=float(prev.get("freight_per_unit", 0.5)), step=0.01, key=f"fpu_{sku}", format="%.2f")
            fba = cols[2].number_input(f"FBA费($)", value=float(prev.get("fba_fee_usd", 3.5)), step=0.01, key=f"fba_{sku}", format="%.2f")
            sp = cols[3].number_input(f"售价($)", value=float(prev.get("sale_price_usd", 12.99)), step=0.01, key=f"sp_{sku}", format="%.2f")
            rr = cols[4].number_input(f"佣金%", value=float(prev.get("referral_rate", 0.15)) * 100, step=0.5, key=f"rr_{sku}", format="%.1f")
            rows_data.append((sku, item["name"], fp, fpu, fba, sp, rr / 100, exchange_rate))

        if st.form_submit_button("💾 保存成本配置", use_container_width=True, type="primary"):
            for r in rows_data:
                sku, name, fp, fpu, fba, sp, rr, er = r
                execute("""
                    INSERT INTO product_costs (sku, product_name, factory_price, freight_per_unit, fba_fee_usd, sale_price_usd, referral_rate, exchange_rate)
                    VALUES (?,?,?,?,?,?,?,?)
                    ON CONFLICT(sku) DO UPDATE SET
                        product_name=excluded.product_name,
                        factory_price=excluded.factory_price,
                        freight_per_unit=excluded.freight_per_unit,
                        fba_fee_usd=excluded.fba_fee_usd,
                        sale_price_usd=excluded.sale_price_usd,
                        referral_rate=excluded.referral_rate,
                        exchange_rate=excluded.exchange_rate,
                        updated_at=datetime('now','localtime')
                """, (sku, name, fp, fpu, fba, sp, rr, er))
            st.success("✅ 成本配置已保存")
            st.rerun()


def _profit_analysis():
    costs = query("SELECT * FROM product_costs ORDER BY sku")
    if not costs:
        st.info("请先在「成本配置」页填写各 SKU 的成本参数")
        return

    rows = []
    for c in costs:
        er = c["exchange_rate"]
        sp = c["sale_price_usd"]
        fp = c["factory_price"]
        fpu = c["freight_per_unit"]
        fba = c["fba_fee_usd"]
        rr = c["referral_rate"]

        referral = sp * rr
        cogs_cny = fp + fpu          # 采购成本（含头程）
        cogs_usd = cogs_cny / er
        total_cost_usd = cogs_usd + fba + referral
        gross_profit_usd = sp - total_cost_usd
        gross_margin = (gross_profit_usd / sp * 100) if sp else 0

        # 扣广告后（假设 ACoS 15%）
        ad_spend = sp * 0.15
        net_profit_usd = gross_profit_usd - ad_spend
        net_margin = (net_profit_usd / sp * 100) if sp else 0

        rows.append({
            "SKU": c["sku"],
            "产品": c["product_name"],
            "售价($)": sp,
            "出厂(¥)": fp,
            "头程(¥)": fpu,
            "FBA($)": fba,
            "佣金($)": round(referral, 2),
            "总成本($)": round(total_cost_usd, 2),
            "毛利($)": round(gross_profit_usd, 2),
            "毛利率%": round(gross_margin, 1),
            "广告费($)": round(ad_spend, 2),
            "净利润($)": round(net_profit_usd, 2),
            "净利率%": round(net_margin, 1),
        })

    df = pd.DataFrame(rows)

    # 颜色标注
    def color_profit(val):
        if isinstance(val, (int, float)):
            return "color: green" if val > 0 else "color: red"
        return ""

    st.dataframe(
        df.style.applymap(color_profit, subset=["毛利($)", "净利润($)", "毛利率%", "净利率%"]),
        use_container_width=True,
        hide_index=True
    )

    # 可视化
    st.divider()
    best = df.loc[df["净利率%"].idxmax()]
    worst = df.loc[df["净利率%"].idxmin()]
    col1, col2 = st.columns(2)
    col1.success(f"**利润率最高**：{best['SKU']} — {best['净利率%']}%")
    col2.warning(f"**利润率最低**：{worst['SKU']} — {worst['净利率%']}%")

    st.bar_chart(df.set_index("SKU")[["毛利率%", "净利率%"]])

    csv = df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button("📥 导出利润分析", csv, "成本利润分析.csv", "text/csv")
