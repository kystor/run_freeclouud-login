import time
import os
import base64
import sys
import re
import random
from seleniumbase import SB
import ddddocr

# ==========================================
# 1. 网站配置区域 (保存所有的网页元素选择器)
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

# 确保当前目录下有一个叫做 screenshots 的文件夹，用来存报错截图
os.makedirs("screenshots", exist_ok=True)

def take_screenshot(sb, step_name, username="system"):
    """
    截图工具函数：在关键步骤或报错时拍照留存，方便我们回头排查问题。
    """
    safe_name = username.replace("@", "_").replace(".", "_")
    filepath = f"screenshots/{safe_name}_{step_name}.png"
    try:
        sb.save_screenshot(filepath)
        print(f"    📸 已截图: {step_name}.png")
    except Exception as e:
        print(f"    ⚠️ 截图失败 ({filepath}): {e}")

# ==========================================
# 2. WebGL 指纹伪装增强模块 (核心反检测)
# ==========================================
def get_random_webgl_params():
    """获取随机的WebGL参数，模拟真实用户设备"""
    vendors = [
        "NVIDIA Corporation", 
        "Intel Inc", 
        "AMD", 
        "Apple Inc.", 
        "Qualcomm"
    ]
    
    renderers = [
        "NVIDIA GeForce RTX 3080/PCIe/SSE2",
        "Intel(R) UHD Graphics 630",
        "AMD Radeon Pro 5500M",
        "Apple M1 GPU",
        "Qualcomm Adreno (TM) 640"
    ]
    
    return {
        "vendor": random.choice(vendors),
        "renderer": random.choice(renderers),
        "version": f"WebGL {random.uniform(1.0, 2.0):.1f}",
        "shading_language_version": f"WebGL GLSL ES {random.uniform(1.0, 3.0):.1f}"
    }

