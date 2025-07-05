#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据源可用性测试脚本
测试所有股票数据源和新闻数据源的连接状态
"""

import requests
import pandas as pd
import json
from datetime import datetime

def test_stock_data_sources():
    """测试股票数据源"""
    print("=== 股票数据源测试 ===")
    
    stock_code = "sh603259"  # 药明康德
    start_date = "20240101"
    end_date = datetime.now().strftime("%Y%m%d")
    
    # 股票数据源列表
    stock_sources = [
        {
            'name': '网易财经',
            'url': f"http://quotes.money.163.com/service/chddata.html?code={stock_code}&start={start_date}&end={end_date}&fields=TCLOSE;HIGH;LOW;OPEN;LCLOSE;PCHG;VOL",
            'method': 'csv'
        },
        {
            'name': '新浪财经',
            'url': f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={stock_code}&scale=240&ma=5&datalen=10",
            'method': 'json'
        },
        {
            'name': '东方财富',
            'url': f"http://push2his.eastmoney.com/api/qt/stock/kline/get?secid={stock_code}&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt=101&fqt=1&beg=0&end=20500101&smplmt=10&lmt=1000000",
            'method': 'json'
        },
        {
            'name': '腾讯财经',
            'url': f"http://qt.gtimg.cn/q={stock_code}",
            'method': 'text'
        },
        {
            'name': '雪球',
            'url': f"https://stock.xueqiu.com/v5/stock/chart/kline.json?symbol={stock_code}&period=day&type=before&count=10&indicator=kline",
            'method': 'json'
        },
        {
            'name': '同花顺',
            'url': f"http://d.10jqka.com.cn/v6/line/hs_{stock_code}/01/today.js",
            'method': 'text'
        },
        {
            'name': '大智慧',
            'url': f"http://hq.gw.com.cn/kline?code={stock_code}&period=day&count=10",
            'method': 'json'
        },
        {
            'name': '金融界',
            'url': f"http://q.jrjimg.cn/?q=cn|s|{stock_code}&n=hq&c=1&o=0&f=1&v=1.1",
            'method': 'text'
        },
        {
            'name': '和讯网',
            'url': f"http://webstock.10jqka.com.cn/hs_zfzq/hq/{stock_code}/",
            'method': 'text'
        },
        {
            'name': '凤凰网',
            'url': f"http://api.finance.ifeng.com/akdaily/?code={stock_code}&type=last&start={start_date}&end={end_date}",
            'method': 'csv'
        }
    ]
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    results = []
    
    for i, source in enumerate(stock_sources):
        print(f"\n{i+1}. 测试 {source['name']}...")
        try:
            if source['method'] == 'csv':
                df = pd.read_csv(source['url'], encoding='gbk', nrows=5)
                status = "✅ 成功" if not df.empty else "❌ 无数据"
                data_count = len(df)
            elif source['method'] == 'json':
                resp = requests.get(source['url'], headers=headers, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    status = "✅ 成功" if data else "❌ 无数据"
                    data_count = len(data) if isinstance(data, list) else 1
                else:
                    status = f"❌ HTTP {resp.status_code}"
                    data_count = 0
            else:  # text
                resp = requests.get(source['url'], headers=headers, timeout=10)
                if resp.status_code == 200:
                    status = "✅ 成功" if resp.text else "❌ 无数据"
                    data_count = len(resp.text)
                else:
                    status = f"❌ HTTP {resp.status_code}"
                    data_count = 0
                    
        except Exception as e:
            status = f"❌ 错误: {str(e)[:50]}"
            data_count = 0
            
        results.append({
            'name': source['name'],
            'status': status,
            'data_count': data_count
        })
        print(f"   状态: {status}")
        print(f"   数据量: {data_count}")
    
    return results

def test_news_data_sources():
    """测试新闻数据源"""
    print("\n=== 新闻数据源测试 ===")
    
    stock_code = "sh603259"
    symbol = stock_code
    
    # 新闻数据源列表
    news_sources = [
        {
            'name': '新浪财经新闻',
            'url': "https://vip.stock.finance.sina.com.cn/corp/view/vCB_AllNewsStock.php",
            'params': {"symbol": symbol, "Page": 1}
        },
        {
            'name': '东方财富新闻',
            'url': "http://np-anotice-stock.eastmoney.com/api/security/announcement/getAnnouncementList",
            'params': {"cb": "jQuery", "pageSize": 5, "pageIndex": 1, "stock": symbol}
        },
        {
            'name': '雪球新闻',
            'url': f"https://xueqiu.com/statuses/search.json?count=5&comment=0&source=all&sort=time&page=1&stock={symbol}",
            'params': {}
        },
        {
            'name': '同花顺新闻',
            'url': f"http://news.10jqka.com.cn/tapp/news/push/stock/{symbol}/",
            'params': {}
        },
        {
            'name': '金融界新闻',
            'url': f"http://stock.jrj.com.cn/report/{symbol}/",
            'params': {}
        }
    ]
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    results = []
    
    for i, source in enumerate(news_sources):
        print(f"\n{i+1}. 测试 {source['name']}...")
        try:
            resp = requests.get(source['url'], params=source['params'], headers=headers, timeout=10)
            if resp.status_code == 200:
                status = "✅ 成功"
                data_count = len(resp.text)
            else:
                status = f"❌ HTTP {resp.status_code}"
                data_count = 0
        except Exception as e:
            status = f"❌ 错误: {str(e)[:50]}"
            data_count = 0
            
        results.append({
            'name': source['name'],
            'status': status,
            'data_count': data_count
        })
        print(f"   状态: {status}")
        print(f"   响应大小: {data_count} 字符")
    
    return results

def generate_report(stock_results, news_results):
    """生成测试报告"""
    print("\n" + "="*60)
    print("📊 数据源可用性测试报告")
    print("="*60)
    
    print("\n📈 股票数据源状态:")
    print("-" * 40)
    for result in stock_results:
        print(f"{result['name']:<12} | {result['status']:<20} | 数据量: {result['data_count']}")
    
    print("\n📰 新闻数据源状态:")
    print("-" * 40)
    for result in news_results:
        print(f"{result['name']:<12} | {result['status']:<20} | 响应: {result['data_count']} 字符")
    
    # 统计成功率
    stock_success = sum(1 for r in stock_results if '✅' in r['status'])
    news_success = sum(1 for r in news_results if '✅' in r['status'])
    
    print(f"\n📊 成功率统计:")
    print(f"股票数据源: {stock_success}/{len(stock_results)} ({stock_success/len(stock_results)*100:.1f}%)")
    print(f"新闻数据源: {news_success}/{len(news_results)} ({news_success/len(news_results)*100:.1f}%)")
    
    # 保存报告
    report_data = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'stock_sources': stock_results,
        'news_sources': news_results,
        'stock_success_rate': stock_success/len(stock_results)*100,
        'news_success_rate': news_success/len(news_results)*100
    }
    
    with open('数据源测试报告.json', 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 详细报告已保存至: 数据源测试报告.json")

def main():
    """主函数"""
    print("🚀 开始测试数据源可用性...")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试股票数据源
    stock_results = test_stock_data_sources()
    
    # 测试新闻数据源
    news_results = test_news_data_sources()
    
    # 生成报告
    generate_report(stock_results, news_results)
    
    print("\n✅ 测试完成！")

if __name__ == "__main__":
    main() 