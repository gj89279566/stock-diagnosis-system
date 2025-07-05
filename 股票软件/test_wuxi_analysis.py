import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# 模拟股票数据生成函数
def generate_mock_stock_data(stock_code="sh603259", days=100):
    """生成模拟的股票数据用于测试"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # 生成日期序列
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # 生成价格数据（模拟真实股票走势）
    np.random.seed(42)  # 固定随机种子以便重现
    base_price = 50.0
    prices = [base_price]
    
    for i in range(1, len(dates)):
        # 模拟价格变化（-2%到+2%的随机变化）
        change = np.random.normal(0, 0.02)
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, 1.0))  # 确保价格不为负
    
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
        volume = int(np.random.uniform(1000000, 5000000))
        
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

# 模拟新闻数据生成函数
def generate_mock_news_data():
    """生成模拟的新闻数据用于测试"""
    positive_news = [
        "公司发布重大利好消息，业绩超预期增长",
        "新产品获得市场认可，订单量大幅增加",
        "与知名企业达成战略合作",
        "获得重要专利授权，技术优势进一步巩固",
        "海外市场拓展顺利，营收增长显著"
    ]
    
    negative_news = [
        "公司面临监管调查，股价承压",
        "主要客户订单减少，业绩预期下调",
        "行业竞争加剧，市场份额下降",
        "原材料成本上涨，毛利率受压",
        "高管离职引发市场担忧"
    ]
    
    neutral_news = [
        "公司发布季度报告，符合市场预期",
        "召开股东大会，讨论年度计划",
        "参与行业展会，展示最新产品",
        "获得行业奖项认可",
        "发布社会责任报告"
    ]
    
    # 生成混合新闻数据
    all_news = []
    for i in range(10):
        if i < 4:
            all_news.append((datetime.now().strftime("%Y-%m-%d"), positive_news[i % len(positive_news)]))
        elif i < 7:
            all_news.append((datetime.now().strftime("%Y-%m-%d"), negative_news[i % len(negative_news)]))
        else:
            all_news.append((datetime.now().strftime("%Y-%m-%d"), neutral_news[i % len(neutral_news)]))
    
    return all_news

# 导入原代码中的分析函数
from snownlp import SnowNLP

def analyze_sentiment(news_list):
    count_positive = 0
    count_negative = 0
    count_neutral = 0
    for date, title in news_list:
        s = SnowNLP(title)
        score = s.sentiments
        if score > 0.7:
            count_positive += 1
        elif score < 0.3:
            count_negative += 1
        else:
            count_neutral += 1
    total = len(news_list)
    sentiment_label = "中性"
    if total > 0:
        if count_negative > count_positive * 1.5:
            sentiment_label = "负面"
        elif count_positive > count_negative * 1.5:
            sentiment_label = "正面"
    print(f"新闻情绪统计: 正面{count_positive}条, 中性{count_neutral}条, 负面{count_negative}条")
    print(f"总体新闻情绪倾向: {sentiment_label}")
    return sentiment_label, count_positive, count_neutral, count_negative

def calculate_technical_indicators(df):
    """计算技术指标"""
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
    
    return df

def evaluate_signals(sentiment_label, tech):
    signal = "观望"
    if sentiment_label == "负面":
        if tech.get('pct_change', 0) > 0 and tech.get('volume_high', False):
            signal = "考虑高抛"
        else:
            signal = "观望"
    elif sentiment_label == "正面":
        if tech.get('oversold', False):
            signal = "考虑低吸"
        else:
            signal = "继续持有"
    else:
        if tech.get('overbought', False) and tech.get('volume_high', False):
            signal = "考虑高抛"
        elif tech.get('oversold', False):
            signal = "考虑低吸"
        else:
            signal = "观望"
    return signal

def save_result_to_file(sentiment_label, tech, suggestion, filename="test_result.txt", stock_name="测试股票"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"{stock_name}股票分析报告\n")
        f.write(f"分析时间：{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"新闻情绪：{sentiment_label}\n")
        f.write(f"收盘价：{tech['last_close']:.2f} 元\n")
        f.write(f"涨跌幅：{tech['pct_change']:.2f}%\n")
        f.write(f"成交量：{tech['volume']}\n")
        f.write(f"均线：MA5={tech['ma5']:.2f}, MA10={tech['ma10']:.2f}, MA20={tech['ma20']:.2f}\n")
        f.write(f"MACD：DIF={tech['diff']:.2f}, DEA={tech['dea']:.2f}, Histogram={tech['macd_hist']:.2f}\n")
        f.write(f"KDJ：K={tech['K']:.1f}, D={tech['D']:.1f}, J={tech['J']:.1f}\n")
        f.write(f"技术信号：{'超卖' if tech['oversold'] else ('超买' if tech['overbought'] else '正常')}\n\n")
        f.write(f"综合操作建议：{suggestion}\n")
    print(f"\n分析结果已保存至 {filename}")

def main():
    """主测试函数"""
    print("=== 股票分析系统测试版本 ===")
    
    # 测试股票列表
    test_stocks = [
        {"code": "sh603259", "name": "药明康德"},
        {"code": "sz000651", "name": "格力电器"},
        {"code": "sz000333", "name": "美的集团"}
    ]
    
    for stock in test_stocks:
        print(f"\n========== 正在分析：{stock['name']}（{stock['code']}） ==========")
        
        # 生成模拟新闻数据
        news_list = generate_mock_news_data()
        print(f"生成 {len(news_list)} 条模拟新闻")
        
        # 分析新闻情绪
        sentiment_label, pos_count, neu_count, neg_count = analyze_sentiment(news_list)
        
        # 生成模拟股票数据
        df = generate_mock_stock_data(stock['code'], days=100)
        df = calculate_technical_indicators(df)
        
        # 获取最新技术指标
        latest = df.iloc[-1]
        recent_vol_avg = df['Volume'].iloc[-6:-1].mean() if len(df) > 5 else df['Volume'].mean()
        
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
            'J': latest['J'],
            'volume_high': latest['Volume'] > 1.2 * recent_vol_avg,
            'oversold': latest['K'] < 20 and latest['D'] < 20,
            'overbought': latest['K'] > 80 and latest['D'] > 80
        }
        
        # 显示技术指标
        print(f"\n最近交易日({tech['last_date']})收盘: {tech['last_close']:.2f} 元  涨跌: {tech['pct_change']:.2f}%  成交量: {tech['volume']}")
        print(f"均线: MA5={tech['ma5']:.2f}, MA10={tech['ma10']:.2f}, MA20={tech['ma20']:.2f}")
        
        if tech['K'] < 20 or tech['D'] < 20:
            kdj_status = "超卖区"
        elif tech['K'] > 80 or tech['D'] > 80:
            kdj_status = "超买区"
        else:
            kdj_status = "中性区"
        print(f"KDJ指标: K={tech['K']:.1f}, D={tech['D']:.1f}, J={tech['J']:.1f} ({kdj_status})")
        
        macd_status = "多头" if tech['diff'] > tech['dea'] else "空头"
        print(f"MACD指标: DIF={tech['diff']:.2f}, DEA={tech['dea']:.2f}, 状态: {macd_status}趋势")
        
        # 生成建议
        suggestion = evaluate_signals(sentiment_label, tech)
        print("\n========= 综合分析结论 =========")
        print(f"新闻面情绪: {sentiment_label}，技术面信号: {'超卖' if tech['oversold'] else ('超买' if tech['overbought'] else '正常')}")
        print("操作建议：", suggestion)
        
        # 保存结果
        filename_txt = f"{stock['name']}_测试分析结果.txt"
        save_result_to_file(sentiment_label, tech, suggestion, filename=filename_txt, stock_name=stock['name'])
        
        # 生成走势图
        try:
            plt.figure(figsize=(12, 6))
            df_tail = df.tail(30)
            plt.plot(df_tail['Date'], df_tail['Close'], label='收盘价', linewidth=2)
            plt.plot(df_tail['Date'], df_tail['MA5'], label='MA5', alpha=0.7)
            plt.plot(df_tail['Date'], df_tail['MA10'], label='MA10', alpha=0.7)
            plt.plot(df_tail['Date'], df_tail['MA20'], label='MA20', alpha=0.7)
            plt.xticks(rotation=45)
            plt.legend()
            plt.title(f"{stock['name']} 最近30日走势（模拟数据）")
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(f"{stock['name']}_测试走势图.png", dpi=150, bbox_inches='tight')
            plt.close()
            print(f"走势图已保存为 {stock['name']}_测试走势图.png")
        except Exception as e:
            print(f"绘图失败: {e}")
        
        # 显示风险提示
        risk_keywords = ['减持', '问询函', '诉讼', '亏损', '下修', '退市']
        warning_news = [title for _, title in news_list if any(k in title for k in risk_keywords)]
        if warning_news:
            print("⚠️ 风险公告提示：")
            for title in warning_news:
                print(" -", title)
        
        print("\n" + "="*50)

if __name__ == "__main__":
    main() 