import time as t
import os
import json
import sys
from collections import deque
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)


# ========== 常量 ==========

# 程序所在目录（兼容源码和 exe）
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

COOKIE_DIR = os.path.join(BASE_DIR, 'cookies')
DRIVER_PATH = os.path.join(BASE_DIR, 'msedgedriver.exe')
CUR_PHOTO_BASE = os.path.join(BASE_DIR, 'cur_photo')
COURSE_LIST_URL = "https://lms.dgut.edu.cn/ulearning/index.html#/index/courseList"
LOGIN_URL = "https://auth.dgut.edu.cn/authserver/login?service=https://application.dgut.edu.cn/appapi/cas/fromcas"
BASE_URL = "https://lms.dgut.edu.cn/ulearning"

# 当前截图保存目录（由选中的cookie文件名决定，运行时动态设置）
CUR_PHOTO_DIR = None


# ========== 工具函数 ==========

def print_disclaimer():
    """打印免责叠甲声明"""
    j = 1
    for i in ["运行前请检查同路径下是否包含mesdgedriver.exe 这是浏览器驱动 没有的话无法运行", "因为这个项目是基于edge浏览器写的 所以如果你是从谷歌浏览器获取的cookie 可能会有些神秘的bug?", "这个项目的参考是基于dgut2025级信科1班的形策课件写的 包含刷视频和自动答题的功能 所以如果用户的刷课要求包含其他题目 会失败的 如果可以的话请提交以下issues", "最后 输入cookie和网址时请检查一下输入是否正确", "刷课一旦开始就是默认完成所有的任务 所以如果你有什么想要手动的? 可能得手动中断(ctrl+c)"]:
        print(f"叠甲{j}:\n{i}")
        j += 1
        #t.sleep(1)


def print_banner():
    """打印启动Banner"""
    print()
    print("█████╗█████╗█████╗█████╗█████╗█████╗█████╗█████╗█████╗█████╗█████╗")
    print("╚════╝╚════╝╚════╝╚════╝╚════╝╚════╝╚════╝╚════╝╚════╝╚════╝╚════╝")
    print("                                                                  ")
    print("██████╗ ██╗  ██╗██╗███╗   ██╗███████╗    ██╗      █████╗ ██████╗  ")
    print("██╔══██╗██║  ██║██║████╗  ██║██╔════╝    ██║     ██╔══██╗██╔══██╗ ")
    print("██████╔╝███████║██║██╔██╗ ██║█████╗      ██║     ███████║██████╔╝ ")
    print("██╔══██╗██╔══██║██║██║╚██╗██║██╔══╝      ██║     ██╔══██║██╔══██╗ ")
    print("██║  ██║██║  ██║██║██║ ╚████║███████╗    ███████╗██║  ██║██████╔╝ ")
    print("╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝╚══════╝    ╚══════╝╚═╝  ╚═╝╚═════╝  ")
    print("                                                                  ")
    print("█████╗█████╗█████╗█████╗█████╗█████╗█████╗█████╗█████╗█████╗█████╗")
    print("╚════╝╚════╝╚════╝╚════╝╚════╝╚════╝╚════╝╚════╝╚════╝╚════╝╚════╝")


def save_cookies_to_file(driver, filepath):
    """保存当前浏览器cookies到文件，返回cookie列表"""
    cookies = driver.get_cookies()
    print("\n> 收集到以下Cookie:")
    for c in cookies:
        print(f"  - {c['name']}: {c['value'][:50]}{'...' if len(c['value']) > 50 else ''}")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(cookies, f, ensure_ascii=False, indent=2)
    print(f"> 共 {len(cookies)} 个Cookie已保存到 {filepath}")
    return cookies


def load_cookies_from_file(filepath):
    """从文件加载cookies，文件不存在时返回None"""
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def list_cookie_files():
    """列出cookies文件夹下所有json文件，不存在时返回空列表"""
    if not os.path.exists(COOKIE_DIR):
        return []
    files = [f for f in os.listdir(COOKIE_DIR) if f.endswith('.json')]
    return sorted(files)


def is_session_valid(driver):
    """检查当前lms.dgut.edu.cn会话是否有效"""
    try:
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        if 'auth.dgut.edu.cn' in driver.current_url:
            return False
        return True
    except:
        return False


def log_error(error_type, error_msg, context=""):
    """将错误信息追加写入当前用户目录下的 error.txt"""
    log_dir = CUR_PHOTO_DIR or BASE_DIR
    log_path = os.path.join(log_dir, "error.txt")
    timestamp = t.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [{error_type}] {context}: {error_msg}\n"
    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(line)
    except:
        pass


def perform_login(driver, cookie_path):
    """尝试使用已保存的Cookie自动登录，成功返回cookie列表，失败返回None"""
    saved_cookies = load_cookies_from_file(cookie_path)
    if not saved_cookies:
        return None

    print("\n======================")
    print("> 检测到已保存的Cookie，尝试自动登录")

    # 先导航到目标域，使浏览器与域名建立关联
    driver.get(BASE_URL)
    t.sleep(2)

    # 使用标准Selenium API注入cookie，确保domain自动匹配当前页面
    success_count = 0
    for cookie in saved_cookies:
        try:
            driver.add_cookie(cookie)
            success_count += 1
        except:
            pass
    driver.refresh()
    t.sleep(3)
    print(f"> 已注入 {success_count} 个Cookie")

    if is_session_valid(driver):
        print("> 自动登录成功！")
        driver.get(COURSE_LIST_URL)
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'course-item-wrapper'))
            )
            print("> 课程列表加载完成")
        except:
            print("> 警告：课程列表加载超时，尝试继续...")
        return saved_cookies
    else:
        print("> Cookie已过期或登录失败")
        return None


