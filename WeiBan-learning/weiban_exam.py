"""
微伴课程刷题自动化脚本
第一阶段：获取课程列表
第二阶段：自动刷课（翻页 + 静音 + 自动完成）
"""

import os
import sys
import glob
import json
import time
import math
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains

# ============================================================
# 配置区
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, "frozen", False) else __file__))
EDGE_DRIVER_PATH = os.path.join(BASE_DIR, "msedgedriver.exe")
COOKIE_FILE = os.path.join(BASE_DIR, "cookies.json")
SCREENSHOT_PATH = os.path.join(BASE_DIR, "click.png")

TARGET_URL = (
    "https://weiban.mycourse.cn/#/course"
    "?projectId=b4fa1a0f-7ef8-4181-b849-2dd8aa3ef587"
    "&projectType=special&id=undefined"
)

# 黑名单课程（自动跳过，不进行刷课）
BLACKLIST_COURSES = {
    "常见诈骗—冒充网购客服退款诈骗",
    "长治久安",
    "差之毫厘谬以千里",
    "预防食物中毒",
    "溺水自救篇",
    "常见诈骗—投资理财诈骗",
    "网购游戏装备骗局",
    "网购二手手机骗局",
    "校园反诈行动：这些坑别踩！",
    "话不能乱听！",
    "火场逃脱生存战",
    "隐秘的伤害",
    "电动自行车违法违规之消防篇",
}

def take_screenshot(driver):
    """截图保存为 click.png。"""
    try:
        driver.save_screenshot(SCREENSHOT_PATH)
    except Exception:
        pass


# ============================================================
# Cookie 持久化
# ============================================================
def get_browser_storage(driver):
    """读取浏览器localStorage和sessionStorage，打印调试信息"""
    ls = driver.execute_script("""
        var items = {};
        for (var i = 0; i < localStorage.length; i++) {
            var key = localStorage.key(i);
            items[key] = localStorage.getItem(key);
        }
        return items;
    """)
    ss = driver.execute_script("""
        var items = {};
        for (var i = 0; i < sessionStorage.length; i++) {
            var key = sessionStorage.key(i);
            items[key] = sessionStorage.getItem(key);
        }
        return items;
    """)
    print(f"\n  [debug] localStorage ({len(ls)} 项): {json.dumps(ls, ensure_ascii=False)}")
    print(f"  [debug] sessionStorage ({len(ss)} 项): {json.dumps(ss, ensure_ascii=False)}")
    return ls, ss


def save_cookies_to_file(driver):
    """保存当前浏览器cookies + localStorage + sessionStorage到文件"""
    cookies = driver.get_cookies()
    local_storage, session_storage = get_browser_storage(driver)
    print(f"\n> 收集到 {len(cookies)} 个 Cookie")
    try:
        with open(COOKIE_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                "cookies": cookies,
                "localStorage": local_storage,
                "sessionStorage": session_storage,
            }, f, ensure_ascii=False, indent=2)
        print(f"> 已保存到 {COOKIE_FILE}")
    except Exception as e:
        print(f"[!] 保存失败: {e}")
    return cookies, local_storage, session_storage


def load_cookies_from_file():
    """从文件加载cookies+storage，文件不存在时返回None"""
    if not os.path.exists(COOKIE_FILE):
        return None
    try:
        with open(COOKIE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # 兼容旧格式（纯cookie列表）
        if isinstance(data, list):
            return {"cookies": data, "localStorage": {}, "sessionStorage": {}}
        return data
    except Exception:
        return None


def is_session_valid(driver):
    """检查当前 weiban.mycourse.cn 会话是否有效"""
    try:
        time.sleep(2)
        if "login" in driver.current_url.lower():
            return False
        return True
    except:
        return False


# ============================================================
# 浏览器初始化
# ============================================================
def check_driver():
    if not os.path.exists(EDGE_DRIVER_PATH):
        print(f"[!] 未找到 Edge Driver: {EDGE_DRIVER_PATH}")
        print(f"\n请先运行 update_driver.py 自动下载匹配的驱动:")
        print(f"  python {os.path.join(BASE_DIR, 'update_driver.py')}\n")
        return False
    return True


def create_driver(headless=True):
    """初始化Edge浏览器，headless=False 时有界面模式用于首次登录"""
    if not check_driver():
        raise FileNotFoundError(f"msedgedriver.exe 不存在于 {EDGE_DRIVER_PATH}")

    service = Service(executable_path=EDGE_DRIVER_PATH)
    options = webdriver.EdgeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    if headless:
        options.add_argument("--headless")
    return webdriver.Edge(service=service, options=options)


# ============================================================
# 登录
# ============================================================
def ensure_logged_in(driver):
    """使用已保存的Cookie+localStorage+sessionStorage自动登录，返回数据或 None（失败）"""
    saved = load_cookies_from_file()
    if saved is None:
        return None

    print("  [自动登录] 检测到已保存的凭据，尝试自动登录")
    driver.get("https://weiban.mycourse.cn/")
    time.sleep(2)

    for cookie in saved.get("cookies", []):
        try:
            driver.add_cookie(cookie)
        except:
            pass

    ls = saved.get("localStorage", {})
    if ls:
        driver.execute_script("""
            var data = arguments[0];
            for (var key in data) {
                localStorage.setItem(key, data[key]);
            }
        """, ls)
    ss = saved.get("sessionStorage", {})
    if ss:
        driver.execute_script("""
            var data = arguments[0];
            for (var key in data) {
                sessionStorage.setItem(key, data[key]);
            }
        """, ss)
    if ls or ss:
        print(f"  [OK] 已恢复 localStorage={len(ls)}项 sessionStorage={len(ss)}项")

    # 直接导航到课程页，让 SPA 初始化时读 localStorage 拿 token
    driver.get("https://weiban.mycourse.cn/#/course")
    time.sleep(5)

    if is_session_valid(driver):
        print("  [OK] 自动登录成功")
        return saved
    else:
        print("  [凭据已过期]")
        return None


def check_duplicate_login(driver) -> bool:
    """检测是否出现重复登录提示，如果是则清空 JSON 并返回 True。"""
    page_text = driver.find_element(By.TAG_NAME, "body").text
    if "重复登录" in page_text:
        print("\n" + "=" * 55)
        print("  [!] 检测到重复登录!")
        print("  请确保账号不在其他设备登录")
        print("=" * 55)
        take_screenshot(driver)
        cleanup_old_json()
        return True
    return False


# ============================================================
# 获取课程列表
# ============================================================
def get_course_list(driver) -> list[dict]:
    """展开所有分类，返回完整课程列表。"""
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "van-collapse")))

    category_items = driver.find_elements(By.CLASS_NAME, "van-collapse-item")
    print(f"\n共发现 {len(category_items)} 个分类")

    all_courses = []

    for idx, item in enumerate(category_items):
        try:
            title_el = item.find_element(By.CSS_SELECTOR, ".van-collapse-item__title .text")
            category_name = title_el.text.strip()

            count_el = item.find_element(By.CSS_SELECTOR, ".van-collapse-item__title .count")
            count_text = count_el.text.strip()

            print(f"\n[{idx + 1}] {category_name} ({count_text})")

            # 滚动 + 展开
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'})", item
            )
            time.sleep(0.5)

            if idx > 0:
                prev_title = category_items[idx - 1].find_element(
                    By.CSS_SELECTOR, ".van-collapse-item__title"
                )
                driver.execute_script("arguments[0].click()", prev_title)
                time.sleep(0.2)

            driver.execute_script("arguments[0].click()", title_el)
            time.sleep(0.5)

            # 提取课程
            items = item.find_elements(By.CSS_SELECTOR, ".img-texts-list .img-texts-item")
            for course in items:
                all_courses.append({
                    "category": category_name,
                    "title": course.find_element(By.CSS_SELECTOR, ".title").text.strip(),
                    "passed": "passed" in course.get_attribute("class"),
                })

            print(f"    抓取到 {len(items)} 个课程")

        except Exception as e:
            print(f"    [错误] {e}")

    return all_courses


# ============================================================
# 自动刷课
# ============================================================

def collapse_all_categories(driver):
    """将所有分类收起来。"""
    category_items = driver.find_elements(By.CLASS_NAME, "van-collapse-item")
    for item in category_items:
        try:
            wrapper = item.find_element(By.CSS_SELECTOR, ".van-collapse-item__wrapper")
            if "display: none" not in (wrapper.get_attribute("style") or ""):
                title = item.find_element(By.CSS_SELECTOR, ".van-collapse-item__title")
                driver.execute_script("arguments[0].click()", title)
                time.sleep(0.2)
        except Exception:
            pass


