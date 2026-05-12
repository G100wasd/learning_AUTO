import time as t
import os
import json
import sys
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import ElementClickInterceptedException, ElementNotInteractableException


# ========== 常量 ==========

# 程序所在目录（兼容源码和 exe）
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

COOKIE_FILE = os.path.join(BASE_DIR, 'cookies.json')
DRIVER_PATH = os.path.join(BASE_DIR, 'msedgedriver.exe')
COURSE_LIST_URL = "https://lms.dgut.edu.cn/ulearning/index.html#/index/courseList"
LOGIN_URL = "https://auth.dgut.edu.cn/authserver/login?service=https://application.dgut.edu.cn/appapi/cas/fromcas"
BASE_URL = "https://lms.dgut.edu.cn/ulearning"


# ========== 工具函数 ==========

def print_disclaimer():
    """打印免责叠甲声明"""
    j = 1
    for i in ["运行前请检查同路径下是否包含mesdgedriver.exe 这是浏览器驱动 没有的话无法运行", "因为这个项目是基于edge浏览器写的 所以如果你是从谷歌浏览器获取的cookie 可能会有些神秘的bug?", "这个项目的参考是基于dgut2025级信科1班的形策课件写的 包含刷视频和自动答题的功能 所以如果用户的刷课要求包含其他题目 会失败的 如果可以的话请提交以下issues", "最后 输入cookie和网址时请检查一下输入是否正确", "刷课一旦开始就是默认完成所有的任务 所以如果你有什么想要手动的? 可能得手动中断(ctrl+c)"]:
        print(f"叠甲{j}:\n{i}")
        j += 1


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


def save_cookies_to_file(driver, filepath=COOKIE_FILE):
    """保存当前浏览器cookies到文件，返回cookie列表"""
    cookies = driver.get_cookies()
    print("\n> 收集到以下Cookie:")
    for c in cookies:
        print(f"  - {c['name']}: {c['value'][:50]}{'...' if len(c['value']) > 50 else ''}")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(cookies, f, ensure_ascii=False, indent=2)
    print(f"> 共 {len(cookies)} 个Cookie已保存到 {filepath}")
    return cookies


def load_cookies_from_file(filepath=COOKIE_FILE):
    """从文件加载cookies，文件不存在时返回None"""
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def is_session_valid(driver):
    """检查当前lms.dgut.edu.cn会话是否有效"""
    try:
        t.sleep(2)
        if 'auth.dgut.edu.cn' in driver.current_url:
            return False
        return True
    except:
        return False


def perform_login(driver):
    """尝试使用已保存的Cookie自动登录，成功返回cookie列表，失败返回None"""
    saved_cookies = load_cookies_from_file()
    if not saved_cookies:
        return None

    print("\n======================")
    print("> 检测到已保存的Cookie，尝试自动登录")
    driver.get(BASE_URL)
    t.sleep(2)

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
        t.sleep(3)
        return saved_cookies
    else:
        print("> Cookie已过期")
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
        qt.add_argument('--disable-blink-features=AutomationControlled')
        qt.add_argument('--window-size=1920,1080')
        qt.add_argument('--lang=zh-CN')
        qt.add_argument('--log-level=3')
        qt.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0')
        qt.add_experimental_option("excludeSwitches", ["enable-automation"])
        qt.add_experimental_option("useAutomationExtension", False)
        qt.add_experimental_option(name='detach', value=True)
        driver = webdriver.Edge(service=Service(DRIVER_PATH, log_output=os.devnull), options=qt)
        actions = ActionChains(driver)
        print(os.getcwd())
        print("> 成功")
        return driver, actions
    except Exception as e:
        print("> 失败")
        print(f"> 发生报错:\n{e}")
        print("> 程序已退出")
        sys.exit()


# ========== 认证修复 ==========