# ========== 浏览器初始化 ==========

def init_driver(headless=True):
    """初始化Edge浏览器，headless=False 时有界面模式用于首次登录"""
    mode = "无头" if headless else "有界面"
    print("\n======================")
    print(f"> 正在以{mode}浏览器模式运行")
    print("> 正在进行初始化")
    try:
        qt = Options()
        qt.add_argument("--no-sandbox")
        qt.add_argument("--disable-gpu")
        if headless:
            qt.add_argument('--headless')
            pass
        qt.add_argument('--disable-blink-features=AutomationControlled')
        qt.add_argument('--window-size=1920,1080')
        qt.add_argument('--lang=zh-CN')
        qt.add_argument('--log-level=3')
        qt.add_argument('--silent')
        qt.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0')
        qt.add_experimental_option("excludeSwitches", ["enable-automation"])
        qt.add_experimental_option("useAutomationExtension", False)
        qt.add_experimental_option(name='detach', value=True)
        driver = webdriver.Edge(service=Service(DRIVER_PATH, log_output=os.devnull, service_args=['--silent']), options=qt)
        actions = ActionChains(driver)
        print(os.getcwd())
        print("> 成功")
        return driver, actions
    except Exception as e:
        print("> 失败")
        print(f"> 发生报错:\n{e}")
        print("> 程序已退出")
        input("\n按 Enter 键退出...")
        sys.exit()


# ========== 认证修复 ==========

def fix_auth_issue(driver, all_cookies):
    """修复新窗口的401/undefined认证问题（不删除cookie，避免污染主窗口）"""
    print("检测到401/undefined问题，开始修复认证...")
    try:
        token_val = next((c['value'] for c in all_cookies if c['name'] == 'token'), '')
        auth_val = next((c['value'] for c in all_cookies if c['name'] == 'AUTHORIZATION'), '')
        driver.execute_script("""
            localStorage.setItem('token', arguments[0]);
            localStorage.setItem('AUTHORIZATION', arguments[1]);
            localStorage.setItem('userInfo', document.cookie.match(/USER_INFO=([^;]+)/)?.[1] || '');
        """, token_val, auth_val)
        driver.execute_script("""
            var failedResources = ['User.js', 'Course.js'];
            failedResources.forEach(function(resource) {
                var scripts = document.querySelectorAll('script[src*="' + resource + '"]');
                scripts.forEach(function(script) {
                    var newScript = document.createElement('script');
                    newScript.src = script.src + '?' + new Date().getTime();
                    document.head.appendChild(newScript);
                });
            });
        """)
        t.sleep(2)
    except Exception as js_error:
        print(f"JavaScript修复失败: {js_error}")
    driver.refresh()
    t.sleep(3)
    print("认证修复完成")


def handle_new_window(driver, all_cookies):
    """
    处理新窗口：检测并修复 undefined/401 问题
    返回 True 表示已处理新窗口，False 表示没有新窗口
    """
    try:
        t.sleep(2)
        all_windows = driver.window_handles
        if len(all_windows) <= 1:
            return False
        new_window = all_windows[-1]
        driver.switch_to.window(new_window)
        t.sleep(2)
        page_source = driver.page_source
        console_errors = []
        try:
            logs = driver.get_log('browser')
            for log in logs:
                if '401' in log['message'] or 'error' in log['message'].lower():
                    console_errors.append(log['message'][:100])
        except:
            pass
        if "undefined" in page_source or console_errors or '401' in str(page_source):
            fix_auth_issue(driver, all_cookies)
            # fix_auth_issue 内部已 refresh，这里不再重复刷新
        else:
            driver.refresh()
            t.sleep(3)
        return True
    except Exception as e:
        print(f"处理新窗口时出错: {e}")
        return False


# ========== 学习流程 - 通用 ==========

def get_learn_tabs(driver):
    """获取学习选项卡列表，返回 (learn_list, is_list)"""
    try:
        learn_list = driver.find_element(By.CLASS_NAME, 'textbook-tab-list').find_elements(By.CLASS_NAME, 'textbook-tab-item')
        print(f"> 共有{len(learn_list)}个学习界面")
        for i in range(len(learn_list)):
            print(f"> {i+1}.{learn_list[i].text}")
        print("-----------------------")
        return learn_list, True
    except:
        return [0], False


def skip_all_tips(driver):
    """跳过所有提示弹窗"""
    # 判断当前页面是否有视频
    is_video_page = False
    try:
        driver.find_element(By.CLASS_NAME, 'video-element')
        is_video_page = True
    except:
        pass

    if is_video_page:
        # 视频页面：先关视频引导弹窗，再关新手引导
        for _ in range(3):
            try:
                modal = driver.find_element(By.CLASS_NAME, 'modal-content')
                btn = modal.find_element(By.CLASS_NAME, 'btn-submit')
                t.sleep(1)
                driver.execute_script("arguments[0].click();", btn)
                t.sleep(1)
            except:
                pass
        for _ in range(3):
            try:
                guide = driver.find_element(By.CLASS_NAME, 'user-guide')
                close_btn = guide.find_element(By.CLASS_NAME, 'close-btn')
                t.sleep(1)
                driver.execute_script("arguments[0].click();", close_btn)
                t.sleep(1)
            except:
                pass
    else:
        # 非视频页面：直接跳过新手引导
        for _ in range(3):
            try:
                guide = driver.find_element(By.CLASS_NAME, 'user-guide')
                close_btn = guide.find_element(By.CLASS_NAME, 'close-btn')
                t.sleep(1)
                driver.execute_script("arguments[0].click();", close_btn)
                t.sleep(1)
            except:
                pass

    # 统一处理 alertModal（学习记录保存提示等）
    try:
        alert_modal = driver.find_element(By.ID, 'alertModal')
        if alert_modal.is_displayed():
            driver.execute_script("arguments[0].style.display='none'; arguments[0].remove();", alert_modal)
            # 移除遮罩层
            backdrop = driver.find_element(By.CLASS_NAME, 'modal-backdrop')
            driver.execute_script("arguments[0].remove();", backdrop)
    except:
        pass