def expand_category(driver, category_name: str):
    """找到指定名称的分类并展开。"""
    category_items = driver.find_elements(By.CLASS_NAME, "van-collapse-item")
    for item in category_items:
        try:
            text = item.find_element(By.CSS_SELECTOR, ".van-collapse-item__title .text").text.strip()
            if text == category_name:
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'})", item
                )
                time.sleep(0.3)
                title = item.find_element(By.CSS_SELECTOR, ".van-collapse-item__title")
                driver.execute_script("arguments[0].click()", title)
                time.sleep(0.5)

                # 确保展开
                wrapper = item.find_element(By.CSS_SELECTOR, ".van-collapse-item__wrapper")
                if "display: none" in (wrapper.get_attribute("style") or ""):
                    driver.execute_script("arguments[0].click()", title)
                    time.sleep(0.5)
                return item
        except Exception:
            continue
    return None


def find_unfinished_courses(driver, category_item) -> list[str]:
    """从已展开的分类中找出所有未完成课程的标题（只返回标题，不存元素引用防 stale）。"""
    items = category_item.find_elements(By.CSS_SELECTOR, ".img-texts-list .img-texts-item")
    titles = []
    for item in items:
        if "passed" not in (item.get_attribute("class") or ""):
            title = item.find_element(By.CSS_SELECTOR, ".title").text.strip()
            titles.append(title)
    return titles


def find_course_element(driver, category_item, title: str):
    """从分类中按标题找到对应的课程元素。"""
    items = category_item.find_elements(By.CSS_SELECTOR, ".img-texts-list .img-texts-item")
    for item in items:
        try:
            t = item.find_element(By.CSS_SELECTOR, ".title").text.strip()
            if t == title:
                return item
        except Exception:
            continue
    return None


def cleanup_old_json():
    """删除之前生成的所有 course_list JSON 文件及 Cookie 文件。"""
    pattern = os.path.join(BASE_DIR, "course_list_*.json")
    for f in glob.glob(pattern):
        os.remove(f)
        print(f"  删除旧文件: {os.path.basename(f)}")
    if os.path.exists(COOKIE_FILE):
        os.remove(COOKIE_FILE)
        print(f"  删除Cookie文件: {os.path.basename(COOKIE_FILE)}")


def save_course_list_json(all_courses: list[dict], total: int, passed: int):
    """将课程列表保存为 JSON（文件名只精确到日）。"""
    today = datetime.now().strftime("%Y%m%d")
    output = {
        "date": today,
        "total": total,
        "passed": passed,
        "courses": all_courses,
    }
    filepath = os.path.join(BASE_DIR, f"course_list_{today}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n课程列表已保存至: {filepath}")


def click_course(driver, title: str, category_item):
    """按标题找到课程并点击，等 Vue 页面渲染完再返回。"""
    elem = find_course_element(driver, category_item, title)
    if not elem:
        raise Exception(f"未找到课程 '{title}'")
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'})", elem)
    time.sleep(0.3)
    link = elem.find_element(By.CSS_SELECTOR, "h5.title, .title")
    driver.execute_script("arguments[0].click()", link)
    # 等 Vue 路由切换到课程详情页
    try:
        WebDriverWait(driver, 8).until(
            lambda d: "course/detail" in (d.current_url or "")
        )
    except Exception as e:
        print(f"    [debug] 等待 course/detail URL 超时: {e}")
    # 等页面完全渲染（关键延迟）
    print("    [debug] 等待页面渲染...")
    time.sleep(4)


def mute_audio(driver):
    """静音页面中的 audio/video 元素（只静音，不暂停）。"""
    driver.execute_script("""
        document.querySelectorAll('audio, video').forEach(el => {
            el.muted = true;
            el.volume = 0;
        });
    """)


CONTENT_IFRAME_SRC_PREFIX = "mcwk.mycourse.cn"


def switch_to_content_iframe(driver) -> bool:
    """切换到内容 iframe（mcwk.mycourse.cn），返回是否成功。"""
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    for f in iframes:
        src = f.get_attribute("src") or ""
        if CONTENT_IFRAME_SRC_PREFIX in src:
            driver.switch_to.frame(f)
            return True
    return False


def get_active_section(driver):
    """返回当前可见的 section（优先 page-active，其次任何显示中的 page-item）。"""
    for sel in ("section.page-active", "section[class*='page-'].page-active"):
        sections = driver.find_elements(By.CSS_SELECTOR, sel)
        if sections:
            return sections[0]
    # 没有 page-active → 找任何 visible 的 page-item（page-none + display:block）
    sections = driver.find_elements(By.CSS_SELECTOR, "section.page-item")
    for sec in sections:
        visible = driver.execute_script(
            "return arguments[0].offsetParent !== null && "
            "arguments[0].getBoundingClientRect().height > 0",
            sec
        )
        if visible:
            return sec
    return None


def wait_for_video_completion(driver):
    """检测页面是否有视频，在视频正中心模拟点击播放，等播放完成。"""
    # 轮询等待视频元素出现（有些课程点开始后视频才加载）
    video_info = None
    for _ in range(10):  # 最多等 10 秒
        video_info = driver.execute_script("""
            var v = document.querySelector('video');
            if (!v) return null;
            var r = v.getBoundingClientRect();
            return {
                duration: v.duration,
                currentTime: v.currentTime,
                paused: v.paused,
                x: r.left + r.width / 2,
                y: r.top + r.height / 2,
                w: r.width,
                h: r.height
            };
        """)
        if video_info and video_info.get("w", 0) > 0 and video_info.get("h", 0) > 0:
            break
        video_info = None
        time.sleep(1)
    if not video_info:
        return False

    print("    [视频] 检测到视频元素")

    # 先静音
    mute_audio(driver)
    driver.execute_script("""
        var v = document.querySelector('video');
        if (v) { v.muted = true; v.volume = 0; }
    """)

    # 在视频正中心模拟真实点击（先播放，HLS 视频需要开始加载后才能获取 duration）
    try:
        video_el = driver.find_element(By.TAG_NAME, "video")
        ActionChains(driver).move_to_element(video_el).click().perform()
        print(f"    [视频] 在视频中心({video_info['x']:.0f}, {video_info['y']:.0f})点击播放")
    except Exception:
        driver.execute_script("""
            var v = document.querySelector('video');
            if (v) { v.muted = true; if (v.paused) v.play(); }
        """)
        print("    [视频] JS 方式播放")

    # 获取 duration（HLS/m3u8 视频在播放前 duration 为 NaN，需等 metadata 加载）
    duration = video_info.get("duration")
    if not duration or duration == float("inf"):
        print("    [视频] 等待视频元数据加载...")
        for _ in range(8):  # 最多等 16 秒
            time.sleep(2)
            duration = driver.execute_script("""
                var v = document.querySelector('video');
                return v ? v.duration : null;
            """)
            if duration and duration != float("inf"):
                break

    if duration and duration != float("inf"):
        print(f"    [视频] 时长 {int(duration)} 秒 ({int(duration // 60)} 分 {int(duration % 60)} 秒)")
        wait_sec = math.ceil(duration / 30) * 30 + 15
        had_valid_duration = True
    else:
        print("    [视频] 无法获取时长，最多等待 10 分钟")
        wait_sec = 600
        had_valid_duration = False

    end_time = time.time() + wait_sec
    last_time = -1
    stall_count = 0
    while time.time() < end_time:
        status = driver.execute_script("""
            var v = document.querySelector('video');
            if (!v) return { done: true };
            return {
                done: v.ended || (v.currentTime > 0 && v.duration > 0 && v.currentTime >= v.duration - 1),
                currentTime: v.currentTime
            };
        """)
        if status.get("done"):
            print(f"    [视频] 播放完成")
            return True

        # 检测视频卡住：currentTime 持续无变化说明已播完或卡住
        ct = status.get("currentTime", 0)
        if ct == last_time and ct > 0:
            stall_count += 1
        else:
            stall_count = 0
        last_time = ct
        if stall_count >= 15:  # 30 秒没变化
            print(f"    [视频] 播放似乎已结束 (currentTime={ct:.1f})")
            return True

        time.sleep(2)

    # 超时：区分是网络问题还是正常长视频
    if not had_valid_duration:
        print("\n" + "=" * 55)
        print("  [!] 视频长时间无法加载")
        print("  [!] 请检查网络环境或代理设置")
        print("=" * 55)
        print("\n  可能的原因:")
        print("  · 网络连接不稳定")
        print("  · 代理/VPN 拦截了视频请求")
        print("  · 平台视频服务器不可达")
        print("  · 浏览器需要登录验证（尝试手动打开一次视频页面）")
        print("\n  ⚠ 排查网络问题后重新运行程序\n")
        input("按 Enter 退出...")
        sys.exit(1)
    else:
        print("    [视频] 等待超时")
        return False


