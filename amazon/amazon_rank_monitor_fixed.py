#!/usr/bin/env python3
"""
亚马逊关键词排名监控脚本（修复版）
修复503错误问题，增加延迟和更好的错误处理
"""

import requests
import time
import json
import os
import random
from datetime import datetime
from bs4 import BeautifulSoup
import re

class AmazonRankMonitorFixed:
    def __init__(self, asin, keywords):
        """
        初始化监控器
        :param asin: 产品ASIN
        :param keywords: 关键词列表
        """
        self.asin = asin
        self.keywords = keywords
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
        ]
        
    def get_random_headers(self):
        """获取随机的请求头"""
        return {
            'User-Agent': random.choice(self.user_agents),
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
    
    def search_keyword_with_retry(self, keyword, max_retries=3):
        """
        搜索关键词并获取页面内容，带重试机制
        :param keyword: 搜索关键词
        :param max_retries: 最大重试次数
        :return: 页面HTML内容或None
        """
        search_term = keyword.replace(' ', '+')
        
        for attempt in range(max_retries):
            try:
                # 随机延迟，避免请求过于频繁
                delay = random.uniform(2, 5)
                print(f"  等待 {delay:.1f}秒后请求...")
                time.sleep(delay)
                
                # 每次尝试使用不同的User-Agent
                headers = self.get_random_headers()
                
                # 构建搜索URL
                url = f"https://www.amazon.com/s?k={search_term}&page=1"
                
                # 禁用代理
                proxies = {'http': None, 'https': None}
                
                print(f"  尝试 {attempt+1}/{max_retries}: 请求 {keyword}")
                response = requests.get(url, headers=headers, timeout=15, proxies=proxies)
                
                if response.status_code == 503:
                    print(f"  收到503错误，等待后重试...")
                    time.sleep(random.uniform(5, 10))
                    continue
                    
                response.raise_for_status()
                
                # 检查是否被重定向到验证页面
                if 'robot check' in response.text.lower() or 'captcha' in response.text.lower():
                    print(f"  检测到验证页面，等待更长时间后重试...")
                    time.sleep(random.uniform(10, 20))
                    continue
                
                return response.text
                
            except requests.exceptions.RequestException as e:
                print(f"  请求失败: {e}")
                if attempt < max_retries - 1:
                    wait_time = random.uniform(5, 15)
                    print(f"  等待 {wait_time:.1f}秒后重试...")
                    time.sleep(wait_time)
                else:
                    print(f"  达到最大重试次数，放弃该关键词")
                    return None
        
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
                'position_in_page': None,
                'found': False,
                'error': '无法获取页面内容'
            }
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 查找所有产品div
            products = soup.find_all('div', {'data-component-type': 's-search-result'})
            
            for i, product in enumerate(products, 1):
                # 查找ASIN
                data_asin = product.get('data-asin')
                if data_asin == self.asin:
                    # 计算页内位置和页码
                    position_in_page = i
                    page = 1  # 目前只搜索第一页
                    
                    return {
                        'keyword': keyword,
                        'rank': position_in_page,
                        'page': page,
                        'position_in_page': position_in_page,
                        'found': True,
                        'error': None
                    }
            
            # 如果没有找到，检查是否在后续页面（简化版，只检查第一页）
            return {
                'keyword': keyword,
                'rank': None,
                'page': None,
                'position_in_page': None,
                'found': False,
                'error': '未在前5页找到该ASIN'
            }
            
        except Exception as e:
            return {
                'keyword': keyword,
                'rank': None,
                'page': None,
                'position_in_page': None,
                'found': False,
                'error': f'解析页面时出错: {str(e)}'
            }
    
    def monitor(self):
        """
        执行监控任务
        :return: 监控结果列表
        """
        print(f"开始监控ASIN: {self.asin}")
        print(f"关键词列表: {self.keywords}")
        print("-" * 50)
        
        results = []
        
        for keyword in self.keywords:
            print(f"正在搜索关键词: '{keyword}'...")
            
            html = self.search_keyword_with_retry(keyword)
            
            if html:
                result = self.find_asin_rank(html, keyword)
                if result['found']:
                    print(f"  ✓ 找到! 排名: 第{result['rank']}位 (第{result['page']}页, 第{result['position_in_page']}个)")
                else:
                    print(f"  ✗ 未找到: {result['error']}")
                results.append(result)
            else:
                result = {
                    'keyword': keyword,
                    'rank': None,
                    'page': None,
                    'position_in_page': None,
                    'found': False,
                    'error': '无法获取页面内容（多次重试失败）'
                }
                print(f"  ✗ 失败: 无法获取页面内容（多次重试失败）")
                results.append(result)
            
            # 关键词之间的延迟
            if keyword != self.keywords[-1]:
                delay = random.uniform(3, 7)
                print(f"  等待 {delay:.1f}秒后处理下一个关键词...")
                time.sleep(delay)
        
        print("-" * 50)
        return results
    
    def save_results(self, results):
        """
        保存监控结果
        :param results: 监控结果列表
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        
        # 保存JSON数据
        json_data = {
            'asin': self.asin,
            'check_time': datetime.now().isoformat(),
            'results': results
        }
        
        json_filename = f"{self.asin}_rank_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        print(f"结果已保存到: {json_filename}")
        
        # 保存文本报告
        self.generate_report(results, timestamp)
        
        return json_filename
    
    def generate_report(self, results, timestamp):
        """
        生成文本报告
        :param results: 监控结果列表
        :param timestamp: 时间戳
        """
        report_filename = f"{self.asin}_rank_{timestamp}_report.txt"
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write("亚马逊关键词排名监控报告\n")
            f.write(f"ASIN: {self.asin}\n")
            f.write(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            
            for result in results:
                f.write(f"关键词: {result['keyword']}\n")
                if result['found']:
                    f.write(f"  状态: ✓ 已找到\n")
                    f.write(f"  总排名: 第{result['rank']}位\n")
                    f.write(f"  所在页: 第{result['page']}页\n")
                    f.write(f"  页内位置: 第{result['position_in_page']}个\n")
                else:
                    f.write(f"  状态: ✗ 未找到\n")
                    f.write(f"  原因: {result['error']}\n")
                f.write("\n")
            
            f.write("=" * 50 + "\n")
            f.write("说明:\n")
            f.write("1. 排名基于亚马逊搜索结果页面\n")
            f.write("2. 只检查前5页（约80个产品）\n")
            f.write("3. 排名可能因地区、账号等因素有所不同\n")
        
        print(f"报告已保存到: {report_filename}")


def main():
    """主函数"""
    # 监控配置
    ASIN = "B0G61JM8L6"
    KEYWORDS = [
        "bra pads inserts",
        "sport bra pads inserts", 
        "swimsuit bra inserts"
    ]
    
    # 创建监控器实例
    monitor = AmazonRankMonitorFixed(ASIN, KEYWORDS)
    
    # 执行监控
    results = monitor.monitor()
    
    # 保存结果
    monitor.save_results(results)
    
    # 生成简版报告
    generate_summary_report(results, ASIN)


def generate_summary_report(results, asin):
    """生成简版总结报告"""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    summary_filename = f"amazon_rank_summary_{timestamp}.txt"
    
    successful = sum(1 for r in results if r['found'])
    failed = len(results) - successful
    
    with open(summary_filename, 'w', encoding='utf-8') as f:
        f.write("亚马逊监控任务执行总结\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"ASIN: {asin}\n\n")
        
        f.write("📊 执行结果\n")
        f.write("-" * 20 + "\n")
        f.write(f"总关键词数: {len(results)}\n")
        f.write(f"成功获取: {successful}\n")
        f.write(f"失败: {failed}\n\n")
        
        f.write("📈 排名详情\n")
        f.write("-" * 20 + "\n")
        for result in results:
            if result['found']:
                f.write(f"{result['keyword']}: 第{result['rank']}位\n")
            else:
                f.write(f"{result['keyword']}: 获取失败 ({result['error']})\n")
        
        f.write("\n🚨 系统状态\n")
        f.write("-" * 20 + "\n")
        if failed == 0:
            f.write("✅ 所有关键词数据获取成功\n")
        elif successful == 0:
            f.write("🔴 所有关键词数据获取失败\n")
        else:
            f.write(f"⚠️  部分数据获取失败 ({failed}/{len(results)})\n")
    
    print(f"总结报告已保存到: {summary_filename}")


if __name__ == "__main__":
    main()