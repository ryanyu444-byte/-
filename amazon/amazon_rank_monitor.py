#!/usr/bin/env python3
"""
亚马逊关键词排名监控脚本
监控ASIN在指定关键词下的排名情况
"""

import requests
import time
import json
import os
from datetime import datetime
from bs4 import BeautifulSoup
import re

class AmazonRankMonitor:
    def __init__(self, asin, keywords):
        """
        初始化监控器
        :param asin: 产品ASIN
        :param keywords: 关键词列表
        """
        self.asin = asin
        self.keywords = keywords
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        
    def search_keyword(self, keyword, page=1):
        """
        搜索关键词并获取页面内容
        :param keyword: 搜索关键词
        :param page: 页码
        :return: 页面HTML内容
        """
        try:
            # 构建搜索URL
            search_term = keyword.replace(' ', '+')
            url = f"https://www.amazon.com/s?k={search_term}&page={page}"
            
            # 临时禁用代理
            proxies = {
                'http': None,
                'https': None
            }
            
            response = requests.get(url, headers=self.headers, timeout=10, proxies=proxies)
            response.raise_for_status()
            
            return response.text
        except Exception as e:
            print(f"搜索关键词 '{keyword}' 时出错: {e}")
            return None
    
    def find_asin_rank(self, html, keyword):
        """
        在搜索结果中查找ASIN的排名
        :param html: 搜索结果页面HTML
        :param keyword: 搜索关键词
        :return: 排名信息字典
        """
        if not html:
            return {
                'keyword': keyword,
                'rank': None,
                'page': None,
                'position': None,
                'found': False,
                'error': '无法获取页面内容'
            }
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 查找所有产品卡片
            product_divs = soup.find_all('div', {'data-asin': True})
            
            # 在第一页搜索
            for i, div in enumerate(product_divs):
                asin_value = div.get('data-asin', '')
                if asin_value == self.asin:
                    # 计算排名位置（从1开始）
                    position = i + 1
                    page = 1  # 第一页
                    
                    # 计算页面内的位置
                    items_per_page = 16  # 亚马逊通常每页16个产品
                    if position > items_per_page:
                        page = (position - 1) // items_per_page + 1
                        position_in_page = position - (page - 1) * items_per_page
                    else:
                        position_in_page = position
                    
                    return {
                        'keyword': keyword,
                        'rank': position,
                        'page': page,
                        'position_in_page': position_in_page,
                        'found': True,
                        'error': None
                    }
            
            # 如果在第一页没找到，检查后续页面
            max_pages_to_check = 5  # 最多检查5页
            
            for page_num in range(2, max_pages_to_check + 1):
                print(f"  正在搜索第 {page_num} 页...")
                page_html = self.search_keyword(keyword, page_num)
                if not page_html:
                    break
                
                soup = BeautifulSoup(page_html, 'html.parser')
                product_divs = soup.find_all('div', {'data-asin': True})
                
                for i, div in enumerate(product_divs):
                    asin_value = div.get('data-asin', '')
                    if asin_value == self.asin:
                        # 计算总排名
                        position = (page_num - 1) * 16 + i + 1
                        return {
                            'keyword': keyword,
                            'rank': position,
                            'page': page_num,
                            'position_in_page': i + 1,
                            'found': True,
                            'error': None
                        }
                
                # 添加延迟避免请求过快
                time.sleep(1)
            
            # 如果在前5页都没找到
            return {
                'keyword': keyword,
                'rank': None,
                'page': None,
                'position': None,
                'found': False,
                'error': f'在前{max_pages_to_check}页中未找到ASIN {self.asin}'
            }
            
        except Exception as e:
            return {
                'keyword': keyword,
                'rank': None,
                'page': None,
                'position': None,
                'found': False,
                'error': f'解析页面时出错: {str(e)}'
            }
    
    def check_all_keywords(self):
        """
        检查所有关键词的排名
        :return: 排名结果列表
        """
        results = []
        print(f"开始监控ASIN: {self.asin}")
        print(f"关键词列表: {self.keywords}")
        print("-" * 50)
        
        for keyword in self.keywords:
            print(f"正在搜索关键词: '{keyword}'...")
            
            # 搜索关键词
            html = self.search_keyword(keyword)
            
            # 查找ASIN排名
            rank_info = self.find_asin_rank(html, keyword)
            results.append(rank_info)
            
            # 输出结果
            if rank_info['found']:
                print(f"  ✓ 找到! 排名: 第{rank_info['rank']}位 (第{rank_info['page']}页, 第{rank_info['position_in_page']}个)")
            else:
                print(f"  ✗ 未找到: {rank_info['error']}")
            
            # 添加延迟避免请求过快
            time.sleep(2)
        
        print("-" * 50)
        return results
    
    def save_results(self, results, filename=None):
        """
        保存结果到文件
        :param results: 排名结果
        :param filename: 文件名，默认为asin_rank_日期.json
        """
        if filename is None:
            date_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
            filename = f"{self.asin}_rank_{date_str}.json"
        
        data = {
            'asin': self.asin,
            'check_time': datetime.now().isoformat(),
            'results': results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"结果已保存到: {filename}")
        return filename
    
    def generate_report(self, results):
        """
        生成文本报告
        :param results: 排名结果
        :return: 报告文本
        """
        report_lines = []
        report_lines.append(f"亚马逊关键词排名监控报告")
        report_lines.append(f"ASIN: {self.asin}")
        report_lines.append(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("=" * 50)
        
        for result in results:
            report_lines.append(f"\n关键词: {result['keyword']}")
            if result['found']:
                report_lines.append(f"  状态: ✓ 已找到")
                report_lines.append(f"  总排名: 第{result['rank']}位")
                report_lines.append(f"  所在页: 第{result['page']}页")
                report_lines.append(f"  页内位置: 第{result['position_in_page']}个")
            else:
                report_lines.append(f"  状态: ✗ 未找到")
                report_lines.append(f"  原因: {result['error']}")
        
        report_lines.append("\n" + "=" * 50)
        report_lines.append("说明:")
        report_lines.append("1. 排名基于亚马逊搜索结果页面")
        report_lines.append("2. 只检查前5页（约80个产品）")
        report_lines.append("3. 排名可能因地区、账号等因素有所不同")
        
        return "\n".join(report_lines)


def main():
    # 配置监控参数
    ASIN = "B0G61JM8L6"
    KEYWORDS = [
        "bra pads inserts",
        "sport bra pads inserts", 
        "swimsuit bra inserts"
    ]
    
    # 创建监控器
    monitor = AmazonRankMonitor(ASIN, KEYWORDS)
    
    # 检查所有关键词
    results = monitor.check_all_keywords()
    
    # 保存结果
    json_file = monitor.save_results(results)
    
    # 生成报告
    report = monitor.generate_report(results)
    print("\n" + report)
    
    # 同时保存报告为文本文件
    report_file = json_file.replace('.json', '_report.txt')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n报告已保存到: {report_file}")
    
    return results, report


if __name__ == "__main__":
    main()