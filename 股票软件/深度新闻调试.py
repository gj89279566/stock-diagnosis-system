#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度新闻调试脚本
检查新浪财经新闻页面的具体内容，找出新闻获取失败的原因
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

def deep_debug_sina_news():
    """深度调试新浪财经新闻页面"""
    print("=== 深度调试新浪财经新闻页面 ===")
    
    stock_code = "sh603259"
    url = "https://vip.stock.finance.sina.com.cn/corp/view/vCB_AllNewsStock.php"
    params = {"symbol": stock_code, "Page": 1}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code == 200:
            resp.encoding = 'gbk'
            content = resp.text
            
            print(f"页面标题: {re.search(r'<title>(.*?)</title>', content, re.IGNORECASE).group(1) if re.search(r'<title>(.*?)</title>', content, re.IGNORECASE) else '未找到标题'}")
            
            # 查找所有可能包含新闻的元素
            soup = BeautifulSoup(content, 'html.parser')
            
            # 1. 查找所有链接
            links = soup.find_all('a', href=True)
            news_links = []
            for link in links:
                href = link.get('href', '')
                text = link.get_text().strip()
                if any(keyword in href.lower() for keyword in ['news', 'notice', 'announcement', 'report']):
                    news_links.append((text, href))
            
            print(f"\n找到 {len(news_links)} 个可能的新闻链接:")
            for text, href in news_links[:10]:  # 显示前10个
                print(f"  {text} -> {href}")
            
            # 2. 查找所有表格
            tables = soup.find_all('table')
            print(f"\n找到 {len(tables)} 个表格:")
            
            for i, table in enumerate(tables):
                print(f"\n表格 {i+1}:")
                rows = table.find_all('tr')
                print(f"  行数: {len(rows)}")
                
                if len(rows) > 0:
                    # 显示前几行的内容
                    for j, row in enumerate(rows[:3]):
                        cells = row.find_all(['td', 'th'])
                        cell_texts = [cell.get_text().strip() for cell in cells]
                        print(f"  行 {j+1}: {cell_texts}")
            
            # 3. 查找特定的新闻容器
            news_containers = soup.find_all(['div', 'ul', 'ol'], class_=re.compile(r'news|list|item'))
            print(f"\n找到 {len(news_containers)} 个可能的新闻容器:")
            
            for i, container in enumerate(news_containers[:5]):
                print(f"\n容器 {i+1} (class={container.get('class', '无')}):")
                print(f"  内容: {container.get_text()[:200]}...")
            
            # 4. 查找日期模式
            date_pattern = re.compile(r'\d{4}-\d{2}-\d{2}')
            dates = date_pattern.findall(content)
            print(f"\n找到 {len(dates)} 个日期:")
            for date in dates[:10]:
                print(f"  {date}")
            
            # 5. 检查页面是否包含"没有"、"暂无"等关键词
            no_data_keywords = ['没有', '暂无', '无数据', 'empty', 'no data']
            for keyword in no_data_keywords:
                if keyword in content:
                    print(f"\n⚠️ 页面包含关键词: {keyword}")
            
            # 6. 查找新闻列表的特定模式
            # 新浪财经新闻通常在这个位置
            news_section = soup.find('div', {'id': 'con02-0'})
            if news_section:
                print(f"\n找到新闻区域 (con02-0):")
                print(f"内容: {news_section.get_text()[:500]}...")
            else:
                print(f"\n❌ 未找到新闻区域 (con02-0)")
            
            # 7. 尝试其他可能的新闻区域
            possible_news_areas = [
                soup.find('div', {'id': 'con02-1'}),
                soup.find('div', {'id': 'con02-2'}),
                soup.find('div', {'class': 'news_list'}),
                soup.find('ul', {'class': 'news_list'}),
            ]
            
            for i, area in enumerate(possible_news_areas):
                if area:
                    print(f"\n找到可能的新闻区域 {i+1}:")
                    print(f"内容: {area.get_text()[:300]}...")
            
            # 8. 检查是否有分页信息
            pagination = soup.find_all('a', href=re.compile(r'Page='))
            if pagination:
                print(f"\n找到分页链接: {len(pagination)} 个")
                for page_link in pagination[:5]:
                    print(f"  {page_link.get_text()} -> {page_link.get('href')}")
            
            # 9. 保存页面内容到文件以便进一步分析
            with open('sina_news_page.html', 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"\n📄 页面内容已保存到 sina_news_page.html")
            
        else:
            print(f"❌ HTTP请求失败: {resp.status_code}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")

def test_different_stock_codes():
    """测试不同股票代码的新闻获取"""
    print("\n=== 测试不同股票代码的新闻获取 ===")
    
    test_stocks = [
        {"code": "sh603259", "name": "药明康德"},
        {"code": "sh600519", "name": "贵州茅台"},  # 热门股票
        {"code": "sz000001", "name": "平安银行"},  # 深市股票
        {"code": "sh000001", "name": "上证指数"},  # 指数
    ]
    
    for stock in test_stocks:
        print(f"\n测试 {stock['name']} ({stock['code']}):")
        
        url = "https://vip.stock.finance.sina.com.cn/corp/view/vCB_AllNewsStock.php"
        params = {"symbol": stock['code'], "Page": 1}
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            if resp.status_code == 200:
                resp.encoding = 'gbk'
                content = resp.text
                
                # 检查是否包含新闻表格
                soup = BeautifulSoup(content, 'html.parser')
                tables = soup.find_all('table')
                
                news_count = 0
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows[1:]:  # 跳过表头
                        cells = row.find_all('td')
                        if len(cells) >= 2:
                            date_text = cells[0].get_text().strip()
                            if re.match(r'\d{4}-\d{2}-\d{2}', date_text):
                                news_count += 1
                
                print(f"  找到 {news_count} 条新闻")
                
                if news_count == 0:
                    # 检查页面是否包含"没有"等关键词
                    if '没有' in content or '暂无' in content:
                        print(f"  ✅ 页面显示没有相关新闻")
                    else:
                        print(f"  ❓ 页面内容异常")
                else:
                    print(f"  ✅ 成功获取新闻")
                    
            else:
                print(f"  ❌ HTTP请求失败: {resp.status_code}")
                
        except Exception as e:
            print(f"  ❌ 请求异常: {e}")

def main():
    """主函数"""
    print("🔍 开始深度调试新闻获取...")
    print(f"⏰ 调试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 深度调试新浪财经新闻页面
    deep_debug_sina_news()
    
    # 测试不同股票代码
    test_different_stock_codes()
    
    print("\n✅ 深度调试完成！")
    print("\n💡 建议:")
    print("1. 检查 sina_news_page.html 文件了解页面结构")
    print("2. 根据页面结构调整新闻解析逻辑")
    print("3. 考虑使用其他新闻源作为补充")

if __name__ == "__main__":
    main() 