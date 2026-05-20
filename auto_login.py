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
    """检测当前页面是否处于 CF 5秒盾拦截或人机验证状态"""
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
    """如果 UC 无感模式没有直接放行，执行底层补救穿透解盾"""
    print("    🛡️ 检测到 CF 挑战页面仍未自动放行，准备执行备用穿透...")
    for attempt in range(max_attempts):
        print(f"      ▶ 尝试破盾 ({attempt+1}/{max_attempts})...")
        try:
            time.sleep(3)
            sb.set_window_rect(0, 0, 1920, 1080)
            time.sleep(1)

            iframe_selector = 'iframe[src*="cloudflare"], iframe[src*="turnstile"]'
            if sb.is_element_present(iframe_selector):
                print("      🎯 找到精确的验证码框架，正在利用 CDP 驱动发送底层点击...")
                sb.uc_click(iframe_selector)
                time.sleep(8)
            else:
                print("      ⚠️ 未捕获特定框架，尝试使用页面底层盲穿机制...")
                # 在虚拟屏幕中，传统的虚拟物理鼠标盲点极易失效，改用原生 uc_click 点击 body
                try:
                    sb.uc_click("body")
                except:
                    pass
                time.sleep(8)
            
            if not is_cloudflare_interstitial(sb):
                print("      ✅ CF 5秒盾挑战已成功通过！")
                return True
        except Exception as e:
            print(f"      ⚠️ 点击过程中断: {e}")
            pass
            
        print("      🔄 穿透未生效，强制刷新页面以重置 Cloudflare 安全状态...")
        sb.refresh()
        time.sleep(5)
        
    return False

def handle_turnstile_verification(sb) -> bool:
    """处理页面中嵌入的 Turnstile 隐藏验证模块"""
    try:
        cookie_btn = 'button[data-cky-tag="accept-button"]'
        if sb.is_element_visible(cookie_btn):
            sb.click(cookie_btn)
            time.sleep(1)
    except:
        pass

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
        print("    🟢 无感验证直接通过 (页面中没有阻断性 Turnstile 模块)")
        return True

    print("    🧩 页面内嵌入了人机验证码，尝试底层穿透...")
    verified = False
    iframe_selector = 'iframe[src*="cloudflare"], iframe[src*="turnstile"]'
    
    for attempt in range(1, 4):
        try:
            if sb.is_element_present(iframe_selector):
                sb.uc_click(iframe_selector)
            else:
                sb.uc_click("body")
        except:
            pass
            
        for _ in range(10):
            if sb.is_element_present('input[name="cf-turnstile-response"]'):
                token = sb.get_attribute('input[name="cf-turnstile-response"]', 'value')
                if token and len(token) > 20:
                    print("      ✅ 验证码点击成功，已成功获取系统 Token！")
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
                    print("      ✅ 验证码自动放行，已捕获系统 Token！")
                    verified = True
                    break
            time.sleep(1)

    return verified

