import time
import os
import base64
import sys
import re  
from seleniumbase import SB
import ddddocr

# ==========================================
# 1. 网站配置区域 (定义你要操作的网页元素位置)
# ==========================================
CONFIG = {
    "target_url": "https://run.freecloud.ltd/login",
    "username_selector": "#emailInp",             
    "password_selector": "#emailPwdInp",          
    "captcha_img_selector": "#allow_login_email_captcha",          
    "captcha_input_selector": "#captcha_allow_login_email_captcha", 
    "login_btn_selector": 'button[type="submit"]',
    
    # 核心判断：如果能找到这个用户中心的按钮，说明登录成功了
    "user_center_selector": 'a[href="clientarea"]',
    
    "sign_in_url": 'https://run.freecloud.ltd/addons?_plugin=5&_controller=index&_action=index',
    "sign_in_btn_selector": 'button[onclick="showMathVerification()"]', 
    "math_question_selector": '#mathQuestion',                       
    "math_input_selector": '#userAnswer',                            
    "verify_btn_selector": 'button[onclick="checkAnswer()"]',        
    "popup_content_selector": ".layui-layer-content", 
    "popup_confirm_btn_selector": ".layui-layer-btn0", 
    "points_balance_selector": "div.alert-success span",
    
    "server_list_url": "https://run.freecloud.ltd/service?groupid=305", 
    "server_checkbox_selector": '.row-checkbox',              
    "list_renew_btn_selector": '#readBtn',                    
    "confirm_renew_btn_selector": '.xfSubmit',          
    "order_pay_btn_selector": '#payamount',                   
    "modal_pay_btn_selector": 'button.pay-now'                
}

# 创建一个专门存放截图的文件夹，如果已经存在就不会报错
os.makedirs("screenshots", exist_ok=True)

# 定义一个截图辅助函数，方便我们随时知道程序卡在哪里了
def take_screenshot(sb, step_name, username="system"):
    # 把邮箱里的 @ 和 . 替换成下划线，防止文件名报错
    safe_name = username.replace("@", "_").replace(".", "_")
    filepath = f"screenshots/{safe_name}_{step_name}.png"
    try:
        sb.save_screenshot(filepath)
        print(f"    📸 已截图: {step_name}.png")
    except Exception as e:
        print(f"    ⚠️ 截图失败 ({filepath}): {e}")

# ==========================================
# 2. Cloudflare (CF) 绕过辅助函数 
# ==========================================
def is_cloudflare_interstitial(sb) -> bool:
    """检测当前页面是否处于 CF 5秒盾拦截状态"""
    try:
        page_source = sb.get_page_source()
        title = sb.get_title().lower() if sb.get_title() else ""
        indicators = ["Just a moment", "Verify you are human", "Checking your browser", "Checking if the site connection is secure"]
        for ind in indicators:
            if ind in page_source:
                return True
        if "just a moment" in title or "attention required" in title:
            return True
        # 检测网页正文内容如果特别少，且包含 cf 的域名，通常是被拦截了
        body_len = sb.execute_script('(function() { return document.body ? document.body.innerText.length : 0; })();')
        if body_len is not None and body_len < 200 and "challenges.cloudflare.com" in page_source:
            return True
        return False
    except:
        return False

def bypass_cloudflare_interstitial(sb, max_attempts=4) -> bool:
    """尝试通过模拟点击绕过 CF 5秒盾 (坐标精准强化版)"""
    print("    🛡️ 检测到 CF 5秒盾，准备破除...")
    for attempt in range(max_attempts):
        print(f"      ▶ 尝试绕过 ({attempt+1}/{max_attempts})...")
        try:
            # 多等几秒，确保那个框框完全加载出来
            time.sleep(3)
            
            # 【关键修复 2】强制把网页滚动条拉到最顶部、最左边，防止坐标偏移
            sb.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)

            # 调用物理鼠标进行点击
            sb.uc_gui_click_captcha()
            time.sleep(6)
            
            if not is_cloudflare_interstitial(sb):
                print("      ✅ CF 5秒盾已通过！")
                return True
        except Exception as e:
            print(f"      ⚠️ 点击过程遇到小问题: {e}")
            pass
            
        print("      🔄 鼠标似乎没点中，刷新页面重置坐标状态...")
        sb.refresh()
        time.sleep(5)
        
    return False

