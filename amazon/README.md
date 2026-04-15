# Amazon 工具集

Ryan 的亚马逊业务相关脚本。

## 产品信息

| 账号 | ASIN | 产品 |
|------|------|------|
| F 号 | B0G61JM8L6 | 硅胶胸垫 |
| N 号 | B0CTFHB5J5 | 硅胶胸垫 |

市场：美国站（amazon.com）

## 脚本说明

- `amazon_rank_monitor_fixed.py` — 关键词排名监控（主力脚本，修复了503错误）
- `amazon_rank_monitor.py` — 关键词排名监控（原版）
- `compare_ranks.py` — 排名对比分析

## 主要监控关键词

```
sticky bra
adhesive bra
strapless bra
backless bra
nipple cover
bra inserts
silicone bra
```

## 运行方式

```bash
python amazon/amazon_rank_monitor_fixed.py
```

输出：JSON 格式排名数据，存到 `output/` 目录