# ========== 学习流程 - 视频处理 ==========

def _parse_seconds(timestamp):
    """将 MM:SS 或 HH:MM:SS 转为总秒数"""
    parts = timestamp.strip().split(':')
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return 0


def _is_video_finished(video_element):
    """检测 video-progress 的 DOM 完成标志"""
    try:
        progress = video_element.find_element(By.CLASS_NAME, 'video-progress')
        cls = progress.get_attribute('class') or ''
        if 'complete' in cls.split():
            return True
        try:
            span = progress.find_element(By.CLASS_NAME, 'text').find_element(By.XPATH, './span')
            if span.text == "已看完":
                return True
        except:
            pass
    except:
        pass
    return False


def play_single_video(driver, actions, video_element):
    """播放单个视频并等待完成"""
    video = video_element.find_element(By.CLASS_NAME, 'mejs__container')
    driver.execute_script("arguments[0].scrollIntoView();", video)
    t.sleep(1)

    # 检查是否已看完
    if _is_video_finished(video_element):
        print(">   该视频已看完")
        return

    t.sleep(1)
    # 获取控制组件（仅用于初始静音和播放）
    video_control = video.find_element(By.CLASS_NAME, 'mejs__controls')
    video_volumn = video_control.find_element(By.CLASS_NAME, 'mejs__volume-button').find_element(By.XPATH, './button')
    video_play_btn = video_control.find_element(By.CLASS_NAME, 'mejs__play').find_element(By.XPATH, './button')

    # 静音并播放
    actions.click(video_volumn).perform()
    actions.click(video_play_btn).perform()
    print(">   已静音")
    print(">   已自动播放")
    t.sleep(5)

    # 输出视频总时长信息
    video_time = video_control.find_element(By.CLASS_NAME, 'mejs__duration-container').find_element(By.XPATH, './span').text
    if not video_time or _parse_seconds(video_time) == 0:
        print(">   无法获取视频时长，等待 60 秒后检查...")
        t.sleep(60)
        try:
            video_control = video.find_element(By.CLASS_NAME, 'mejs__controls')
            video_time = video_control.find_element(By.CLASS_NAME, 'mejs__duration-container').find_element(By.XPATH, './span').text
        except:
            video_time = "0:01"
    total_sec = _parse_seconds(video_time)
    if total_sec == 0:
        total_sec = 60  # 保底值，至少等一分钟
    # 向上取整到整分钟，余数 > 30s 再加 1 分钟
    base = ((total_sec + 59) // 60) * 60
    remain_sec = base + (60 if total_sec % 60 > 30 else 0)
    print(f">   视频时长: {video_time}（整为 {remain_sec // 60} 分钟）")

    _photo_dir = CUR_PHOTO_DIR or BASE_DIR
    os.makedirs(_photo_dir, exist_ok=True)
    _vedio_path = os.path.join(_photo_dir, "cur_vedio.png")

    # 每60秒检测一次视频是否播完
    check_count = 0
    while check_count * 60 < remain_sec:
        t.sleep(60)
        # 优先检测 DOM 完成标志，再检测播放器时间归零
        if _is_video_finished(video_element):
            print("\n>   视频已看完（完成标志）")
            driver.save_screenshot(_vedio_path)
            return
        # 每次循环重新获取控制组件，避免 stale element
        try:
            video_control = video.find_element(By.CLASS_NAME, 'mejs__controls')
        except:
            break
        try:
            cur_text = video_control.find_element(By.CLASS_NAME, 'mejs__currenttime-container').find_element(By.XPATH, './span').text
        except:
            cur_text = ""
        if cur_text == "00:00":
            print("\n>   视频已看完")
            driver.save_screenshot(_vedio_path)
            return
        # 防挂机前先检查是否有挂机提醒弹窗
        try:
            modal = driver.find_element(By.CLASS_NAME, 'modal-content')
            if modal.is_displayed():
                btn = modal.find_element(By.CLASS_NAME, 'btn-submit')
                if btn.is_displayed():
                    driver.execute_script("arguments[0].click();", btn)
                    print("\n>   检测到挂机提醒，已点击继续学习")
                    t.sleep(2)
        except:
            pass

        # 防挂机：暂停 → 截图 → 恢复
        try:
            video_play_btn = video_control.find_element(By.CLASS_NAME, 'mejs__play').find_element(By.XPATH, './button')
            actions.click(video_play_btn).perform()
            t.sleep(1)
            driver.save_screenshot(_vedio_path)
            actions.click(video_play_btn).perform()
        except:
            pass
        check_count += 1
        print(f"\r>   防挂机检测X{check_count}", end="", flush=True)
    t.sleep(1)


def handle_video_content(driver, actions):
    """检测并处理视频类型内容，返回 True 如果成功处理"""
    try:
        driver.find_element(By.CLASS_NAME, 'video-element')
    except NoSuchElementException:
        return False

    video_elements = driver.find_elements(By.CLASS_NAME, 'video-element')
    print("> 当前部分 : 视频")
    print(f"> 数量: {len(video_elements)}")
    for video_count, video_element in enumerate(video_elements, 1):
        print(f">   视频{video_count}")
        play_single_video(driver, actions, video_element)
    return True


# ========== 学习流程 - 答题处理 ==========

def handle_question_content(driver, actions):
    """检测并处理题目类型内容，返回 True 如果成功处理"""
    try:
        driver.find_element(By.CLASS_NAME, 'question-view')
        print(">    当前部分 : 小测")

        question_view = driver.find_element(By.CLASS_NAME, 'question-view')
        submit_btn = driver.find_element(By.CLASS_NAME, 'question-operation-area').find_element(By.CLASS_NAME, 'btn-submit')

        # 检测所属栏目
        section_name = None
        try:
            active_page = driver.find_element(By.CSS_SELECTOR, '.page-name.active')
            section_item = active_page.find_element(By.XPATH, './ancestor::div[contains(@class, "section-item")]')
            section_name = section_item.find_element(By.CSS_SELECTOR, '.section-name .text').get_attribute('textContent').strip()
        except:
            pass
        if section_name:
            print(f">   当前栏目: {section_name}")
            # 章节测试栏目直接提交跳过答题
            if '章节测试' in section_name:
                print(">   章节测试，直接提交")
                driver.execute_script("arguments[0].scrollIntoView();", submit_btn)
                t.sleep(1)
                driver.execute_script("arguments[0].click();", submit_btn)
                t.sleep(3)
                return True

        qustion_list = question_view.find_element(By.CLASS_NAME, 'question-element-node-list').find_elements(By.CLASS_NAME, 'question-element-node')

        for question in qustion_list:
            driver.execute_script("arguments[0].scrollIntoView();", question)
            question_wrapper = question.find_element(By.CLASS_NAME, 'question-body-wrapper')

            # 检测是否为简答题
            try:
                question_wrapper.find_element(By.CLASS_NAME, 'short-answer-type')
                print(">    识别到简答题")
                textarea = question.find_element(By.CLASS_NAME, 'short-answer-type').find_element(By.TAG_NAME, 'textarea')
                driver.execute_script("arguments[0].scrollIntoView();", textarea)
                t.sleep(1)
                textarea.click()
                textarea.send_keys("ROMIN")
                t.sleep(0.5)
                q_submit = question.find_element(By.CLASS_NAME, 'question-operation-wrapper').find_element(By.CLASS_NAME, 'btn-submit')
                driver.execute_script("arguments[0].click();", q_submit)
                t.sleep(1)
                continue
            except:
                pass

            # 选择题处理
            try:
                answer_choice = question_wrapper.find_elements(By.CLASS_NAME, 'choice-item')[0]
            except:
                answer_choice = question_wrapper.find_elements(By.CLASS_NAME, 'choice-btn')[0]
            actions.click(answer_choice).perform()
            t.sleep(0.5)

        print(">    题目已全完成")
        driver.execute_script("arguments[0].scrollIntoView();", submit_btn)
        t.sleep(1)
        actions.click(submit_btn).perform()
        t.sleep(3)
        return True
    except:
        return False


# ========== 学习流程 - 页面项处理 ==========

def _reclick_page_item(driver, title_text):
    """刷新后在 DOM 中根据标题重新找到并点击 page-item，返回 (page_item, page_name) 或 (None, None)"""
    try:
        all_items = driver.find_elements(By.CLASS_NAME, 'page-item')
        for pi in all_items:
            try:
                pn = pi.find_element(By.CLASS_NAME, 'page-name')
                pt = pn.find_element(By.CLASS_NAME, 'text').find_element(By.XPATH, './span')
                if pt.get_attribute('textContent').strip() == title_text:
                    return pi, pn
            except:
                continue
    except:
        pass
    return None, None


def process_page_item(driver, actions, page_item):
    """处理单个页面项（视频或题目），带10次刷新重试和错误日志"""
    _photo_dir = CUR_PHOTO_DIR or BASE_DIR
    os.makedirs(_photo_dir, exist_ok=True)
    try:
        page_name = page_item.find_element(By.CLASS_NAME, 'page-name')
        title_el = page_name.find_element(By.CLASS_NAME, 'text').find_element(By.XPATH, './span')
        title_text = title_el.get_attribute('textContent').strip()
    except Exception as e:
        log_error(type(e).__name__, str(e)[:200], "process_page_item 初始化")
        print(">   无法读取页面项信息，已跳过")
        return

    os.system('cls')
    print_banner()
    print("\n-----------------------")
    print(f"> 当前项目:{title_text}")

    try:
        class_attr = page_name.get_attribute('class')
        if 'complete' in class_attr.split():
            print(">   状态: 已完成")
            print("-----------------------")
            return
    except StaleElementReferenceException:
        log_error("StaleElementReferenceException", "page_name 在完成检测时已失效", title_text)
        print(">   页面项引用失效，已跳过")
        return

    for attempt in range(10):
        if attempt > 0:
            print(f"> 刷新重试 ({attempt + 1}/10)...")
            driver.refresh()
            t.sleep(3)
            skip_all_tips(driver)
            page_item, page_name = _reclick_page_item(driver, title_text)
            if page_item is None:
                print(f">   刷新后未找到项目「{title_text}」，继续重试...")
                continue

        try:
            driver.execute_script("arguments[0].scrollIntoView();", page_name)
            for _ in range(3):
                try:
                    actions.click(page_name).perform()
                    break
                except ElementNotInteractableException:
                    driver.execute_script("arguments[0].click();", page_name)
                    break
                except ElementClickInterceptedException:
                    skip_all_tips(driver)
                    t.sleep(1)
            t.sleep(2)
            for _ in range(3):
                try:
                    actions.click(page_name).perform()
                    break
                except ElementNotInteractableException:
                    driver.execute_script("arguments[0].click();", page_name)
                    break
                except ElementClickInterceptedException:
                    skip_all_tips(driver)
                    t.sleep(1)
            driver.save_screenshot(os.path.join(_photo_dir, "cur_start.png"))
            t.sleep(2)

            skip_all_tips(driver)

            if not handle_video_content(driver, actions):
                handle_question_content(driver, actions)

            driver.save_screenshot(os.path.join(_photo_dir, "cur_end.png"))
            print("-----------------------")
            t.sleep(1)
            return

        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)[:200]
            if attempt < 9:
                print(f">   捕获异常 [{error_type}]，准备刷新重试...")
            else:
                log_error(error_type, error_msg, title_text)
                print(f">   10次重试后仍失败 [{error_type}]，已跳过此项目")
                print(f">   详情已写入 error.txt")
                print("-----------------------")