def enhanced_webgl_spoofing(sb):
    """
    高级WebGL指纹伪装：通过JavaScript注入修改WebGL相关属性
    这是绕过高级反爬检测的关键步骤
    """
    print("    🎭 正在执行高级WebGL指纹伪装...")
    
    webgl_params = get_random_webgl_params()
    
    try:
        # 注入WebGL伪装脚本
        sb.execute_script(f"""
            // 保存原始函数
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            const getContext = HTMLCanvasElement.prototype.getContext;
            
            // 重写getContext方法，防止被检测到修改
            HTMLCanvasElement.prototype.getContext = function(type, attributes) {{
                const context = getContext.call(this, type, attributes);
                
                if (type === 'webgl' || type === 'experimental-webgl') {{
                    // 重写getParameter方法
                    context.getParameter = function(parameter) {{
                        if (parameter === 37445) {{ // UNMASKED_VENDOR_WEBGL
                            return '{webgl_params["vendor"]}';
                        }} else if (parameter === 37446) {{ // UNMASKED_RENDERER_WEBGL
                            return '{webgl_params["renderer"]}';
                        }} else if (parameter === 35724) {{ // SHADING_LANGUAGE_VERSION
                            return '{webgl_params["shading_language_version"]}';
                        }} else if (parameter === 35723) {{ // VERSION
                            return '{webgl_params["version"]}';
                        }}
                        return getParameter.apply(this, [parameter]);
                    }};
                    
                    // 添加真实用户常见的WebGL扩展
                    const getSupportedExtensions = context.getSupportedExtensions;
                    context.getSupportedExtensions = function() {{
                        const extensions = getSupportedExtensions.call(this) || [];
                        const commonExtensions = [
                            'ANGLE_instanced_arrays',
                            'EXT_blend_minmax',
                            'EXT_color_buffer_half_float',
                            'EXT_disjoint_timer_query',
                            'EXT_float_blend',
                            'EXT_frag_depth',
                            'EXT_shader_texture_lod',
                            'EXT_sRGB',
                            'OES_element_index_uint',
                            'OES_standard_derivatives',
                            'OES_texture_float',
                            'OES_texture_float_linear',
                            'OES_texture_half_float',
                            'OES_texture_half_float_linear',
                            'OES_vertex_array_object',
                            'WEBGL_color_buffer_float',
                            'WEBGL_compressed_texture_s3tc',
                            'WEBGL_debug_renderer_info',
                            'WEBGL_debug_shaders',
                            'WEBGL_depth_texture',
                            'WEBGL_draw_buffers',
                            'WEBGL_lose_context'
                        ];
                        
                        // 随机添加一些常见扩展
                        const randomExtensions = commonExtensions
                            .sort(() => 0.5 - Math.random())
                            .slice(0, Math.floor(Math.random() * 5) + 3);
                        
                        return [...new Set([...extensions, ...randomExtensions])];
                    }};
                }}
                
                return context;
            }};
            
            // 伪装WebGL2上下文
            WebGL2RenderingContext.prototype.getParameter = function(parameter) {{
                if (parameter === 37445) {{ // UNMASKED_VENDOR_WEBGL
                    return '{webgl_params["vendor"]}';
                }} else if (parameter === 37446) {{ // UNMASKED_RENDERER_WEBGL
                    return '{webgl_params["renderer"]}';
                }} else if (parameter === 35724) {{ // SHADING_LANGUAGE_VERSION
                    return '{webgl_params["shading_language_version"]}';
                }} else if (parameter === 35723) {{ // VERSION
                    return '{webgl_params["version"]}';
                }}
                return getParameter.apply(this, [parameter]);
            }};
            
            console.log('✅ WebGL指纹伪装已成功注入');
            console.log('Vendor:', '{webgl_params["vendor"]}');
            console.log('Renderer:', '{webgl_params["renderer"]}');
        """)
        
        # 验证伪装是否成功
        verification_result = sb.execute_script("""
            try {
                const canvas = document.createElement('canvas');
                const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                
                if (!gl) {
                    console.log('❌ 无法获取WebGL上下文');
                    return false;
                }
                
                const vendor = gl.getParameter(gl.UNMASKED_VENDOR_WEBGL);
                const renderer = gl.getParameter(gl.UNMASKED_RENDERER_WEBGL);
                
                console.log('🔧 WebGL伪装验证:');
                console.log('Vendor:', vendor);
                console.log('Renderer:', renderer);
                
                return {
                    success: true,
                    vendor: vendor,
                    renderer: renderer
                };
            } catch (e) {
                console.log('❌ WebGL验证失败:', e);
                return {success: false, error: e.message};
            }
        """)
        
        if verification_result and verification_result.get('success'):
            print(f"    ✅ WebGL伪装验证成功! Vendor: {verification_result['vendor']}, Renderer: {verification_result['renderer']}")
            return True
        else:
            print("    ⚠️ WebGL伪装验证失败，但将继续执行")
            return False
            
    except Exception as e:
        print(f"    ⚠️ WebGL伪装执行失败: {e}")
        return False

