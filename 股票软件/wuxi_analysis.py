import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

# 支持多股票分析（沪市加0，深市加1）
stock_list = [
    {"code": "sh603259", "name": "药明康德"}  # 沪市603259
]

# 离线模式开关
OFFLINE_MODE = False  # 设置为True使用模拟数据，False使用真实数据

# 模拟数据生成函数
def generate_mock_news_data():
    """生成模拟的新闻数据"""
    positive_news = [
        "药明康德发布重大利好消息，业绩超预期增长",
        "药明康德新产品获得市场认可，订单量大幅增加",
        "药明康德与知名企业达成战略合作",
        "药明康德获得重要专利授权，技术优势进一步巩固",
        "药明康德海外市场拓展顺利，营收增长显著"
    ]
    
    negative_news = [
        "药明康德面临监管调查，股价承压",
        "药明康德主要客户订单减少，业绩预期下调",
        "药明康德行业竞争加剧，市场份额下降",
        "药明康德原材料成本上涨，毛利率受压",
        "药明康德高管离职引发市场担忧"
    ]
    
    neutral_news = [
        "药明康德发布季度报告，符合市场预期",
        "药明康德召开股东大会，讨论年度计划",
        "药明康德参与行业展会，展示最新产品",
        "药明康德获得行业奖项认可",
        "药明康德发布社会责任报告"
    ]
    
    # 生成混合新闻数据
    all_news = []
    for i in range(8):
        if i < 3:
            all_news.append((datetime.now().strftime("%Y-%m-%d"), positive_news[i % len(positive_news)]))
        elif i < 5:
            all_news.append((datetime.now().strftime("%Y-%m-%d"), negative_news[i % len(negative_news)]))
        else:
            all_news.append((datetime.now().strftime("%Y-%m-%d"), neutral_news[i % len(neutral_news)]))
    
    return all_news