def handle_turnstile_verification(sb) -> bool:
    """处理可能出现的 Turnstile (人机验证) 模块"""
    try:
        cookie_btn = 'button[data-cky-tag="accept-button"]'
        if sb.is_element_visible(cookie_btn):
            sb.click(cookie_btn)
            time.sleep(1)
    except:
        pass

    # 尝试把验证码模块滚动到屏幕中央，方便点击
    sb.execute_script('''
        try {
            var t = document.querySelector('.cf-turnstile') || 
                    document.querySelector('iframe[src*="challenges.cloudflare"]') || 
                    document.querySelector('iframe[src*="turnstile"]');
            if (t) t.scrollIntoView({behavior:'smooth', block:'center'});
        } catch(e) {}
    ''')
    time.sleep(2)

    has_turnstile = False
    for _ in range(15):
        if (sb.is_element_present('iframe[src*="challenges.cloudflare"]') or 
            sb.is_element_present('iframe[src*="turnstile"]') or 
            sb.is_element_present('.cf-turnstile') or 
            sb.is_element_present('input[name="cf-turnstile-response"]')):
            has_turnstile = True
            break
        time.sleep(1)

    if not has_turnstile:
        print("    🟢 无感验证通过 (未发现 Turnstile)")
        return True

    print("    🧩 发现验证码，执行拟人点击...")
    verified = False
    
    for attempt in range(1, 4):
        try:
            sb.uc_gui_click_captcha()
        except:
            pass
            
        for _ in range(10):
            if sb.is_element_present('input[name="cf-turnstile-response"]'):
                token = sb.get_attribute('input[name="cf-turnstile-response"]', 'value')
                if token and len(token) > 20:
                    print("      ✅ 物理点击成功，已获取 Token！")
                    verified = True
                    break
            time.sleep(1)
            
        if verified:
            break

    # 兜底机制：即使没有点击成功，有些时候 CF 会自动放行，我们多等一会儿
    if not verified:
        for _ in range(30):
            if sb.is_element_present('input[name="cf-turnstile-response"]'):
                token = sb.get_attribute('input[name="cf-turnstile-response"]', 'value')
                if token and len(token) > 20:
                    print("      ✅ 验证码自动放行，已获取 Token！")
                    verified = True
                    break
            time.sleep(1)

    return verified