def apply_browser_fingerprint_spoofing(sb):
    """
    应用完整的浏览器指纹伪装，包括WebGL、Canvas、AudioContext等
    """
    print("    🛡️ 应用完整的浏览器指纹伪装...")
    
    # WebGL伪装
    enhanced_webgl_spoofing(sb)
    
    # Canvas指纹伪装
    sb.execute_script("""
        // Canvas指纹伪装
        const toBlob = HTMLCanvasElement.prototype.toBlob;
        HTMLCanvasElement.prototype.toBlob = function() {
            const context = this.getContext('2d');
            const shift = {
                'r': Math.floor(Math.random() * 10) - 5,
                'g': Math.floor(Math.random() * 10) - 5,
                'b': Math.floor(Math.random() * 10) - 5,
                'a': Math.floor(Math.random() * 10) - 5
            };
            
            const width = this.width, height = this.height;
            const imageData = context.getImageData(0, 0, width, height);
            const data = imageData.data;
            
            for (let i = 0; i < data.length; i += 4) {
                data[i] += shift.r;
                data[i + 1] += shift.g;
                data[i + 2] += shift.b;
                data[i + 3] += shift.a;
            }
            
            context.putImageData(imageData, 0, 0);
            return toBlob.apply(this, arguments);
        };
    """)
    
    # AudioContext指纹伪装
    sb.execute_script("""
        // AudioContext指纹伪装
        if (window.AudioContext) {
            const originalGetChannelData = AnalyserNode.prototype.getChannelData;
            AnalyserNode.prototype.getChannelData = function() {
                const results = originalGetChannelData.apply(this, arguments);
                for (let i = 0; i < results.length; i++) {
                    results[i] = results[i] + (Math.random() - 0.5) * 0.0001;
                }
                return results;
            };
        }
    """)
    
    # 屏幕分辨率伪装
    screen_resolutions = [
        [1920, 1080], [1366, 768], [1440, 900], 
        [1536, 864], [1600, 900], [1680, 1050],
        [1280, 720], [2560, 1440]
    ]
    width, height = random.choice(screen_resolutions)
    
    sb.execute_script(f"""
        // 屏幕分辨率伪装
        Object.defineProperty(window.screen, 'width', {{ get: () => {width} }});
        Object.defineProperty(window.screen, 'height', {{ get: () => {height} }});
        Object.defineProperty(window.screen, 'availWidth', {{ get: () => {width} }});
        Object.defineProperty(window.screen, 'availHeight', {{ get: () => {height - 50} }});
    """)
    
    print("    ✅ 完整浏览器指纹伪装已应用")

# ==========================================
# 3. Cloudflare 绕过辅助函数 (核心破盾逻辑)
# ==========================================
def is_cloudflare_interstitial(sb) -> bool:
    """
    侦测器：通过分析网页源代码和标题，判断我们当前是不是被 CF 的 5秒盾卡住了。
    """
    try:
        page_source = sb.get_page_source()
        title = sb.get_title().lower() if sb.get_title() else ""
        
        # 这些都是 CF 盾页面经常会出现的关键词特征
        indicators = [
            "Just a moment", 
            "Verify you are human", 
            "Checking your browser", 
            "Checking if the site connection is secure",
            "Performing security verification",  # 专门为你截图里出现的特征词新增的检测
            "Cloudflare", 
            "cf-chl-bypass"
        ]
        
        # 只要源码里命中任何一个特征词，就判定为撞盾了
        for ind in indicators:
            if ind in page_source:
                return True
                
        # 标题检测
        if "just a moment" in title or "attention required" in title or "cloudflare" in title:
            return True
            
        # 页面内容非常少，且包含 challenges.cloudflare.com 链接，也属于撞盾
        body_len = sb.execute_script('(function() { return document.body ? document.body.innerText.length : 0; })();')
        if body_len is not None and body_len < 200 and "challenges.cloudflare.com" in page_source:
            return True
            
        return False
    except:
        return False

def bypass_cloudflare_interstitial(sb, max_attempts=4) -> bool:
    """
    破盾器：尝试用鼠标去点击那个证明自己是人类的框框。
    """
    print("    🛡️ 检测到 CF 5秒盾，准备破除...")
    for attempt in range(max_attempts):
        print(f"      ▶ 尝试绕过 ({attempt+1}/{max_attempts})...")
        try:
            # 等待 3 秒，让 CF 验证码那个框框在网页里彻底加载出来
            time.sleep(3)
            
            # 【关键优化】用 JS 代码把 CF 的验证框强制拖拉到屏幕的正中间！
            # 这一步非常重要，因为在 Github Actions 的虚拟屏幕里，如果不居中，鼠标可能点到空气。
            sb.execute_script('''
                var iframe = document.querySelector('iframe[src*="challenges.cloudflare"]') || 
                             document.querySelector('iframe[src*="turnstile"]');
                if (iframe) {
                    iframe.scrollIntoView({behavior:'smooth', block:'center'});
                    // 强制iframe可见
                    iframe.style.display = 'block';
                    iframe.style.visibility = 'visible';
                }
                
                // 同时尝试点击可能的按钮
                var buttons = document.querySelectorAll('button, input[type="button"], input[type="submit"]');
                for (var i = 0; i < buttons.length; i++) {
                    if (buttons[i].innerText.toLowerCase().includes('verify') || 
                        buttons[i].innerText.toLowerCase().includes('human') ||
                        buttons[i].innerText.toLowerCase().includes('continue')) {
                        buttons[i].scrollIntoView({behavior:'smooth', block:'center'});
                        break;
                    }
                }
            ''')
            time.sleep(2) # 稍微等一下页面滚动动画结束
            
            # 调用 SeleniumBase 自带的终极拟人化点击大法
            sb.uc_gui_click_captcha()
            
            # 点完之后不要急，给 CF 服务器 8 秒钟时间去验算和放行网页
            time.sleep(8) 
            
            # 再查一次看看是不是还在盾里，如果不在了，说明破盾成功
            if not is_cloudflare_interstitial(sb):
                print("      ✅ CF 5秒盾已通过！")
                return True
        except Exception as e:
            print(f"      ⚠️ 尝试 {attempt+1} 失败: {e}")
            time.sleep(2) # 发生小报错没关系，继续下一轮尝试
            
    return False

