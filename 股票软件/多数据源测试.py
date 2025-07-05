#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多数据源测试脚本
测试所有新闻数据源的效果，并生成综合报告
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import time

def test_sina_news(stock_code="sh603259"):
    """测试新浪财经新闻"""
    print("=== 测试新浪财经新闻 ===")
    
    url = "https://vip.stock.finance.sina.com.cn/corp/view/vCB_AllNewsStock.php"
    params = {"symbol": stock_code, "Page": 1}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code == 200:
            resp.encoding = 'gbk'
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            news_container = soup.find('div', class_='datelist')
            if news_container:
                news_pattern = r'(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})\s+<a[^>]*>([^<]+)</a>'
                news_matches = re.findall(news_pattern, str(news_container))
                
                news_list = []
                for match in news_matches:
                    date_str = match[0]
                    time_str = match[1]
                    title = match[2].strip()
                    full_date = f"{date_str} {time_str}"
                    news_list.append((full_date, title))
                
                print(f"✅ 新浪财经: 成功获取 {len(news_list)} 条新闻")
                return news_list
            else:
                print("❌ 新浪财经: 未找到新闻容器")
                return []
        else:
            print(f"❌ 新浪财经: HTTP错误 {resp.status_code}")
            return []
    except Exception as e:
        print(f"❌ 新浪财经: {e}")
        return []

def test_eastmoney_news(stock_code="sh603259"):
    """测试东方财富新闻"""
    print("\n=== 测试东方财富新闻 ===")
    
    url = "http://np-anotice-stock.eastmoney.com/api/security/announcement/getAnnouncementList"
    params = {"cb": "jQuery", "pageSize": 20, "pageIndex": 1, "stock": stock_code}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code == 200 and resp.text:
            content = resp.text
            news_list = []
            
            # 尝试解析JSONP格式
            if content.startswith('jQuery(') and content.endswith(')'):
                json_str = content[7:-1]
                try:
                    data = json.loads(json_str)
                    if 'data' in data and 'list' in data['data']:
                        news_items = data['data']['list']
                        for item in news_items:
                            date_str = item.get('notice_date', '')
                            title = item.get('title', '')
                            if date_str and title:
                                news_list.append((date_str, title))
                        
                        print(f"✅ 东方财富: 成功获取 {len(news_list)} 条公告")
                        return news_list
                except json.JSONDecodeError:
                    pass
            
            # 尝试直接解析JSON
            try:
                data = resp.json()
                if 'data' in data and 'list' in data['data']:
                    news_items = data['data']['list']
                    for item in news_items:
                        date_str = item.get('notice_date', '')
                        title = item.get('title', '')
                        if date_str and title:
                            news_list.append((date_str, title))
                    
                    print(f"✅ 东方财富: 成功获取 {len(news_list)} 条公告")
                    return news_list
            except json.JSONDecodeError:
                pass
            
            print("❌ 东方财富: 解析失败")
            return []
        else:
            print(f"❌ 东方财富: 响应为空或HTTP错误 {resp.status_code}")
            return []
    except Exception as e:
        print(f"❌ 东方财富: {e}")
        return []

def test_xueqiu_news(stock_code="sh603259"):
    """测试雪球新闻"""
    print("\n=== 测试雪球新闻 ===")
    
    url = f"https://xueqiu.com/statuses/search.json?count=20&comment=0&source=all&sort=time&page=1&stock={stock_code}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://xueqiu.com/",
        "Accept": "application/json, text/plain, */*",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            try:
                data = resp.json()
                if 'list' in data:
                    news_items = data['list']
                    news_list = []
                    
                    for item in news_items:
                        created_at = item.get('created_at', '')
                        title = item.get('title', '')
                        if created_at and title:
                            try:
                                from datetime import datetime
                                dt = datetime.fromtimestamp(created_at / 1000)
                                date_str = dt.strftime('%Y-%m-%d %H:%M')
                                news_list.append((date_str, title))
                            except:
                                news_list.append((str(created_at), title))
                    
                    print(f"✅ 雪球: 成功获取 {len(news_list)} 条新闻")
                    return news_list
                else:
                    print("❌ 雪球: 数据结构不符合预期")
                    return []
            except json.JSONDecodeError as e:
                print(f"❌ 雪球: JSON解析失败 {e}")
                return []
        else:
            print(f"❌ 雪球: HTTP错误 {resp.status_code}")
            return []
    except Exception as e:
        print(f"❌ 雪球: {e}")
        return []

def test_ths_news(stock_code="sh603259"):
    """测试同花顺新闻"""
    print("\n=== 测试同花顺新闻 ===")
    
    url = f"http://news.10jqka.com.cn/tapp/news/push/stock/{stock_code}/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # 查找新闻列表
            news_items = soup.find_all(['div', 'li'], class_=re.compile(r'news|item|list'))
            news_list = []
            
            for item in news_items:
                date_elem = item.find(['span', 'div'], class_=re.compile(r'date|time'))
                title_elem = item.find('a')
                
                if date_elem and title_elem:
                    date_str = date_elem.get_text().strip()
                    title = title_elem.get_text().strip()
                    if date_str and title:
                        news_list.append((date_str, title))
            
            if news_list:
                print(f"✅ 同花顺: 成功获取 {len(news_list)} 条新闻")
                return news_list
            else:
                print("❌ 同花顺: 未找到新闻")
                return []
        else:
            print(f"❌ 同花顺: HTTP错误 {resp.status_code}")
            return []
    except Exception as e:
        print(f"❌ 同花顺: {e}")
        return []

