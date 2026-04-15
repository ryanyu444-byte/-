#!/usr/bin/env python3
import json
import os
from datetime import datetime

def load_rank_data(filepath):
    """加载排名数据"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)



def compare_ranks(old_data, new_data):
    """对比两个时间点的排名数据"""
    comparison = {}
    
    # 创建关键词到排名的映射
    old_ranks = {}
    for result in old_data['results']:
        old_ranks[result['keyword']] = result['rank']
    
    new_ranks = {}
    for result in new_data['results']:
        new_ranks[result['keyword']] = result['rank']
    
    # 对比每个关键词
    for keyword in old_ranks:
        if keyword in new_ranks:
            old_rank = old_ranks[keyword]
            new_rank = new_ranks[keyword]
            
            change = old_rank - new_rank  # 正数表示排名上升，负数表示下降
            trend = "上升" if change > 0 else "下降" if change < 0 else "稳定"
            
            # 确定状态
            if change > 0:
                status = "🟢 改善"
            elif change < 0:
                status = "🔴 下降"
            else:
                status = "🟡 保持"
            
            comparison[keyword] = {
                'old_rank': old_rank,
                'new_rank': new_rank,
                'change': change,
                'trend': trend,
                'status': status
            }
    
    return comparison

def generate_report(comparison, old_time, new_time):
    """生成对比报告"""
    report = f"""# 亚马逊关键词排名对比报告

## 📊 对比摘要

**对比时间**: {old_time} → {new_time}
**监控ASIN**: B0G61JM8L6
**对比基准**: 昨天16:07 vs 今天20:00

## 📈 排名变化概览

| 关键词 | 昨天排名 | 今天排名 | 变化 | 趋势 | 状态 |
|--------|----------|----------|------|------|------|
"""
    
    for keyword, data in comparison.items():
        report += f"| **{keyword}** | 第{data['old_rank']}位 | 第{data['new_rank']}位 | {data['change']:+d}位 | {data['trend']} | {data['status']} |\n"
    
    report += """
## 🔍 详细分析

"""
    
    for keyword, data in comparison.items():
        report += f"### **{keyword}**\n"
        report += f"- **昨天排名**: 第{data['old_rank']}位\n"
        report += f"- **今天排名**: 第{data['new_rank']}位\n"
        report += f"- **变化**: {data['change']:+d}位 ({data['trend']})\n"
        report += f"- **状态**: {data['status']}\n\n"
        
        # 添加分析建议
        if data['change'] > 0:
            report += f"  **✅ 积极信号**: 排名上升{abs(data['change'])}位，表现良好\n"
        elif data['change'] < 0:
            report += f"  **⚠️ 关注点**: 排名下降{abs(data['change'])}位，需要关注\n"
        else:
            report += f"  **📊 稳定**: 排名保持不变\n"
        
        # 添加具体建议
        if "bra pads inserts" in keyword:
            report += f"  **💡 建议**: 这是核心关键词，需要重点关注\n"
        elif "sport" in keyword:
            report += f"  **💡 建议**: 运动场景关键词，可考虑增加运动相关优化\n"
        elif "swimsuit" in keyword:
            report += f"  **💡 建议**: 泳装场景关键词，注意季节性因素\n"
        
        report += "\n"
    
    # 总体趋势分析
    report += "## 📊 总体趋势分析\n\n"
    
    improvements = sum(1 for data in comparison.values() if data['change'] > 0)
    declines = sum(1 for data in comparison.values() if data['change'] < 0)
    stable = sum(1 for data in comparison.values() if data['change'] == 0)
    
    report += f"**改善关键词**: {improvements}个\n"
    report += f"**下降关键词**: {declines}个\n"
    report += f"**稳定关键词**: {stable}个\n\n"
    
    if improvements > declines:
        report += "**✅ 总体趋势**: 积极向好，多数关键词排名有所改善\n"
    elif declines > improvements:
        report += "**⚠️ 总体趋势**: 需要关注，多数关键词排名下降\n"
    else:
        report += "**📊 总体趋势**: 基本稳定，变化不大\n"
    
    # 建议部分
    report += """
## 🎯 优化建议

### 短期行动 (1-3天)
"""
    
    for keyword, data in comparison.items():
        if data['change'] < -2:  # 下降超过2位
            report += f"1. **{keyword}**: 检查Listing优化，考虑调整关键词密度\n"
    
    report += """
### 中期目标 (1-2周)
1. **核心突破**: 将至少1个关键词推进到第一页 (前16名)
2. **稳定排名**: 保持核心关键词在第二页前部位置
3. **趋势监控**: 持续监控排名变化，及时调整策略

### 重点关注
1. **bra pads inserts**: 核心关键词，需要稳定在较好位置
2. **排名波动**: 关注下降超过3位的关键词
3. **竞争分析**: 观察竞争对手的排名变化
"""
    
    # 技术状态
    report += f"""
## 🔧 监控系统状态

| 项目 | 状态 | 说明 |
|------|------|------|
| **数据采集** | ✅ 正常 | 成功获取所有关键词排名 |
| **对比分析** | ✅ 完成 | 与昨天数据对比完成 |
| **趋势识别** | ✅ 正常 | 识别出排名变化趋势 |
| **报告生成** | ✅ 完成 | 本报告已生成 |

---

**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**对比基准**: 昨天16:07 vs 今天20:00
**数据来源**: 亚马逊美国站搜索结果
**监控系统**: 亚马逊关键词排名监控 v1.1.0
"""
    
    return report

def main():
    # 文件路径
    old_file = "B0G61JM8L6_rank_2026-03-23_16-07.json"
    new_file = "B0G61JM8L6_rank_2026-03-24_20-00.json"
    
    # 检查文件是否存在
    if not os.path.exists(old_file):
        print(f"错误: 旧数据文件 {old_file} 不存在")
        return
    
    if not os.path.exists(new_file):
        print(f"错误: 新数据文件 {new_file} 不存在")
        return
    
    # 加载数据
    old_data = load_rank_data(old_file)
    new_data = load_rank_data(new_file)
    
    # 提取时间信息
    old_time = old_data.get('check_time', '2026-03-23 16:07')
    new_time = new_data.get('check_time', '2026-03-24 20:00')
    
    # 对比排名
    comparison = compare_ranks(old_data, new_data)
    
    # 生成报告
    report = generate_report(comparison, old_time, new_time)
    
    # 保存报告
    report_filename = f"amazon_rank_comparison_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.md"
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"对比报告已保存到: {report_filename}")
    
    # 同时生成简版文本报告
    text_report = f"""亚马逊关键词排名对比报告
对比时间: {old_time} → {new_time}
ASIN: B0G61JM8L6

排名变化概览:
"""
    
    for keyword, data in comparison.items():
        change_str = f"+{data['change']}" if data['change'] > 0 else str(data['change'])
        text_report += f"{keyword}: 第{data['old_rank']}位 → 第{data['new_rank']}位 ({change_str}位)\n"
    
    text_report += f"""
总体趋势: {sum(1 for data in comparison.values() if data['change'] > 0)}个改善, 
          {sum(1 for data in comparison.values() if data['change'] < 0)}个下降, 
          {sum(1 for data in comparison.values() if data['change'] == 0)}个稳定

报告详情请查看: {report_filename}
"""
    
    text_filename = f"amazon_rank_comparison_{datetime.now().strftime('%Y-%m-%d_%H-%M')}_summary.txt"
    with open(text_filename, 'w', encoding='utf-8') as f:
        f.write(text_report)
    
    print(f"简版报告已保存到: {text_filename}")
    print("\n" + text_report)

if __name__ == "__main__":
    main()