def try_click_bottom_area(driver):
    """
    在页面 50% 宽度处，从 99% 高度开始每 2% 向上点击一次（共 5 次）。
    若检测到页面发生变化（有效点击）则立即停止。
    返回 True 表示至少有一次有效点击。
    """
    for i in range(5):
        y_pct = 99 - i * 2
        before = driver.execute_script("""
            var a = document.querySelector('.page-active');
            return a ? a.className : document.body.innerHTML.length;
        """)
        driver.execute_script("""
            var x = window.innerWidth * 0.5;
            var y = window.innerHeight * """ + str(y_pct) + """ / 100;
            var el = document.elementFromPoint(x, y);
            if (el) { el.click(); return true; }
            return false;
        """)
        time.sleep(1)
        after = driver.execute_script("""
            var a = document.querySelector('.page-active');
            return a ? a.className : document.body.innerHTML.length;
        """)
        if before != after:
            return True
    return False


def wait_for_start_button(driver, timeout=8):
    """等待并点击"开始"按钮，支持多种页面结构。"""
    end_time = time.time() + timeout

    # 策略1: 等页 DOM 稳定
    while time.time() < end_time:
        ready = driver.execute_script("""
            return document.readyState === 'complete'
                && document.body !== null
                && document.body.children.length > 0;
        """)
        if ready:
            break
        time.sleep(0.5)

    # 策略2: CSS 选择器遍历（覆盖 a / button / div / span / 多种 class 风格）
    css_selectors = [
        "section.page-start a.btn-start",
        "section[class*='page-start'] a.btn-start",
        "a.btn-start",
        "a.base-an.btn-start",
        "a.an-position.btn-start",
        "a[class*='btn-start']",
        "button.btn-start",
        "button[class*='btn-start']",
        "section.page-start button",
        "section[class*='page-start'] button",
        "div.btn-start",
        "div[class*='btn-start']",
        "span[class*='btn-start']",
        "span[class*='start-btn']",
        "[class*='btn-start']",
        "[class*='start-btn']",
        ".pri-start-btn",
        "span.pri-start-btn",
    ]
    for sel in css_selectors:
        try:
            btn = driver.find_element(By.CSS_SELECTOR, sel)
            driver.execute_script("arguments[0].click()", btn)
            print(f"    [OK] 点击开始按钮 (via '{sel}')")
            time.sleep(3)
            mute_audio(driver)
            return True
        except NoSuchElementException:
            continue

    # 策略3: 图片链接
    try:
        imgs = driver.find_elements(By.CSS_SELECTOR, "img[src*='start'], img[src*='Start'], img[src*='begin']")
        for img in imgs:
            parent = driver.execute_script("return arguments[0].closest('a') || arguments[0].parentElement", img)
            if parent:
                driver.execute_script("arguments[0].click()", parent)
                print("    [OK] 点击开始按钮 (via img)")
                time.sleep(3)
                mute_audio(driver)
                return True
    except Exception:
        pass

    # 策略4: XPath 文本匹配（任何可见的 a/button/span/div 含"开始"文本）
    for text in ("开始学习", "开始", "进入课程", "进入学习", "进入", "start", "Start"):
        try:
            btns = driver.find_elements(
                By.XPATH,
                f"//*[contains(text(), '{text}')][self::a or self::button or self::span or self::div]"
            )
            for btn in btns:
                visible = driver.execute_script(
                    "return arguments[0].offsetParent !== null && arguments[0].getBoundingClientRect().width > 0",
                    btn
                )
                if visible:
                    driver.execute_script("arguments[0].click()", btn)
                    print(f"    [OK] 点击开始按钮 (via text '{text}')")
                    time.sleep(3)
                    mute_audio(driver)
                    return True
        except Exception:
            continue

    # 策略5: JS 万能扫描 —— 找任意内含"开始"的可点击元素
    clicked = driver.execute_script("""
        var keywords = ['开始', '进入', 'start', 'Start'];
        var all = document.querySelectorAll('a, button, span, div, h1, h2, h3, p, i, em');
        for (var k = 0; k < keywords.length; k++) {
            var kw = keywords[k];
            for (var i = 0; i < all.length; i++) {
                var el = all[i];
                if (el.offsetParent === null) continue;
                var text = (el.textContent || '').trim();
                if (text.indexOf(kw) !== -1 && text.length < 20) {
                    el.click();
                    return true;
                }
            }
        }
        return false;
    """)
    if clicked:
        print("    [OK] 点击开始按钮 (via JS 文本扫描)")
        time.sleep(3)
        mute_audio(driver)
        return True

    # 策略6: 如果 page-start 处于 page-none（未激活），强制激活并点击
    activated = driver.execute_script("""
        var start = document.querySelector('.page-start');
        if (!start) return 'no_start_section';
        if (start.classList.contains('page-active')) return 'already_active';
        // 强制激活 page-start 区域
        start.classList.remove('page-none');
        start.classList.add('page-active');
        // 尝试点击里面的开始按钮（覆盖多种 class 风格）
        var btn = start.querySelector('.page-start-btn, [class*=\"btn-start\"], [class*=\"start-btn\"], a, button, .pri-start-btn, span[class*=\"pri-start\"]');
        if (btn) {
            btn.click();
            return 'activated_and_clicked';
        }
        return 'activated_but_no_button';
    """)
    if activated == "activated_and_clicked":
        print("    [OK] 强制激活 page-start 并点击开始按钮")
        time.sleep(3)
        mute_audio(driver)
        return True
    elif activated == "activated_but_no_button":
        print("    [debug] 已激活 page-start，但未在里面找到按钮")
        # 重新跑一遍 CSS 选择器
        for sel in css_selectors:
            try:
                btn = driver.find_element(By.CSS_SELECTOR, sel)
                driver.execute_script("arguments[0].click()", btn)
                print(f"    [OK] 点击开始按钮 (via activate + '{sel}')")
                time.sleep(3)
                mute_audio(driver)
                return True
            except NoSuchElementException:
                continue

    print("    [!] 未找到开始按钮")
    return False


def click_return_or_back(driver) -> bool:
    """点击"返回"或"返回列表"按钮。"""
    for text in ("返回列表", "返回", "back"):
        try:
            btn = driver.find_element(By.XPATH, f"//*[contains(text(), '{text}')]")
            driver.execute_script("arguments[0].click()", btn)
            time.sleep(1)
            return True
        except NoSuchElementException:
            pass
    return False


def handle_multi_buttons(driver) -> bool:
    """
    处理多按钮页面：界面上有多个按钮需要依次点击。
    每个按钮点开后等显示完全，点"返回"回到选择页，再点下一个。
    全部点完后返回 True，由主循环继续找"下一页"。
    """
    active = get_active_section(driver)
    if not active:
        return False

    buttons = active.find_elements(By.CSS_SELECTOR, "a.base-an, a.btn-option")
    if len(buttons) < 2:
        # 也试试看是不是 page-start 里有多按钮
        buttons = active.find_elements(By.CSS_SELECTOR, "a.an-position")
        buttons = [b for b in buttons if "btn-start" not in (b.get_attribute("class") or "")]
        if len(buttons) < 2:
            return False

    texts_seen = set()
    for btn in buttons:
        text = btn.text.strip()
        if not text or text in texts_seen:
            continue
        texts_seen.add(text)
        try:
            print(f"    点击选项: {text}")
            driver.execute_script("arguments[0].click()", btn)
            time.sleep(2)
            mute_audio(driver)
            for _ in range(4):
                if click_return_or_back(driver):
                    break
                time.sleep(2)
        except Exception:
            continue

    print("    所有选项点完，找下一页...")
    return True