def process_section_pages(driver, actions, section_items):
    """遍历一个section下的所有page items"""
    for idx, section_item in enumerate(section_items):
        try:
            page_items = section_item.find_element(By.CLASS_NAME, 'page-list').find_elements(By.CLASS_NAME, 'page-item')
        except (StaleElementReferenceException, NoSuchElementException):
            print(f"> section-item {idx} 失效，跳过")
            continue
        t.sleep(1)
        for page_item in page_items:
            process_page_item(driver, actions, page_item)


# ========== 学习流程 - 专题/章节处理 ==========

def process_chapter_by_name(driver, actions, chapter_name):
    """在子窗口侧边栏中按名称匹配单个 chapter-item，只遍历该专题的 page 列表"""
    # 在 catalog-list 中按名称匹配
    chapters = driver.find_element(By.CLASS_NAME, 'catalog-list').find_elements(By.CLASS_NAME, 'chapter-item')
    target = None
    for ch in chapters:
        try:
            text = ch.find_element(By.CLASS_NAME, 'text').text.strip()
            # 双向包含匹配
            if chapter_name in text or text in chapter_name:
                target = ch
                break
        except:
            pass

    if target is None:
        print(f"> 未在侧边栏找到匹配专题: {chapter_name}")
        return

    chapter_text = target.find_element(By.CLASS_NAME, 'text').text.strip()
    print(f"> 匹配专题:{chapter_text}")

    # 展开专题
    for _ in range(5):
        try:
            name_el = target.find_element(By.CLASS_NAME, 'chapter-name')
            WebDriverWait(driver, 5).until(
                lambda _: name_el.is_displayed() and name_el.is_enabled()
            )
            name_el.click()
            break
        except (ElementClickInterceptedException, ElementNotInteractableException,
                StaleElementReferenceException, TimeoutException):
            skip_all_tips(driver)
            t.sleep(1)
    t.sleep(1)

    # 重新获取 DOM 后收集该专题下所有 section → page-item
    try:
        chapters = driver.find_element(By.CLASS_NAME, 'catalog-list').find_elements(By.CLASS_NAME, 'chapter-item')
        for ch in chapters:
            try:
                if ch.find_element(By.CLASS_NAME, 'text').text.strip() == chapter_text:
                    target = ch
                    break
            except:
                pass
    except NoSuchElementException:
        print("> catalog-list 丢失")
        return

    # 初始化：一次性收集未完成页面的名称（存字符串，不存 DOM 引用）
    page_name_list = []  # [(section_name, page_name_text)]
    total = 0
    try:
        sections = target.find_element(By.CLASS_NAME, 'section-list').find_elements(By.CLASS_NAME, 'section-item')
        for si in sections:
            try:
                sec_name = si.find_element(By.CSS_SELECTOR, '.section-name .text').get_attribute('textContent').strip()
            except:
                sec_name = "未知栏目"
            try:
                pages = si.find_element(By.CLASS_NAME, 'page-list').find_elements(By.CLASS_NAME, 'page-item')
                for pi in pages:
                    total += 1
                    try:
                        pn = pi.find_element(By.CLASS_NAME, 'page-name')
                        cls = pn.get_attribute('class') or ''
                        if 'complete' not in cls.split():
                            pname = pn.find_element(By.CLASS_NAME, 'text').find_element(By.XPATH, './span').get_attribute('textContent').strip()
                            page_name_list.append((sec_name, pname))
                    except:
                        pass
            except:
                pass
    except:
        pass

    if not page_name_list:
        print("> 该专题无未完成页面")
        return

    done = total - len(page_name_list)
    print(f"> 共 {total} 个页面 ({done} 已完成, {len(page_name_list)} 待处理)")
    print("-----------------------")
    t.sleep(1)

    # 遍历：每次从侧边栏按名称实时查找最新 DOM 引用
    for sec_name, pname in page_name_list:
        print(f"> [{sec_name}] {pname}")

        # 从侧边栏按名称查找 page-item
        page_item = None
        pn_el = None
        all_items = driver.find_elements(By.CLASS_NAME, 'page-item')
        for pi in all_items:
            try:
                pn = pi.find_element(By.CLASS_NAME, 'page-name')
                span = pn.find_element(By.CLASS_NAME, 'text').find_element(By.XPATH, './span')
                if span.get_attribute('textContent').strip() == pname:
                    page_item = pi
                    pn_el = pn
                    break
            except:
                pass

        if page_item is None:
            print(f">   未找到，跳过")
            continue

        cls = pn_el.get_attribute('class') or ''
        if 'active' not in cls.split():
            driver.execute_script("arguments[0].scrollIntoView();", pn_el)
            driver.execute_script("arguments[0].click();", pn_el)
            t.sleep(2)
            skip_all_tips(driver)
        else:
            print(">   已是当前节点，跳过点击")

        process_page_item(driver, actions, page_item)

    print(f"> {chapter_text} 处理完毕")


