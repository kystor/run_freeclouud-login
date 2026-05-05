import time
import os
import base64
import sys
import re
from seleniumbase import SB
import ddddocr

# ==========================================
# 1. 网站配置区域：定义了我们要操作的所有网页元素的位置
# ==========================================
CONFIG = {
    # 登录页面的元素定位器
    "target_url": "https://run.freecloud.ltd/login",
    "username_selector": "#emailInp",              # 邮箱账号输入框
    "password_selector": "#emailPwdInp",           # 密码输入框
    "captcha_img_selector": "#allow_login_email_captcha",  # 图形验证码图片
    "captcha_input_selector": "#captcha_allow_login_email_captcha", # 验证码输入框
    "login_btn_selector": 'button[type="submit"]', # 登录按钮
    
    # 签到页面的元素定位器
    "sign_in_url": 'https://run.freecloud.ltd/addons?_plugin=5&_controller=index&_action=index', # 签到页面的直接网址
    "sign_in_btn_selector": 'button[onclick="showMathVerification()"]', # 点击签到的按钮
    "math_question_selector": '#mathQuestion',                           # 弹出的数学算式问题
    "math_input_selector": '#userAnswer',                                # 填入数学答案的输入框
    "verify_btn_selector": 'button[onclick="checkAnswer()"]',            # 提交验证答案的按钮
    "popup_content_selector": ".layui-layer-content", # 提示弹窗（比如“签到成功”）的内容
    "popup_confirm_btn_selector": ".layui-layer-btn0", # 提示弹窗的确认/关闭按钮
    "points_balance_selector": "div.alert-success span", # 显示当前积分余额的位置
    
    # 云服务器续费流程的元素定位器
    "server_list_url": "https://run.freecloud.ltd/service?groupid=305", # 云服务器列表网址
    "server_checkbox_selector": '.row-checkbox',               # 服务器列表左侧的勾选框
    "list_renew_btn_selector": '#readBtn',                     # 列表上方的“续费”按钮
    "confirm_renew_btn_selector": '.xfSubmit',                 # 订单页面的“立即续费”按钮
    "order_pay_btn_selector": '#payamount',                    # 收银台的确认支付按钮
    "modal_pay_btn_selector": 'button.pay-now'                 # 最终弹窗的“确认支付”按钮
}

# 自动创建一个名为 screenshots 的文件夹，如果已经存在则忽略
os.makedirs("screenshots", exist_ok=True)

# 截图辅助函数
def take_screenshot(sb, step_name, username="system"):
    """
    负责拍下当前网页的画面并保存。
    sb: seleniumbase 浏览器对象
    step_name: 当前操作的步骤名称，用于命名图片
    username: 当前的账号，用于区分不同账号的截图
    """
    # 将账号中的 @ 和 . 替换成下划线，防止作为文件名时报错
    safe_name = username.replace("@", "_").replace(".", "_")
    # 构造保存路径，例如: screenshots/user_qq_com_1_初始访问页面.png
    filepath = f"screenshots/{safe_name}_{step_name}.png"
    try:
        sb.save_screenshot(filepath)
        print(f"    📸 已截图保存: {filepath}")
    except Exception as e:
        print(f"    ⚠️ 截图失败 ({filepath}): {e}")

# ==========================================
# 2. 绕过网站防护 (Cloudflare) 的辅助函数 
# ==========================================
def is_cloudflare_interstitial(sb) -> bool:
    """检查当前页面是不是 Cloudflare 的5秒盾拦截页面"""
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

def bypass_cloudflare_interstitial(sb, max_attempts=4) -> bool:
    """尝试自动点击突破 Cloudflare 的拦截"""
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