def click_next_or_btn(driver) -> str:
    """
    基于 .page-active 切换的翻页逻辑：
      1. 全局搜"返回列表"按钮（优先检测课程结束）
      2. 检测 active section 中的 page-test-btn（进入答题页）
      3. 若 .page-end 激活 → 点 a.back-list → "return_list"
      4. 若普通 page 激活 → 点 a.btn-next → "next_page"
      5. 无匹配 → "not_found"
    """
    # 优先检查"返回列表"按钮（必须在可视范围内）
    for sel in ("button.comment-footer-button",
                "section.comment-footer button",
                "a.back-list", "a[class*='back-list']"):
        try:
            btn = driver.find_element(By.CSS_SELECTOR, sel)
            visible = driver.execute_script(
                "return arguments[0].offsetParent !== null", btn
            )
            if not visible:
                continue
            text = btn.text.strip()
            if "返回" in text or "back" in text.lower() or "list" in text.lower() or btn.tag_name == "a":
                driver.execute_script("arguments[0].click()", btn)
                time.sleep(1)
                return "return_list"
        except NoSuchElementException:
            continue
    # 按 text 全局搜索（也检查可视）
    try:
        btn = driver.find_element(By.XPATH, "//*[contains(text(), '返回列表')]")
        visible = driver.execute_script(
            "return arguments[0].offsetParent !== null", btn
        )
        if visible:
            driver.execute_script("arguments[0].click()", btn)
            time.sleep(1)
            return "return_list"
    except NoSuchElementException:
        pass

    active = get_active_section(driver)
    if not active:
        return "not_found"

    # 检测 page-test-btn（进入答题的特殊按钮，无标准翻页按钮）
    try:
        test_btn = active.find_element(By.CSS_SELECTOR, "span.page-test-btn")
        driver.execute_script("arguments[0].click()", test_btn)
        time.sleep(2)
        return "next_page"
    except NoSuchElementException:
        pass

    classes = active.get_attribute("class") or ""
    is_end = "page-end" in classes.split()

    if is_end:
        for sel in ("a.back-list", "a.page-end-back", "a[class*='back-list']",
                     "button.comment-footer-button"):
            try:
                btn = active.find_element(By.CSS_SELECTOR, sel)
                if btn.tag_name == "button" and btn.text.strip() not in ("返回列表", "返回"):
                    continue
                driver.execute_script("arguments[0].click()", btn)
                time.sleep(1)
                return "return_list"
            except NoSuchElementException:
                continue

    # 普通内容页 → 找 btn-next
    for sel in ("a.btn-next", "a.base-an.btn-next", "a.btn-base.btn-next",
                "a[class*='btn-next']", "div.btn-next", "div[class*='btn-next']",
                "div.page-content-common.btn-next"):
        try:
            btn = active.find_element(By.CSS_SELECTOR, sel)
            driver.execute_script("arguments[0].click()", btn)
            time.sleep(2)
            return "next_page"
        except NoSuchElementException:
            continue

    # 全局兜底：active section 可能是旧的 page-start（仍带 page-active），
    # 而真正的 btn-next 在当前 iframe 的其它位置
    for sel in ("div.btn-next", "div[class*='btn-next']",
                "div.page-content-common.btn-next",
                "a.btn-next", "a[class*='btn-next']",
                ".page-success-button"):
        try:
            btn = driver.find_element(By.CSS_SELECTOR, sel)
            # 强制激活 btn 所在的 section（防止 page-none 导致不可见）
            driver.execute_script("""
                var sec = arguments[0].closest('section.page-item');
                if (sec && sec.classList.contains('page-none')) {
                    sec.classList.remove('page-none');
                    sec.style.display = 'block';
                }
            """, btn)
            visible = driver.execute_script(
                "return arguments[0].offsetParent !== null && "
                "arguments[0].getBoundingClientRect().height > 0",
                btn
            )
            if visible:
                driver.execute_script("arguments[0].click()", btn)
                time.sleep(2)
                return "next_page"
        except NoSuchElementException:
            continue

    # 最后兜底：可能结束页没有 page-end class
    try:
        btn = active.find_element(By.CSS_SELECTOR, "button.comment-footer-button")
        if btn.text.strip() in ("返回列表", "返回"):
            driver.execute_script("arguments[0].click()", btn)
            time.sleep(1)
            return "return_list"
    except NoSuchElementException:
        pass

    return "not_found"


def _generate_combinations(n):
    """生成所有非空的多选组合，返回索引列表的列表。"""
    combos = []
    for mask in range(1, 1 << n):
        combo = []
        for i in range(n):
            if mask & (1 << i):
                combo.append(i)
        combos.append(combo)
    return combos


def _find_in_section(section, selectors):
    """从 section 内找第一个存在的元素（不判断可见性，改用 JS 判断）。"""
    for sel in selectors:
        try:
            el = section.find_element(By.CSS_SELECTOR, sel)
            visible = el.parent.execute_script(
                "return arguments[0].offsetParent !== null", el
            )
            if visible:
                return el
        except NoSuchElementException:
            continue
    return None


def _click_submit_and_check(driver, submit_btn) -> bool:
    """点击提交，检测结果。返回 True 表示答对并继续，False 表示答错。"""
    driver.execute_script("arguments[0].click()", submit_btn)
    print(f"    [小测] 已提交，等待结果...")

    # 等 1~5 秒，轮询检测按钮
    active = None
    for i in range(5):
        time.sleep(1)
        take_screenshot(driver)
        active = get_active_section(driver)
        if not active:
            continue

        # 先查继续按钮（btn-at）—— 答对优先
        cont = _find_in_section(active, (
            "a.btn-at", "a[class*='btn-at']",
        ))
        if cont:
            driver.execute_script("arguments[0].click()", cont)
            print(f"    [小测] 正确，点击继续!")
            time.sleep(2)
            take_screenshot(driver)
            return True

        # 再查返回按钮（btn-af）—— 答错
        back = _find_in_section(active, (
            "a.btn-af", "a[class*='btn-af']",
            "a.btn-back", "a[class*='btn-back']",
        ))
        if back:
            driver.execute_script("arguments[0].click()", back)
            time.sleep(1)
            return False

    print("    [小测] 结果不确定")
    return False


def handle_quiz(driver) -> bool:
    """
    处理测验页：自动答题。
    支持单选（逐题尝试选项）和多选（遍历组合）。
    """
    active = get_active_section(driver)
    if not active:
        return False

    # 检测是否为测验页
    is_quiz = False
    for sel in ("a.btn-ce", "a.btn-aq"):
        try:
            active.find_element(By.CSS_SELECTOR, sel)
            is_quiz = True
            break
        except NoSuchElementException:
            continue
    if not is_quiz:
        return False

    print("    [小测] 检测到测验页")

    # 进入测验（btn-ce）
    try:
        ce = active.find_element(By.CSS_SELECTOR, "a.btn-ce, a[class*='btn-ce']")
        driver.execute_script("arguments[0].click()", ce)
        print("    [小测] 进入测验...")
        time.sleep(3)
        take_screenshot(driver)
        active = get_active_section(driver)
        if not active:
            return False
    except NoSuchElementException:
        pass

    # 有 btn-at 直接跳过（可能已答过）
    try:
        at = active.find_element(By.CSS_SELECTOR, "a.btn-at, a[class*='btn-at']")
        if at.is_displayed():
            driver.execute_script("arguments[0].click()", at)
            print("    [小测] 跳过!")
            time.sleep(2)
            return True
    except NoSuchElementException:
        pass

    # 解析题目选项（按 name 属性分组，不依赖容器类名）
    def _parse_options(section):
        # 找所有 radio 和 checkbox
        all_inputs = section.find_elements(
            By.CSS_SELECTOR,
            "input[type='radio'].aq-item-sl, input[type='checkbox']"
        )
        # 按 name 分组（同一题选项共享 name）
        groups = {}
        for inp in all_inputs:
            name = inp.get_attribute("name") or "_no_name"
            if name not in groups:
                groups[name] = []
            groups[name].append(inp)
        result = []
        for name, group in groups.items():
            opts = []
            for inp in group:
                t = 'radio' if inp.get_attribute("type") == "radio" else 'checkbox'
                opts.append((t, inp, inp.find_element(By.XPATH, "./ancestor::label")))
            if opts:
                result.append(opts)
        return result

    questions = _parse_options(active)
    if not questions:
        print("    [小测] 未找到题目")
        try:
            aq = active.find_element(By.CSS_SELECTOR, "a.btn-aq, a[class*='btn-aq']")
            return _click_submit_and_check(driver, aq)
        except NoSuchElementException:
            return False

    print(f"    [小测] 共 {len(questions)} 题")

    # 检查是否有复选框（多选题）
    has_checkbox = any(opts and opts[0][0] == 'checkbox' for opts in questions)

    if not has_checkbox:
        # === 纯单选题：每轮每道题选第 round_idx 个选项 ===
        for round_idx in range(max(len(opts) for opts in questions)):
            for q_opts in questions:
                if round_idx < len(q_opts):
                    driver.execute_script("arguments[0].click()", q_opts[round_idx][2])
            time.sleep(1)
            try:
                aq = active.find_element(By.CSS_SELECTOR, "a.btn-aq, a[class*='btn-aq']")
                if _click_submit_and_check(driver, aq):
                    return True
            except NoSuchElementException:
                continue
            # 答错了 → 重获页面元素
            time.sleep(1)
            active = get_active_section(driver)
            if not active:
                return False
            questions = _parse_options(active)
    else:
        # === 多选题：遍历组合 ===
        for q_opts in questions:
            if not q_opts or q_opts[0][0] != 'checkbox':
                continue
            all_checkboxes = [opt[1] for opt in q_opts]
            for combo in _generate_combinations(len(q_opts)):
                # 用 JS 清空所有选中（绕过 is_selected() 不可靠问题）
                driver.execute_script(
                    "arguments[0].forEach(function(el){ el.checked = false; "
                    "el.dispatchEvent(new Event('change', {bubbles: true})) });",
                    all_checkboxes
                )
                time.sleep(0.3)
                # 选中 combo 中的选项
                for idx in combo:
                    driver.execute_script("arguments[0].click()", q_opts[idx][2])
                time.sleep(1)
                try:
                    aq = active.find_element(By.CSS_SELECTOR, "a.btn-aq, a[class*='btn-aq']")
                    if _click_submit_and_check(driver, aq):
                        return True
                except NoSuchElementException:
                    continue
                time.sleep(1)
                active = get_active_section(driver)
                if not active:
                    return False
                questions = _parse_options(active)

    print("    [小测] 答题完成")
    return True