# ========== 学习流程 - 学习选项卡处理 ==========

def click_back_save(driver):
    """所有专题完成后，点击返回课程章节按钮保存进度，循环3次"""
    for i in range(3):
        try:
            back_btn = driver.find_element(By.CLASS_NAME, 'back-btn')
            driver.execute_script("arguments[0].click();", back_btn)
            print(f"> 点击返回保存({i+1}/3)")
        except:
            print(f"> 返回按钮未找到({i+1}/3)")
        t.sleep(5)


def print_chapter_list(driver):
    """打印当前学习界面的章节列表"""
    chapter_rows = driver.find_elements(By.XPATH, '//tr[starts-with(@id, "chapterTr")]')
    if not chapter_rows:
        print("> 未检测到章节列表")
        return chapter_rows

    print("> 课件章节列表：\n")
    for row in chapter_rows:
        try:
            name = row.find_element(By.CLASS_NAME, 'tabchapter-name').text
        except:
            name = "未知章节"
        try:
            progress = row.find_element(By.XPATH, './/td[2]/span').text
        except:
            progress = "--"
        try:
            time = row.find_element(By.XPATH, './/td[3]').text
        except:
            time = "--"
        try:
            score = row.find_element(By.XPATH, './/td[4]').text
        except:
            score = "--"
        try:
            btn_text = row.find_element(By.CLASS_NAME, 'button-red-hollow').text
        except:
            btn_text = "--"
        print(f"  {name}")
        print(f"    进度: {progress}  学时: {time}  得分: {score}  [{btn_text}]")
    print(f"\n> 共 {len(chapter_rows)} 个章节")
    return chapter_rows