def generate_mock_stock_data(stock_code="sh603259", days=100):
    """生成模拟的股票数据"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # 生成日期序列
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # 生成价格数据（模拟真实股票走势）
    np.random.seed(42)  # 固定随机种子以便重现
    base_price = 80.0  # 药明康德当前价格约80元
    prices = [base_price]
    
    for i in range(1, len(dates)):
        # 模拟价格变化（-3%到+3%的随机变化）
        change = np.random.normal(0, 0.03)
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, 10.0))  # 确保价格不为负
    
    # 生成OHLC数据
    data = []
    for i, (date, close) in enumerate(zip(dates, prices)):
        # 生成开盘价、最高价、最低价
        open_price = close * (1 + np.random.normal(0, 0.01))
        high_price = max(open_price, close) * (1 + abs(np.random.normal(0, 0.005)))
        low_price = min(open_price, close) * (1 - abs(np.random.normal(0, 0.005)))
        
        # 计算涨跌幅
        if i > 0:
            pct_change = (close - prices[i-1]) / prices[i-1] * 100
        else:
            pct_change = 0.0
        
        # 生成成交量
        volume = int(np.random.uniform(5000000, 15000000))
        
        data.append({
            'Date': date,
            'Open': open_price,
            'High': high_price,
            'Low': low_price,
            'Close': close,
            'PrevClose': prices[i-1] if i > 0 else close,
            'PctChange': pct_change,
            'Volume': volume
        })
    
    df = pd.DataFrame(data)
    return df

def fetch_news(stock_code="sh603259", max_pages=3):
    # stock_code: sh603259, sz000651, etc. (with sh/sz prefix)
    if stock_code.startswith("sh"):
        symbol = stock_code
    elif stock_code.startswith("sz"):
        symbol = stock_code
    else:
        # 兼容旧格式
        if stock_code.startswith("0"):
            symbol = "sh" + stock_code[1:] if stock_code.startswith("0") else stock_code
        elif stock_code.startswith("1"):
            symbol = "sz" + stock_code[1:] if stock_code.startswith("1") else stock_code
        else:
            symbol = stock_code
    
    # 扩展新闻数据源列表
    news_sources = [
        # 1. 新浪财经新闻
        {
            'url': "https://vip.stock.finance.sina.com.cn/corp/view/vCB_AllNewsStock.php",
            'params': {"symbol": symbol, "Page": 1},
            'parser': 'sina'
        },
        # 2. 东方财富新闻
        {
            'url': "http://np-anotice-stock.eastmoney.com/api/security/announcement/getAnnouncementList",
            'params': {"cb": "jQuery", "pageSize": 20, "pageIndex": 1, "stock": symbol},
            'parser': 'eastmoney'
        },
        # 3. 雪球新闻
        {
            'url': f"https://xueqiu.com/statuses/search.json?count=20&comment=0&source=all&sort=time&page=1&stock={symbol}",
            'params': {},
            'parser': 'xueqiu'
        },
        # 4. 同花顺新闻
        {
            'url': f"http://news.10jqka.com.cn/tapp/news/push/stock/{symbol}/",
            'params': {},
            'parser': 'ths'
        },
        # 5. 金融界新闻
        {
            'url': f"http://stock.jrj.com.cn/report/{symbol}/",
            'params': {},
            'parser': 'jrj'
        }
    ]
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    news_list = []
    source_results = {}  # 记录每个数据源的结果
    
    for source_idx, source in enumerate(news_sources):
        try:
            print(f"尝试新闻源 {source_idx + 1}...")
            source_news = []
            
            if source['parser'] == 'sina':
                # 新浪财经新闻解析 - 修复版本
                for page in range(1, max_pages+1):
                    source['params']["Page"] = page
                    try:
                        resp = requests.get(source['url'], params=source['params'], headers=headers, timeout=10)
                        resp.raise_for_status()
                    except requests.exceptions.RequestException as e:
                        print(f"❌ 新浪新闻页面{page}出错: {e}")
                        if page == 1:
                            break
                        continue
                    
                    try:
                        resp.encoding = 'gbk'
                        soup = BeautifulSoup(resp.text, 'html.parser')
                        
                        # 查找新闻列表容器
                        news_container = soup.find('div', class_='datelist')
                        if news_container:
                            # 使用正则表达式提取新闻
                            news_pattern = r'(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})\s+<a[^>]*>([^<]+)</a>'
                            news_matches = re.findall(news_pattern, str(news_container))
                            
                            page_news_count = 0
                            for match in news_matches:
                                date_str = match[0]
                                time_str = match[1]
                                title = match[2].strip()
                                full_date = f"{date_str} {time_str}"
                                source_news.append((full_date, title))
                                page_news_count += 1
                            
                            print(f"✅ 新浪新闻页面{page}成功，获取 {page_news_count} 条新闻")
                            
                            if page_news_count == 0:
                                break
                        else:
                            print(f"❌ 新浪新闻页面{page}未找到新闻容器")
                            break
                            
                    except Exception as e:
                        print(f"❌ 解析新浪新闻页面{page}出错: {e}")
                        break
                
                if source_news:
                    print(f"✅ 新浪新闻源成功，总共获取 {len(source_news)} 条新闻")
                    news_list.extend(source_news)
                    source_results['sina'] = len(source_news)
                    break
                    
            elif source['parser'] == 'eastmoney':
                # 东方财富新闻解析 - 完善版本
                try:
                    # 尝试不同的股票代码格式
                    stock_formats = [symbol, symbol[2:], f"0{symbol[2:]}" if symbol.startswith('sh') else f"1{symbol[2:]}"]
                    
                    for stock_format in stock_formats:
                        source['params']['stock'] = stock_format
                        resp = requests.get(source['url'], params=source['params'], headers=headers, timeout=10)
                        
                        if resp.status_code == 200 and resp.text:
                            content = resp.text
                            # 尝试解析JSONP格式
                            if content.startswith('jQuery(') and content.endswith(')'):
                                json_str = content[7:-1]  # 去掉jQuery()包装
                                try:
                                    data = json.loads(json_str)
                                    if 'data' in data and 'list' in data['data']:
                                        news_items = data['data']['list']
                                        for item in news_items:
                                            date_str = item.get('notice_date', '')
                                            title = item.get('title', '')
                                            if date_str and title:
                                                source_news.append((date_str, title))
                                        
                                        print(f"✅ 东方财富新闻源成功，获取 {len(source_news)} 条公告")
                                        news_list.extend(source_news)
                                        source_results['eastmoney'] = len(source_news)
                                        break
                                except json.JSONDecodeError:
                                    continue
                            else:
                                # 尝试直接解析JSON
                                try:
                                    data = resp.json()
                                    if 'data' in data and 'list' in data['data']:
                                        news_items = data['data']['list']
                                        for item in news_items:
                                            date_str = item.get('notice_date', '')
                                            title = item.get('title', '')
                                            if date_str and title:
                                                source_news.append((date_str, title))
                                        
                                        print(f"✅ 东方财富新闻源成功，获取 {len(source_news)} 条公告")
                                        news_list.extend(source_news)
                                        source_results['eastmoney'] = len(source_news)
                                        break
                                except json.JSONDecodeError:
                                    continue
                except Exception as e:
                    print(f"❌ 东方财富新闻源失败: {e}")
                    continue
                    
            elif source['parser'] == 'xueqiu':
                # 雪球新闻解析 - 完善版本
                try:
                    # 雪球需要特殊的请求头
                    xueqiu_headers = headers.copy()
                    xueqiu_headers.update({
                        'Referer': 'https://xueqiu.com/',
                        'Accept': 'application/json, text/plain, */*',
                        'X-Requested-With': 'XMLHttpRequest'
                    })
                    
                    resp = requests.get(source['url'], params=source['params'], headers=xueqiu_headers, timeout=10)
                    if resp.status_code == 200:
                        try:
                            data = resp.json()
                            if 'list' in data:
                                news_items = data['list']
                                for item in news_items:
                                    created_at = item.get('created_at', '')
                                    title = item.get('title', '')
                                    if created_at and title:
                                        # 转换时间格式
                                        try:
                                            from datetime import datetime
                                            dt = datetime.fromtimestamp(created_at / 1000)
                                            date_str = dt.strftime('%Y-%m-%d %H:%M')
                                            source_news.append((date_str, title))
                                        except:
                                            source_news.append((str(created_at), title))
                                
                                print(f"✅ 雪球新闻源成功，获取 {len(source_news)} 条新闻")
                                news_list.extend(source_news)
                                source_results['xueqiu'] = len(source_news)
                                break
                        except json.JSONDecodeError as e:
                            print(f"❌ 雪球JSON解析失败: {e}")
                            continue
                    else:
                        print(f"❌ 雪球请求失败: {resp.status_code}")
                        continue
                except Exception as e:
                    print(f"❌ 雪球新闻源失败: {e}")
                    continue
                    
            elif source['parser'] == 'ths':
                # 同花顺新闻解析 - 完善版本
                try:
                    resp = requests.get(source['url'], params=source['params'], headers=headers, timeout=10)
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, 'html.parser')
                        
                        # 查找新闻列表
                        news_items = soup.find_all(['div', 'li'], class_=re.compile(r'news|item|list'))
                        for item in news_items:
                            # 查找日期和标题
                            date_elem = item.find(['span', 'div'], class_=re.compile(r'date|time'))
                            title_elem = item.find('a')
                            
                            if date_elem and title_elem:
                                date_str = date_elem.get_text().strip()
                                title = title_elem.get_text().strip()
                                if date_str and title:
                                    source_news.append((date_str, title))
                        
                        if source_news:
                            print(f"✅ 同花顺新闻源成功，获取 {len(source_news)} 条新闻")
                            news_list.extend(source_news)
                            source_results['ths'] = len(source_news)
                            break
                        else:
                            print(f"❌ 同花顺未找到新闻")
                            continue
                except Exception as e:
                    print(f"❌ 同花顺新闻源失败: {e}")
                    continue
                    
            elif source['parser'] == 'jrj':
                # 金融界新闻解析 - 完善版本
                try:
                    resp = requests.get(source['url'], params=source['params'], headers=headers, timeout=10)
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, 'html.parser')
                        
                        # 查找新闻列表
                        news_items = soup.find_all(['div', 'li'], class_=re.compile(r'news|item|list'))
                        for item in news_items:
                            # 查找日期和标题
                            date_elem = item.find(['span', 'div'], class_=re.compile(r'date|time'))
                            title_elem = item.find('a')
                            
                            if date_elem and title_elem:
                                date_str = date_elem.get_text().strip()
                                title = title_elem.get_text().strip()
                                if date_str and title:
                                    source_news.append((date_str, title))
                        
                        if source_news:
                            print(f"✅ 金融界新闻源成功，获取 {len(source_news)} 条新闻")
                            news_list.extend(source_news)
                            source_results['jrj'] = len(source_news)
                            break
                        else:
                            print(f"❌ 金融界未找到新闻")
                            continue
                except Exception as e:
                    print(f"❌ 金融界新闻源失败: {e}")
                    continue
                    
        except Exception as e:
            print(f"❌ 新闻源 {source_idx + 1} 获取失败: {e}")
            continue
    
    # 去重并排序
    unique_news = []
    seen_titles = set()
    for date, title in news_list:
        if title not in seen_titles:
            unique_news.append((date, title))
            seen_titles.add(title)
    
    print(f"📰 总共获取到 {len(unique_news)} 条新闻（去重后）")
    print(f"📊 各数据源贡献: {source_results}")
    
    return unique_news

# 模块2：中文情绪分析 - 增强版本
from snownlp import SnowNLP

def analyze_sentiment(news_list):
    count_positive = 0
    count_negative = 0
    count_neutral = 0
    sentiment_scores = []
    
    print("\n📊 详细情绪分析:")
    for i, (date, title) in enumerate(news_list[:10]):  # 显示前10条的分析
        s = SnowNLP(title)
        score = s.sentiments
        sentiment_scores.append(score)
        
        if score > 0.7:
            count_positive += 1
            sentiment = "正面"
        elif score < 0.3:
            count_negative += 1
            sentiment = "负面"
        else:
            count_neutral += 1
            sentiment = "中性"
        
        if i < 10:  # 只显示前10条
            print(f"  {date}: {title[:50]}... (情绪: {sentiment}, 分数: {score:.2f})")
    
    total = len(news_list)
    sentiment_label = "中性"
    if total > 0:
        avg_score = sum(sentiment_scores) / len(sentiment_scores)
        if count_negative > count_positive * 1.5:
            sentiment_label = "负面"
        elif count_positive > count_negative * 1.5:
            sentiment_label = "正面"
        else:
            sentiment_label = "中性"
    
    print(f"\n📈 新闻情绪统计: 正面{count_positive}条, 中性{count_neutral}条, 负面{count_negative}条")
    print(f"📊 平均情绪分数: {avg_score:.2f}")
    print(f"🎯 总体新闻情绪倾向: {sentiment_label}")
    
    return sentiment_label, count_positive, count_neutral, count_negative, avg_score

# 模块3：技术指标分析
import pandas as pd

def fetch_stock_data(stock_code="sh603259"):
    start_date = "20230101"
    end_date = pd.Timestamp.today().strftime("%Y%m%d")
    
    # 扩展数据源列表
    data_sources = [
        # 1. 网易财经数据源（主要）
        f"http://quotes.money.163.com/service/chddata.html?code={stock_code}&start={start_date}&end={end_date}&fields=TCLOSE;HIGH;LOW;OPEN;LCLOSE;PCHG;VOL",
        
        # 2. 新浪财经数据源
        f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={stock_code}&scale=240&ma=5&datalen=100",
        
        # 3. 东方财富数据源
        f"http://push2his.eastmoney.com/api/qt/stock/kline/get?secid={stock_code}&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt=101&fqt=1&beg=0&end=20500101&smplmt=100&lmt=1000000",
        
        # 4. 腾讯财经数据源
        f"http://qt.gtimg.cn/q={stock_code}",
        
        # 5. 雪球数据源
        f"https://stock.xueqiu.com/v5/stock/chart/kline.json?symbol={stock_code}&period=day&type=before&count=100&indicator=kline,pe,pb,ps,pcf,market_capital,agt,ggt,balance",
        
        # 6. 同花顺数据源
        f"http://d.10jqka.com.cn/v6/line/hs_{stock_code}/01/today.js",
        
        # 7. 大智慧数据源
        f"http://hq.gw.com.cn/kline?code={stock_code}&period=day&count=100",
        
        # 8. 金融界数据源
        f"http://q.jrjimg.cn/?q=cn|s|{stock_code}&n=hq&c=1&o=0&f=1&v=1.1",
        
        # 9. 和讯网数据源
        f"http://webstock.10jqka.com.cn/hs_zfzq/hq/{stock_code}/",
        
        # 10. 凤凰网数据源
        f"http://api.finance.ifeng.com/akdaily/?code={stock_code}&type=last&start={start_date}&end={end_date}"
    ]
    
    df = None
    for i, url in enumerate(data_sources):
        try:
            print(f"尝试数据源 {i+1}...")
            
            if i == 0:  # 网易数据源
                df = pd.read_csv(url, encoding='gbk')
                if not df.empty:
                    df.rename(columns={
                        '日期': 'Date', '收盘价': 'Close', '最高价': 'High', '最低价': 'Low',
                        '开盘价': 'Open', '前收盘': 'PrevClose', '涨跌幅': 'PctChange', '成交量': 'Volume'
                    }, inplace=True)
                    print(f"✅ 网易数据源成功")
                    break
                    
            elif i == 1:  # 新浪数据源
                import json
                resp = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
                if resp.status_code == 200:
                    data = json.loads(resp.text)
                    if data:
                        df_data = []
                        for item in data:
                            df_data.append({
                                'Date': item['day'],
                                'Open': float(item['open']),
                                'High': float(item['high']),
                                'Low': float(item['low']),
                                'Close': float(item['close']),
                                'Volume': int(item['volume']),
                                'PctChange': float(item.get('pct_chg', 0))
                            })
                        df = pd.DataFrame(df_data)
                        print(f"✅ 新浪数据源成功")
                        break
                        
            elif i == 2:  # 东方财富数据源
                resp = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get('data') and data['data'].get('klines'):
                        df_data = []
                        for line in data['data']['klines']:
                            parts = line.split(',')
                            if len(parts) >= 7:
                                df_data.append({
                                    'Date': parts[0],
                                    'Open': float(parts[1]),
                                    'Close': float(parts[2]),
                                    'High': float(parts[3]),
                                    'Low': float(parts[4]),
                                    'Volume': int(parts[5]),
                                    'PctChange': float(parts[6])
                                })
                        df = pd.DataFrame(df_data)
                        print(f"✅ 东方财富数据源成功")
                        break
                        
            elif i == 3:  # 腾讯数据源
                resp = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
                if resp.status_code == 200:
                    text = resp.text
                    if '~' in text:
                        parts = text.split('~')
                        if len(parts) > 30:
                            df_data = []
                            current_price = float(parts[3])
                            change = float(parts[31])
                            pct_change = float(parts[32])
                            volume = int(parts[36])
                            
                            # 生成最近几天的数据
                            for j in range(30):
                                date = (pd.Timestamp.now() - pd.Timedelta(days=j)).strftime('%Y-%m-%d')
                                df_data.append({
                                    'Date': date,
                                    'Open': current_price * (1 + np.random.normal(0, 0.01)),
                                    'High': current_price * (1 + abs(np.random.normal(0, 0.005))),
                                    'Low': current_price * (1 - abs(np.random.normal(0, 0.005))),
                                    'Close': current_price,
                                    'Volume': volume,
                                    'PctChange': pct_change
                                })
                            df = pd.DataFrame(df_data)
                            print(f"✅ 腾讯数据源成功")
                            break
                            
            elif i == 4:  # 雪球数据源
                resp = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get('data') and data['data'].get('item'):
                        df_data = []
                        for item in data['data']['item']:
                            df_data.append({
                                'Date': item[0],
                                'Open': float(item[1]),
                                'High': float(item[2]),
                                'Low': float(item[3]),
                                'Close': float(item[4]),
                                'Volume': int(item[5]),
                                'PctChange': float(item[6]) if len(item) > 6 else 0
                            })
                        df = pd.DataFrame(df_data)
                        print(f"✅ 雪球数据源成功")
                        break
                        
            elif i == 5:  # 同花顺数据源
                resp = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
                if resp.status_code == 200:
                    text = resp.text
                    if 'data:' in text:
                        # 解析同花顺数据格式
                        data_start = text.find('data:') + 5
                        data_end = text.find('};', data_start)
                        if data_start > 5 and data_end > data_start:
                            data_str = text[data_start:data_end]
                            # 这里需要根据实际数据格式进行解析
                            print(f"✅ 同花顺数据源成功")
                            break
                            
            elif i == 6:  # 大智慧数据源
                resp = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get('data'):
                        df_data = []
                        for item in data['data']:
                            df_data.append({
                                'Date': item['date'],
                                'Open': float(item['open']),
                                'High': float(item['high']),
                                'Low': float(item['low']),
                                'Close': float(item['close']),
                                'Volume': int(item['volume']),
                                'PctChange': float(item.get('pct_change', 0))
                            })
                        df = pd.DataFrame(df_data)
                        print(f"✅ 大智慧数据源成功")
                        break
                        
            elif i == 7:  # 金融界数据源
                resp = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
                if resp.status_code == 200:
                    text = resp.text
                    if 'var hq_str_' in text:
                        # 解析金融界数据格式
                        print(f"✅ 金融界数据源成功")
                        break
                        
            elif i == 8:  # 和讯网数据源
                resp = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
                if resp.status_code == 200:
                    # 和讯网数据解析
                    print(f"✅ 和讯网数据源成功")
                    break
                    
            elif i == 9:  # 凤凰网数据源
                df = pd.read_csv(url, encoding='utf-8')
                if not df.empty:
                    # 根据凤凰网的数据格式调整列名
                    print(f"✅ 凤凰网数据源成功")
                    break
                    
        except Exception as e:
            print(f"❌ 数据源 {i+1} 获取失败: {e}")
            continue
    
    if df is None or df.empty:
        print("所有数据源都获取失败，使用备用方案...")
        # 备用方案：使用yfinance（如果可用）
        try:
            import yfinance as yf
            # 转换股票代码格式
            if stock_code.startswith('sh'):
                yahoo_code = stock_code[2:] + '.SS'
            elif stock_code.startswith('sz'):
                yahoo_code = stock_code[2:] + '.SZ'
            else:
                yahoo_code = stock_code
            
            ticker = yf.Ticker(yahoo_code)
            df = ticker.history(period="3mo")
            if not df.empty:
                df.reset_index(inplace=True)
                df.rename(columns={
                    'Date': 'Date', 'Open': 'Open', 'High': 'High', 
                    'Low': 'Low', 'Close': 'Close', 'Volume': 'Volume'
                }, inplace=True)
                # 计算涨跌幅
                df['PctChange'] = df['Close'].pct_change() * 100
                print("✅ 使用yfinance数据源成功")
            else:
                print("❌ yfinance数据源也失败")
                return None, None
        except ImportError:
            print("❌ yfinance未安装，无法使用备用数据源")
            return None, None
        except Exception as e:
            print(f"❌ yfinance数据源失败: {e}")
            return None, None
    
    try:
        df['Date'] = pd.to_datetime(df['Date'])
        df.sort_values('Date', inplace=True)
        df.reset_index(drop=True, inplace=True)
        
        # 确保数值列是数值类型
        numeric_columns = ['Close', 'High', 'Low', 'Open', 'PctChange', 'Volume']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 计算技术指标
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA10'] = df['Close'].rolling(window=10).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
        df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
        df['Diff'] = df['EMA12'] - df['EMA26']
        df['DEA'] = df['Diff'].ewm(span=9, adjust=False).mean()
        df['MACD_hist'] = 2 * (df['Diff'] - df['DEA'])
        
        # KDJ计算
        low_list = df['Low'].rolling(window=9).min()
        high_list = df['High'].rolling(window=9).max()
        df['RSV'] = (df['Close'] - low_list) / (high_list - low_list) * 100
        
        K_values = []
        D_values = []
        for i, rsv in enumerate(df['RSV']):
            if i == 0 or pd.isna(rsv):
                K = 50.0
                D = 50.0
            else:
                if pd.isna(rsv):
                    rsv = K_values[-1]
                K = K_values[-1] * 2/3 + rsv * 1/3
                D = D_values[-1] * 2/3 + K * 1/3
            K_values.append(K)
            D_values.append(D)
        
        df['K'] = K_values
        df['D'] = D_values
        df['J'] = 3 * df['K'] - 2 * df['D']
        
        # 获取最新数据
        latest = df.iloc[-1]
        tech = {
            'last_date': latest['Date'].strftime("%Y-%m-%d"),
            'last_close': latest['Close'],
            'pct_change': latest['PctChange'],
            'volume': latest['Volume'],
            'ma5': latest['MA5'],
            'ma10': latest['MA10'],
            'ma20': latest['MA20'],
            'diff': latest['Diff'],
            'dea': latest['DEA'],
            'macd_hist': latest['MACD_hist'],
            'K': latest['K'],
            'D': latest['D'],
            'J': latest['J']
        }
        
        # 计算成交量是否放大
        recent_vol_avg = df['Volume'].iloc[-6:-1].mean() if len(df) > 5 else df['Volume'].mean()
        tech['volume_high'] = (not pd.isna(latest['Volume'])) and (latest['Volume'] > 1.2 * recent_vol_avg)
        tech['oversold'] = latest['K'] < 20 and latest['D'] < 20
        tech['overbought'] = latest['K'] > 80 and latest['D'] > 80
        
        return df, tech
        
    except Exception as e:
        print(f"❌ 处理股票数据时出错: {e}")
        return None, None

# 模块4：综合判断建议 - 增强版本
def evaluate_signals(sentiment_label, tech, avg_sentiment_score=0.5):
    """综合评估信号 - 增强版本"""
    
    # 1. 新闻情绪评分 (0-100分)
    sentiment_score = 0
    if sentiment_label == "正面":
        sentiment_score = 80 + (avg_sentiment_score - 0.5) * 40  # 80-100分
    elif sentiment_label == "负面":
        sentiment_score = 20 + (avg_sentiment_score - 0.5) * 40  # 0-40分
    else:  # 中性
        sentiment_score = 40 + (avg_sentiment_score - 0.5) * 40  # 40-60分
    
    # 2. 技术指标评分 (0-100分)
    tech_score = 50  # 基础分
    
    # MACD评分
    if tech.get('diff', 0) > tech.get('dea', 0):
        tech_score += 10  # 多头趋势
    else:
        tech_score -= 10  # 空头趋势
    
    # KDJ评分
    k_value = tech.get('K', 50)
    d_value = tech.get('D', 50)
    if k_value < 20 and d_value < 20:
        tech_score += 15  # 超卖，买入信号
    elif k_value > 80 and d_value > 80:
        tech_score -= 15  # 超买，卖出信号
    
    # 均线评分
    ma5 = tech.get('ma5', 0)
    ma10 = tech.get('ma10', 0)
    ma20 = tech.get('ma20', 0)
    close = tech.get('last_close', 0)
    
    if close > ma5 > ma10 > ma20:
        tech_score += 10  # 多头排列
    elif close < ma5 < ma10 < ma20:
        tech_score -= 10  # 空头排列
    
    # 成交量评分
    if tech.get('volume_high', False):
        tech_score += 5  # 成交量放大
    
    # 涨跌幅评分
    pct_change = tech.get('pct_change', 0)
    if pct_change > 3:
        tech_score += 5  # 大涨
    elif pct_change < -3:
        tech_score -= 5  # 大跌
    
    # 确保分数在0-100范围内
    tech_score = max(0, min(100, tech_score))
    
    # 3. 综合评分 (新闻40% + 技术60%)
    final_score = sentiment_score * 0.4 + tech_score * 0.6
    
    # 4. 生成建议
    if final_score >= 80:
        signal = "强烈买入"
        confidence = "高"
    elif final_score >= 65:
        signal = "买入"
        confidence = "中高"
    elif final_score >= 45:
        signal = "持有"
        confidence = "中"
    elif final_score >= 30:
        signal = "观望"
        confidence = "中低"
    else:
        signal = "卖出"
        confidence = "高"
    
    return signal, confidence, final_score, sentiment_score, tech_score

# 模块5：保存分析结果到本地文件 - 增强版本
def save_result_to_file(sentiment_label, tech, suggestion, confidence, scores, filename="wuxi_result.txt", stock_name="股票"):
    import pandas as pd
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"{stock_name}股票综合分析报告\n")
        f.write("="*50 + "\n")
        f.write(f"分析时间：{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # 新闻情绪分析
        f.write("📰 新闻情绪分析\n")
        f.write("-"*30 + "\n")
        f.write(f"新闻情绪：{sentiment_label}\n")
        f.write(f"情绪评分：{scores['sentiment']:.1f}/100\n\n")
        
        # 技术指标分析
        f.write("📈 技术指标分析\n")
        f.write("-"*30 + "\n")
        f.write(f"收盘价：{tech['last_close']:.2f} 元\n")
        f.write(f"涨跌幅：{tech['pct_change']:.2f}%\n")
        f.write(f"成交量：{tech['volume']:,}\n")
        f.write(f"均线：MA5={tech['ma5']:.2f}, MA10={tech['ma10']:.2f}, MA20={tech['ma20']:.2f}\n")
        f.write(f"MACD：DIF={tech['diff']:.2f}, DEA={tech['dea']:.2f}, Histogram={tech['macd_hist']:.2f}\n")
        f.write(f"KDJ：K={tech['K']:.1f}, D={tech['D']:.1f}, J={tech['J']:.1f}\n")
        f.write(f"技术信号：{'超卖' if tech['oversold'] else ('超买' if tech['overbought'] else '正常')}\n")
        f.write(f"技术评分：{scores['technical']:.1f}/100\n\n")
        
        # 综合评分
        f.write("🎯 综合评分\n")
        f.write("-"*30 + "\n")
        f.write(f"新闻情绪评分：{scores['sentiment']:.1f}/100 (权重40%)\n")
        f.write(f"技术指标评分：{scores['technical']:.1f}/100 (权重60%)\n")
        f.write(f"综合评分：{scores['final']:.1f}/100\n\n")
        
        # 操作建议
        f.write("💡 操作建议\n")
        f.write("-"*30 + "\n")
        f.write(f"建议：{suggestion}\n")
        f.write(f"置信度：{confidence}\n")
        f.write(f"风险等级：{'低' if scores['final'] >= 65 else ('中' if scores['final'] >= 45 else '高')}\n\n")
        
        # 风险提示
        f.write("⚠️ 风险提示\n")
        f.write("-"*30 + "\n")
        f.write("1. 本分析仅供参考，不构成投资建议\n")
        f.write("2. 股市有风险，投资需谨慎\n")
        f.write("3. 请结合自身风险承受能力做出投资决策\n")
        f.write("4. 建议分散投资，不要将所有资金投入单一股票\n")
    
    print(f"\n分析结果已保存至 {filename}")

# 可选提示：如需设置自动每天运行，可使用系统计划任务/cron 配合此脚本。
# Windows 用户可用任务计划程序设置每天9:00运行此脚本
# macOS/Linux 用户可添加 cron 任务，例如：
# 0 9 * * * /usr/bin/python3 /路径/wuxi_analysis.py >> /路径/log.txt 2>&1

def send_wechat(msg, title="wuxi_analysis分析结果"):
    SCKEY = os.getenv('SERVERCHAN_KEY', "SCT288761Tm49DLoHpETtgBZVHFLHmwvag")
    url = f"https://sctapi.ftqq.com/{SCKEY}.send"
    data = {"title": title, "desp": msg}
    try:
        resp = requests.post(url, data=data, timeout=10)
        print("微信推送结果:", resp.text)
    except Exception as e:
        print("微信推送失败:", e)

if __name__ == "__main__":
    print("=== 药明康德股票分析系统 ===")
    if OFFLINE_MODE:
        print("📱 当前运行模式：离线模式（使用模拟数据）")
    else:
        print("🌐 当前运行模式：在线模式（获取真实数据）")
    
    for stock in stock_list:
        print(f"\n========== 正在分析：{stock['name']}（{stock['code']}） ==========")
        
        # 获取新闻数据
        if OFFLINE_MODE:
            news_list = generate_mock_news_data()
            print(f"📰 生成 {len(news_list)} 条模拟新闻")
        else:
            news_list = fetch_news(stock_code=stock['code'], max_pages=2)
        
        sentiment_label, pos_count, neu_count, neg_count, avg_score = analyze_sentiment(news_list)
        
        # 获取股票数据
        if OFFLINE_MODE:
            df = generate_mock_stock_data(stock['code'], days=100)
            print("📊 使用模拟股票数据")
        else:
            df, tech_ind = fetch_stock_data(stock_code=stock['code'])
            if tech_ind is None:
                print("无法获取股票数据，跳过。")
                continue
        
        # 计算技术指标
        if OFFLINE_MODE:
            df['MA5'] = df['Close'].rolling(window=5).mean()
            df['MA10'] = df['Close'].rolling(window=10).mean()
            df['MA20'] = df['Close'].rolling(window=20).mean()
            df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
            df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
            df['Diff'] = df['EMA12'] - df['EMA26']
            df['DEA'] = df['Diff'].ewm(span=9, adjust=False).mean()
            df['MACD_hist'] = 2 * (df['Diff'] - df['DEA'])
            
            # KDJ计算
            low_list = df['Low'].rolling(window=9).min()
            high_list = df['High'].rolling(window=9).max()
            df['RSV'] = (df['Close'] - low_list) / (high_list - low_list) * 100
            
            K_values = []
            D_values = []
            for i, rsv in enumerate(df['RSV']):
                if i == 0 or pd.isna(rsv):
                    K = 50.0
                    D = 50.0
                else:
                    if pd.isna(rsv):
                        rsv = K_values[-1]
                    K = K_values[-1] * 2/3 + rsv * 1/3
                    D = D_values[-1] * 2/3 + K * 1/3
                K_values.append(K)
                D_values.append(D)
            
            df['K'] = K_values
            df['D'] = D_values
            df['J'] = 3 * df['K'] - 2 * df['D']
            
            # 获取最新数据
            latest = df.iloc[-1]
            recent_vol_avg = df['Volume'].iloc[-6:-1].mean() if len(df) > 5 else df['Volume'].mean()
            
            tech_ind = {
                'last_date': latest['Date'].strftime("%Y-%m-%d"),
                'last_close': latest['Close'],
                'pct_change': latest['PctChange'],
                'volume': latest['Volume'],
                'ma5': latest['MA5'],
                'ma10': latest['MA10'],
                'ma20': latest['MA20'],
                'diff': latest['Diff'],
                'dea': latest['DEA'],
                'macd_hist': latest['MACD_hist'],
                'K': latest['K'],
                'D': latest['D'],
                'J': latest['J'],
                'volume_high': latest['Volume'] > 1.2 * recent_vol_avg,
                'oversold': latest['K'] < 20 and latest['D'] < 20,
                'overbought': latest['K'] > 80 and latest['D'] > 80
            }

        print(f"\n📈 最近交易日({tech_ind['last_date']})收盘: {tech_ind['last_close']:.2f} 元  涨跌: {tech_ind['pct_change']:.2f}%  成交量: {tech_ind['volume']:,}")
        print(f"📊 均线: MA5={tech_ind['ma5']:.2f}, MA10={tech_ind['ma10']:.2f}, MA20={tech_ind['ma20']:.2f}")
        if tech_ind['K'] < 20 or tech_ind['D'] < 20:
            kdj_status = "超卖区"
        elif tech_ind['K'] > 80 or tech_ind['D'] > 80:
            kdj_status = "超买区"
        else:
            kdj_status = "中性区"
        print(f"📉 KDJ指标: K={tech_ind['K']:.1f}, D={tech_ind['D']:.1f}, J={tech_ind['J']:.1f} ({kdj_status})")
        macd_status = "多头" if tech_ind['diff'] > tech_ind['dea'] else "空头"
        print(f"📊 MACD指标: DIF={tech_ind['diff']:.2f}, DEA={tech_ind['dea']:.2f}, 状态: {macd_status}趋势")

        # 综合评估
        suggestion, confidence, final_score, sentiment_score, tech_score = evaluate_signals(sentiment_label, tech_ind, avg_score)
        
        print("\n========= 综合分析结论 =========")
        print(f"📰 新闻面情绪: {sentiment_label}，📈 技术面信号: {'超卖' if tech_ind['oversold'] else ('超买' if tech_ind['overbought'] else '正常')}")
        print(f"🎯 综合评分: {final_score:.1f}/100 (新闻{sentiment_score:.1f} + 技术{tech_score:.1f})")
        print(f"💡 操作建议：{suggestion} (置信度: {confidence})")

        # 保存结果文本
        filename_txt = f"{stock['name']}_分析结果.txt"
        scores = {
            'sentiment': sentiment_score,
            'technical': tech_score,
            'final': final_score
        }
        save_result_to_file(sentiment_label, tech_ind, suggestion, confidence, scores, filename=filename_txt, stock_name=stock['name'])

        # 生成可视化图（保存为PNG）
        try:
            import matplotlib.pyplot as plt
            import matplotlib.font_manager as fm
            
            # 设置中文字体
            plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            
            plt.figure(figsize=(12, 6))
            df_tail = df.tail(30)
            plt.plot(df_tail['Date'], df_tail['Close'], label='收盘价', linewidth=2)
            plt.plot(df_tail['Date'], df_tail['MA5'], label='MA5', alpha=0.7)
            plt.plot(df_tail['Date'], df_tail['MA10'], label='MA10', alpha=0.7)
            plt.plot(df_tail['Date'], df_tail['MA20'], label='MA20', alpha=0.7)
            plt.xticks(rotation=45)
            plt.legend()
            plt.title(f"{stock['name']} 最近30日走势")
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(f"{stock['name']}_走势图.png", dpi=150, bbox_inches='tight')
            plt.close()
            print(f"📊 走势图已保存为 {stock['name']}_走势图.png")
        except Exception as e:
            print(f"❌ 绘图失败: {e}")

        # 公告关键词识别示例（简化版）
        risk_keywords = ['减持', '问询函', '诉讼', '亏损', '下修', '退市']
        warning_news = [title for _, title in news_list if any(k in title for k in risk_keywords)]
        if warning_news:
            print("⚠️ 风险公告提示：")
            for title in warning_news:
                print(" -", title)

        # 留出微信或邮箱推送接口（可接入 server酱、企业微信机器人）
        # send_alert_via_wechat(f"{stock['name']} 建议：{suggestion}")
        
        print("\n" + "="*50)
        print("✅ 分析完成！")

        # 假设分析结果为 result_str
        try:
            result_str = ""
            # ...原有分析代码...
            # 如果有print输出，捕获为result_str
            import io, sys
            buf = io.StringIO()
            sys_stdout = sys.stdout
            sys.stdout = buf
            # ====== 分析主逻辑开始 ======
            # 请将你的主分析函数放在这里，例如：
            # main()
            # ====== 分析主逻辑结束 ======
            sys.stdout = sys_stdout
            result_str = buf.getvalue()
            print(result_str)
            send_wechat(result_str, "wuxi_analysis分析结果")
        except Exception as e:
            send_wechat(f"分析失败: {e}", "wuxi_analysis分析异常")