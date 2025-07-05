#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据源故障诊断脚本
详细分析每个数据源失败的原因，并提供解决方案
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import time

def diagnose_eastmoney(stock_code="sh603259"):
    """诊断东方财富数据源"""
    print("=== 诊断东方财富数据源 ===")
    
    # 测试不同的URL和参数组合
    test_cases = [
        {
            'name': '公告接口1',
            'url': "http://np-anotice-stock.eastmoney.com/api/security/announcement/getAnnouncementList",
            'params': {"cb": "jQuery", "pageSize": 20, "pageIndex": 1, "stock": stock_code}
        },
        {
            'name': '公告接口2',
            'url': "http://np-anotice-stock.eastmoney.com/api/security/announcement/getAnnouncementList",
            'params': {"cb": "jQuery", "pageSize": 20, "pageIndex": 1, "stock": stock_code[2:]}
        },
        {
            'name': '公告接口3',
            'url': "http://np-anotice-stock.eastmoney.com/api/security/announcement/getAnnouncementList",
            'params': {"cb": "jQuery", "pageSize": 20, "pageIndex": 1, "stock": f"0{stock_code[2:]}" if stock_code.startswith('sh') else f"1{stock_code[2:]}"}
        },
        {
            'name': '新闻接口',
            'url': "http://np-anotice-stock.eastmoney.com/api/security/announcement/getAnnouncementList",
            'params': {"cb": "jQuery", "pageSize": 20, "pageIndex": 1, "stock": stock_code, "type": "news"}
        }
    ]
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    for test_case in test_cases:
        print(f"\n测试 {test_case['name']}:")
        print(f"URL: {test_case['url']}")
        print(f"参数: {test_case['params']}")
        
        try:
            resp = requests.get(test_case['url'], params=test_case['params'], headers=headers, timeout=10)
            print(f"状态码: {resp.status_code}")
            print(f"响应长度: {len(resp.text)} 字符")
            print(f"响应内容: {resp.text[:200]}...")
            
            if resp.status_code == 200:
                if resp.text:
                    if resp.text.startswith('jQuery('):
                        print("✅ 返回JSONP格式")
                        # 尝试解析
                        json_str = resp.text[7:-1]
                        try:
                            data = json.loads(json_str)
                            if 'data' in data and 'list' in data['data']:
                                print(f"✅ 解析成功，找到 {len(data['data']['list'])} 条数据")
                                return True
                            else:
                                print("❌ 数据结构不符合预期")
                        except json.JSONDecodeError as e:
                            print(f"❌ JSON解析失败: {e}")
                    else:
                        print("❌ 不是JSONP格式")
                else:
                    print("❌ 响应为空")
            else:
                print(f"❌ HTTP错误: {resp.status_code}")
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
    
    return False