# ==========================================
# 3. 单个账号的处理流程 (核心反检测与执行逻辑)
# ==========================================
def process_single_account(username, password):
    print(f"\n==========================================")
    print(f"➡️ 开始处理账号: {username}")
    print(f"==========================================")
    
    # 获取系统里的代理信息 (跑 GitHub Actions 的时候，这会获取到本机的 Socks5 端口)
    env_proxy = os.environ.get("HTTP_PROXY")
    
    # 【核心伪装参数】为了让 CF 觉得我们是一个正常的浏览器，需要带上这些参数
    with SB(
        uc=True,            # 开启反检测模式 (必须)
        test=True,          # 隐藏一些测试条
        locale="en-US",     # 伪装成英文浏览器环境
        headless=False,     # 保持 False！在 GitHub Actions 中会用 Xvfb 创建虚拟屏幕，让它以为有显示器
        proxy=env_proxy,    # 走我们设定的代理 IP
        chromium_arg=[
            "--disable-blink-features=AutomationControlled", # 去掉自动化标识
            "--window-size=1920,1080",                       # 伪装正常显示器大小
            "--disable-infobars",                            # 去掉各种提示条
            "--disable-popup-blocking",                      # 允许弹窗
            "--no-sandbox",                                  # Linux 运行必备
            "--disable-dev-shm-usage",                       # 避免内存不足崩溃
            "--lang=en-US",                                  
        ]
    ) as sb:
        print(f"🌐 正在访问目标网站: {CONFIG['target_url']}")
        # 使用带有重连功能的访问，防止因为代理网络波动导致打不开
        sb.uc_open_with_reconnect(CONFIG['target_url'], reconnect_time=8)
        
        # 【关键修复 1】强制最大化窗口！保证虚拟屏幕和浏览器窗口 100% 重合
        sb.maximize_window()
        time.sleep(4)
        
        take_screenshot(sb, "01_初始访问页面", username)

        # 检查代理 IP 是否被网站的防火墙彻底拉黑了
        page_source = sb.get_page_source()
        if "Error 1005" in page_source or "Access denied" in page_source:
            print("🚨 致命错误：当前代理节点的 IP 被彻底封锁 (Error 1005)！")
            take_screenshot(sb, "Error_1005_节点被封锁", username)
            sys.exit(1) # IP 都被拉黑了，直接强制终止程序

        # 【核心修改点1：处理 CF 破盾失败】
        if is_cloudflare_interstitial(sb):
            if not bypass_cloudflare_interstitial(sb):
                # 破盾失败，不再使用 return 跳过，而是直接让程序报错并退出
                print("    🚨 致命错误：无法绕过 Cloudflare 5秒盾，程序将立即终止运行！")
                take_screenshot(sb, "Error_CF破盾失败彻底卡死", username)
                sys.exit(1) 
            time.sleep(3) 
            
        handle_turnstile_verification(sb)
        time.sleep(3)
        take_screenshot(sb, "02_绕过CF准备填写表单", username)

        try:
            # --- 登录模块 ---
            login_success = False 
            
            for login_attempt in range(2):
                print(f"    ▶ 开始第 {login_attempt + 1} 次尝试登录...")
                
                captcha_success = False 
                
                # 开始识别验证码图片
                for captcha_attempt in range(10): 
                    sb.wait_for_element(CONFIG['captcha_img_selector'], timeout=10)
                    img_src = sb.get_attribute(CONFIG['captcha_img_selector'], "src")
                    
                    if img_src and "base64," in img_src:
                        base64_data = img_src.split(',')[1]
                        img_bytes = base64.b64decode(base64_data)
                        ocr = ddddocr.DdddOcr(show_ad=False)
                        captcha_text = ocr.classification(img_bytes)
                        
                        # 这个网站的验证码通常是纯数字，如果是数字就认为识别成功
                        if captcha_text.isdigit():
                            print(f"      ✅ 验证码识别成功 (纯数字): {captcha_text}")
                            captcha_success = True 
                            break 
                        else:
                            print(f"      ⚠️ 第 {captcha_attempt + 1} 次识别结果含字母/乱码 ({captcha_text})，点击刷新...")
                            sb.click(CONFIG['captcha_img_selector'])
                            time.sleep(2) 
                    else:
                        print("      ⚠️ 无法获取验证码图片。")
                        break
                
                if not captcha_success:
                    print("    🚨 致命错误：验证码连续 10 次识别失败！程序将直接退出。")
                    take_screenshot(sb, "Error_验证码十次识别失败", username)
                    sys.exit(1) 

                # 填写账号、密码、验证码
                sb.clear(CONFIG['username_selector'])
                sb.type(CONFIG['username_selector'], username)
                
                sb.clear(CONFIG['password_selector'])
                sb.type(CONFIG['password_selector'], password)
                
                sb.clear(CONFIG['captcha_input_selector'])
                sb.type(CONFIG['captcha_input_selector'], captcha_text)
                
                take_screenshot(sb, "03_填写账号和验证码", username)
                
                sb.click(CONFIG['login_btn_selector'])
                time.sleep(5)
                
                # 检查是否成功找到了代表“用户中心”的按钮
                if sb.is_element_present(CONFIG['user_center_selector']):
                    login_success = True
                    print(f"    📄 登录验证成功！当前页面: {sb.get_title()}")
                    take_screenshot(sb, "04_登录成功_用户中心", username)
                    break 
                else:
                    print(f"    ⚠️ 第 {login_attempt + 1} 次登录似乎失败了（没找到用户中心），正在准备重试...")
                    take_screenshot(sb, f"Error_第{login_attempt + 1}次登录失败", username)
                    sb.refresh() 
                    time.sleep(3)
            
            # 【核心修改点2：处理登录失败】
            if not login_success:
                # 如果连续重试了都不行，使用 sys.exit(1) 强制中断整个 GitHub Actions 流程并报错
                print("    🚨 致命错误：两次登录尝试均未成功！可能是网站风控或账号密码错误。程序将立即终止运行！")
                take_screenshot(sb, "Error_最终登录失败", username)
                sys.exit(1)

            # ==========================================
            # 🌟 每日签到与积分提取模块
            # ==========================================
            print("\n>>> 🎁 准备执行每日签到任务...")
            sb.open(CONFIG['sign_in_url'])
            time.sleep(4) 
            take_screenshot(sb, "05_跳转到签到页面", username)
            
            balance_value = 0.0 
            
            max_retries = 5
            for attempt in range(max_retries):
                sb.click(CONFIG['sign_in_btn_selector'])
                time.sleep(2) 
                
                # 提取系统给的算术题，比如 "请计算：5 + 3 ="，并计算出结果
                question_text = sb.get_text(CONFIG['math_question_selector'])
                math_expr = question_text.replace("请计算：", "").replace("=", "").strip()
                result = eval(math_expr)
                
                # 如果算出来的是小数（说明遇到除法且除不尽），我们刷新一下换一道题
                if isinstance(result, float) and not result.is_integer():
                    sb.refresh() 
                    time.sleep(3)
                    continue     
                
                final_answer = int(result) 
                print(f"    ✅ 计算结果为整数: {final_answer}，正在提交...")
                
                sb.clear(CONFIG['math_input_selector']) 
                sb.type(CONFIG['math_input_selector'], str(final_answer))
                
                take_screenshot(sb, "06_填写签到算术答案", username)
                sb.click(CONFIG['verify_btn_selector'])
                
                sb.wait_for_element(CONFIG['popup_content_selector'], timeout=5)
                popup_msg = sb.get_text(CONFIG['popup_content_selector'])
                print(f"    🔔 签到系统提示: 【{popup_msg}】")
                
                take_screenshot(sb, "07_签到结果弹窗", username)
                
                sb.click(CONFIG['popup_confirm_btn_selector'])
                time.sleep(2) 
                
                print("    🔄 正在强制刷新页面以同步最新的余额数据...")
                sb.refresh()
                time.sleep(4)
                
                take_screenshot(sb, "08_刷新获取最新积分", username)
                
                # 提取页面上的积分数字并转为小数点数字，方便后面做比较
                try:
                    balance_text = sb.get_text(CONFIG['points_balance_selector'])
                    print(f"    💰 当前账户原始信息: {balance_text}")
                    match = re.search(r"(\d+(?:\.\d+)?)", balance_text)
                    if match:
                        balance_value = float(match.group(1))
                        print(f"    🔍 提取并转换可用积分为: {balance_value}")
                except Exception:
                    print("    ⚠️ 无法获取积分余额。")

                print("    🎉 签到流程结束。\n")
                break 
            else:
                print("    ❌ 签到失败：连续 5 次刷新都没有遇到可以整除的算术题。")
                take_screenshot(sb, "Error_签到数学题失败", username)

            # ==========================================
            # 🌟 积分判断与云服务器续费模块
            # ==========================================
            if balance_value >= 2:
                print(f">>> 💻 积分达标 (当前 {balance_value})，开始执行云服务器续费任务...")
                
                print("    ▶ 正在强制跳转至云服务器列表网址...")
                sb.open(CONFIG['server_list_url'])
                time.sleep(4) 
                take_screenshot(sb, "09_云服务器列表页", username)
                
                # 只有页面上存在勾选框，才说明有服务器可以续费
                if sb.is_element_present(CONFIG['server_checkbox_selector']):
                    sb.click(CONFIG['server_checkbox_selector'])
                    print("    ▶ 已勾选目标云服务器。")
                    
                    sb.js_click(CONFIG['list_renew_btn_selector'])
                    time.sleep(4) 
                    
                    print("    ▶ 正在生成续费订单...")
                    sb.wait_for_element(CONFIG['confirm_renew_btn_selector'], timeout=10)
                    take_screenshot(sb, "10_生成续费订单页", username)
                    
                    sb.js_click(CONFIG['confirm_renew_btn_selector']) 
                    time.sleep(5) 
                    
                    print("    ▶ 已调起支付面板，等待确认...")
                    sb.wait_for_element(CONFIG['order_pay_btn_selector'], timeout=15)
                    take_screenshot(sb, "11_调起支付收银台", username)
                    
                    sb.js_click(CONFIG['order_pay_btn_selector']) 
                    
                    sb.wait_for_element(CONFIG['modal_pay_btn_selector'], timeout=10)
                    sb.js_click(CONFIG['modal_pay_btn_selector']) 
                    print("    ▶ 💸 已在弹窗中确认支付，正在等待系统处理并跳转...")
                    
                    time.sleep(8) 
                    take_screenshot(sb, "12_支付完成详情页", username)
                    
                    # 尝试从页面上抓取新的到期时间并打印出来
                    try:
                        p_elements = sb.find_elements('section.text-gray p')
                        for p in p_elements:
                            if "到期时间" in p.text:
                                print(f"    📅 续费成功！最新 {p.text}")
                                break
                    except Exception as e:
                        pass
                    
                    print("\n>>> 🔄 续费完成，返回签到中心查看最新积分...")
                    sb.open(CONFIG['sign_in_url'])
                    time.sleep(4)
                    
                    take_screenshot(sb, "13_最终核针对积分页", username)
                    
                    try:
                        final_balance_text = sb.get_text(CONFIG['points_balance_selector'])
                        print(f"    💰 续费后账户最新信息: {final_balance_text}")
                        match = re.search(r"(\d+(?:\.\d+)?)", final_balance_text)
                        if match:
                            print(f"    ✨ 最终剩余可用积分: {float(match.group(1))}")
                    except Exception:
                        print("    ⚠️ 无法获取最终积分余额。")
                        
                else:
                    print("    ⚠️ 当前账号下未检测到可续费的云服务器，已跳过。")
            else:
                print(f">>> 🛑 积分不足 (当前 {balance_value} < 2)，安全退出当前账号的后续操作！")

        except Exception as e:
            # 如果中间任何一步代码报错（比如网卡了导致某个元素找不到），就会跳到这里
            print(f"    ❌ 账号处理或执行过程中出现错误: {e}")
            take_screenshot(sb, "Error_程序崩溃截图", username)
            # 为了防止意外假死，我们在报错后也强制杀掉程序
            sys.exit(1)

# ==========================================
# 4. 主程序入口
# ==========================================
def main():
    print("🚀 自动化任务启动...")
    # 获取 GitHub Secrets 里的账号密码字符串
    accounts_str = os.environ.get("acount")
    
    if not accounts_str:
        print("⚠️ 未获取到名为 'acount' 的环境变量！")
        return

    # 把字符串按逗号拆分成列表（支持多账号）
    account_list = accounts_str.split(',')
    print(f"📋 共检测到 {len(account_list)} 个账号。")
    
    for item in account_list:
        item = item.strip()
        if ':' in item:
            parts = item.split(':', 1) 
            username = parts[0].strip()
            password = parts[1].strip()
            # 开始执行我们在上面定义好的主流程函数
            process_single_account(username, password)
        else:
            pass
            
    print("\n🏁 所有队列任务已全部执行完成！")

# 只要你是把这个文件当作主程序运行，就会执行 main() 函数
if __name__ == "__main__":
    main()
