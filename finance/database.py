# coding=utf-8
"""
财务数据库 — SQLite 存储层
所有表的创建、读写操作
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional

DB_PATH = Path(__file__).parent / "data" / "finance.db"


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """建表，幂等操作"""
    with get_conn() as conn:
        conn.executescript("""
        -- 工厂账单
        CREATE TABLE IF NOT EXISTS factory_bills (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_no     TEXT NOT NULL,           -- 账单编号 FAC-YYYYMMDD-XXX
            bill_date   TEXT NOT NULL,           -- 账单日期
            factory     TEXT NOT NULL,           -- 工厂名称
            product     TEXT NOT NULL,           -- 产品名称
            sku         TEXT,                    -- SKU
            qty         REAL NOT NULL,           -- 数量
            unit        TEXT DEFAULT '件',
            unit_price  REAL NOT NULL,           -- 单价（元）
            amount      REAL NOT NULL,           -- 总金额（元）
            freight     REAL DEFAULT 0,          -- 国内运费（元）
            pay_status  TEXT DEFAULT '未付款',   -- 未付款/已付款/部分付款
            pay_date    TEXT,                    -- 付款日期
            note        TEXT,
            created_at  TEXT DEFAULT (datetime('now','localtime'))
        );

        -- 物流账单
        CREATE TABLE IF NOT EXISTS logistics_bills (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_no     TEXT NOT NULL,
            bill_date   TEXT NOT NULL,
            carrier     TEXT NOT NULL,           -- 物流商（安君/快船/UPS等）
            tracking_no TEXT,                   -- 运单号
            warehouse   TEXT,                   -- 目标仓库（HGR6/ABE8等）
            boxes       INTEGER,                -- 箱数
            weight_kg   REAL,                   -- 重量（kg）
            amount_usd  REAL DEFAULT 0,         -- 金额（美元）
            amount_cny  REAL DEFAULT 0,         -- 金额（人民币）
            pay_status  TEXT DEFAULT '未付款',
            note        TEXT,
            created_at  TEXT DEFAULT (datetime('now','localtime'))
        );

        -- 产品成本配置（每个SKU的成本构成）
        CREATE TABLE IF NOT EXISTS product_costs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            sku             TEXT NOT NULL UNIQUE,
            product_name    TEXT NOT NULL,
            factory_price   REAL NOT NULL,      -- 出厂价（元/件）
            freight_per_unit REAL DEFAULT 0,    -- 头程物流摊销（元/件）
            fba_fee_usd     REAL DEFAULT 0,     -- FBA配送费（美元/件）
            referral_rate   REAL DEFAULT 0.15,  -- 亚马逊佣金比例
            sale_price_usd  REAL DEFAULT 0,     -- 当前售价（美元）
            exchange_rate   REAL DEFAULT 7.2,   -- 汇率
            updated_at      TEXT DEFAULT (datetime('now','localtime'))
        );

        -- 费用登记（广告/仓储/杂费等）
        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT NOT NULL,
            category    TEXT NOT NULL,          -- 广告/仓储/退款/杂费/平台费/其他
            sub_cat     TEXT,                   -- 子分类
            amount_usd  REAL DEFAULT 0,
            amount_cny  REAL DEFAULT 0,
            account     TEXT DEFAULT 'F号',     -- F号/N号/共用
            note        TEXT,
            created_at  TEXT DEFAULT (datetime('now','localtime'))
        );

        -- 亚马逊月度销售（手动录入或上传报表）
        CREATE TABLE IF NOT EXISTS amazon_sales (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            year_month  TEXT NOT NULL,          -- 2026-04
            account     TEXT NOT NULL,          -- F号/N号
            sku         TEXT NOT NULL,
            units_sold  INTEGER DEFAULT 0,
            units_returned INTEGER DEFAULT 0,
            revenue_usd REAL DEFAULT 0,        -- 销售额（美元）
            fba_fees    REAL DEFAULT 0,        -- FBA费用
            referral    REAL DEFAULT 0,        -- 亚马逊佣金
            ad_spend    REAL DEFAULT 0,        -- 广告费
            other_fees  REAL DEFAULT 0,        -- 其他费用
            net_proceed REAL DEFAULT 0,        -- 亚马逊实际打款
            exchange_rate REAL DEFAULT 7.2,
            UNIQUE(year_month, account, sku)
        );

        -- 广告数据（上传亚马逊广告报表）
        CREATE TABLE IF NOT EXISTS ad_reports (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT NOT NULL,
            account     TEXT NOT NULL,
            campaign    TEXT,                  -- 广告活动
            ad_group    TEXT,
            sku         TEXT,
            impressions INTEGER DEFAULT 0,
            clicks      INTEGER DEFAULT 0,
            spend_usd   REAL DEFAULT 0,
            sales_usd   REAL DEFAULT 0,
            orders      INTEGER DEFAULT 0,
            acos        REAL DEFAULT 0,        -- ACoS (spend/sales)
            created_at  TEXT DEFAULT (datetime('now','localtime'))
        );
        """)


# ─── 便捷查询 ─────────────────────────────────────────────

def query(sql: str, params=()) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]


def execute(sql: str, params=()) -> int:
    with get_conn() as conn:
        cur = conn.execute(sql, params)
        return cur.lastrowid


def next_bill_no(prefix: str) -> str:
    today = datetime.now().strftime("%Y%m%d")
    rows = query(
        "SELECT bill_no FROM factory_bills WHERE bill_no LIKE ? UNION "
        "SELECT bill_no FROM logistics_bills WHERE bill_no LIKE ?",
        (f"{prefix}-{today}%", f"{prefix}-{today}%")
    )
    return f"{prefix}-{today}-{len(rows)+1:03d}"
