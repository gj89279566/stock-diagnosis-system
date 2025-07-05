#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票综合评价系统
整合多个权威数据源，生成综合投资建议
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import pandas as pd
import numpy as np
from snownlp import SnowNLP

class StockAnalyzer:
    """股票分析器"""
    
    def __init__(self, stock_code, stock_name):
        self.stock_code = stock_code
        self.stock_name = stock_name
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        
    def fetch_all_news(self):
        """获取所有可用数据源的新闻"""
        print(f"📰 正在获取 {self.stock_name} 的新闻数据...")
        
        all_news = []
        source_results = {}
        
        # 1. 新浪财经新闻（主要数据源）
        sina_news = self.fetch_sina_news()
        if sina_news:
            all_news.extend(sina_news)
            source_results['新浪财经'] = len(sina_news)
            print(f"✅ 新浪财经: {len(sina_news)} 条新闻")
        
        # 2. 东方财富新闻（备用数据源）
        eastmoney_news = self.fetch_eastmoney_news()
        if eastmoney_news:
            all_news.extend(eastmoney_news)
            source_results['东方财富'] = len(eastmoney_news)
            print(f"✅ 东方财富: {len(eastmoney_news)} 条公告")
        
        # 去重
        unique_news = []
        seen_titles = set()
        for date, title in all_news:
            if title not in seen_titles:
                unique_news.append((date, title))
                seen_titles.add(title)
        
        print(f"📊 总计获取 {len(unique_news)} 条新闻（去重后）")
        print(f"📈 数据源贡献: {source_results}")
        
        return unique_news, source_results
    
    def fetch_sina_news(self):
        """获取新浪财经新闻"""
        url = "https://vip.stock.finance.sina.com.cn/corp/view/vCB_AllNewsStock.php"
        params = {"symbol": self.stock_code, "Page": 1}
        
        try:
            resp = requests.get(url, params=params, headers=self.headers, timeout=10)
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
                    
                    return news_list
        except Exception as e:
            print(f"❌ 新浪财经获取失败: {e}")
        
        return []
    
    def fetch_eastmoney_news(self):
        """获取东方财富新闻"""
        url = "http://np-anotice-stock.eastmoney.com/api/security/announcement/getAnnouncementList"
        params = {"cb": "jQuery", "pageSize": 20, "pageIndex": 1, "stock": self.stock_code}
        
        try:
            resp = requests.get(url, params=params, headers=self.headers, timeout=10)
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
                            return news_list
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            print(f"❌ 东方财富获取失败: {e}")
        
        return []
    
    def analyze_sentiment(self, news_list):
        """分析新闻情绪"""
        print(f"\n📊 正在分析新闻情绪...")
        
        if not news_list:
            return "中性", 0, 0, 0, 0.5
        
        count_positive = 0
        count_negative = 0
        count_neutral = 0
        sentiment_scores = []
        
        print("📰 详细情绪分析:")
        for i, (date, title) in enumerate(news_list[:10]):  # 显示前10条
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
            
            if i < 10:
                print(f"  {date}: {title[:50]}... (情绪: {sentiment}, 分数: {score:.2f})")
        
        # 计算总体情绪
        total = len(news_list)
        avg_score = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.5
        
        sentiment_label = "中性"
        if total > 0:
            if count_negative > count_positive * 1.5:
                sentiment_label = "负面"
            elif count_positive > count_negative * 1.5:
                sentiment_label = "正面"
        
        print(f"\n📈 新闻情绪统计: 正面{count_positive}条, 中性{count_neutral}条, 负面{count_negative}条")
        print(f"📊 平均情绪分数: {avg_score:.2f}")
        print(f"🎯 总体新闻情绪倾向: {sentiment_label}")
        
        return sentiment_label, count_positive, count_neutral, count_negative, avg_score
    
    def fetch_stock_data(self):
        """获取股票技术数据"""
        print(f"\n📈 正在获取 {self.stock_name} 的技术数据...")
        
        # 使用新浪数据源获取股票数据
        url = "http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"
        params = {"symbol": self.stock_code, "scale": 240, "ma": 5, "datalen": 100}
        
        try:
            resp = requests.get(url, params=params, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
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
                    df['Date'] = pd.to_datetime(df['Date'])
                    df.sort_values('Date', inplace=True)
                    df.reset_index(drop=True, inplace=True)
                    
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
                    recent_vol_avg = df['Volume'].iloc[-6:-1].mean() if len(df) > 5 else df['Volume'].mean()
                    
                    tech_data = {
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
                    
                    print(f"✅ 技术数据获取成功")
                    return df, tech_data
                    
        except Exception as e:
            print(f"❌ 技术数据获取失败: {e}")
        
        return None, None
    
    def calculate_comprehensive_score(self, sentiment_label, tech_data, avg_sentiment_score):
        """计算综合评分"""
        print(f"\n🎯 正在计算综合评分...")
        
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
        if tech_data.get('diff', 0) > tech_data.get('dea', 0):
            tech_score += 10  # 多头趋势
        else:
            tech_score -= 10  # 空头趋势
        
        # KDJ评分
        k_value = tech_data.get('K', 50)
        d_value = tech_data.get('D', 50)
        if k_value < 20 and d_value < 20:
            tech_score += 15  # 超卖，买入信号
        elif k_value > 80 and d_value > 80:
            tech_score -= 15  # 超买，卖出信号
        
        # 均线评分
        ma5 = tech_data.get('ma5', 0)
        ma10 = tech_data.get('ma10', 0)
        ma20 = tech_data.get('ma20', 0)
        close = tech_data.get('last_close', 0)
        
        if close > ma5 > ma10 > ma20:
            tech_score += 10  # 多头排列
        elif close < ma5 < ma10 < ma20:
            tech_score -= 10  # 空头排列
        
        # 成交量评分
        if tech_data.get('volume_high', False):
            tech_score += 5  # 成交量放大
        
        # 涨跌幅评分
        pct_change = tech_data.get('pct_change', 0)
        if pct_change > 3:
            tech_score += 5  # 大涨
        elif pct_change < -3:
            tech_score -= 5  # 大跌
        
        # 确保分数在0-100范围内
        tech_score = max(0, min(100, tech_score))
        
        # 3. 综合评分 (新闻40% + 技术60%)
        final_score = sentiment_score * 0.4 + tech_score * 0.6
        
        print(f"📊 评分详情:")
        print(f"  新闻情绪评分: {sentiment_score:.1f}/100")
        print(f"  技术指标评分: {tech_score:.1f}/100")
        print(f"  综合评分: {final_score:.1f}/100")
        
        return final_score, sentiment_score, tech_score
    
    def generate_investment_advice(self, final_score):
        """生成投资建议"""
        if final_score >= 80:
            signal = "强烈买入"
            confidence = "高"
            risk_level = "低"
        elif final_score >= 65:
            signal = "买入"
            confidence = "中高"
            risk_level = "低"
        elif final_score >= 45:
            signal = "持有"
            confidence = "中"
            risk_level = "中"
        elif final_score >= 30:
            signal = "观望"
            confidence = "中低"
            risk_level = "中"
        else:
            signal = "卖出"
            confidence = "高"
            risk_level = "高"
        
        return signal, confidence, risk_level
    
    def generate_report(self, news_list, sentiment_data, tech_data, scores, advice):
        """生成综合分析报告"""
        print(f"\n📄 正在生成综合分析报告...")
        
        filename = f"{self.stock_name}_综合评价报告.txt"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"{self.stock_name}股票综合评价报告\n")
            f.write("="*60 + "\n")
            f.write(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"股票代码：{self.stock_code}\n\n")
            
            # 新闻分析
            f.write("📰 新闻情绪分析\n")
            f.write("-"*40 + "\n")
            f.write(f"新闻总数：{len(news_list)} 条\n")
            f.write(f"正面新闻：{sentiment_data[1]} 条\n")
            f.write(f"中性新闻：{sentiment_data[2]} 条\n")
            f.write(f"负面新闻：{sentiment_data[3]} 条\n")
            f.write(f"平均情绪分数：{sentiment_data[4]:.2f}\n")
            f.write(f"总体情绪倾向：{sentiment_data[0]}\n")
            f.write(f"情绪评分：{scores[1]:.1f}/100\n\n")
            
            # 技术分析
            f.write("📈 技术指标分析\n")
            f.write("-"*40 + "\n")
            f.write(f"最新交易日：{tech_data['last_date']}\n")
            f.write(f"收盘价：{tech_data['last_close']:.2f} 元\n")
            f.write(f"涨跌幅：{tech_data['pct_change']:.2f}%\n")
            f.write(f"成交量：{tech_data['volume']:,}\n")
            f.write(f"均线系统：MA5={tech_data['ma5']:.2f}, MA10={tech_data['ma10']:.2f}, MA20={tech_data['ma20']:.2f}\n")
            f.write(f"MACD指标：DIF={tech_data['diff']:.2f}, DEA={tech_data['dea']:.2f}\n")
            f.write(f"KDJ指标：K={tech_data['K']:.1f}, D={tech_data['D']:.1f}, J={tech_data['J']:.1f}\n")
            f.write(f"技术信号：{'超卖' if tech_data['oversold'] else ('超买' if tech_data['overbought'] else '正常')}\n")
            f.write(f"技术评分：{scores[2]:.1f}/100\n\n")
            
            # 综合评分
            f.write("🎯 综合评分\n")
            f.write("-"*40 + "\n")
            f.write(f"新闻情绪权重：40%\n")
            f.write(f"技术指标权重：60%\n")
            f.write(f"综合评分：{scores[0]:.1f}/100\n\n")
            
            # 投资建议
            f.write("💡 投资建议\n")
            f.write("-"*40 + "\n")
            f.write(f"操作建议：{advice[0]}\n")
            f.write(f"置信度：{advice[1]}\n")
            f.write(f"风险等级：{advice[2]}\n\n")
            
            # 风险提示
            f.write("⚠️ 风险提示\n")
            f.write("-"*40 + "\n")
            f.write("1. 本分析基于公开数据，仅供参考，不构成投资建议\n")
            f.write("2. 股市有风险，投资需谨慎\n")
            f.write("3. 请结合自身风险承受能力做出投资决策\n")
            f.write("4. 建议分散投资，不要将所有资金投入单一股票\n")
            f.write("5. 定期关注公司公告和行业动态\n\n")
            
            # 最新新闻列表
            f.write("📰 最新相关新闻\n")
            f.write("-"*40 + "\n")
            for i, (date, title) in enumerate(news_list[:20]):
                f.write(f"{i+1}. {date}: {title}\n")
        
        print(f"✅ 报告已保存至: {filename}")
        return filename
    
    def run_analysis(self):
        """运行完整分析"""
        print(f"🚀 开始分析 {self.stock_name} ({self.stock_code})")
        print("="*60)
        
        # 1. 获取新闻数据
        news_list, source_results = self.fetch_all_news()
        
        # 2. 分析新闻情绪
        sentiment_data = self.analyze_sentiment(news_list)
        
        # 3. 获取技术数据
        df, tech_data = self.fetch_stock_data()
        if tech_data is None:
            print("❌ 无法获取技术数据，分析终止")
            return
        
        # 4. 计算综合评分
        scores = self.calculate_comprehensive_score(sentiment_data[0], tech_data, sentiment_data[4])
        
        # 5. 生成投资建议
        advice = self.generate_investment_advice(scores[0])
        
        # 6. 显示结果
        print(f"\n========= 综合分析结论 =========")
        print(f"📰 新闻面情绪: {sentiment_data[0]}")
        print(f"📈 技术面信号: {'超卖' if tech_data['oversold'] else ('超买' if tech_data['overbought'] else '正常')}")
        print(f"🎯 综合评分: {scores[0]:.1f}/100")
        print(f"💡 操作建议: {advice[0]} (置信度: {advice[1]}, 风险: {advice[2]})")
        
        # 7. 生成报告
        report_file = self.generate_report(news_list, sentiment_data, tech_data, scores, advice)
        
        print(f"\n✅ {self.stock_name} 分析完成！")
        print(f"📄 详细报告: {report_file}")
        
        return {
            'news_count': len(news_list),
            'sentiment': sentiment_data[0],
            'tech_score': scores[2],
            'final_score': scores[0],
            'advice': advice[0],
            'confidence': advice[1],
            'risk_level': advice[2]
        }

def main():
    """主函数"""
    print("🎯 股票综合评价系统")
    print("="*60)
    
    # 分析药明康德
    analyzer = StockAnalyzer("sh603259", "药明康德")
    result = analyzer.run_analysis()
    
    print(f"\n🎉 分析完成！")
    print(f"📊 结果摘要:")
    print(f"  新闻数量: {result['news_count']} 条")
    print(f"  情绪倾向: {result['sentiment']}")
    print(f"  技术评分: {result['tech_score']:.1f}/100")
    print(f"  综合评分: {result['final_score']:.1f}/100")
    print(f"  投资建议: {result['advice']}")
    print(f"  置信度: {result['confidence']}")
    print(f"  风险等级: {result['risk_level']}")

if __name__ == "__main__":
    main() 