def handle_turnstile_verification(sb) -> bool:
    """处理 Cloudflare 的 Turnstile 验证码（复选框验证）"""
    try:
        cookie_btn = 'button[data-cky-tag="accept-button"]'
        if sb.is_element_visible(cookie_btn):
            sb.click(cookie_btn)
            time.sleep(1)
    except:
        pass

    # 将页面滚动到验证码所在的位置
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
# 3. 单个账号的核心处理流程（包含截图）
# ==========================================
def process_single_account(username, password):
    print(f"\n==========================================")
    print(f"➡️ 开始处理账号: {username}")
    print(f"==========================================")
    
    env_proxy = os.environ.get("HTTP_PROXY")
    
    # 启动浏览器
    with SB(
        uc=True,            # 开启反反爬虫模式
        test=True,          
        locale="en",        
        headless=False,     # False代表显示浏览器窗口，您可以直观看到操作
        proxy=env_proxy,    
        chromium_arg="--disable-blink-features=AutomationControlled,--window-size=1920,1080"
    ) as sb:
        print(f"🌐 正在访问目标网站: {CONFIG['target_url']}")
        sb.uc_open_with_reconnect(CONFIG['target_url'], reconnect_time=8)
        time.sleep(4)
        
        # 【截图步骤 1】: 刚打开网页时
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
        # 【截图步骤 2】: 突破防御，准备开始填表
        take_screenshot(sb, "02_准备填写表单", username)

        try:
            # --- 登录模块 ---
            sb.wait_for_element(CONFIG['captcha_img_selector'], timeout=10)
            img_src = sb.get_attribute(CONFIG['captcha_img_selector'], "src")
            
            # 使用 AI 识别图片验证码
            if "base64," in img_src:
                base64_data = img_src.split(',')[1]
                img_bytes = base64.b64decode(base64_data)
                ocr = ddddocr.DdddOcr(show_ad=False)
                captcha_text = ocr.classification(img_bytes)
            else:
                return

            # 模拟键盘输入账号、密码和识别出的验证码
            sb.type(CONFIG['username_selector'], username)
            sb.type(CONFIG['password_selector'], password)
            sb.type(CONFIG['captcha_input_selector'], captcha_text)
            
            # 【截图步骤 3】: 信息填写完毕，点击登录前
            take_screenshot(sb, "03_填写账号密码及验证码完成", username)
            
            sb.click(CONFIG['login_btn_selector'])
            time.sleep(5)
            
            # 【截图步骤 4】: 登录结果
            take_screenshot(sb, "04_点击登录后的页面", username)
            print(f"📄 登录成功，当前页面: {sb.get_title()}")

            # ==========================================
            # 🌟 每日签到与积分提取模块
            # ==========================================
            print("\n>>> 🎁 准备执行每日签到任务...")
            sb.open(CONFIG['sign_in_url'])
            time.sleep(4) 
            
            # 【截图步骤 5】: 进入签到页面
            take_screenshot(sb, "05_进入签到页面", username)
            
            balance_value = 0.0 
            
            max_retries = 5
            for attempt in range(max_retries):
                sb.click(CONFIG['sign_in_btn_selector'])
                time.sleep(2) 
                
                # 抓取页面上的数学题并计算
                question_text = sb.get_text(CONFIG['math_question_selector'])
                math_expr = question_text.replace("请计算：", "").replace("=", "").strip()
                result = eval(math_expr)
                
                # 如果除法有小数，刷新重来
                if isinstance(result, float) and not result.is_integer():
                    sb.refresh() 
                    time.sleep(3)
                    continue     
                
                final_answer = int(result) 
                print(f"    ✅ 计算结果为整数: {final_answer}，正在提交...")
                sb.type(CONFIG['math_input_selector'], str(final_answer))
                
                # 【截图步骤 6】: 数学验证码填写完成
                take_screenshot(sb, "06_填写数学验证码", username)
                
                sb.click(CONFIG['verify_btn_selector'])
                time.sleep(3) # 等待弹窗出现
                
                # 【截图步骤 7】: 签到弹窗结果（成功或已签到）
                take_screenshot(sb, "07_签到弹窗提示结果", username)
                
                sb.wait_for_element(CONFIG['popup_content_selector'], timeout=5)
                popup_msg = sb.get_text(CONFIG['popup_content_selector'])
                print(f"    🔔 签到系统提示: 【{popup_msg}】")
                
                # 点击关闭弹窗
                sb.click(CONFIG['popup_confirm_btn_selector'])
                time.sleep(2) 
                
                # 【截图步骤 8】: 弹窗关闭后，准备抓取积分
                take_screenshot(sb, "08_关闭弹窗后页面", username)
                
                try:
                    balance_text = sb.get_text(CONFIG['points_balance_selector'])
                    print(f"    💰 当前账户原始信息: {balance_text}")
                    # 使用正则表达式提取积分数字
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
            if balance_value >= 0.01:
                print(f">>> 💻 积分达标 (当前 {balance_value})，开始执行云服务器续费任务...")
                
                print("    ▶ 正在强制跳转至云服务器列表网址...")
                sb.open(CONFIG['server_list_url'])
                time.sleep(4) 
                
                # 【截图步骤 9】: 服务器列表页
                take_screenshot(sb, "09_云服务器列表页", username)
                
                if sb.is_element_present(CONFIG['server_checkbox_selector']):
                    # 1. 勾选第一台服务器
                    sb.click(CONFIG['server_checkbox_selector'])
                    print("    ▶ 已勾选目标云服务器。")
                    
                    # 【截图步骤 10】: 勾选服务器
                    take_screenshot(sb, "10_勾选云服务器", username)
                    
                    # 2. 列表点击续费
                    sb.js_click(CONFIG['list_renew_btn_selector'])
                    time.sleep(4) 
                    
                    # 【截图步骤 11】: 点击续费后的界面
                    take_screenshot(sb, "11_点击列表续费按钮后", username)
                    
                    print("    ▶ 正在生成续费订单...")
                    # 3. 立即续费
                    sb.wait_for_element(CONFIG['confirm_renew_btn_selector'], timeout=10)
                    sb.js_click(CONFIG['confirm_renew_btn_selector']) 
                    time.sleep(5) 
                    
                    # 【截图步骤 12】: 生成订单
                    take_screenshot(sb, "12_点击立即续费按钮", username)
                    
                    print("    ▶ 已调起支付面板，等待确认...")
                    # 4. 收银台确认支付
                    sb.wait_for_element(CONFIG['order_pay_btn_selector'], timeout=15)
                    sb.js_click(CONFIG['order_pay_btn_selector']) 
                    time.sleep(2)
                    
                    # 【截图步骤 13】: 收银台支付
                    take_screenshot(sb, "13_收银台确认支付", username)
                    
                    # 5. 弹窗确认支付
                    sb.wait_for_element(CONFIG['modal_pay_btn_selector'], timeout=10)
                    sb.js_click(CONFIG['modal_pay_btn_selector']) 
                    print("    ▶ 💸 已在弹窗中确认支付，正在等待系统处理并跳转...")
                    
                    time.sleep(8) 
                    # 【截图步骤 14】: 支付完成并跳转
                    take_screenshot(sb, "14_支付完成跳转详情页", username)
                    
                    try:
                        p_elements = sb.find_elements('section.text-gray p')
                        for p in p_elements:
                            if "到期时间" in p.text:
                                print(f"    📅 续费成功！最新 {p.text}")
                                break
                    except Exception as e:
                        pass
                    
                    # ==========================================
                    # 🌟 最终闭环：重返签到中心核对积分
                    # ==========================================
                    print("\n>>> 🔄 续费完成，返回签到中心查看最新积分...")
                    sb.open(CONFIG['sign_in_url'])
                    time.sleep(4)
                    
                    # 【截图步骤 15】: 最后回到签到页查看余额
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
                print(f">>> 🛑 积分不足 (当前 {balance_value} < 0.01)，安全退出当前账号的后续操作！")

        except Exception as e:
            print(f"    ❌ 账号处理或执行过程中出现错误: {e}")
            take_screenshot(sb, "Error_程序崩溃异常截图", username)

# ==========================================
# 4. 主程序入口：程序的起点
# ==========================================
def main():
    print("🚀 自动化任务启动...")
    # 从操作系统的环境变量中读取账号信息
    accounts_str = os.environ.get("acount")
    
    if not accounts_str:
        print("⚠️ 未获取到名为 'acount' 环境变量！")
        return

    # 按逗号切割出多个账号
    account_list = accounts_str.split(',')
    print(f"📋 共检测到 {len(account_list)} 个账号。")
    
    # 循环处理每一个账号
    for item in account_list:
        item = item.strip()
        if ':' in item:
            parts = item.split(':', 1) 
            username = parts[0].strip()
            password = parts[1].strip()
            # 传递给上方我们写好的函数执行
            process_single_account(username, password)
        else:
            pass
            
    print("\n🏁 所有队列任务已全部执行完成！")

# 这是 Python 脚本执行的固定格式
if __name__ == "__main__":
    main()