def fix_auth_issue(driver, all_cookies):
    """修复新窗口的401/undefined认证问题"""
    print("检测到401/undefined问题，开始修复认证...")
    current_url = driver.current_url
    if '//' in current_url:
        domain = current_url.split('//')[1].split('/')[0]
    else:
        domain = 'lms.dgut.edu.cn'
    driver.delete_all_cookies()
    new_window_cookies = []
    for cookie in all_cookies:
        cookie_copy = cookie.copy()
        cookie_copy['domain'] = domain
        new_window_cookies.append(cookie_copy)
    for cookie in new_window_cookies:
        try:
            driver.add_cookie(cookie)
        except:
            pass
    try:
        driver.execute_script("""
            localStorage.setItem('token', 'D9C8E6D3D66FDEE7239B26544E5A74F6');
            localStorage.setItem('AUTHORIZATION', 'D9C8E6D3D66FDEE7239B26544E5A74F6');
            localStorage.setItem('userInfo', document.cookie.match(/USER_INFO=([^;]+)/)?.[1] || '');
        """)
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


def play_single_video(driver, actions, video_element):
    """播放单个视频并等待完成"""
    video = video_element.find_element(By.CLASS_NAME, 'mejs__container')
    driver.execute_script("arguments[0].scrollIntoView();", video)
    t.sleep(1)

    # 检查是否已看完
    video_check = video_element.find_element(By.CLASS_NAME, 'video-progress').find_element(By.CLASS_NAME, 'text').find_element(By.XPATH, './span')
    if video_check.text == "已看完":
        print(">   该视频已看完")
        return

    t.sleep(1)
    # 获取控制组件
    video_control = video.find_element(By.CLASS_NAME, 'mejs__controls')
    video_play_btn = video_control.find_element(By.CLASS_NAME, 'mejs__play').find_element(By.XPATH, './button')
    video_volumn = video_control.find_element(By.CLASS_NAME, 'mejs__volume-button').find_element(By.XPATH, './button')

    # 静音并播放
    actions.click(video_volumn).perform()
    actions.click(video_play_btn).perform()
    print(">   已静音")
    print(">   已自动播放")
    t.sleep(5)

    # 计算还需等待的秒数 = 总时长 - 已播放 + 30
    video_current_time = video_control.find_element(By.CLASS_NAME, 'mejs__currenttime-container').find_element(By.XPATH, './span').text
    video_time = video_control.find_element(By.CLASS_NAME, 'mejs__duration-container').find_element(By.XPATH, './span').text
    total_sec = _parse_seconds(video_time)
    current_sec = _parse_seconds(video_current_time)
    remain_sec = total_sec - current_sec + 30
    if remain_sec < 0:
        remain_sec = 0
    print(f">   视频时长: {video_time}")
    print(f">   已播放: {video_current_time}")
    print(f">   还需等待: {remain_sec}秒")
    t.sleep(1)

    # 每60秒暂停一次以防挂机检测
    loops = (remain_sec + 59) // 60  # 向上取整
    for i in range(loops):
        t.sleep(60 if i < loops - 1 else (remain_sec % 60 or 60))
        actions.click(video_play_btn).perform()
        print(f"\r>   防挂机检测X{i + 1}", end="", flush=True)
        driver.save_screenshot(os.path.join(BASE_DIR, "cur_vedio.png"))
        t.sleep(1)
        actions.click(video_play_btn).perform()
    t.sleep(1)


def handle_video_content(driver, actions):
    """检测并处理视频类型内容，返回 True 如果成功处理"""
    try:
        driver.find_element(By.CLASS_NAME, 'video-element')
        video_elements = driver.find_elements(By.CLASS_NAME, 'video-element')
        print("> 当前部分 : 视频")
        print(f"> 数量: {len(video_elements)}")
        for video_count, video_element in enumerate(video_elements, 1):
            print(f">   视频{video_count}")
            play_single_video(driver, actions, video_element)
        return True
    except:
        return False


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