def _scan_incomplete_chapters(driver):
    """扫描当前课件页，返回未完成章节索引列表"""
    incomplete = []
    chapter_rows = driver.find_elements(By.XPATH, '//tr[starts-with(@id, "chapterTr")]')
    for idx, row in enumerate(chapter_rows):
        try:
            progress = int(row.find_element(By.XPATH, './/td[2]/span').text.strip('%'))
            if progress != 100:
                incomplete.append(idx)
        except:
            pass
    return incomplete, chapter_rows


def process_tab_with_queue(driver, actions, tab_text, is_list, all_cookies, textbook_url):
    """队列式处理单个学习选项卡，最多3轮验证"""
    handle = driver.current_window_handle
    print("\n-----------------------")
    print(f"> 当前目标:{tab_text}")

    # 检查隐藏
    try:
        hide_page = driver.find_element(By.CLASS_NAME, 'hide-page')
        if hide_page.is_displayed():
            print("> 该课件已被教师隐藏，跳过")
            return
    except NoSuchElementException:
        pass

    # 等待章节列表
    for attempt in range(3):
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//tr[starts-with(@id, "chapterTr")]'))
            )
            break
        except:
            if attempt < 2:
                print(f"> 章节列表未加载，正在刷新重试({attempt+1}/2)...")
                driver.refresh()
                t.sleep(3)
    print_chapter_list(driver)
    print("-----------------------")

    MAX_ROUNDS = 3
    for round_num in range(MAX_ROUNDS):
        # 扫描未完成章节并入队
        incomplete, chapter_rows = _scan_incomplete_chapters(driver)
        if not incomplete:
            print(f"> 第{round_num+1}轮: 全部完成")
            break

        queue = deque(incomplete)
        print(f"> 第{round_num+1}轮: 待刷 {len(queue)} 个章节")

        while queue:
            idx = queue.popleft()

            # 重新获取最新DOM
            chapter_rows = driver.find_elements(By.XPATH, '//tr[starts-with(@id, "chapterTr")]')
            if idx >= len(chapter_rows):
                continue

            # 二次确认是否已完成
            try:
                progress = int(chapter_rows[idx].find_element(By.XPATH, './/td[2]/span').text.strip('%'))
                if progress == 100:
                    chapter_name = chapter_rows[idx].find_element(By.CLASS_NAME, 'tabchapter-name').text
                    print(f"> {chapter_name} 已完成，跳过")
                    continue
            except:
                pass

            try:
                chapter_name = chapter_rows[idx].find_element(By.CLASS_NAME, 'tabchapter-name').text
            except:
                chapter_name = f"章节{idx+1}"
            print(f"> 正在处理: {chapter_name}")

            learn_btn = chapter_rows[idx].find_elements(By.CLASS_NAME, 'button-red-hollow')
            if not learn_btn:
                print(f"> 未找到开始学习按钮，重新入队")
                queue.append(idx)
                continue

            # 点击开始学习
            for _ in range(3):
                try:
                    actions.click(learn_btn[0]).perform()
                    break
                except ElementClickInterceptedException:
                    skip_all_tips(driver)
                    t.sleep(1)
                except ElementNotInteractableException:
                    driver.execute_script("arguments[0].click();", learn_btn[0])
                    break

            # 处理新窗口
            has_new = handle_new_window(driver, all_cookies)
            if not has_new:
                print(f"> 未检测到新窗口，重新入队")
                queue.append(idx)
                continue

            skip_all_tips(driver)

            # 获取专题列表并处理
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'catalog-list'))
                )
                process_chapter_by_name(driver, actions, chapter_name)
            except Exception as e:
                print(f"> 处理失败 [{type(e).__name__}]，重新入队")
                queue.append(idx)

            # 返回保存
            click_back_save(driver)
            t.sleep(10)
            try:
                driver.close()
            except:
                pass
            t.sleep(1)
            try:
                driver.switch_to.window(handle)
            except:
                pass

        # 队列空 → 回课件页验证
        if round_num < MAX_ROUNDS - 1:
            print(f"> 第{round_num+1}轮队列已空，回课件页验证...")
            loaded = False
            for retry in range(3):
                driver.get(textbook_url)
                t.sleep(2)
                driver.refresh()
                try:
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.XPATH, '//tr[starts-with(@id, "chapterTr")]'))
                    )
                    loaded = True
                    break
                except:
                    print(f">   课件页加载超时，重试({retry+1}/3)...")
            if not loaded:
                print(">   课件页多次加载失败，信任已完成结果")
                break
            t.sleep(2)
            # 重新点击学习标签
            if is_list:
                learn_pages, _ = get_learn_tabs(driver)
                for lp in learn_pages:
                    try:
                        if lp.text.strip() == tab_text.strip():
                            actions.click(lp).perform()
                            t.sleep(2)
                            break
                    except:
                        pass

    print("> 当前界面处理完毕")
    print("-----------------------")


