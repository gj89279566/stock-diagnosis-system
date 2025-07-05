import subprocess

def activate_window(window_title):
    """激活指定窗口"""
    script = f'''
    tell application "System Events"
        set appList to name of every process
        if "{window_title}" is in appList then
            tell process "{window_title}" to perform action "AXRaise" of window 1
        end if
    end tell
    '''
    try:
        subprocess.run(["osascript", "-e", script])
        print(f"窗口 {window_title} 已激活。")
    except Exception as e:
        print(f"激活窗口失败: {e}")

# 运行激活 Kindle
activate_window("Kindle")