def handle_page_quiz(driver):  # returns True(pass) / None(wrong,retry) / False(no quiz)
    """处理 page-options / page-commit 型测验（带 data-answer 的 div 选项）。"""
    # 只在当前激活的 section 中查找 commit（防止找到已答过的页面）
    active = get_active_section(driver)
    if not active:
        return False
    active_class = active.get_attribute("class") or ""
    # 跳过 page-start 和 page-end 等非测验页
    if "page-start" in active_class or "page-end" in active_class:
        return False

    commit = None
    for tag in ("span.page-commit", "div.page-commit"):
        try:
            el = active.find_element(By.CSS_SELECTOR, tag)
            commit = el
            break
        except NoSuchElementException:
            continue
    if not commit:
        return False

    print("    [page小测] 检测到 page-commit 型测验")

    # 选项也限定到当前激活 section（防止跨页混杂）
    options = active.find_elements(By.CSS_SELECTOR, "div.page-option")
    if not options:
        print("    [page小测] 未找到选项")
        return False

    print(f"    [page小测] 共 {len(options)} 个选项")

    # 策略1: 从 data-all-answer 直接获取答案
    #    优先查 commit 自身，其次查兄弟/同 section 内的 page-options
    all_answer = commit.get_attribute("data-all-answer")
    if not all_answer:
        all_answer = driver.execute_script("""
            var commit = arguments[0];
            // 兄弟节点中的 page-options
            var parent = commit.parentElement;
            if (parent) {
                var opts = parent.querySelector('[class*="page-options"]');
                if (opts) return opts.getAttribute('data-all-answer') || '';
            }
            // 兜底：同 section 内查找
            var sec = commit.closest('section.page-item');
            if (sec) {
                var opts = sec.querySelector('[class*="page-options"]');
                if (opts) return opts.getAttribute('data-all-answer') || '';
            }
            return '';
        """, commit)

    # 将选项限定到 commit 所在的 section（防止跨页混杂）
    options = driver.execute_script("""
        var commit = arguments[0];
        var sec = commit.closest('section.page-item');
        if (!sec) return [];
        var items = sec.querySelectorAll('div.page-option');
        return Array.from(items);
    """, commit)
    if not options:
        print("    [page小测] 未找到选项（限定范围后）")
        return False

    if all_answer:
        print(f"    [page小测] 从 data-all-answer 获取答案: {all_answer}")
        correct = list(all_answer)
        for opt in options:
            ans = (opt.get_attribute("data-answer") or "").lower()
            if ans in correct:
                driver.execute_script("arguments[0].click()", opt)
                print(f"    [page小测] 选择选项 {ans}")
                time.sleep(0.3)

        driver.execute_script("arguments[0].click()", commit)
        print("    [page小测] 已提交")
        time.sleep(3)

        # 检测结果页：JS 查找+激活，赋临时 ID，Python 用 ActionChains 点击
        btn_info = driver.execute_script("""
            var TEMP_ID = '_tmp_result_btn';
            function mark(el, type) {
                if (!el) return null;
                el.scrollIntoView({block:'center'});
                el.id = TEMP_ID;
                return type;
            }
            function vis(el) {
                if (!el) return false;
                var r = el.getBoundingClientRect();
                return r.width > 0 && r.height > 0;
            }
            // 1) success
            var s = document.querySelector('.page-success-button');
            if (vis(s)) return mark(s, 'success');
            // 2) fail
            var f = document.querySelector('.page-fail-button');
            if (f && f.getBoundingClientRect().width > 0) return mark(f, 'fail');
            // 3) page-fail 区域（可能 page-none）
            var fs = document.querySelector('.page-fail');
            if (fs) {
                fs.classList.remove('page-none');
                fs.classList.add('page-active');
                fs.style.display = 'block';
                var fb = fs.querySelector('img, [class*="button"], a, button, div[onclick]');
                if (fb && fb.getBoundingClientRect().width > 0) return mark(fb, 'fail');
            }
            // 4) 模糊 fail 匹配
            var fuzzy = document.querySelectorAll('[class*="fail-button"], [class*="fail_btn"], '+
                '[class*="error-back"], img[src*="fail"], img[src*="error"]');
            for (var i = 0; i < fuzzy.length; i++) {
                if (fuzzy[i].getBoundingClientRect().width > 0) return mark(fuzzy[i], 'fail');
            }
            // 5) "返回"/"重试" 文本
            var all = document.querySelectorAll('a, button, span, div, img');
            for (var i = 0; i < all.length; i++) {
                var txt = (all[i].textContent || all[i].alt || '').trim();
                if (txt.indexOf('返回') !== -1 || txt.indexOf('重试') !== -1 || txt.indexOf('重新') !== -1) {
                    if (all[i].getBoundingClientRect().width > 0) return mark(all[i], 'fail');
                }
            }
            return null;
        """)
        if btn_info:
            try:
                btn_el = driver.find_element(By.ID, "_tmp_result_btn")
                ActionChains(driver).move_to_element(btn_el).click().perform()
                if btn_info == "success":
                    print("    [page小测] 正确！点击成功页继续按钮")
                    time.sleep(2)
                    # 让主循环自行处理后续翻页/下个测验
                    return True
                else:
                    print("    [page小测] 答错，点击失败页返回按钮（ActionChains）")
                    time.sleep(2)
                    return None
            except Exception as e:
                print(f"    [page小测][debug] 找到按钮({btn_info})但点击失败: {e}")

        # 未检测到结果按钮 → 检查 commit 是否还在
        leftover = driver.find_elements(By.CSS_SELECTOR,
            "span.page-commit, div.page-commit")
        still_there = (
            leftover
            and driver.execute_script(
                "return arguments[0].offsetParent !== null && "
                "arguments[0].getBoundingClientRect().height > 0",
                leftover[0]
            )
        )
        if still_there:
            print("    [page小测] 提交后仍在同一页，可能答错")
            return None

        # commit 消失 → 扫最大可见元素，用 ActionChains 点
        print("    [page小测][debug] 页面已切换，扫描最大可见元素...")
        best_id = driver.execute_script("""
            var candidates = document.querySelectorAll(
                'img, a, button, [onclick], [class*="button"], [class*="btn"], [role="button"]'
            );
            var best = null, bestArea = 0;
            for (var i = 0; i < candidates.length; i++) {
                var r = candidates[i].getBoundingClientRect();
                var area = r.width * r.height;
                if (area > 100 && area > bestArea) { best = candidates[i]; bestArea = area; }
            }
            if (best) { best.scrollIntoView({block:'center'}); best.id = '_tmp_best'; return best.tagName + '.' + (best.className || ''); }
            return null;
        """)
        if best_id:
            try:
                best_el = driver.find_element(By.ID, "_tmp_best")
                print(f"    [page小测] ActionChains 点击元素 <{best_id}>")
                ActionChains(driver).move_to_element(best_el).click().perform()
                time.sleep(2)
                return None
            except Exception:
                pass

        # 真找不到
        print("    [page小测] 提交后页面无任何可交互元素")
        return None

    # 策略2: 没有 data-all-answer → 遍历
    n = len(options)
    is_multi = any(
        "check" in (opt.get_attribute("class") or "")
        or "multi" in (opt.get_attribute("class") or "")
        for opt in options
    )

    def _is_page_gone():
        return driver.execute_script("""
            var commit = arguments[0];
            var sec = commit.closest('section.page-item');
            if (!sec) return true;
            var c = sec.querySelector('span.page-commit, div.page-commit');
            return !c || c.offsetParent === null;
        """, commit)

    def _refetch_options():
        return driver.execute_script("""
            var commit = arguments[0];
            var sec = commit.closest('section.page-item');
            if (!sec) return [];
            return Array.from(sec.querySelectorAll('div.page-option'));
        """, commit)

    if not is_multi:
        for idx in range(n):
            driver.execute_script("arguments[0].click()", options[idx])
            print(f"    [page小测] 尝试选项 {idx + 1}")
            time.sleep(0.5)
            driver.execute_script("arguments[0].click()", commit)
            time.sleep(1.5)
            if _is_page_gone():
                return True
            options = _refetch_options()
            if len(options) != n:
                return None
        return None

    # 多选：遍历组合
    for mask in range(1, 1 << n):
        for i in range(n):
            if mask & (1 << i):
                driver.execute_script("arguments[0].click()", options[i])
        time.sleep(0.5)
        driver.execute_script("arguments[0].click()", commit)
        time.sleep(1.5)
        if _is_page_gone():
            return True
        options = _refetch_options()
        if len(options) != n:
            return None
    return None