# ========== 课程选择 ==========

def select_course(driver):
    """遍历所有分页收集完整课程列表，输出课程名，等待用户选择"""
    courses = []       # [(title, course_id), ...]
    seen_ids = set()

    # 先等待第一页加载
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'course-item-wrapper'))
        )
    except:
        print("> 课程列表加载超时，请检查页面是否加载完整")
        return

    while True:
        t.sleep(1)

        # 收集当前页的课程
        wrappers = driver.find_elements(By.CLASS_NAME, 'course-item-wrapper')
        for w in wrappers:
            try:
                course_item = w.find_element(By.CLASS_NAME, 'course-item')
                cid = course_item.get_attribute('id')          # e.g. "courseCard155382"
                if cid and cid not in seen_ids:
                    seen_ids.add(cid)
                    title = w.find_element(By.CLASS_NAME, 'title').text
                    courses.append((title, cid.replace('courseCard', '')))
            except:
                pass

        # 尝试翻到下一页
        try:
            pagination = driver.find_element(By.ID, 'courseListPagination')
            active_before = pagination.find_element(By.CLASS_NAME, 'active').text
            next_btn = pagination.find_element(By.CLASS_NAME, 'next')
            next_btn.click()
            # 等待页面切换完成：active 页码变化
            WebDriverWait(driver, 5).until(
                lambda _: pagination.find_element(By.CLASS_NAME, 'active').text != active_before
            )
        except:
            break   # 没有下一页了

    if not courses:
        print("> 未找到课程列表，请检查页面是否加载完整")
        return []

    os.system('cls')
    print_banner()

    print("\n======================")
    print(f"> 检测到以下课程（共 {len(courses)} 门）：")
    for idx, (title, _) in enumerate(courses, 1):
        print(f"  {idx}. {title}")
    print("-----------------------")
    print("> 输入课程编号（空格分隔），如: 1 2 3")
    print("> 将按输入顺序依次刷课")

    try:
        raw = input("\n请输入课程编号: ").strip()
        choices = [int(x) for x in raw.split()]
        selected = []
        for c in choices:
            if c < 1 or c > len(courses):
                print(f"> 编号 {c} 超出范围，已跳过")
                continue
            selected.append(courses[c - 1])
        if not selected:
            print("> 无有效课程编号，程序退出")
            input("\n按 Enter 键退出...")
            sys.exit()
    except ValueError:
        print("> 输入无效，程序退出")
        input("\n按 Enter 键退出...")
        sys.exit()

    print(f"> 已选择 {len(selected)} 门课程：")
    for title, cid in selected:
        print(f"    {title} : {cid}")
    return selected


# ========== 主函数 ==========

