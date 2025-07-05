#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻获取调试脚本
详细检查新闻获取过程，判断是获取失败还是确实没有新闻
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

def debug_sina_news(stock_code="sh603259"):
    """调试新浪财经新闻获取"""
    print("=== 调试新浪财经新闻获取 ===")
    
    symbol = stock_code
    url = "https://vip.stock.finance.sina.com.cn/corp/view/vCB_AllNewsStock.php"
    params = {"symbol": symbol, "Page": 1}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        print(f"请求URL: {url}")
        print(f"参数: {params}")
        print(f"股票代码: {symbol}")
        
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"响应状态码: {resp.status_code}")
        print(f"响应头: {dict(resp.headers)}")
        
        if resp.status_code == 200:
            resp.encoding = 'gbk'
            content = resp.text
            print(f"响应内容长度: {len(content)} 字符")
            print(f"响应内容前500字符: {content[:500]}")
            
            # 检查是否包含新闻表格
            if 'table' in content.lower():
                print("✅ 页面包含表格元素")
                soup = BeautifulSoup(content, 'html.parser')
                tables = soup.find_all('table')
                print(f"找到 {len(tables)} 个表格")
                
                for i, table in enumerate(tables):
                    rows = table.find_all('tr')
                    print(f"表格 {i+1}: {len(rows)} 行")
                    
                    if len(rows) > 0:
                        # 检查第一行是否是表头
                        first_row = rows[0]
                        cells = first_row.find_all(['td', 'th'])
                        print(f"第一行单元格数: {len(cells)}")
                        if len(cells) > 0:
                            print(f"第一行内容: {[cell.get_text().strip() for cell in cells]}")
                        
                        # 检查是否有数据行
                        data_rows = []
                        for row in rows[1:]:  # 跳过表头
                            cells = row.find_all('td')
                            if len(cells) >= 2:
                                date_text = cells[0].get_text().strip()
                                title_text = cells[1].get_text().strip()
                                if re.match(r'\d{4}-\d{2}-\d{2}', date_text):
                                    data_rows.append((date_text, title_text))
                        
                        print(f"找到 {len(data_rows)} 条有效新闻")
                        for date, title in data_rows[:3]:  # 显示前3条
                            print(f"  {date}: {title}")
                        
                        if data_rows:
                            return data_rows
            else:
                print("❌ 页面不包含表格元素")
                # 检查是否包含错误信息
                if 'error' in content.lower() or '404' in content.lower():
                    print("❌ 页面包含错误信息")
                elif '没有找到' in content or '暂无数据' in content:
                    print("✅ 页面显示没有相关新闻")
                else:
                    print("❓ 页面内容异常")
        else:
            print(f"❌ HTTP请求失败: {resp.status_code}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    return []

def debug_eastmoney_news(stock_code="sh603259"):
    """调试东方财富新闻获取"""
    print("\n=== 调试东方财富新闻获取 ===")
    
    symbol = stock_code
    url = "http://np-anotice-stock.eastmoney.com/api/security/announcement/getAnnouncementList"
    params = {"cb": "jQuery", "pageSize": 20, "pageIndex": 1, "stock": symbol}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        print(f"请求URL: {url}")
        print(f"参数: {params}")
        print(f"股票代码: {symbol}")
        
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"响应状态码: {resp.status_code}")
        print(f"响应内容长度: {len(resp.text)} 字符")
        print(f"响应内容: {resp.text[:500]}")
        
        if resp.status_code == 200:
            content = resp.text
            if content:
                print("✅ 接口响应正常")
                # 尝试解析JSONP格式
                if content.startswith('jQuery(') and content.endswith(')'):
                    json_str = content[7:-1]  # 去掉jQuery()包装
                    try:
                        data = json.loads(json_str)
                        print(f"解析JSON成功: {data}")
                        if 'data' in data and 'list' in data['data']:
                            news_list = data['data']['list']
                            print(f"找到 {len(news_list)} 条公告")
                            return [(item.get('notice_date', ''), item.get('title', '')) for item in news_list]
                        else:
                            print("❌ 数据结构不符合预期")
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON解析失败: {e}")
                else:
                    print("❌ 响应格式不是JSONP")
            else:
                print("✅ 接口响应为空（可能确实没有公告）")
        else:
            print(f"❌ HTTP请求失败: {resp.status_code}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    return []

def debug_xueqiu_news(stock_code="sh603259"):
    """调试雪球新闻获取"""
    print("\n=== 调试雪球新闻获取 ===")
    
    symbol = stock_code
    url = f"https://xueqiu.com/statuses/search.json?count=20&comment=0&source=all&sort=time&page=1&stock={symbol}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        print(f"请求URL: {url}")
        print(f"股票代码: {symbol}")
        
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"响应状态码: {resp.status_code}")
        print(f"响应内容: {resp.text[:500]}")
        
        if resp.status_code == 200:
            try:
                data = resp.json()
                print(f"解析JSON成功: {data}")
                if 'list' in data:
                    news_list = data['list']
                    print(f"找到 {len(news_list)} 条新闻")
                    return [(item.get('created_at', ''), item.get('title', '')) for item in news_list]
                else:
                    print("❌ 数据结构不符合预期")
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析失败: {e}")
        else:
            print(f"❌ HTTP请求失败: {resp.status_code}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    return []

def check_stock_code_validity(stock_code="sh603259"):
    """检查股票代码的有效性"""
    print("\n=== 检查股票代码有效性 ===")
    
    # 测试不同的股票代码格式
    test_codes = [
        stock_code,  # 原始代码
        stock_code[2:] if stock_code.startswith(('sh', 'sz')) else stock_code,  # 去掉前缀
        f"0{stock_code[2:]}" if stock_code.startswith('sh') else stock_code,  # 网易格式
        f"1{stock_code[2:]}" if stock_code.startswith('sz') else stock_code,  # 网易格式
    ]
    
    for code in test_codes:
        print(f"测试股票代码: {code}")
        
        # 测试新浪接口
        url = "http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"
        params = {"symbol": code, "scale": 240, "ma": 5, "datalen": 1}
        
        try:
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data:
                    print(f"✅ {code} 在新浪接口有效")
                else:
                    print(f"❌ {code} 在新浪接口无数据")
            else:
                print(f"❌ {code} 在新浪接口请求失败")
        except Exception as e:
            print(f"❌ {code} 测试异常: {e}")

def main():
    """主函数"""
    print("🔍 开始调试新闻获取过程...")
    print(f"⏰ 调试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    stock_code = "sh603259"  # 药明康德
    
    # 检查股票代码有效性
    check_stock_code_validity(stock_code)
    
    # 调试各个新闻源
    sina_news = debug_sina_news(stock_code)
    eastmoney_news = debug_eastmoney_news(stock_code)
    xueqiu_news = debug_xueqiu_news(stock_code)
    
    # 总结
    print("\n" + "="*60)
    print("📊 新闻获取调试总结")
    print("="*60)
    
    print(f"\n新浪财经新闻: {len(sina_news)} 条")
    print(f"东方财富新闻: {len(eastmoney_news)} 条")
    print(f"雪球新闻: {len(xueqiu_news)} 条")
    
    total_news = len(sina_news) + len(eastmoney_news) + len(xueqiu_news)
    
    if total_news == 0:
        print("\n❓ 结论: 所有新闻源都返回0条新闻")
        print("可能原因:")
        print("1. 股票代码格式不正确")
        print("2. 该股票确实没有相关新闻")
        print("3. 新闻源接口变更或限制")
        print("4. 网络连接问题")
    else:
        print(f"\n✅ 结论: 成功获取到 {total_news} 条新闻")
    
    print("\n✅ 调试完成！")

if __name__ == "__main__":
    main() 