# ==========================================
# 3. 单个账号的处理流程 
# ==========================================
def process_single_account(username, password):
    print(f"\n==========================================")
    print(f"➡️ 开始处理账号: {username}")
    print(f"==========================================")
    
    env_proxy = os.environ.get("HTTP_PROXY")
    
    # 净化升级后的 SeleniumBase UC 启动核心模块
    with SB(
        uc=True,            # 开启 Undetected 浏览器指纹抗反爬探测
        test=True,          
        locale="en-US",     
        headless=False,     # 在 Xvfb 虚拟屏幕中必须保持 False，否则 CF 通过率为 0
        proxy=env_proxy,    
        # 💡 核心改动：移除了所有与 UC 框架冲突、会导致 Action 环境暴露的硬编码标志
        chromium_arg=[
            "--window-size=1920,1080",                       
            "--lang=en-US",                                  
            "--disable-popup-blocking",                      
            "--force-device-scale-factor=1" # 锁死缩放比例，防止 Xvfb 像素错位
        ]
    ) as sb:
        print(f"🌐 正在发起网络握手，尝试访问目标网站: {CONFIG['target_url']}")
        # 💡 优化点：把 reconnect_time 延长至 15 秒，给云端虚拟网络留出更多的初始化缓冲时间
        sb.uc_open_with_reconnect(CONFIG['target_url'], reconnect_time=15)
        sb.maximize_window()
        time.sleep(6) # 留出时间让浏览器渲染完整的安全证书
        
        take_screenshot(sb, "01_初始访问页面", username)

        page_source = sb.get_page_source()
        if "Error 1005" in page_source or "Access denied" in page_source:
            print("🚨 致命错误：当前代理节点的 IP 被彻底封锁 (Error 1005)！")
            take_screenshot(sb, "Error_1005_节点被封锁", username)
            sys.exit(1) 

        # 如果原生无感未通过，执行降级点击穿透
        if is_cloudflare_interstitial(sb):
            if not bypass_cloudflare_interstitial(sb):
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
                
                for captcha_attempt in range(10): 
                    sb.wait_for_element(CONFIG['captcha_img_selector'], timeout=10)
                    img_src = sb.get_attribute(CONFIG['captcha_img_selector'], "src")
                    
                    if img_src and "base64," in img_src:
                        base64_data = img_src.split(',')[1]
                        img_bytes = base64.b64decode(base64_data)
                        ocr = ddddocr.DdddOcr(show_ad=False)
                        captcha_text = ocr.classification(img_bytes)
                        
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

                sb.clear(CONFIG['username_selector'])
                sb.type(CONFIG['username_selector'], username)
                
                sb.clear(CONFIG['password_selector'])
                sb.type(CONFIG['password_selector'], password)
                
                sb.clear(CONFIG['captcha_input_selector'])
                sb.type(CONFIG['captcha_input_selector'], captcha_text)
                
                take_screenshot(sb, "03_填写账号和验证码", username)
                sb.click(CONFIG['login_btn_selector'])
                time.sleep(5)
                
                if sb.is_element_present(CONFIG['user_center_selector']):
                    login_success = True
                    print(f"    📄 登录验证成功！当前页面: {sb.get_title()}")
                    take_screenshot(sb, "04_登录成功_用户中心", username)
                    break 
                else:
                    print(f"    ⚠️ 第 {login_attempt + 1} 次登录似乎失败了，正在准备重试...")
                    take_screenshot(sb, f"Error_第{login_attempt + 1}次登录失败", username)
                    sb.refresh() 
                    time.sleep(3)
            
            if not login_success:
                print("    🚨 致命错误：两次登录尝试均未成功！可能是网站风控或账号密码错误。")
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
                
                question_text = sb.get_text(CONFIG['math_question_selector'])
                math_expr = question_text.replace("请计算：", "").replace("=", "").strip()
                result = eval(math_expr)
                
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
                
                print("    >>> 正在等待“验证成功”弹窗出现...")
                
                try:
                    sb.wait_for_element_visible(CONFIG['popup_content_selector'], timeout=10)
                    first_popup_msg = sb.get_text(CONFIG['popup_content_selector'])
                    print(f"    🔔 第一层验证提示: 【{first_popup_msg}】")
                    take_screenshot(sb, "07_第一层验证成功弹窗", username)
                    
                    sb.click(CONFIG['popup_confirm_btn_selector'])
                    time.sleep(1.5) 
                    
                    if "验证成功" in first_popup_msg:
                        print("    >>> 准备点击紫色的【我要签到】按钮...")
                        
                        sb.click('//*[contains(text(), "我要签到")]')
                        time.sleep(1)
                        
                        print("    >>> 正在等待最终的签到结果弹窗...")
                        sb.wait_for_element_visible(CONFIG['popup_content_selector'], timeout=10)
                        second_popup_msg = sb.get_text(CONFIG['popup_content_selector'])
                        print(f"    🎉 最终签到状态: 【{second_popup_msg}】")
                        take_screenshot(sb, "08_最终签到结果弹窗", username)
                        
                        sb.click(CONFIG['popup_confirm_btn_selector'])
                        time.sleep(1.5)
                        
                except Exception as e:
                    print(f"    ⚠️ 处理弹窗时发生意外（可能是没弹出来）: {e}")
                
                print("    🔄 正在强制刷新页面以同步最新的余额数据...")
                sb.refresh()
                time.sleep(4)
                
                take_screenshot(sb, "09_刷新获取最新积分", username)
                
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
            # 🌟 积分判断与云服务器续费模块 (最终优化版)
            # ==========================================
            if balance_value >= 2:
                print(f">>> 💻 积分达标 (当前 {balance_value})，开始执行云服务器续费任务...")
                
                print("    ▶ 正在强制跳转至云服务器列表网址...")
                sb.open(CONFIG['server_list_url'])
                time.sleep(4) 
                take_screenshot(sb, "10_云服务器列表页", username)
                
                if sb.is_element_present(CONFIG['server_checkbox_selector']):
                    # 勾选服务器
                    sb.click(CONFIG['server_checkbox_selector'])
                    print("    ▶ 已勾选目标云服务器。")
                    
                    # 点击底部的续费按钮，调出确认页面
                    sb.click(CONFIG['list_renew_btn_selector'])
                    time.sleep(4) 
                    
                    print("    ▶ 正在生成续费订单...")
                    # 确保订单页面的按钮完全可见
                    sb.wait_for_element_visible(CONFIG['confirm_renew_btn_selector'], timeout=10)
                    take_screenshot(sb, "11_生成续费订单页", username)
                    
                    # 尝试点击生成订单
                    print("    ▶ 尝试点击【立即续费】按钮...")
                    try:
                        sb.click(CONFIG['confirm_renew_btn_selector'])
                    except Exception:
                        sb.uc_click(CONFIG['confirm_renew_btn_selector'])
                    
                    print("    ▶ 点击已发送，正在等待系统生成收银台...")
                    
                    # 智能等待下一页的特征按钮出现，最多等20秒
                    try:
                        sb.wait_for_element_clickable(CONFIG['order_pay_btn_selector'], timeout=20)
                    except Exception as e:
                        print("    ⚠️ 严重：页面没有成功跳转到收银台！")
                        take_screenshot(sb, "Error_点击续费后未跳转", username)
                        raise e 
                        
                    time.sleep(2)
                    take_screenshot(sb, "12_调起支付收银台", username)
                    
                    print("    ▶ 尝试点击右上角【立即支付】调出弹窗...")
                    try:
                        sb.click(CONFIG['order_pay_btn_selector']) 
                    except Exception:
                        pass
                    
                    try:
                        sb.wait_for_element_visible(CONFIG['modal_pay_btn_selector'], timeout=5)
                    except Exception:
                        print("    ⚠️ 物理点击似乎失效，弹窗未弹出！正在使用底层 JS 强制触发...")
                        sb.js_click(CONFIG['order_pay_btn_selector'])
                        sb.wait_for_element_visible(CONFIG['modal_pay_btn_selector'], timeout=10)
                        
                    time.sleep(1.5) 
                    
                    print("    ▶ 💸 弹窗已出现，点击弹窗内的【确认支付】...")
                    try:
                        sb.click(CONFIG['modal_pay_btn_selector']) 
                    except Exception:
                        sb.js_click(CONFIG['modal_pay_btn_selector'])
                        
                    print("    ▶ 正在等待系统处理扣费并跳转...")
                    
                    time.sleep(8) 
                    take_screenshot(sb, "13_支付完成详情页", username)
                    
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
                    
                    take_screenshot(sb, "14_最终核准积分页", username)
                    
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
            print(f"    ❌ 账号处理或执行过程中出现错误: {e}")
            take_screenshot(sb, "Error_程序崩溃截图", username)
            sys.exit(1)

# ==========================================
# 4. 主程序入口
# ==========================================
def main():
    print("🚀 自动化任务启动...")
    accounts_str = os.environ.get("acount")
    
    if not accounts_str:
        print("⚠️ 未获取到名为 'acount' 的环境变量！请检查 GitHub Secrets 配置。")
        return

    account_list = accounts_str.split(',')
    print(f"📋 共检测到 {len(account_list)} 个账号。")
    
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

if __name__ == "__main__":
    main()