def handle_turnstile_verification(sb) -> bool:
    """
    二次保险机制：有时候 CF 盾是隐藏的（无感验证），这部分代码专门应对这些老六验证码。
    """
    try:
        # 如果网页上有烦人的 Cookie 接受按钮，先把它点掉，免得挡住验证码
        cookie_btn = 'button[data-cky-tag="accept-button"]'
        if sb.is_element_visible(cookie_btn):
            sb.click(cookie_btn)
            time.sleep(1)
    except:
        pass

    # 尝试把隐藏的 Turnstile 模块也拉到屏幕中间
    sb.execute_script('''
        try {
            var elements = [
                document.querySelector('.cf-turnstile'),
                document.querySelector('iframe[src*="challenges.cloudflare"]'),
                document.querySelector('iframe[src*="turnstile"]'),
                document.querySelector('[data-callback*="turnstile"]'),
                document.querySelector('.turnstile')
            ];
            
            for (var el of elements) {
                if (el) {
                    el.scrollIntoView({behavior:'smooth', block:'center'});
                    el.style.display = 'block';
                    el.style.visibility = 'visible';
                    break;
                }
            }
        } catch(e) {}
    ''')
    time.sleep(2)

    has_turnstile = False
    # 扫描 15 秒，看看网页到底有没有埋伏隐藏的验证码
    for _ in range(15):
        if (sb.is_element_present('iframe[src*="challenges.cloudflare"]') or 
            sb.is_element_present('iframe[src*="turnstile"]') or 
            sb.is_element_present('.cf-turnstile') or 
            sb.is_element_present('input[name="cf-turnstile-response"]') or
            sb.is_element_present('[data-sitekey]')):
            has_turnstile = True
            break
        time.sleep(1)

    if not has_turnstile:
        print("    🟢 无感验证通过 (未发现 Turnstile)")
        return True

    print("    🧩 发现验证码，执行拟人点击...")
    verified = False
    
    # 尝试物理点击 3 次
    for attempt in range(1, 4):
        try:
            print(f"      ▶ 尝试点击 ({attempt}/3)...")
            sb.uc_gui_click_captcha()
        except Exception as e:
            print(f"      ⚠️ 点击失败: {e}")
            pass
            
        # 每次点完检查 10 秒，看看隐藏的通过令牌 (Token) 有没有发下来
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

    # 如果还没好，死等 30 秒，有时候网站自己会慢慢放行
    if not verified:
        print("      ⏳ 等待自动放行 (30秒)...")
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
# 4. 单个账号的处理流程 (登录 -> 签到 -> 续费)
# ==========================================
def process_single_account(username, password):
    print(f"\n==========================================")
    print(f"➡️ 开始处理账号: {username}")
    print(f"==========================================")
    
    # 获取我们在 Github Actions 里布置好的本地 Xray 代理端口
    env_proxy = os.environ.get("HTTP_PROXY")
    
    # 打开一个拥有极强反检测能力的浏览器 (UC Mode)
    with SB(
        uc=True,            # 启用无痕模式
        test=True,          # 启用测试模式
        locale="en",        # 设置英语环境
        headless=False,     # 必须是 False，因为我们要配合 xvfb 虚拟屏幕来模拟真人
        proxy=env_proxy,    # 代理设置
        chromium_arg="--disable-blink-features=AutomationControlled,--window-size=1920,1080,--disable-webrtc"
    ) as sb:
        print(f"🌐 正在访问目标网站: {CONFIG['target_url']}")
        # 带有自动重连机制的打开网址，防抖动
        sb.uc_open_with_reconnect(CONFIG['target_url'], reconnect_time=8)
        time.sleep(4)
        
        take_screenshot(sb, "01_初始访问页面", username)

        # 应用高级浏览器指纹伪装
        apply_browser_fingerprint_spoofing(sb)
        time.sleep(2)
        
        # 检查 IP 是不是被 CF 直接掐断了 (Error 1005)
        page_source = sb.get_page_source()
        if "Error 1005" in page_source or "Access denied" in page_source:
            print("🚨 致命错误：当前代理节点的 IP 被彻底封锁 (Error 1005)！")
            take_screenshot(sb, "Error_1005_节点被封锁", username)
            sys.exit(1) # IP 死了，直接停掉整个程序

        # 第一道关卡：CF 5秒盾处理
        if is_cloudflare_interstitial(sb):
            # 第一轮（尝试4次点击）
            if not bypass_cloudflare_interstitial(sb):
                print("    ⚠️ 首次绕过 CF 盾失败，正在刷新页面重新尝试...")
                sb.refresh() # 刷新网页从头再来
                time.sleep(5)
                
                if is_cloudflare_interstitial(sb):
                    # 第二轮（再尝试4次点击）
                    if not bypass_cloudflare_interstitial(sb):
                        print("    🚨 致命错误：刷新网页后再次破盾失败！退出整个程序。")
                        take_screenshot(sb, "Error_CF破盾彻底失败", username)
                        sys.exit(1) # 彻底绝望，杀死 Python 程序，抛出红灯报警
                        
            time.sleep(3) 
            
        # 第二道关卡：隐藏盾处理
        handle_turnstile_verification(sb)
        time.sleep(3)
        take_screenshot(sb, "02_绕过CF准备填写表单", username)

        try:
            # --- 登录模块 ---
            login_success = False 
            
            # 给自己 2 次登录机会，防止网络波动
            for login_attempt in range(2):
                print(f"    ▶ 开始第 {login_attempt + 1} 次尝试登录...")
                
                captcha_success = False 
                
                # 图片验证码识别循环 (最多尝试刷新识别10次)
                for captcha_attempt in range(10): 
                    sb.wait_for_element(CONFIG['captcha_img_selector'], timeout=10)
                    img_src = sb.get_attribute(CONFIG['captcha_img_selector'], "src")
                    
                    if img_src and "base64," in img_src:
                        base64_data = img_src.split(',')[1]
                        img_bytes = base64.b64decode(base64_data)
                        
                        # 调用 ddddocr 库，给图片里的验证码做识别
                        ocr = ddddocr.DdddOcr(show_ad=False)
                        captcha_text = ocr.classification(img_bytes)
                        
                        # 这个网站的验证码通常是纯数字，用 isdigit() 排除乱码
                        if captcha_text.isdigit() and len(captcha_text) == 4:  # 假设是4位数字验证码
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
                
                # 如果 10 次都没看懂图片验证码，说明网站改版了，停工报错。
                if not captcha_success:
                    print("    🚨 致命错误：验证码连续 10 次识别失败！程序将直接退出。")
                    take_screenshot(sb, "Error_验证码十次识别失败", username)
                    sys.exit(1) 

                # 自动填写账号密码和验证码
                sb.clear(CONFIG['username_selector'])
                sb.type(CONFIG['username_selector'], username)
                
                sb.clear(CONFIG['password_selector'])
                sb.type(CONFIG['password_selector'], password)
                
                sb.clear(CONFIG['captcha_input_selector'])
                sb.type(CONFIG['captcha_input_selector'], captcha_text)
                
                take_screenshot(sb, "03_填写账号和验证码", username)
                
                # 点击登录大按钮
                sb.click(CONFIG['login_btn_selector'])
                time.sleep(5)
                
                # 检查网页上有没有出现用户中心的专属链接，有的话代表登进去了
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
            
            # 两轮都没进去，直接跳过处理下个账号，不要在死胡同里硬钻
            if not login_success:
                print("    ❌ 两次登录尝试均未成功，跳过当前账号的后续任务。")
                return 

            # ==========================================
            # 🌟 每日签到与积分提取模块
            # ==========================================
            print("\n>>> 🎁 准备执行每日签到任务...")
            sb.open(CONFIG['sign_in_url'])
            time.sleep(4) 
            take_screenshot(sb, "05_跳转到签到页面", username)
            
            balance_value = 0.0 
            
            # 给自己 5 次机会刷简单的数学题
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    sb.click(CONFIG['sign_in_btn_selector'])
                    time.sleep(2) 
                    
                    # 抓取算术题文字，然后利用 Python 的 eval 函数直接计算答案！
                    question_text = sb.get_text(CONFIG['math_question_selector'])
                    math_expr = question_text.replace("请计算：", "").replace("=", "").strip()
                    
                    # 安全计算表达式
                    if any(char in math_expr for char in ['+', '-', '*', '/']):
                        result = eval(math_expr)
                        
                        # 如果除法遇到小数，填进去可能不认，干脆刷新换一题
                        if isinstance(result, float) and not result.is_integer():
                            print(f"      ⚠️ 题目 {math_expr} = {result} 包含小数，刷新换题...")
                            sb.refresh() 
                            time.sleep(3)
                            continue     
                        
                        final_answer = int(result) 
                        print(f"    ✅ 计算结果为整数: {final_answer}，正在提交...")
                        
                        # 填写算出来的答案
                        sb.clear(CONFIG['math_input_selector']) 
                        sb.type(CONFIG['math_input_selector'], str(final_answer))
                        
                        take_screenshot(sb, "06_填写签到算术答案", username)
                        sb.click(CONFIG['verify_btn_selector'])
                        
                        # 抓取签到成功或者失败的弹窗文字播报出来
                        sb.wait_for_element(CONFIG['popup_content_selector'], timeout=5)
                        popup_msg = sb.get_text(CONFIG['popup_content_selector'])
                        print(f"    🔔 签到系统提示: 【{popup_msg}】")
                        
                        take_screenshot(sb, "07_签到结果弹窗", username)
                        
                        sb.click(CONFIG['popup_confirm_btn_selector'])
                        time.sleep(2) 
                        
                        # 强制刷新一下网页，让积分立刻更新显示
                        print("    🔄 正在强制刷新页面以同步最新的余额数据...")
                        sb.refresh()
                        time.sleep(4)
                        
                        take_screenshot(sb, "08_刷新获取最新积分", username)
                        
                        # 用正则表达式 (Regex) 从一段文字里抠出数字余额
                        try:
                            balance_text = sb.get_text(CONFIG['points_balance_selector'])
                            print(f"    💰 当前账户原始信息: {balance_text}")
                            match = re.search(r"(\d+(?:\.\d+)?)", balance_text)
                            if match:
                                balance_value = float(match.group(1))
                                print(f"    🔍 提取并转换可用积分为: {balance_value}")
                        except Exception as e:
                            print(f"    ⚠️ 无法获取积分余额: {e}")

                        print("    🎉 签到流程结束。\n")
                        break 
                    else:
                        print(f"    ⚠️ 无法识别数学题格式: '{question_text}'")
                        sb.refresh()
                        time.sleep(3)
                except Exception as e:
                    print(f"    ⚠️ 签到尝试失败: {e}")
                    sb.refresh()
                    time.sleep(3)
            else:
                # 这里的 else 是搭配上面的 for 使用的，意思是一层一层的循环跑完了都没成功
                print("    ❌ 签到失败：连续 5 次刷新都没有遇到可以整除的算术题。")
                take_screenshot(sb, "Error_签到数学题失败", username)

            # ==========================================
            # 🌟 积分判断与云服务器续费模块
            # ==========================================
            # 大于或等于 2 分才够续费，否则跳过
            if balance_value >= 2:
                print(f">>> 💻 积分达标 (当前 {balance_value} 分)，开始执行云服务器续费任务...")
                
                print("    ▶ 正在强制跳转至云服务器列表网址...")
                sb.open(CONFIG['server_list_url'])
                time.sleep(4) 
                take_screenshot(sb, "09_云服务器列表页", username)
                
                # 看看列表里有没有可以打钩的云服务器
                if sb.is_element_present(CONFIG['server_checkbox_selector']):
                    sb.click(CONFIG['server_checkbox_selector'])
                    print("    ▶ 已勾选目标云服务器。")
                    
                    # 使用 js_click（一种非常强力的后台点击）点下续费按钮
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
                    
                    # 在支付完成的小票页面里翻找"到期时间"这几个字，找到了就说明彻底成功
                    try:
                        p_elements = sb.find_elements('section.text-gray p')
                        for p in p_elements:
                            if "到期时间" in p.text:
                                print(f"    📅 续费成功！最新 {p.text}")
                                break
                        else:
                            print("    ⚠️ 未找到到期时间信息，但支付流程已完成")
                    except Exception as e:
                        print(f"    ⚠️ 检查到期时间时出错: {e}")
                    
                    # 收尾动作：跳回签到中心看看钱扣成功了没
                    print("\n>>> 🔄 续费完成，返回签到中心查看最新积分...")
                    sb.open(CONFIG['sign_in_url'])
                    time.sleep(4)
                    
                    take_screenshot(sb, "13_最终核对积分页", username)
                    
                    try:
                        final_balance_text = sb.get_text(CONFIG['points_balance_selector'])
                        print(f"    💰 续费后账户最新信息: {final_balance_text}")
                        match = re.search(r"(\d+(?:\.\d+)?)", final_balance_text)
                        if match:
                            print(f"    ✨ 最终剩余可用积分: {float(match.group(1))} 分")
                    except Exception as e:
                        print(f"    ⚠️ 无法获取最终积分余额: {e}")
                        
                else:
                    print("    ⚠️ 当前账号下未检测到可续费的云服务器，已跳过。")
            else:
                print(f">>> 🛑 积分不足 (当前 {balance_value} < 2)，安全退出当前账号的后续操作！")

        except Exception as e:
            # 抓捕所有不可预知的崩溃，拍照并打印出错误原因
            print(f"    ❌ 账号处理或执行过程中出现错误: {e}")
            import traceback
            traceback.print_exc()
            take_screenshot(sb, "Error_程序崩溃截图", username)

# ==========================================
# 5. 主程序入口
# ==========================================
def main():
    print("🚀 自动化任务启动...")
    print(f"⏰ 当前时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 从 Github Actions 的环境机密变量里拿取账号本
    accounts_str = os.environ.get("acount")
    
    if not accounts_str:
        print("⚠️ 未获取到名为 'acount' 环境变量！")
        print("💡 请在环境变量中设置格式为: email1:password1,email2:password2")
        return

    # 按英文逗号切割所有的账号密码
    account_list = accounts_str.split(',')
    print(f"📋 共检测到 {len(account_list)} 个账号。")
    
    for item in account_list:
        item = item.strip()
        # 识别类似 admin@gmail.com:123456 的格式
        if ':' in item:
            parts = item.split(':', 1) 
            username = parts[0].strip()
            password = parts[1].strip()
            
            # 开始进入上面写的那个庞大的流程函数干活
            process_single_account(username, password)
        else:
            print(f"⚠️ 跳过无效格式: '{item}'，正确格式应为 'email:password'")
            
    print("\n🏁 所有队列任务已全部执行完成！")

# 这是 Python 约定俗成的入口保护门
if __name__ == "__main__":
    main()