def complete_single_course(driver, course_title: str, category_item) -> bool:
    """
    完成单个课程的学习流程。
    基于 .page-active 切换检测，每次找当前激活 section 的翻页按钮。
    返回 True 表示完成，False 表示失败。
    """
    print(f"\n  --- 开始课程: {course_title} ---")

    click_course(driver, course_title, category_item)

    # 切换到内容 iframe
    in_content = switch_to_content_iframe(driver)
    if in_content:
        print(f"    [OK] 已切换到内容 iframe")
    mute_audio(driver)

    # 等待并点击开始按钮
    found_start = wait_for_start_button(driver)
    take_screenshot(driver)
    if not found_start:
        print("    没有开始按钮，尝试在底部区域逐点点击...")
        if try_click_bottom_area(driver):
            print("    [OK] 底部点击触发了页面变化")
        mute_audio(driver)
        # 点击后重新找开始按钮
        found_start = wait_for_start_button(driver)
        if found_start:
            print("    [OK] 点击后找到开始按钮")
        else:
            print("    仍未找到开始按钮，直接翻页...")

    # 检测视频并等待播放完成
    wait_for_video_completion(driver)

    # 循环翻页
    page_count = 0
    while True:
        time.sleep(2)
        page_count += 1
        mute_audio(driver)

        # 检测是否回到了课程列表（切回主 frame 检查）
        if in_content:
            driver.switch_to.parent_frame()
        try:
            driver.find_element(By.CLASS_NAME, "van-collapse")
            print(f"    [OK] 检测到课程列表，已回到列表")
            return True
        except NoSuchElementException:
            pass
        # 切回内容 iframe（重新查找，避免 stale reference）
        if in_content:
            switch_to_content_iframe(driver)

        # 先检查是否是测验页
        if handle_quiz(driver):
            continue

        # 检查 page-commit 型测验（data-answer 版）
        page_quiz_result = handle_page_quiz(driver)
        if page_quiz_result is True:      # 答对 → 下一页
            continue
        elif page_quiz_result is None:    # 答错 → 点 fail 按钮后已回退，重试
            continue

        result = click_next_or_btn(driver)
        if result == "return_list":
            print(f"    [OK] 课程完成！（共 {page_count} 页）")
            take_screenshot(driver)
            time.sleep(2)
            return True
        elif result == "next_page":
            take_screenshot(driver)
            if page_count % 5 == 0:
                print(f"    已翻 {page_count} 页...")
        else:
            print(f"    未找到翻页按钮（第 {page_count} 次）")
            if handle_multi_buttons(driver):
                time.sleep(2)
                continue

            # 至少重试 2 次找翻页按钮
            retried = False
            for _ in range(2):
                time.sleep(3)
                result = click_next_or_btn(driver)
                if result == "return_list":
                    print(f"    [OK] 课程完成！（共 {page_count} 页）")
                    take_screenshot(driver)
                    time.sleep(2)
                    return True
                elif result == "next_page":
                    take_screenshot(driver)
                    retried = True
                    break
            if retried:
                continue

            # 最后尝试：在底部逐点点击
            print("    尝试底部区域逐点点击...")
            try_click_bottom_area(driver)
            time.sleep(2)
            result = click_next_or_btn(driver)
            if result == "return_list":
                print(f"    [OK] 课程完成！（共 {page_count} 页）")
                take_screenshot(driver)
                time.sleep(2)
                return True
            elif result == "next_page":
                take_screenshot(driver)
                continue

            print("    [!] 无法找到翻页按钮，跳过此课程")
            return False


def auto_complete(driver, all_courses: list[dict]):
    """
    自动刷课主流程：
      1. 收起所有大类
      2. 遍历存在未完成课程的大类
      3. 展开 → 逐个点击未完成课程 → 自动翻页完成
    """
    # 先回到课程列表页
    driver.get(TARGET_URL)
    time.sleep(3)

    # 收起所有分类
    print("\n收起所有分类...")
    collapse_all_categories(driver)

    # 按大类分组，只处理有未完成课程的大类
    categories = {}
    for c in all_courses:
        if not c["passed"]:
            categories.setdefault(c["category"], []).append(c["title"])

    total_unfinished = sum(len(v) for v in categories.values())
    if total_unfinished == 0:
        print("\n[OK] 所有课程已完成！")
        return

    print(f"\n待完成课程: {total_unfinished} 个，分布在 {len(categories)} 个分类")

    completed = 0
    failed_courses = []
    for cat_name, course_titles in categories.items():
        print(f"\n{'=' * 50}")
        print(f"分类: {cat_name}（待完成 {len(course_titles)} 个）")
        print(f"{'=' * 50}")

        # 展开当前分类
        cat_item = expand_category(driver, cat_name)
        if not cat_item:
            print(f"  [!] 无法展开分类 '{cat_name}'，跳过")
            continue

        # 获取该分类下未完成课程的标题列表
        unfinished_titles = find_unfinished_courses(driver, cat_item)
        if not unfinished_titles:
            print("  该分类下未找到未完成课程")
            continue

        for course_title in unfinished_titles:
            # 检查黑名单（视作课程失败）
            if course_title in BLACKLIST_COURSES:
                print(f"  [-] 黑名单课程，跳过: {course_title}")
                failed_courses.append(course_title)
                continue

            # 清屏 + 输出头图 + 失败记录
            if os.name == "nt":
                os.system("cls")
            else:
                os.system("clear")
            print("              :::::::::::::::::::                                  :::::::::::::::::::              ")
            print("          ::::::::::::::::::::::::::;                           :::::::::::::::::::::::::;          ")
            print("        ::::::::::::::::::::::::::::::                        ::::::::::::::::::::::::::::::        ")
            print("      ::::::::::::::::::::::::::::::::::;                    :::::::::::::::::::::::::::::::::      ")
            print("    ::::::::::::::::::::::::::::::::::::::;                  :::::::::::::::::::::::::::::::::::    ")
            print("    :::::::::::::             :::::::::::::::                ::::::::::            ::::::::::::::   ")
            print("  ::::::::::::                  :::::::::::::::                ::::;                  ::::::::::::  ")
            print(" ;::::::::::;         :::         ::::::::::::::;  ::::::::                            ;::::::::::; ")
            print(" ::::::::::          :::::          ;:::::::::::::::::::::::                             :::::::::: ")
            print(";:::::::::;          :::::             :::::::::::::::::::::                             :::::::::::")
            print("::::::::::      ;:::::::::::::;         :::::::::::::::::::           :::::::::::::       ::::::::::")
            print("::::::::::      :::::::::::::::            ::::::::::::::;           :::::::::::::::      ::::::::::")
            print("::::::::::      :::::::::::::::          ::::::::::::::::::           ::::::::::::::      ::::::::::")
            print(";::::::::::          :::::             ::::::::::::::::::::::                            ;:::::::::;")
            print(" ::::::::::          :::::           ::::::::::::::::::::::::::                          :::::::::: ")
            print(" :::::::::::         :::::         ::::::::::::::; ::::::::::::::                       ::::::::::: ")
            print("  :::::::::::;                   :::::::::::::::    :::::::::::::::                   ::::::::::::  ")
            print("   ::::::::::::                ::::::::::::::          ::::::::::::::                ::::::::::::   ")
            print("    :::::::::::::::;       ::::::::::::::::              ::::::::::::::::       ::::::::::::::::    ")
            print("     ::::::::::::::::::::::::::::::::::::;                 ::::::::::::::::::::::::::::::::::::     ")
            print("       ;:::::::::::::::::::::::::::::::                      ::::::::::::::::::::::::::::::::       ")
            print("         ;:::::::::::::::::::::::::::                          ::::::::::::::::::::::::::::         ")
            print("            ;::::::::::::::::::::::                               ::::::::::::::::::::::            ")
            print("                 ::::::::::::;                                        :::::::::::::          ")
            if failed_courses:
                print(f"\n  [!] 之前 {len(failed_courses)} 个课程失败:")
                for name in failed_courses:
                    print(f"      · {name}")
            print()

            try:
                success = complete_single_course(driver, course_title, cat_item)
                if success:
                    completed += 1
                    print(f"  [OK] 已完成 ({completed}/{total_unfinished})")
                else:
                    failed_courses.append(course_title)

                # 课程完成后检查是否被踢到登录页，是则尝试恢复
                time.sleep(2)
                if "login" in driver.current_url.lower():
                    print("  [!] 检测到登录页，尝试恢复...")
                    login_result = ensure_logged_in(driver)
                    if login_result is None:
                        print("  [!] 恢复失败，终止运行")
                        break
                    print("  [OK] 已恢复，继续下一课")
                    print(f"  [!] 课程失败 ({completed}/{total_unfinished})")

                # 回到课程列表继续下一个
                driver.get(TARGET_URL)
                time.sleep(2)
                # 重新展开当前分类
                cat_item = expand_category(driver, cat_name)

            except Exception as e:
                failed_courses.append(course_title)
                print(f"  [错误] 处理课程时异常: {e}")
                driver.get(TARGET_URL)
                time.sleep(2)
                cat_item = expand_category(driver, cat_name)

    completed_str = f"刷课完成！成功完成 {completed}/{total_unfinished}"
    print(f"\n{' ' * (50 - len(completed_str))}{completed_str}")
    if failed_courses:
        fail_header = f"以下 {len(failed_courses)} 个课程失败:"
        print(f"\n{' ' * (50 - len(fail_header))}{fail_header}")
        for name in failed_courses:
            print(f"  · {name}")
    print()

    return failed_courses