def test_jrj_news(stock_code="sh603259"):
    """测试金融界新闻"""
    print("\n=== 测试金融界新闻 ===")
    
    url = f"http://stock.jrj.com.cn/report/{stock_code}/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # 查找新闻列表
            news_items = soup.find_all(['div', 'li'], class_=re.compile(r'news|item|list'))
            news_list = []
            
            for item in news_items:
                date_elem = item.find(['span', 'div'], class_=re.compile(r'date|time'))
                title_elem = item.find('a')
                
                if date_elem and title_elem:
                    date_str = date_elem.get_text().strip()
                    title = title_elem.get_text().strip()
                    if date_str and title:
                        news_list.append((date_str, title))
            
            if news_list:
                print(f"✅ 金融界: 成功获取 {len(news_list)} 条新闻")
                return news_list
            else:
                print("❌ 金融界: 未找到新闻")
                return []
        else:
            print(f"❌ 金融界: HTTP错误 {resp.status_code}")
            return []
    except Exception as e:
        print(f"❌ 金融界: {e}")
        return []

def generate_comprehensive_report(all_news, stock_code="sh603259"):
    """生成综合报告"""
    print("\n" + "="*60)
    print("📊 多数据源综合报告")
    print("="*60)
    
    # 统计各数据源贡献
    source_stats = {}
    total_news = 0
    
    for source, news_list in all_news.items():
        if news_list:
            source_stats[source] = len(news_list)
            total_news += len(news_list)
        else:
            source_stats[source] = 0
    
    print(f"\n📈 数据源统计:")
    for source, count in source_stats.items():
        status = "✅" if count > 0 else "❌"
        print(f"  {status} {source}: {count} 条")
    
    print(f"\n📊 总计: {total_news} 条新闻")
    
    # 去重统计
    all_titles = set()
    unique_news = []
    
    for source, news_list in all_news.items():
        for date, title in news_list:
            if title not in all_titles:
                unique_news.append((date, title, source))
                all_titles.add(title)
    
    print(f"🎯 去重后: {len(unique_news)} 条新闻")
    
    # 按时间排序
    unique_news.sort(key=lambda x: x[0], reverse=True)
    
    print(f"\n📰 最新新闻 (前10条):")
    for i, (date, title, source) in enumerate(unique_news[:10]):
        print(f"  {i+1}. [{source}] {date}: {title[:60]}...")
    
    # 数据源可靠性评估
    print(f"\n🔍 数据源可靠性评估:")
    reliable_sources = []
    for source, count in source_stats.items():
        if count > 0:
            reliable_sources.append(source)
            print(f"  ✅ {source}: 可用 ({count} 条)")
        else:
            print(f"  ❌ {source}: 不可用")
    
    print(f"\n💡 建议:")
    if reliable_sources:
        print(f"  推荐使用: {', '.join(reliable_sources)}")
        if len(reliable_sources) > 1:
            print(f"  建议组合使用多个数据源以获得更全面的信息")
    else:
        print(f"  所有数据源都不可用，请检查网络连接")
    
    return unique_news, source_stats

def main():
    """主函数"""
    print("🔍 开始多数据源测试...")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    stock_code = "sh603259"  # 药明康德
    
    # 测试所有数据源
    all_news = {}
    
    all_news['新浪财经'] = test_sina_news(stock_code)
    time.sleep(1)  # 避免请求过快
    
    all_news['东方财富'] = test_eastmoney_news(stock_code)
    time.sleep(1)
    
    all_news['雪球'] = test_xueqiu_news(stock_code)
    time.sleep(1)
    
    all_news['同花顺'] = test_ths_news(stock_code)
    time.sleep(1)
    
    all_news['金融界'] = test_jrj_news(stock_code)
    
    # 生成综合报告
    unique_news, source_stats = generate_comprehensive_report(all_news, stock_code)
    
    # 保存详细结果
    with open('多数据源测试结果.txt', 'w', encoding='utf-8') as f:
        f.write("多数据源测试结果\n")
        f.write("="*50 + "\n")
        f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"股票代码: {stock_code}\n\n")
        
        f.write("数据源统计:\n")
        for source, count in source_stats.items():
            f.write(f"  {source}: {count} 条\n")
        
        f.write(f"\n总计: {sum(source_stats.values())} 条\n")
        f.write(f"去重后: {len(unique_news)} 条\n\n")
        
        f.write("详细新闻列表:\n")
        for i, (date, title, source) in enumerate(unique_news):
            f.write(f"{i+1}. [{source}] {date}: {title}\n")
    
    print(f"\n📄 详细结果已保存至: 多数据源测试结果.txt")
    print("\n✅ 多数据源测试完成！")

if __name__ == "__main__":
    main() 