def process_page_item(driver, actions, page_item):
    """处理单个页面项（视频或题目）"""
    page_name = page_item.find_element(By.CLASS_NAME, 'page-name')
    title_el = page_name.find_element(By.CLASS_NAME, 'text').find_element(By.XPATH, './span')
    title_text = title_el.get_attribute('textContent').strip()
    os.system('cls')
    print_banner()
    print("\n-----------------------")
    print(f"> 当前项目:{title_text}")

    # 检查是否已完成
    class_attr = page_name.get_attribute('class')
    if 'complete' in class_attr.split():
        print(">   状态: 已完成")
        print("-----------------------")
        return

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
    driver.save_screenshot(os.path.join(BASE_DIR, "cur_start.png"))
    t.sleep(2)

    # 跳过可能出现的引导弹窗
    skip_all_tips(driver)

    # 先检测视频，再检测题目
    if not handle_video_content(driver, actions):
        handle_question_content(driver, actions)

    driver.save_screenshot(os.path.join(BASE_DIR, "cur_end.png"))
    print("-----------------------")
    t.sleep(1)


def process_section_pages(driver, actions, section_items):
    """遍历一个section下的所有page items"""
    for section_item in section_items:
        page_items = section_item.find_element(By.CLASS_NAME, 'page-list').find_elements(By.CLASS_NAME, 'page-item')
        t.sleep(1)
        for page_item in page_items:
            process_page_item(driver, actions, page_item)


# ========== 学习流程 - 专题/章节处理 ==========

def process_chapters(driver, actions, chapter_list, start_index):
    """从 start_index 开始，遍历并处理所有专题"""
    for chapter_idx in range(start_index, len(chapter_list)):
        # 重新获取最新DOM，避免stale element引用
        chapters = driver.find_element(By.CLASS_NAME, 'catalog-list').find_elements(By.CLASS_NAME, 'chapter-item')
        if chapter_idx >= len(chapters):
            break
        chapter_item = chapters[chapter_idx]

        # 第一个专题从课表点进来时已默认展开，不需要再点
        if chapter_idx > start_index:
            # 跳过弹窗再展开专题（带重试，防止弹窗在点击瞬间出现）
            for _ in range(5):
                try:
                    skip_all_tips(driver)
                    chapter_item.find_element(By.CLASS_NAME, 'chapter-name').click()
                    break
                except ElementClickInterceptedException:
                    skip_all_tips(driver)
                    t.sleep(1)
        else:
            skip_all_tips(driver)
        t.sleep(1)

        section_items = chapter_item.find_element(By.CLASS_NAME, 'section-list').find_elements(By.CLASS_NAME, 'section-item')
        print(f"> 当前专题:{chapter_item.find_element(By.CLASS_NAME, 'text').text}")
        print("-----------------------")
        t.sleep(1)

        process_section_pages(driver, actions, section_items)

        # 处理完后跳过弹窗，为下一轮准备
        skip_all_tips(driver)


# ========== 学习流程 - 学习选项卡处理 ==========

def process_learn_tab(driver, actions, learn_page, is_list, all_cookies):
    """处理单个学习选项卡"""
    handle = driver.current_window_handle
    print("\n-----------------------")
    if is_list:
        print(f"> 当前目标:{learn_page.text}")
        actions.click(learn_page).perform()
        t.sleep(2)

    # 查找章节列表（课件页面 table 结构）
    chapter_rows = driver.find_elements(By.XPATH, '//tr[starts-with(@id, "chapterTr")]')
    if not chapter_rows:
        print("> 未找到章节列表，请检查页面是否加载完整")
        return

    # 寻找第一个未完成章节
    index = -1
    for count, row in enumerate(chapter_rows):
        try:
            progress_span = row.find_element(By.XPATH, './/td[2]/span')
            progress = int(progress_span.text.strip('%'))
            if progress != 100:
                print("> 检测到未完成项目")
                print(f"  {row.find_element(By.CLASS_NAME, 'tabchapter-name').text} — 进度: {progress}%")
                print("> 以该项目为起点")
                index = count
                break
        except:
            pass

    if index == -1:
        print("> 当前界面已全部完成")
        print("-----------------------")
        return

    learn_btn = chapter_rows[index].find_elements(By.CLASS_NAME, 'button-red-hollow')
    if not learn_btn:
        print("> 未找到开始学习按钮")
        return
    actions.click(learn_btn[0]).perform()

    # 处理新窗口的 undefined/401
    handle_new_window(driver, all_cookies)

    # 跳过提示
    skip_all_tips(driver)

    # 获取专题列表
    chapter_list = driver.find_element(By.CLASS_NAME, 'catalog-list').find_elements(By.CLASS_NAME, 'chapter-item')
    print(f"> 该部分有{len(chapter_list)}个专题")

    process_chapters(driver, actions, chapter_list, index)

    t.sleep(10)
    driver.close()
    t.sleep(1)
    driver.switch_to.window(handle)


