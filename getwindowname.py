import subprocess

def get_all_window_titles():
    script = '''
    tell application "System Events"
        set window_list to {}
        repeat with proc in (application processes whose background only is false)
            repeat with win in (windows of proc)
                set end of window_list to name of win
            end repeat
        end repeat
        return window_list
    end tell
    '''
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return result.stdout.strip().split(", ")

# 打印所有窗口标题
for title in get_all_window_titles():
    print(title)