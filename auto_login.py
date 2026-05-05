import time
import os
import base64
import sys
import re
from seleniumbase import SB
import ddddocr

# ==========================================
# 1. 网站配置区域 (保存所有需要用到的网页元素定位器)
# ==========================================
CONFIG = {
    "target_url": "https://run.freecloud.ltd/login",
    "username_selector": "#emailInp",              
    "password_selector": "#emailPwdInp",           
    "captcha_img_selector": "#allow_login_email_captcha",  
    "captcha_input_selector": "#captcha_allow_login_email_captcha", 
    "login_btn_selector": 'button[type="submit"]', 
    
    # 用户中心验证元素的定位器
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

# 创建保存截图的文件夹，如果不存在就自动创建
os.makedirs("screenshots", exist_ok=True)

# 截图辅助函数：方便我们在程序运行出错时查看当时的网页状态
def take_screenshot(sb, step_name, username="system"):
    safe_name = username.replace("@", "_").replace(".", "_")
    filepath = f"screenshots/{safe_name}_{step_name}.png"
    try:
        sb.save_screenshot(filepath)
        print(f"    📸 已截图保存: {filepath}")
    except Exception as e:
        print(f"    ⚠️ 截图失败 ({filepath}): {e}")

# ==========================================
# 2. 绕过辅助函数 (处理 Cloudflare 等人机验证)
# ==========================================
# 检测是否遇到了 CF 5秒盾拦截页面
def is_cloudflare_interstitial(sb) -> bool:
    try:
        page_source = sb.get_page_source()
        title = sb.get_title().lower() if sb.get_title() else ""
        indicators = ["Just a moment", "Verify you are human", "Checking your browser", "Checking if the site connection is secure"]
        for ind in indicators:
            if ind in page_source:
                return True
        if "just a moment" in title or "attention required" in title:
            return True
        body_len = sb.execute_script('(function() { return document.body ? document.body.innerText.length : 0; })();')
        if body_len is not None and body_len < 200 and "challenges.cloudflare.com" in page_source:
            return True
        return False
    except:
        return False

# 尝试自动绕过 CF 5秒盾
def bypass_cloudflare_interstitial(sb, max_attempts=4) -> bool:
    print("    🛡️ 检测到 CF 5秒盾，准备破除...")
    for attempt in range(max_attempts):
        print(f"      ▶ 尝试绕过 ({attempt+1}/{max_attempts})...")
        try:
            sb.uc_gui_click_captcha()
            time.sleep(6)
            if not is_cloudflare_interstitial(sb):
                print("      ✅ CF 5秒盾已通过！")
                return True
        except Exception as e:
            pass
        time.sleep(3)
    return False

# 处理 Turnstile 验证码验证
def handle_turnstile_verification(sb) -> bool:
    try:
        cookie_btn = 'button[data-cky-tag="accept-button"]'
        if sb.is_element_visible(cookie_btn):
            sb.click(cookie_btn)
            time.sleep(1)
    except:
        pass

    # 将验证码滚动到视口中央
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
# 3. 单个账号的处理流程 (登录、签到、续费)
# ==========================================
def process_single_account(username, password):
    print(f"\n==========================================")
    print(f"➡️ 开始处理账号: {username}")
    print(f"==========================================")
    
    env_proxy = os.environ.get("HTTP_PROXY")
    
    with SB(
        uc=True,            
        test=True,          
        locale="en",        
        headless=False,     
        proxy=env_proxy,    
        chromium_arg="--disable-blink-features=AutomationControlled,--window-size=1920,1080"
    ) as sb:
        print(f"🌐 正在访问目标网站: {CONFIG['target_url']}")
        sb.uc_open_with_reconnect(CONFIG['target_url'], reconnect_time=8)
        time.sleep(4)
        
        take_screenshot(sb, "01_初始访问页面", username)

        page_source = sb.get_page_source()
        if "Error 1005" in page_source or "Access denied" in page_source:
            print("🚨 致命错误：当前代理节点的 IP 被彻底封锁 (Error 1005)！")
            take_screenshot(sb, "Error_1005_节点被封锁", username)
            sys.exit(1)

        if is_cloudflare_interstitial(sb):
            if not bypass_cloudflare_interstitial(sb):
                return 
            time.sleep(3) 
            
        handle_turnstile_verification(sb)
        time.sleep(3)
        take_screenshot(sb, "02_准备填写表单", username)

        try:
            # ==========================================
            # 🌟 登录模块
            # ==========================================
            ocr = ddddocr.DdddOcr(show_ad=False)
            login_success = False 
            
            for login_attempt in range(2):
                captcha_text = ""
                
                # 获取并识别纯数字验证码
                for captcha_attempt in range(5):
                    sb.wait_for_element(CONFIG['captcha_img_selector'], timeout=10)
                    img_src = sb.get_attribute(CONFIG['captcha_img_selector'], "src")
                    
                    if "base64," in img_src:
                        base64_data = img_src.split(',')[1]
                        img_bytes = base64.b64decode(base64_data)
                        captcha_text = ocr.classification(img_bytes)
                        print(f"    🔍 OCR 识别结果: {captcha_text}")
                        
                        if captcha_text.isdigit():
                            print("    ✅ 识别为纯数字，准备填写！")
                            break 
                        else:
                            print("    ⚠️ 发现字母或非数字字符，点击刷新验证码...")
                            sb.click(CONFIG['captcha_img_selector'])
                            time.sleep(2) 
                    else:
                        break

                if not captcha_text:
                    print("    ⚠️ 无法获取验证码，跳过登录。")
                    break
                
                # 填写账号、密码、验证码
                sb.clear(CONFIG['username_selector'])
                sb.type(CONFIG['username_selector'], username)
                
                sb.clear(CONFIG['password_selector'])
                sb.type(CONFIG['password_selector'], password)
                
                sb.clear(CONFIG['captcha_input_selector'])
                sb.type(CONFIG['captcha_input_selector'], captcha_text)
                
                take_screenshot(sb, f"03_尝试登录_第{login_attempt+1}次", username)
                
                # 点击登录
                sb.click(CONFIG['login_btn_selector'])
                print(f"    ▶ 第 {login_attempt+1} 次发起登录请求，等待页面跳转验证...")
                time.sleep(5) # 给网页充分的跳转和加载时间
                
                # 精准验证“用户中心”元素是否存在
                if sb.is_element_present(CONFIG['user_center_selector']):
                    print(f"    ✅ 登录成功！已精准检测到【用户中心】标志。")
                    take_screenshot(sb, "04_登录成功_用户中心页面", username)
                    login_success = True
                    break # 登录成功，跳出循环
                
                # 失败原因分析
                current_page_source = sb.get_page_source()
                if "图形验证码有误" in current_page_source or "验证码错误" in current_page_source:
                    print(f"    ❌ 失败原因：网站提示验证码有误（机器识别可能出错）。")
                    sb.click(CONFIG['captcha_img_selector'])
                    time.sleep(2)
                else:
                    print(f"    ❌ 失败原因：未找到【用户中心】入口，可能账号密码错误或网络延迟。")
                
                take_screenshot(sb, f"Error_登录失败第{login_attempt+1}次", username)
                
                # 错误重试限制退出
                if login_attempt == 1:
                    print("    🚨 致命警告：重新登录失败已达 1 次，直接强行退出整个程序！")
                    sys.exit(1) 

            if not login_success:
                print("    🚨 登录流程未成功，跳过后续所有操作。")
                return 

            # ==========================================
            # 🌟 每日签到与积分提取模块
            # ==========================================
            print("\n>>> 🎁 准备执行每日签到任务...")
            sb.open(CONFIG['sign_in_url'])
            time.sleep(4) 
            
            take_screenshot(sb, "05_进入签到页面", username)
            
            balance_value = 0.0 
            
            max_retries = 5
            for attempt in range(max_retries):
                sb.click(CONFIG['sign_in_btn_selector'])
                time.sleep(2) 
                
                question_text = sb.get_text(CONFIG['math_question_selector'])
                math_expr = question_text.replace("请计算：", "").replace("=", "").strip()
                result = eval(math_expr)
                
                # 如果遇到小数，刷新重新获取题目
                if isinstance(result, float) and not result.is_integer():
                    sb.refresh() 
                    time.sleep(3)
                    continue     
                
                final_answer = int(result) 
                print(f"    ✅ 计算结果为整数: {final_answer}，正在提交...")
                sb.type(CONFIG['math_input_selector'], str(final_answer))
                
                take_screenshot(sb, "06_填写数学验证码", username)
                
                sb.click(CONFIG['verify_btn_selector'])
                time.sleep(3) 
                
                take_screenshot(sb, "07_签到弹窗提示结果", username)
                
                # 等待系统提示弹窗并获取文字
                sb.wait_for_element(CONFIG['popup_content_selector'], timeout=5)
                popup_msg = sb.get_text(CONFIG['popup_content_selector'])
                print(f"    🔔 签到系统提示: 【{popup_msg}】")
                
                # 关闭弹窗
                sb.click(CONFIG['popup_confirm_btn_selector'])
                time.sleep(2) 
                
                # ----------------------------------------------------
                # 🛠️ 关键修复：强制刷新页面以同步服务端的最新积分
                # ----------------------------------------------------
                print("    🔄 正在刷新页面以同步最新积分状态...")
                sb.refresh()  # 强制刷新当前页面
                time.sleep(4) # 等待页面完全加载，确保新数据出现
                
                take_screenshot(sb, "08_刷新后重新获取页面", username)
                
                # 重新去获取页面上的积分元素
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

            # ==========================================
            # 🌟 积分判断与云服务器续费模块
            # ==========================================
            if balance_value >= 1:
                print(f">>> 💻 积分达标 (当前 {balance_value})，开始执行云服务器续费任务...")
                
                print("    ▶ 正在强制跳转至云服务器列表网址...")
                sb.open(CONFIG['server_list_url'])
                time.sleep(4) 
                
                take_screenshot(sb, "09_云服务器列表页", username)
                
                if sb.is_element_present(CONFIG['server_checkbox_selector']):
                    sb.click(CONFIG['server_checkbox_selector'])
                    print("    ▶ 已勾选目标云服务器。")
                    
                    take_screenshot(sb, "10_勾选云服务器", username)
                    
                    sb.js_click(CONFIG['list_renew_btn_selector'])
                    time.sleep(4) 
                    
                    take_screenshot(sb, "11_点击列表续费按钮后", username)
                    
                    print("    ▶ 正在生成续费订单...")
                    sb.wait_for_element(CONFIG['confirm_renew_btn_selector'], timeout=10)
                    sb.js_click(CONFIG['confirm_renew_btn_selector']) 
                    time.sleep(5) 
                    
                    take_screenshot(sb, "12_点击立即续费按钮", username)
                    
                    print("    ▶ 已调起支付面板，等待确认...")
                    sb.wait_for_element(CONFIG['order_pay_btn_selector'], timeout=15)
                    sb.js_click(CONFIG['order_pay_btn_selector']) 
                    time.sleep(2)
                    
                    take_screenshot(sb, "13_收银台确认支付", username)
                    
                    sb.wait_for_element(CONFIG['modal_pay_btn_selector'], timeout=10)
                    sb.js_click(CONFIG['modal_pay_btn_selector']) 
                    print("    ▶ 💸 已在弹窗中确认支付，正在等待系统处理并跳转...")
                    
                    time.sleep(8) 
                    take_screenshot(sb, "14_支付完成跳转详情页", username)
                    
                    try:
                        p_elements = sb.find_elements('section.text-gray p')
                        for p in p_elements:
                            if "到期时间" in p.text:
                                print(f"    📅 续费成功！最新 {p.text}")
                                break
                    except Exception as e:
                        pass
                    
                    # 最终闭环：重返签到中心核对积分
                    print("\n>>> 🔄 续费完成，返回签到中心查看最新积分...")
                    sb.open(CONFIG['sign_in_url'])
                    time.sleep(4)
                    
                    take_screenshot(sb, "15_续费后返回签到中心", username)
                    
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
                print(f">>> 🛑 积分不足 (当前 {balance_value} < 1)，安全退出当前账号的后续操作！")

        except Exception as e:
            print(f"    ❌ 账号处理或执行过程中出现错误: {e}")
            take_screenshot(sb, "Error_程序崩溃异常截图", username)

# ==========================================
# 4. 主程序入口
# ==========================================
def main():
    print("🚀 自动化任务启动...")
    # 获取环境变量里面的账号密码信息
    accounts_str = os.environ.get("acount")
    
    if not accounts_str:
        print("⚠️ 未获取到名为 'acount' 环境变量！")
        return

    # 按逗号切割多个账号
    account_list = accounts_str.split(',')
    print(f"📋 共检测到 {len(account_list)} 个账号。")
    
    # 循环处理每一个账号
    for item in account_list:
        item = item.strip()
        if ':' in item:
            parts = item.split(':', 1) 
            username = parts[0].strip()
            password = parts[1].strip()
            process_single_account(username, password)
        else:
            pass
            
    print("\n🏁 所有队列任务已全部执行完成！")

# 这是 Python 程序的标准启动点
if __name__ == "__main__":
    main()