# ========== 课程选择 ==========

def select_course(driver):
    """遍历课程列表，输出课程名，等待用户选择"""
    t.sleep(2)
    course_wrappers = driver.find_elements(By.CLASS_NAME, 'course-item-wrapper')
    if not course_wrappers:
        print("> 未找到课程列表，请检查页面是否加载完整")
        return

    os.system('cls')
    print_banner()

    print("\n======================")
    print("> 检测到以下课程：")
    for idx, wrapper in enumerate(course_wrappers, 1):
        try:
            title = wrapper.find_element(By.CLASS_NAME, 'title').text
            print(f"  {idx}. {title}")
        except:
            print(f"  {idx}. [无法读取课程名]")
    print("-----------------------")

    try:
        choice = int(input("\n请输入课程编号（输入数字后按 Enter）: "))
        if choice < 1 or choice > len(course_wrappers):
            print("> 编号超出范围，程序退出")
            sys.exit()
    except ValueError:
        print("> 输入无效，程序退出")
        sys.exit()

    selected = course_wrappers[choice - 1]
    course_item = selected.find_element(By.CLASS_NAME, 'course-item')
    course_id = course_item.get_attribute('id').replace('courseCard', '')
    textbook_url = f"https://lms.dgut.edu.cn/ulearning/index.html#/course/textbook?courseId={course_id}"
    print(f"> 已选择第 {choice} 门课程，正在跳转到课件页面...")
    driver.get(textbook_url)
    t.sleep(3)


# ========== 主函数 ==========

def main():
    # 开场
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

    # ===== 登录流程 =====
    saved_cookies = load_cookies_from_file()

    if not saved_cookies:
        # 首次使用：有界面模式登录获取Cookie
        print("\n======================")
        print("> 首次使用，请在弹出的浏览器窗口中完成登录")
        print("======================")
        driver, actions = init_driver(headless=False)
        driver.get(LOGIN_URL)
        t.sleep(2)
        input("\n登录完成后请按 Enter 键继续...")
        # 跳转到课程列表确保Cookie完整
        driver.get(COURSE_LIST_URL)
        t.sleep(3)
        save_cookies_to_file(driver)
        driver.quit()
        print("\n======================")
        print("> 首次登录完成，请重新启动程序开始自动刷课")
        print("======================")
        input("按 Enter 键退出...")
        sys.exit()

    # 有Cookie：无头模式自动登录
    driver, actions = init_driver(headless=True)
    all_cookies = perform_login(driver)

    if all_cookies is None:
        # Cookie过期
        driver.quit()
        try:
            os.remove(COOKIE_FILE)
            print("> 已删除过期的Cookie文件")
        except:
            pass
        print("\n======================")
        print("> Cookie已过期，请重新启动程序并重新登录")
        print("======================")
        input("按 Enter 键退出...")
        sys.exit()

    # ===== 登录成功，开始刷课 =====
    # 课程选择
    select_course(driver)

    # 遍历并输出课件章节列表
    print("\n======================")
    print("> 课件章节列表：\n")
    chapter_rows = driver.find_elements(By.XPATH, '//tr[starts-with(@id, "chapterTr")]')
    if chapter_rows:
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
    else:
        print("> 未检测到章节列表")

    # 遍历并输出当前课件的学习界面
    learn_list, is_list = get_learn_tabs(driver)

    # input("\n按 Enter 开始自动刷课...\n")
    t.sleep(5)

    # 进入主流程
    print("\n======================")
    print("> 开始自动刷课\n")

    for learn_page in learn_list:
        process_learn_tab(driver, actions, learn_page, is_list, all_cookies)

    t.sleep(600)
    print("<程序已经运行结束>")
    driver.quit()
    sys.exit()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        import traceback
        print("\n======================")
        print("> 程序运行出错：")
        traceback.print_exc()
        print("======================")
        input("\n按 Enter 键退出...")
