import time
import os
import base64
import sys
import re
import random
import json
from seleniumbase import SB
import ddddocr

# ==========================================
# 1. 网站配置区域
# ==========================================
CONFIG = {
    "target_url": "https://run.freecloud.ltd/login",
    "username_selector": "#emailInp",
    "password_selector": "#emailPwdInp",
    "captcha_img_selector": "#allow_login_email_captcha",
    "captcha_input_selector": "#captcha_allow_login_email_captcha",
    "login_btn_selector": 'button[type="submit"]',
    
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

os.makedirs("screenshots", exist_ok=True)

# ==========================================
# 2. WebGL & Canvas 指纹伪装核心脚本
# ==========================================
WEBGL_SPOOF_SCRIPT = """
(function() {
    'use strict';
    
    // 🎲 随机生成器工具
    const randomItem = arr => arr[Math.floor(Math.random() * arr.length)];
    const randomFloat = (min, max) => +(Math.random() * (max - min) + min).toFixed(6);
    
    // 🎨 常见 GPU 渲染器池 (模拟真实用户分布)
    const RENDERERS = [
        'ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (AMD, AMD Radeon RX 580 Series Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (Apple, Apple M1 Direct3D11 vs_5_0 ps_5_0)',
        'ANGLE (Apple, Apple M2 Direct3D11 vs_5_0 ps_5_0)',
        'Google SwiftShader',
        'Google SwiftShader (LLVM 12.0.0)'
    ];
    
    const VENDORS = [
        'Intel Inc.',
        'Google Inc. (Intel)',
        'NVIDIA Corporation',
        'ATI Technologies Inc.',
        'Apple'
    ];
    
    // 🎭 目标伪装值 (每次会话随机选一组)
    const targetRenderer = randomItem(RENDERERS);
    const targetVendor = randomItem(VENDORS);
    
    // 🔧 WebGL 参数伪装映射
    const spoofedParams = {
        37445: targetVendor,  // UNMASKED_VENDOR_WEBGL
        37446: targetRenderer, // UNMASKED_RENDERER_WEBGL
        7936: 'Google Inc. (Intel)',  // VENDOR (可选伪装)
        7937: 'WebKit WebGL'          // RENDERER (可选伪装)
    };
    
    // 🎨 Canvas 指纹噪声函数
    function addCanvasNoise(ctx) {
        const noise = randomFloat(-0.5, 0.5);
        const origFillText = ctx.fillText;
        ctx.fillText = function(...args) {
            ctx.save();
            ctx.setTransform(1, 0, 0, 1, 0, 0);
            ctx.globalAlpha = 0.0001 + Math.abs(noise) * 0.0001;
            origFillText.apply(ctx, args);
            ctx.restore();
            return origFillText.apply(ctx, args);
        };
        return ctx;
    }
    
    // 🔊 AudioContext 指纹混淆
    function spoofAudioContext() {
        const origCreateGain = AudioContext.prototype.createGain;
        AudioContext.prototype.createGain = function() {
            const gain = origCreateGain.call(this);
            const origGetFrequencyResponse = gain.getFrequencyResponse;
            if (origGetFrequencyResponse) {
                gain.getFrequencyResponse = function(frequencyResponse) {
                    const result = origGetFrequencyResponse.call(this, frequencyResponse);
                    // 添加微小噪声
                    for (let i = 0; i < frequencyResponse.length; i++) {
                        frequencyResponse[i] += randomFloat(-0.0001, 0.0001);
                    }
                    return result;
                };
            }
            return gain;
        };
    }
    
    // 🕸️ WebGL 伪装主函数
    function spoofWebGL() {
        const origGetParameter = WebGLRenderingContext.prototype.getParameter;
        const origGetExtension = WebGLRenderingContext.prototype.getExtension;
        
        WebGLRenderingContext.prototype.getParameter = function(param) {
            if (spoofedParams.hasOwnProperty(param)) {
                return spoofedParams[param];
            }
            // 对某些敏感参数添加随机噪声
            if (param === 7938) { // VERSION
                const ver = origGetParameter.call(this, param);
                return ver + (Math.random() > 0.7 ? ' (spoofed)' : '');
            }
            return origGetParameter.call(this, param);
        };
        
        // 伪装 getExtension 返回
        WebGLRenderingContext.prototype.getExtension = function(name) {
            const ext = origGetExtension.call(this, name);
            if (!ext) return ext;
            
            // 对某些扩展添加噪声或隐藏
            const hiddenExts = ['WEBGL_debug_renderer_info'];
            if (hiddenExts.includes(name)) {
                // 返回伪造对象，但保留基本功能
                const fakeExt = {};
                if (name === 'WEBGL_debug_renderer_info') {
                    fakeExt.UNMASKED_VENDOR_WEBGL = 37445;
                    fakeExt.UNMASKED_RENDERER_WEBGL = 37446;
                }
                return fakeExt;
            }
            return ext;
        };
        
        // 同样处理 WebGL2
        if (typeof WebGL2RenderingContext !== 'undefined') {
            const origGetParameter2 = WebGL2RenderingContext.prototype.getParameter;
            WebGL2RenderingContext.prototype.getParameter = function(param) {
                if (spoofedParams.hasOwnProperty(param)) {
                    return spoofedParams[param];
                }
                return origGetParameter2.call(this, param);
            };
        }
    }
    
    // 🎨 Canvas 2D 伪装
    function spoofCanvas() {
        const origToDataURL = HTMLCanvasElement.prototype.toDataURL;
        const origToBlob = HTMLCanvasElement.prototype.toBlob;
        
        HTMLCanvasElement.prototype.toDataURL = function(...args) {
            const result = origToDataURL.apply(this, args);
            // 对结果添加微小哈希变化（不影响视觉）
            if (result && result.startsWith('data:image')) {
                return result; // 实际项目中可添加 base64 位级扰动
            }
            return result;
        };
        
        // Hook getContext 添加噪声
        const origGetContext = HTMLCanvasElement.prototype.getContext;
        HTMLCanvasElement.prototype.getContext = function(type, attrs) {
            const ctx = origGetContext.call(this, type, attrs);
            if (type === '2d' && ctx) {
                addCanvasNoise(ctx);
            }
            return ctx;
        };
    }
    
    // 🌐 Navigator 属性增强伪装
    function spoofNavigator() {
        const props = {
            'hardwareConcurrency': [4, 8, 12, 16],
            'deviceMemory': [4, 8, 16],
            'platform': ['Win32', 'MacIntel', 'Linux x86_64'],
            'userAgent': [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
        };
        
        for (const [key, values] of Object.entries(props)) {
            try {
                Object.defineProperty(navigator, key, {
                    get: () => randomItem(values),
                    configurable: true
                });
            } catch(e) {}
        }
        
        // 语言伪装
        Object.defineProperty(navigator, 'languages', {
            get: () => ['zh-CN', 'zh', 'en-US', 'en'],
            configurable: true
        });
        Object.defineProperty(navigator, 'language', {
            get: () => 'zh-CN',
            configurable: true
        });
    }
    
    // 🚫 彻底隐藏 WebDriver 特征
    function hideAutomation() {
        // 删除 webdriver 属性
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
            configurable: true
        });
        
        // 隐藏 __driver_evaluate 等 Selenium 特征
        ['__driver_evaluate', '__webdriver_evaluate', '__selenium_evaluate', 
         '__fxdriver_evaluate', '__unwrapped', 'callSelenium', '_Selenium_IDE_Recorder'].forEach(prop => {
            try {
                if (window[prop]) delete window[prop];
            } catch(e) {}
        });
        
        // 修复 permissions 查询
        const origQuery = navigator.permissions?.query;
        if (origQuery) {
            navigator.permissions.query = function(...args) {
                const permission = args[0]?.name;
                if (permission === 'notifications') {
                    return Promise.resolve({
                        state: Notification.permission === 'granted' ? 'granted' : 'prompt',
                        onchange: null
                    });
                }
                return origQuery.apply(this, args);
            };
        }
    }
    
    // 🎯 执行所有伪装
    function initSpoofing() {
        try {
            spoofWebGL();
            spoofCanvas();
            spoofAudioContext();
            spoofNavigator();
            hideAutomation();
            console.log('[✓] Fingerprint spoofing initialized');
        } catch(e) {
            console.warn('[✗] Spoofing error:', e);
        }
    }
    
    // 页面加载完成后执行
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initSpoofing);
    } else {
        initSpoofing();
    }
    
    // 暴露调试接口（生产环境建议移除）
    window.__spoofInfo = { renderer: targetRenderer, vendor: targetVendor };
})();
"""

# ==========================================
# 3. 工具函数区域
# ==========================================
def take_screenshot(sb, step_name, username="system"):
    """截图工具函数"""
    safe_name = username.replace("@", "_").replace(".", "_")
    filepath = f"screenshots/{safe_name}_{step_name}.png"
    try:
        sb.save_screenshot(filepath)
        print(f"    📸 已截图: {step_name}.png")
    except Exception as e:
        print(f"    ⚠️ 截图失败 ({filepath}): {e}")


def inject_fingerprint_spoofing(sb):
    """注入指纹伪装脚本到浏览器"""
    try:
        sb.execute_script(WEBGL_SPOOF_SCRIPT)
        print("    🎭 WebGL/Canvas 指纹伪装已注入")
        return True
    except Exception as e:
        print(f"    ⚠️ 指纹注入失败: {e}")
        return False


def is_cloudflare_interstitial(sb) -> bool:
    """检测 CF 5秒盾"""
    try:
        page_source = sb.get_page_source()
        title = sb.get_title().lower() if sb.get_title() else ""
        
        indicators = [
            "Just a moment", "Verify you are human", "Checking your browser",
            "Checking if the site connection is secure", "Performing security verification"
        ]
        
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
    """CF 5秒盾绕过"""
    print("    🛡️ 检测到 CF 5秒盾，准备破除...")
    for attempt in range(max_attempts):
        print(f"      ▶ 尝试绕过 ({attempt+1}/{max_attempts})...")
        try:
            time.sleep(3)
            sb.execute_script('''
                var iframe = document.querySelector('iframe[src*="challenges.cloudflare"]') || 
                             document.querySelector('iframe[src*="turnstile"]');
                if (iframe) iframe.scrollIntoView({behavior:'smooth', block:'center'});
            ''')
            time.sleep(2)
            sb.uc_gui_click_captcha()
            time.sleep(8)
            if not is_cloudflare_interstitial(sb):
                print("      ✅ CF 5秒盾已通过！")
                return True
        except Exception as e:
            pass
    return False


def handle_turnstile_verification(sb) -> bool:
    """Turnstile 无感验证处理"""
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
# 4. 单账号处理流程
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
        chromium_arg="--disable-blink-features=AutomationControlled,--window-size=1920,1080,--disable-web-security,--disable-features=IsolateOrigins,site-per-process"
    ) as sb:
        # 🎯 关键：注入指纹伪装脚本
        inject_fingerprint_spoofing(sb)
        
        print(f"🌐 正在访问目标网站: {CONFIG['target_url']}")
        sb.uc_open_with_reconnect(CONFIG['target_url'], reconnect_time=8)
        time.sleep(4)
        
        # 二次注入确保页面加载后伪装生效
        inject_fingerprint_spoofing(sb)
        take_screenshot(sb, "01_初始访问页面", username)

        # 检查 IP 封锁
        page_source = sb.get_page_source()
        if "Error 1005" in page_source or "Access denied" in page_source:
            print("🚨 致命错误：当前代理节点的 IP 被彻底封锁 (Error 1005)！")
            take_screenshot(sb, "Error_1005_节点被封锁", username)
            sys.exit(1)

        # CF 盾处理
        if is_cloudflare_interstitial(sb):
            if not bypass_cloudflare_interstitial(sb):
                print("    ⚠️ 首次绕过 CF 盾失败，正在刷新页面重新尝试...")
                sb.refresh()
                time.sleep(5)
                if is_cloudflare_interstitial(sb):
                    if not bypass_cloudflare_interstitial(sb):
                        print("    🚨 致命错误：刷新网页后再次破盾失败！")
                        take_screenshot(sb, "Error_CF破盾彻底失败", username)
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
                    print("    🚨 致命错误：验证码连续 10 次识别失败！")
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
                    print(f"    ⚠️ 第 {login_attempt + 1} 次登录失败，准备重试...")
                    take_screenshot(sb, f"Error_第{login_attempt + 1}次登录失败", username)
                    sb.refresh()
                    time.sleep(3)
            
            if not login_success:
                print("    ❌ 两次登录尝试均未成功，跳过当前账号。")
                return

            # --- 签到模块 ---
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

            # --- 续费模块 ---
            if balance_value >= 2:
                print(f">>> 💻 积分达标 (当前 {balance_value})，开始执行云服务器续费任务...")
                print("    ▶ 正在强制跳转至云服务器列表网址...")
                sb.open(CONFIG['server_list_url'])
                time.sleep(4)
                take_screenshot(sb, "09_云服务器列表页", username)
                
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
                    print("    ▶ 💸 已确认支付，等待系统处理...")
                    time.sleep(8)
                    take_screenshot(sb, "12_支付完成详情页", username)
                    
                    try:
                        p_elements = sb.find_elements('section.text-gray p')
                        for p in p_elements:
                            if "到期时间" in p.text:
                                print(f"    📅 续费成功！最新 {p.text}")
                                break
                    except:
                        pass
                    
                    print("\n>>> 🔄 续费完成，返回签到中心查看最新积分...")
                    sb.open(CONFIG['sign_in_url'])
                    time.sleep(4)
                    take_screenshot(sb, "13_最终核对积分页", username)
                    
                    try:
                        final_balance_text = sb.get_text(CONFIG['points_balance_selector'])
                        print(f"    💰 续费后账户最新信息: {final_balance_text}")
                        match = re.search(r"(\d+(?:\.\d+)?)", final_balance_text)
                        if match:
                            print(f"    ✨ 最终剩余可用积分: {float(match.group(1))}")
                    except:
                        print("    ⚠️ 无法获取最终积分余额。")
                else:
                    print("    ⚠️ 当前账号下未检测到可续费的云服务器，已跳过。")
            else:
                print(f">>> 🛑 积分不足 (当前 {balance_value} < 2)，安全退出！")

        except Exception as e:
            print(f"    ❌ 账号处理过程中出现错误: {e}")
            take_screenshot(sb, "Error_程序崩溃截图", username)


# ==========================================
# 5. 主程序入口
# ==========================================
def main():
    print("🚀 自动化任务启动 (WebGL伪装增强版)...")
    accounts_str = os.environ.get("acount")
    
    if not accounts_str:
        print("⚠️ 未获取到名为 'acount' 环境变量！")
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
            
    print("\n🏁 所有队列任务已全部执行完成！")


if __name__ == "__main__":
    main()
