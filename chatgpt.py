# 要求：pip install selenium webdriver-manager undetected-chromedriver
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver as uc
import time

def wait_for_element(driver, by, value, timeout=10):
    """等待元素出现并返回"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return element
    except TimeoutException:
        print(f"等待元素超时: {value}")
        return None

def send_message(driver, message):
    """发送消息到ChatGPT"""
    try:
        print("等待输入框出现...")
        # 尝试多个可能的选择器
        selectors = [
            "p[data-placeholder='询问任何问题']",
            "p[data-placeholder='Ask anything']",
            "div[contenteditable='true']",
            "div[role='textbox']"
        ]
        
        textarea = None
        for selector in selectors:
            print(f"尝试选择器: {selector}")
            textarea = wait_for_element(driver, By.CSS_SELECTOR, selector)
            if textarea:
                print(f"找到元素: {selector}")
                break
        
        if textarea:
            print("正在输入消息...")
            # 使用 JavaScript 来设置内容
            driver.execute_script("arguments[0].innerHTML = arguments[1]", textarea, message)
            time.sleep(1)  # 等待一下确保内容被设置
            
            print("寻找发送按钮...")
            # 等待发送按钮出现并点击
            send_button = wait_for_element(driver, By.CSS_SELECTOR, "button[data-testid='send-button'], button[aria-label='发送消息']")
            if send_button:
                print("点击发送按钮...")
                send_button.click()
                return True
            else:
                print("未找到发送按钮")
        else:
            print("未找到输入框")
    except Exception as e:
        print(f"发送消息时出错: {str(e)}")
    return False

def wait_for_copy_button(turn, timeout=30):
    """等待复制按钮出现并返回状态"""
    try:
        copy_button = WebDriverWait(turn, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-testid='copy-turn-action-button']"))
        )
        return True
    except TimeoutException:
        return False

def wait_for_new_turn(driver, timeout=30):
    """等待新的对话轮次出现"""
    try:
        # 等待新的对话轮次出现
        WebDriverWait(driver, timeout).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, "article[data-testid^='conversation-turn-']")) > 0
        )
        return True
    except TimeoutException:
        return False

def wait_for_any_copy_button(driver, timeout=30):
    """等待任意复制按钮出现"""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-testid='copy-turn-action-button']"))
        )
        return True
    except TimeoutException:
        return False

def get_last_response(driver, is_first_message=False):
    """获取ChatGPT的最后一条回复"""
    try:
        # 先等待复制按钮出现，表示回复已完成
        print("等待ChatGPT生成回复...")
        max_wait_time = 30  # 最大等待时间（秒）
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            if wait_for_any_copy_button(driver, timeout=1):
                print("回复已完成，开始提取内容...")
                break
            else:
                print("正在生成回复...", end='\r')
                time.sleep(1)
        else:
            print("\n等待回复完成超时")
            return None

        # 等待回复出现
        # 首先找到所有对话轮次
        conversation_turns = driver.find_elements(By.CSS_SELECTOR, "article[data-testid^='conversation-turn-']")
        if not conversation_turns:
            print("未找到任何对话轮次")
            return None
            
        # 根据是否是第一条消息选择不同的轮次
        if is_first_message:
            # 第一次对话从 conversation-turn-2 开始
            target_turn = None
            for turn in conversation_turns:
                if turn.get_attribute("data-testid") == "conversation-turn-2":
                    target_turn = turn
                    break
            if not target_turn:
                print("未找到第一次对话的回复")
                return None
        else:
            # 后续对话取最后一个
            target_turn = conversation_turns[-1]
        
        # 在目标轮次中查找回复内容
        response = target_turn.find_element(By.CSS_SELECTOR, "div.markdown.prose")
        if response:
            # 获取所有文本内容，包括列表项
            text_content = response.text
            return text_content
        else:
            print("在对话轮次中未找到回复内容")
    except Exception as e:
        print(f"获取回复时出错: {str(e)}")
    return None

def main():
    # 启动 Chrome（自动管理驱动）
    options = uc.ChromeOptions()
    options.add_argument('--window-position=0,0')  # 设置窗口位置
    options.add_argument('--window-size=1920,1080')  # 设置窗口大小
    driver = uc.Chrome(options=options)
    
    try:
        # 打开 ChatGPT 登录页
        driver.get("https://chat.openai.com/")
        
        # 确保窗口在最前面
        driver.maximize_window()

        # 提示：在打开的浏览器里手动完成登录
        input("请在打开的浏览器窗口中完成登录，登录成功后按回车继续…")

        # 等待页面加载完成
        time.sleep(2)

        is_first_message = True  # 标记是否是第一条消息

        while True:
            # 获取用户输入
            user_input = input("\n请输入要发送的消息（输入 'quit' 退出）: ")
            
            if user_input.lower() == 'quit':
                break
                
            print(f"发送消息: {user_input}")
            if send_message(driver, user_input):
                # 等待回复
                response = get_last_response(driver, is_first_message)
                if response:
                    print("\nChatGPT的回复:")
                    print(response)
                else:
                    print("未能获取到回复")
                is_first_message = False  # 更新消息状态
            else:
                print("发送消息失败")
        
    except Exception as e:
        print(f"发生错误: {str(e)}")
    finally:
        input("\n按回车键关闭浏览器...")
        driver.quit()

if __name__ == "__main__":
    main()