def diagnose_xueqiu(stock_code="sh603259"):
    """诊断雪球数据源"""
    print("\n=== 诊断雪球数据源 ===")
    
    # 测试不同的请求方式
    test_cases = [
        {
            'name': '标准请求',
            'url': f"https://xueqiu.com/statuses/search.json?count=20&comment=0&source=all&sort=time&page=1&stock={stock_code}",
            'headers': {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://xueqiu.com/",
                "Accept": "application/json, text/plain, */*",
                "X-Requested-With": "XMLHttpRequest"
            }
        },
        {
            'name': '简化请求',
            'url': f"https://xueqiu.com/statuses/search.json?count=20&stock={stock_code}",
            'headers': {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        },
        {
            'name': '移动端请求',
            'url': f"https://xueqiu.com/statuses/search.json?count=20&comment=0&source=all&sort=time&page=1&stock={stock_code}",
            'headers': {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15",
                "Referer": "https://xueqiu.com/",
                "Accept": "application/json"
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n测试 {test_case['name']}:")
        print(f"URL: {test_case['url']}")
        
        try:
            resp = requests.get(test_case['url'], headers=test_case['headers'], timeout=10)
            print(f"状态码: {resp.status_code}")
            print(f"响应长度: {len(resp.text)} 字符")
            print(f"响应内容: {resp.text[:200]}...")
            
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    if 'list' in data:
                        print(f"✅ 解析成功，找到 {len(data['list'])} 条数据")
                        return True
                    elif 'error_description' in data:
                        print(f"❌ 接口错误: {data['error_description']}")
                    else:
                        print("❌ 数据结构不符合预期")
                except json.JSONDecodeError as e:
                    print(f"❌ JSON解析失败: {e}")
            else:
                print(f"❌ HTTP错误: {resp.status_code}")
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
    
    return False

def diagnose_ths(stock_code="sh603259"):
    """诊断同花顺数据源"""
    print("\n=== 诊断同花顺数据源 ===")
    
    # 测试不同的URL格式
    test_cases = [
        {
            'name': '标准URL',
            'url': f"http://news.10jqka.com.cn/tapp/news/push/stock/{stock_code}/"
        },
        {
            'name': '简化URL',
            'url': f"http://news.10jqka.com.cn/stock/{stock_code}/"
        },
        {
            'name': 'API URL',
            'url': f"http://news.10jqka.com.cn/api/news/stock/{stock_code}/"
        },
        {
            'name': '移动端URL',
            'url': f"http://m.10jqka.com.cn/stock/{stock_code}/"
        }
    ]
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    for test_case in test_cases:
        print(f"\n测试 {test_case['name']}:")
        print(f"URL: {test_case['url']}")
        
        try:
            resp = requests.get(test_case['url'], headers=headers, timeout=10)
            print(f"状态码: {resp.status_code}")
            print(f"响应长度: {len(resp.text)} 字符")
            
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                title = soup.find('title')
                print(f"页面标题: {title.get_text() if title else '无标题'}")
                
                # 查找可能的新闻元素
                news_elements = soup.find_all(['div', 'li'], class_=re.compile(r'news|item|list'))
                print(f"找到 {len(news_elements)} 个可能的新闻元素")
                
                if news_elements:
                    print("✅ 页面包含新闻元素")
                    return True
                else:
                    print("❌ 页面不包含新闻元素")
            else:
                print(f"❌ HTTP错误: {resp.status_code}")
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
    
    return False

def diagnose_jrj(stock_code="sh603259"):
    """诊断金融界数据源"""
    print("\n=== 诊断金融界数据源 ===")
    
    # 测试不同的URL格式
    test_cases = [
        {
            'name': '标准URL',
            'url': f"http://stock.jrj.com.cn/report/{stock_code}/"
        },
        {
            'name': '新闻URL',
            'url': f"http://stock.jrj.com.cn/news/{stock_code}/"
        },
        {
            'name': 'API URL',
            'url': f"http://stock.jrj.com.cn/api/news/{stock_code}/"
        },
        {
            'name': '移动端URL',
            'url': f"http://m.jrj.com.cn/stock/{stock_code}/"
        }
    ]
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    for test_case in test_cases:
        print(f"\n测试 {test_case['name']}:")
        print(f"URL: {test_case['url']}")
        
        try:
            resp = requests.get(test_case['url'], headers=headers, timeout=10)
            print(f"状态码: {resp.status_code}")
            print(f"响应长度: {len(resp.text)} 字符")
            
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                title = soup.find('title')
                print(f"页面标题: {title.get_text() if title else '无标题'}")
                
                # 查找可能的新闻元素
                news_elements = soup.find_all(['div', 'li'], class_=re.compile(r'news|item|list'))
                print(f"找到 {len(news_elements)} 个可能的新闻元素")
                
                if news_elements:
                    print("✅ 页面包含新闻元素")
                    return True
                else:
                    print("❌ 页面不包含新闻元素")
            else:
                print(f"❌ HTTP错误: {resp.status_code}")
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
    
    return False

def test_alternative_sources(stock_code="sh603259"):
    """测试替代数据源"""
    print("\n=== 测试替代数据源 ===")
    
    alternative_sources = [
        {
            'name': '腾讯财经',
            'url': f"http://qt.gtimg.cn/q={stock_code}",
            'type': 'realtime'
        },
        {
            'name': '网易财经',
            'url': f"http://quotes.money.163.com/service/chddata.html?code={stock_code}&start=20240101&end=20241231&fields=TCLOSE;HIGH;LOW;OPEN;LCLOSE;PCHG;VOL",
            'type': 'historical'
        },
        {
            'name': '凤凰网财经',
            'url': f"http://api.finance.ifeng.com/akdaily/?code={stock_code}&type=last",
            'type': 'historical'
        }
    ]
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    for source in alternative_sources:
        print(f"\n测试 {source['name']}:")
        print(f"URL: {source['url']}")
        
        try:
            resp = requests.get(source['url'], headers=headers, timeout=10)
            print(f"状态码: {resp.status_code}")
            print(f"响应长度: {len(resp.text)} 字符")
            
            if resp.status_code == 200:
                if source['type'] == 'realtime':
                    if '~' in resp.text:
                        print("✅ 实时数据格式正确")
                    else:
                        print("❌ 实时数据格式错误")
                else:
                    print("✅ 历史数据接口可用")
            else:
                print(f"❌ HTTP错误: {resp.status_code}")
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")

def generate_diagnosis_report():
    """生成诊断报告"""
    print("\n" + "="*60)
    print("🔍 数据源故障诊断报告")
    print("="*60)
    
    stock_code = "sh603259"
    
    print(f"\n📊 诊断结果:")
    
    # 诊断各个数据源
    eastmoney_ok = diagnose_eastmoney(stock_code)
    xueqiu_ok = diagnose_xueqiu(stock_code)
    ths_ok = diagnose_ths(stock_code)
    jrj_ok = diagnose_jrj(stock_code)
    
    # 测试替代数据源
    test_alternative_sources(stock_code)
    
    print(f"\n📈 数据源可用性总结:")
    print(f"  ✅ 新浪财经: 可用")
    print(f"  {'✅' if eastmoney_ok else '❌'} 东方财富: {'可用' if eastmoney_ok else '不可用'}")
    print(f"  {'✅' if xueqiu_ok else '❌'} 雪球: {'可用' if xueqiu_ok else '不可用'}")
    print(f"  {'✅' if ths_ok else '❌'} 同花顺: {'可用' if ths_ok else '不可用'}")
    print(f"  {'✅' if jrj_ok else '❌'} 金融界: {'可用' if jrj_ok else '不可用'}")
    
    print(f"\n💡 问题分析:")
    print(f"1. 东方财富: 可能需要特殊的股票代码格式或API密钥")
    print(f"2. 雪球: 需要登录或特殊的请求头，可能有反爬虫机制")
    print(f"3. 同花顺: URL结构可能已变更，需要更新")
    print(f"4. 金融界: 网站结构可能已更新")
    
    print(f"\n🔧 建议解决方案:")
    print(f"1. 优先使用新浪财经作为主要数据源（稳定可靠）")
    print(f"2. 尝试使用替代数据源如腾讯财经、网易财经")
    print(f"3. 考虑添加数据源轮换机制")
    print(f"4. 定期更新数据源URL和解析逻辑")

def send_wechat(msg, title="数据源诊断报告"):
    """发送微信推送"""
    SCKEY = "SCT288761Tm49DLoHpETtgBZVHFLHmwvag"
    url = f"https://sctapi.ftqq.com/{SCKEY}.send"
    data = {"title": title, "desp": msg}
    try:
        resp = requests.post(url, data=data, timeout=10)
        print(f"微信推送结果: {resp.text}")
        if resp.status_code == 200:
            print("✅ 微信推送成功！")
        else:
            print("❌ 微信推送失败")
    except Exception as e:
        print(f"❌ 微信推送异常: {e}")

def main():
    """主函数"""
    print("🔍 开始数据源故障诊断...")
    print(f"⏰ 诊断时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 捕获输出用于推送
    import io
    import sys
    from contextlib import redirect_stdout
    
    # 重定向输出到字符串
    output_buffer = io.StringIO()
    with redirect_stdout(output_buffer):
        generate_diagnosis_report()
    
    # 获取诊断报告内容
    report_content = output_buffer.getvalue()
    
    # 打印到控制台
    print(report_content)
    
    # 发送微信推送
    print("\n📱 正在发送微信推送...")
    send_wechat(report_content, f"数据源诊断报告 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    print(f"\n✅ 诊断完成！")

if __name__ == "__main__":
    main() 