# ============================================================
# 主流程
# ============================================================
def main():
    print("=" * 55)
    print("微伴课程刷题助手")
    print("=" * 55)

    # ===== 登录流程 =====
    saved_cookies = load_cookies_from_file()

    if saved_cookies is None:
        # 首次使用：有界面模式登录获取Cookie
        print("\n[1/3] 启动浏览器（首次登录）...")
        try:
            driver = create_driver(headless=False)
        except Exception as e:
            print(f"[!] 浏览器启动失败: {e}")
            print(f"[!] 请确认 {EDGE_DRIVER_PATH} 存在且版本匹配")
            input("\n按 Enter 退出...")
            return

        print("\n[2/3] 登录...")
        print("\n" + "=" * 55)
        print("  [首次运行] 请在浏览器中手动登录")
        print("=" * 55)
        print("  登录后回到此终端按 Enter 继续")
        print("=" * 55)
        driver.get("https://weiban.mycourse.cn/")
        time.sleep(3)
        input()
        time.sleep(2)

        # 跳转到课程页面确保Cookie完整
        driver.get("https://weiban.mycourse.cn/#/course")
        time.sleep(3)
        if "login" in driver.current_url.lower():
            print("[!] 登录失败，仍在登录页")
            input("\n按 Enter 退出...")
            driver.quit()
            return

        save_cookies_to_file(driver)
        driver.quit()
        print("\n" + "=" * 55)
        print("  首次登录完成，请重新启动程序开始刷课")
        print("=" * 55)
        input("\n按 Enter 退出...")
        return

    # 有Cookie：无头模式自动登录
    print("\n[1/3] 启动 Edge 浏览器...")
    try:
        driver = create_driver(headless=False)
    except Exception as e:
        print(f"[!] 浏览器启动失败: {e}")
        print(f"[!] 请确认 {EDGE_DRIVER_PATH} 存在且版本匹配")
        input("\n按 Enter 退出...")
        return

    try:
        print("\n[2/3] 登录...")
        saved_cookies = ensure_logged_in(driver)
        if saved_cookies is None:
            driver.quit()
            try:
                os.remove(COOKIE_FILE)
                print("  [已删除过期Cookie文件]")
            except:
                pass
            print("\n" + "=" * 55)
            print("  Cookie已过期，请重新启动程序并重新登录")
            print("=" * 55)
            input("\n按 Enter 退出...")
            return

        # 检测重复登录
        if check_duplicate_login(driver):
            input("\n请处理重复登录后按 Enter 退出...")
            return

        # --- 登录成功 → 清屏并输出艺术字 ---
        if os.name == "nt":
            os.system("cls")
        else:
            os.system("clear")
        print("              :::::::::::::::::::                                  :::::::::::::::::::              ")
        print("          ::::::::::::::::::::::::::;                           :::::::::::::::::::::::::;          ")
        print("        ::::::::::::::::::::::::::::::                        ::::::::::::::::::::::::::::::        ")
        print("      ::::::::::::::::::::::::::::::::::;                    :::::::::::::::::::::::::::::::::      ")
        print("    ::::::::::::::::::::::::::::::::::::::;                  :::::::::::::::::::::::::::::::::::    ")
        print("    :::::::::::::             :::::::::::::::                ::::::::::            ::::::::::::::   ")
        print("  ::::::::::::                  :::::::::::::::                ::::;                  ::::::::::::  ")
        print(" ;::::::::::;         :::         ::::::::::::::;  ::::::::                            ;::::::::::; ")
        print(" ::::::::::          :::::          ;:::::::::::::::::::::::                             :::::::::: ")
        print(";:::::::::;          :::::             :::::::::::::::::::::                             :::::::::::")
        print("::::::::::      ;:::::::::::::;         :::::::::::::::::::           :::::::::::::       ::::::::::")
        print("::::::::::      :::::::::::::::            ::::::::::::::;           :::::::::::::::      ::::::::::")
        print("::::::::::      :::::::::::::::          ::::::::::::::::::           ::::::::::::::      ::::::::::")
        print(";::::::::::          :::::             ::::::::::::::::::::::                            ;:::::::::;")
        print(" ::::::::::          :::::           ::::::::::::::::::::::::::                          :::::::::: ")
        print(" :::::::::::         :::::         ::::::::::::::; ::::::::::::::                       ::::::::::: ")
        print("  :::::::::::;                   :::::::::::::::    :::::::::::::::                   ::::::::::::  ")
        print("   ::::::::::::                ::::::::::::::          ::::::::::::::                ::::::::::::   ")
        print("    :::::::::::::::;       ::::::::::::::::              ::::::::::::::::       ::::::::::::::::    ")
        print("     ::::::::::::::::::::::::::::::::::::;                 ::::::::::::::::::::::::::::::::::::     ")
        print("       ;:::::::::::::::::::::::::::::::                      ::::::::::::::::::::::::::::::::       ")
        print("         ;:::::::::::::::::::::::::::                          ::::::::::::::::::::::::::::         ")
        print("            ;::::::::::::::::::::::                               ::::::::::::::::::::::            ")
        print("                 ::::::::::::;                                        :::::::::::::          ")

        print("\n[3/3] 获取课程列表并自动刷课...")
        driver.get(TARGET_URL)
        time.sleep(3)

        # 再次检测重复登录（页面跳转后可能出现）
        if check_duplicate_login(driver):
            input("\n请处理重复登录后按 Enter 退出...")
            return

        # 获取课程列表
        print("\n--- 获取课程列表 ---")
        all_courses = get_course_list(driver)

        passed = sum(1 for c in all_courses if c["passed"])
        total = len(all_courses)
        print(f"\n课程总数: {total}, 已完成: {passed}, 未完成: {total - passed}")

        # 保存课程列表 JSON（覆盖旧文件）
        save_course_list_json(all_courses, total, passed)

        if passed < total:
            print("\n--- 开始自动刷课 ---")
            failed_courses = auto_complete(driver, all_courses) or []
        else:
            print("\n[OK] 所有课程已完成！")
            failed_courses = []

        # --- 全部完成 → 清屏并输出艺术字 ---
        if os.name == "nt":
            os.system("cls")
        else:
            os.system("clear")
        print("                                              ...                                               ")
        print("                                        .:::::+X$XXX.                                            ")
        print("                                        .:;...;X$$$$.                                            ")
        print("                         ..;;.          .::...;X$$$$..         .x$x:.                            ")
        print("                      .::....::. ...::;;:::...+X$$$$$$Xx+;:.  .x$X$$$X;.                        ")
        print("                   .:::.......:;:::...........+X$$$XXXXX$$$XXxX$XXXX$$$$x:                      ")
        print("                   .;;.........:............+;;;;X$$$$$$XXXXXX$XXX$$$$$$$x                      ")
        print("                    .;;.....:...............+;;;;X$$$$$$$$XXXXXX$$$$$$$&x.                      ")
        print("                    .:;:...:;;;+:...:::;;;;+;;;;;+xxXX$$$$$$$Xx+X$$$$$&X:.                      ")
        print("                  .::.....;;:::;+;;;;;::::::::::::::::::;+xX$+;;;;+$$$$$$x.                     ")
        print("                 :;:......:+::::::::::::::::;;;;;::::::::::::::::;$$$$$$X$$x.                   ")
        print("         ::::...;;:......::;;:::::::;+xxx+++++x$X$$$&$Xx;::::::::X$$$$$$$$$$$;..;XXX:           ")
        print("       .;:....:::......::;;:::::;+x+;:::;+XXXXx;;++xXX$$&$Xx;::::::x$$$$$$$$$&$$$XX$X;          ")
        print("      .;:.............:;::.:.:+x+:::+$$$&$X++xx:.:.::::+xX$$$$x::::::+$$$$$$$$$$$$$$$$;         ")
        print("     .::........:;:..:;....:++;;:::xxxX&$$$+xxx:.........:;x$X$$X::::::X$$X$$$$$$$$$$$$:        ")
        print("     :::.......::..;+:....;x;::+x$$$;++$&$xxxx:............:x$$&$X:::::+X;::x$$$$$$$$$$:       ")
        print("     ..;;;:...::........:+;;X&$xX$X$++x$&$$xxxx:..............;x$$$X;:::::::::x$$$$$$$+:        ")
        print("        .;::..;+;......:+:.;$$xxX$$$xxx$&$$xxxx:...............:x$$$$x.:::::;X$$$$$$;.          ")
        print("        .;.....::+....:+:.:X$$Xx$$$$xxx$$$$xxxx:................:+$$$$X....;$$$$$$X$x.          ")
        print("       .;:......;....:x:..;$$$$xX$$xXx+xXXx++x+:................;;x$XXXx....+$$$$$$$$;          ")
        print("       ::......:;...:+:...xX$$$XxxxXxx+++++++++:........:.......;;+X$$$$+...:X$$$$$X$x.         ")
        print("      .;:.....:;+;;:+;..::$xX&$$XXxxx++x+x+++++:......:::......:+;;X$XXXx:...x$$$$$$$X:         ")
        print("  ....:;;.....:++++;+:...;$xX$&$$XxxXXxx+++XXx+:.....:::.......;+++x$$$&&++xxx$$$$$$$&+.....    ")
        print(" ::..::.:....:;++++;;....+$$XXx+xXXXxXXXXXXxxx+:.....:........:+xx+x$$$$&X;xxxX$$$$$$$$$$XXX.   ")
        print(" ::.......;+++++xx+;;:.;xx&$XXxxxxxxxxxxX$x++++:...::.....::...;xxxX$XXXXX:xxx+xxxx$$$$XXXX$.   ")
        print(" ::......:;+++++x++;;::x+x$xX$XxX$$$$Xx$$$XXXXX+;;++;;+xXX$$$$x;;xxX$$$$$$:xxxxxx++$$$$$XX$$.   ")
        print(".::......:;++++++++;;:+$X+XxXxX$$x$&x$$XxxX$$Xx++xX$$$$$$$&&&&&&x:X$&&&&&$:xxxxx+++$$$XXXX$$.   ")
        print(" ::...:::::;;;+++++;;:xX;;xxXXXx&xX&x$xxXxXxxx+:;x$$$$$$$$&&&&&&X:+$$$$$$X:+++X&&$$$$$$$$$X$.   ")
        print(" .;;;;;;:.:::::+++;;+:$X+:+XXX$$&$$&$&$XXxXXXXx::;X$$$$$$$&&&&&&x;+$XXX$$+;+++$$$$$$$$XXXXx+    ")
        print("      .::::..::;+;;:+;$xX+;XXX$$&$&&$$$XxXxxX$X$$;+X$$$$$$$$$&&&+:+$$$$$X:+++x$$$$$$$$:         ")
        print("       :;:.:...;;;;;:+X+:.:X$$Xx$&&&$$xXXxxx$$&&&X+++X&&&$$$$$$x::;XX$$$+;;;;X$$$$$$$X.         ")
        print("       .+::....:+;;;:;Xx+;;XX$X$$XXXX$XxxxxX$$&&&$++++;;++xx+;::..;$$XXx:;;;+$$$$$$$$+.         ")
        print("        :;:.....:+;;;:;+++;xXX$XXX$$$xxxxxX$$$&&$$X++++++++++;::::+$$$X:;;;;$$$$$$$&X:          ")
        print("        .;;:...:;;:;;;:;;::xxxXXX$&&&$$$XxX$$$$$$$X+x+++xXXXXxx++x$$$X:;;;;;x$$$$$$$;           ")
        print("       .;;::.:;::::::::::+::+XXx+xX$$&$$XxxX$$X+$X;;+x++xx$&&&&&&$X$+:;;;;;;::;&$$$$X;.         ")
        print("     :;:......:+:::;;::::.+;:;;;;;+XX$XXx+++++x;:::::;++xX$$$$$XX$X;:;;;;;;::+$$$$$$X$$X:       ")
        print("     .;::......:++++;+;:::::+;::::;X$$XXx+++++x;::::;:;++X&$X$$$X+::::;x$&$xx$$$$$$$$$$+        ")
        print("     ..;::..:.::::::::;+::::::++::;xXxXxxxxXx+x+::;:+;;;++$$XXX;:::::;$$$$$$$$$$$$$$&$+         ")
        print("       .+;:..:;+;::...::+;:::::::xxXXXX+xx+XxXx:.:;:;:;;+x$X;.:::::;X&$$$$$$$$$$$$$&$+.         ")
        print("        .;;;++;:;;::::::::++::::::..;xXXXXXXXX$$XX$$&$$X+;:::::::+$&$$$$$$$$$x.;xX$$;.          ")
        print("         .::.  ..;;;:::::::;::...:::::::::;;;;;;;;;;;::::::::::::+$$$$$$$$$X;.   .:..           ")
        print("                  .;++;..:;:...:+x+:.:::::::::::::::::::::;x$+::::;$$$$$$$;.                    ")
        print("                  ...+;::::++::++:;;+xx+;::::::::::::+x$&&&$$&x:+$$$XX$$;.                      ")
        print("                    .;:..::::;+;:::::::;;;;++::::x&$$$$$$$$$$$$$$$$$$$$$+.                      ")
        print("                   .::.:::.....:::::::::::::;::::x$$$$$$$$$$$$$$$$$$$$$$$+                      ")
        print("                   .;;;;::::.::+++;;;:::::::+xX$$$$$$$$X$$$$$$$$$$$$$$$$$+.                     ")
        print("                     .:+++;:::;...:;++++++;:::+$$$$$&&$$$$+:. .+$$$&&$X:.                       ")
        print("                        .:;+;:.    .   ..;;:::;X$$$$:..        .x$Xx:.                          ")
        print("                            ..          .:;:::;$$$$$.           ..                              ")
        print("                                        .:;+++x$$$$$.                                           ")
        print("                                          .........                                             ")

        # 输出失败课程列表（含黑名单课程）
        if failed_courses:
            print(f"\n以下 {len(failed_courses)} 个课程失败（含黑名单课程）:")
            for name in failed_courses:
                print(f"  · {name}")
        else:
            print("\n所有课程均已完成！")

        # 截图当前页面
        try:
            driver.save_screenshot(os.path.join(BASE_DIR, "end.png"))
        except Exception:
            pass

        input("\n按 Enter 键退出并关闭浏览器...")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