def main():
    print_disclaimer()
    print_banner()

    # 检查驱动是否存在
    if not os.path.exists(DRIVER_PATH):
        print("\n======================")
        print("> 未检测到浏览器驱动")
        print("> 请先运行 update_driver.exe 下载匹配的 Edge Driver")
        print("> 然后将 msedgedriver.exe 放在程序同目录下")
        print("======================\n")
        input("按 Enter 键退出...")
        sys.exit()

    # ===== Cookie 选择 / 登录流程 =====
    cookie_files = list_cookie_files()

    if cookie_files:
        print("\n======================")
        print("> 检测到以下已保存的Cookie：")
        for idx, fname in enumerate(cookie_files, 1):
            name = fname.replace('.json', '')
            print(f"  {idx}. {name}")
        print("  0. 添加新的Cookie（重新登录）")
        print("======================")

        try:
            choice = int(input("\n请选择要使用的Cookie（输入数字后按 Enter）: "))
        except ValueError:
            print("> 输入无效，程序退出")
            input("\n按 Enter 键退出...")
            sys.exit()

        if choice == 0:
            all_cookies = None
        elif 1 <= choice <= len(cookie_files):
            cookie_name = cookie_files[choice - 1].replace('.json', '')
            selected_path = os.path.join(COOKIE_DIR, cookie_files[choice - 1])
            driver, actions = init_driver(headless=True)
            all_cookies = perform_login(driver, selected_path)
            if all_cookies is None:
                driver.quit()
                print("\n======================")
                print("> Cookie已过期或登录失败")
                print("> 请重新启动程序并选择其他Cookie或重新登录")
                print("======================")
                input("按 Enter 键退出...")
                sys.exit()
            # 设置截图保存目录
            global CUR_PHOTO_DIR
            CUR_PHOTO_DIR = os.path.join(CUR_PHOTO_BASE, cookie_name)
            os.makedirs(CUR_PHOTO_DIR, exist_ok=True)
            print(f"> 截图将保存到: {CUR_PHOTO_DIR}")
            os.system(f'title {cookie_name}')
        else:
            print("> 编号超出范围，程序退出")
            input("\n按 Enter 键退出...")
            sys.exit()
    else:
        all_cookies = None

    if all_cookies is None:
        # 首次使用 / 添加新Cookie：有界面模式登录获取Cookie
        print("\n======================")
        print("> 请在弹出的浏览器窗口中完成登录")
        print("======================")
        driver, actions = init_driver(headless=False)
        driver.get(LOGIN_URL)
        t.sleep(2)
        input("\n登录完成后请按 Enter 键继续...")
        driver.get(COURSE_LIST_URL)
        t.sleep(3)

        # 保存Cookie到cookies文件夹（从cookie中提取标识作为文件名）
        os.makedirs(COOKIE_DIR, exist_ok=True)
        cookies_data = driver.get_cookies()
        # 从USERINFO中提取 userId_name_userNo 作为文件名
        cookie_name = ""
        for c in cookies_data:
            if c['name'] == 'USERINFO':
                try:
                    import urllib.parse
                    decoded = urllib.parse.unquote(c['value'])
                    info = json.loads(decoded)
                    user_id = info.get('userId', '')
                    name = info.get('name', '')
                    user_no = info.get('userNo', '')
                    cookie_name = f"{user_id}_{name}_{user_no}"
                except:
                    pass
                break
        if not cookie_name:
            cookie_name = f"cookie_{t.strftime('%Y%m%d_%H%M%S')}"
        cookie_path = os.path.join(COOKIE_DIR, f"{cookie_name}.json")
        with open(cookie_path, 'w', encoding='utf-8') as f:
            json.dump(cookies_data, f, ensure_ascii=False, indent=2)
        print(f"> 共 {len(cookies_data)} 个Cookie已保存到 {cookie_path}")
        driver.quit()

        if cookie_files:
            print("\n======================")
            print("> 新Cookie已保存，请重新启动程序使用")
            print("======================")
        else:
            print("\n======================")
            print("> 首次登录完成，请重新启动程序开始自动刷课")
            print("======================")
        input("按 Enter 键退出...")
        sys.exit()

    # ===== 登录成功，开始刷课 =====
    selected_courses = select_course(driver)
    if not selected_courses:
        print("> 未选择任何课程，程序退出")
        input("\n按 Enter 键退出...")
        driver.quit()
        sys.exit()

    for course_idx, (title, course_id) in enumerate(selected_courses, 1):
        print(f"\n{'='*30}")
        print(f"> 第 {course_idx}/{len(selected_courses)} 门: {title}")
        print(f"{'='*30}")

        textbook_url = f"https://lms.dgut.edu.cn/courseweb/ulearning/index.html#/course/textbook?courseId={course_id}"
        print(f"> 跳转到: courseId={course_id}")
        driver.get(textbook_url)
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, '//tr[starts-with(@id, "chapterTr")]'))
            )
            print("> 课件页加载完成")
        except:
            print("> 课件页加载超时，尝试继续...")

        # 收集所有学习界面标签名称
        learn_list, is_list = get_learn_tabs(driver)
        tab_names = []
        if is_list:
            for lp in learn_list:
                try:
                    tab_names.append(lp.text.strip())
                except:
                    pass
        else:
            tab_names = [""]  # 无标签时用空字符串

        t.sleep(5)

        # 进入主流程
        print("\n======================")
        print("> 开始自动刷课\n")

        for tab_idx, tab_text in enumerate(tab_names):
            # 重新获取标签并点击
            if is_list:
                learn_pages, _ = get_learn_tabs(driver)
                if tab_idx >= len(learn_pages):
                    break
                try:
                    actions.click(learn_pages[tab_idx]).perform()
                    t.sleep(2)
                except:
                    driver.execute_script("arguments[0].click();", learn_pages[tab_idx])
                    t.sleep(2)

            process_tab_with_queue(driver, actions, tab_text, is_list,
                                   all_cookies, textbook_url)

        print(f"\n> 课程「{title}」已完成")

        # 下一门课直接从 URL 跳入，无需回课程列表


    print("\n======================")
    print("<所有课程已处理完毕>")
    driver.quit()
    sys.exit()


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        pass
    except:
        import traceback
        traceback.print_exc()
        print("\n> 出现未预期的错误，窗口即将关闭")
        input("\n按 Enter 键退出...")
