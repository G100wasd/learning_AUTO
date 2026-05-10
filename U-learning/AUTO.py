import time as t
j = 1
for i in ["运行前请检查同路径下是否包含mesdgedriver.exe 这是浏览器驱动 没有的话无法运行", "因为这个项目是基于edge浏览器写的 所以如果你是从谷歌浏览器获取的cookie 可能会有些神秘的bug?", "这个项目的参考是基于dgut2025级信科1班的形策课件写的 包含刷视频和自动答题的功能 所以如果用户的刷课要求包含其他题目 会失败的 如果可以的话请提交以下issues", "最后 输入cookie和网址时请检查一下输入是否正确", "刷课一旦开始就是默认完成所有的任务 所以如果你有什么想要手动的? 可能得手动中断(ctrl+c)"]:
    print(f"叠甲{j}:\n{i}")
    j+=1
    t.sleep(2)

import os
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

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
print('如果程序报错了 请检查你的输入是不是错的')


def parse_cookies(cookie_str):
    """
    将cookie字符串解析为字典列表
    
    Args:
        cookie_str: cookie字符串，格式为"name1=value1; name2=value2; ..."
    
    Returns:
        cookies_list: 包含字典的列表，每个字典有"name"和"value"键
    """
    cookies_list = []
    
    # 按分号分割每个cookie对
    cookie_pairs = cookie_str.split('; ')
    
    for cookie_pair in cookie_pairs:
        # 按第一个等号分割，因为值中可能包含等号
        if '=' in cookie_pair:
            name, value = cookie_pair.split('=', 1)
            cookies_list.append({
                "name": name.strip(),
                "value": value.strip()
            })
    
    return cookies_list

try:
    print("\n[小刻都看得懂的cookie获取]\n1.点开一个已经登录完成的额优学院(在edge浏览器上登录的)\n2.打开开发者页面(一般是F12)然后切换到控制台\n3.在控制台输入document.cookie之后回车\n4.复制输出的一大串字符,这就是你的cookie了")
    cookies_list = parse_cookies(input("\n输入你的cookie:\n"))
except:
    print("何意味")
    print('发生了神秘的bug')
    print("请检查你的cookie是否正确")
    quit()
url = input("\n目标刷课界面的网址\n")


# ======= 初始化 =========
print("\n======================")
print("> 正在以无头浏览器模式运行")
print("> 正在进行初始化")
try:
    qt = Options()
    qt.add_argument("--no-sandbox")
    qt.add_argument("--headless")
    qt.add_argument("--disable-gpu")
    qt.add_argument('--disable-blink-features=AutomationControlled')
    qt.add_argument('--window-size=1920,1080')
    qt.add_argument('--lang=zh-CN')
    qt.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0')
    qt.add_experimental_option("excludeSwitches", ["enable-automation"])
    qt.add_experimental_option("useAutomationExtension", False)
    qt.add_experimental_option(name='detach', value=True)
    driver = webdriver.Edge(service=Service('msedgedriver.exe'), options=qt)
    #driver = webdriver.Edge( options=qt)
    actions = ActionChains(driver)
    print(os.getcwd())
    print("> 成功")
except Exception as e: 
    print("> 失败")
    print(f"> 发生报错:\n{e}")
    print("> 程序已退出")
    quit()
print("======================")
# ====== 初始化结束 ==========


driver.get("https://lms.dgut.edu.cn/ulearning") # 先跳转到优学院进行cookie注入登录
t.sleep(1)

# ========= cookie注入 ===========
print("\n======================")
print("> 正在注入曲奇")
all_cookies = []
for cookie in cookies_list:# cookie的更详细切分
    cookie_dict = {
        'name': cookie['name'],
        'value': cookie['value'],
        'domain': 'lms.dgut.edu.cn'
    }
    all_cookies.append(cookie_dict)
for cookie in all_cookies:# cookie的注入
    try:
        driver.add_cookie(cookie)
        print(f"✅ 已注入: {cookie['name']}")
    except Exception as e:
        print(f"❌ 注入失败 {cookie['name']}: {e}")
driver.refresh()
t.sleep(1)
print("> 曲奇注入结束 当前状态:已登录")
print("======================")
# ======== cookie注入结束 ========= 

# ========= 跳转到目标刷课界面 ===========
print("\n======================")
print("> 跳转到目标刷课界面")
print("\n> 如果在这里等待超过30s\n> 不用怀疑\n> 程序大概率已经因为网络或者其他原因悄悄似了 \n> 需要重启")

try:
    driver.get(url)
    print("> 成功")
except:
    print("> 何意味")
    quit()
print("======================\n")
t.sleep(2)
# ========= 结束 ===========

print("███╗   ███╗██╗   ██╗███████╗███████╗██╗  ██╗   ██╗███████╗███████╗")
print("████╗ ████║██║   ██║██╔════╝██╔════╝██║  ╚██╗ ██╔╝██╔════╝██╔════╝")
print("██╔████╔██║██║   ██║█████╗  ███████╗██║   ╚████╔╝ ███████╗█████╗  ")
print("██║╚██╔╝██║██║   ██║██╔══╝  ╚════██║██║    ╚██╔╝  ╚════██║██╔══╝  ")
print("██║ ╚═╝ ██║╚██████╔╝███████╗███████║███████╗██║   ███████║███████╗")
print("╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚══════╝╚══════╝╚═╝   ╚══════╝╚══════╝")



# ========= 主程序 ============
print("\n======================")
print("> 主程序已启动\n")
print("-----------------------")
is_list = False
learn_list = [0]
try:
    learn_list = driver.find_element(By.CLASS_NAME, 'textbook-tab-list').find_elements(By.CLASS_NAME, 'textbook-tab-item')
    print(f"> 共有{len(learn_list)}个学习界面")
    for i in range(len(learn_list)):
        print(f"> {i+1}.{learn_list[i].text}")
    print("-----------------------")
    is_list = True
except:
    pass

for current_learn_page in learn_list:
    handle = driver.current_window_handle
    print("\n-----------------------")
    if(is_list):
        print(f"> 当前目标:{current_learn_page.text}")
        actions.click(current_learn_page).perform()
        t.sleep(2)

    learn_rate_list = driver.find_element(By.CLASS_NAME, 'directory-table').find_elements(By.XPATH, '//td[2]/span')
    learn_btn = driver.find_element(By.CLASS_NAME, 'directory-table').find_elements(By.CLASS_NAME, 'button-red-hollow')

    index = -1
    for count in range(len(learn_rate_list)):
        if((int)((learn_rate_list[count].text).strip('%')) != 100):
            print("> 检测到未完成项目")
            print("> 以该项目为起点")
            index=count
            break
    
    if(index == -1):
        print("> 当前界面已全部完成")
        print("-----------------------")
        continue

    actions.click(learn_btn[index]).perform()

    # ====== 处理新窗口的undefined问题 ======
    try:
        # 1. 等待新窗口出现
        t.sleep(2)
        # 2. 获取所有窗口句柄
        all_windows = driver.window_handles
        if len(all_windows) > 1:
            # 3. 切换到新窗口（最后一个通常是新打开的）
            new_window = all_windows[-1]
            driver.switch_to.window(new_window)
            # 4. 等待页面加载
            t.sleep(2)
            # 5. 检查是否有undefined错误
            page_source = driver.page_source
            console_errors = []
            # 获取控制台错误
            try:
                logs = driver.get_log('browser')
                for log in logs:
                    if '401' in log['message'] or 'error' in log['message'].lower():
                        console_errors.append(log['message'][:100])
            except:
                pass
            
            # 6. 如果发现401错误或undefined，修复认证
            if "undefined" in page_source or console_errors or '401' in str(page_source):
                print("检测到401/undefined问题，开始修复认证...")
                # 获取当前窗口的域名
                current_url = driver.current_url
                if '//' in current_url:
                    domain = current_url.split('//')[1].split('/')[0]
                else:
                    domain = 'lms.dgut.edu.cn'
                # 重新注入Cookie
                driver.delete_all_cookies()
                # 构建新窗口的Cookie（使用正确的域名）
                new_window_cookies = []
                for cookie in all_cookies:
                    cookie_copy = cookie.copy()
                    cookie_copy['domain'] = domain
                    new_window_cookies.append(cookie_copy)
                # 添加Cookie到新窗口
                for cookie in new_window_cookies:
                    try:
                        driver.add_cookie(cookie)
                    except:
                        pass
                    
                # 执行JavaScript修复脚本
                try:
                    # 设置localStorage认证信息
                    driver.execute_script("""
                        localStorage.setItem('token', 'D9C8E6D3D66FDEE7239B26544E5A74F6');
                        localStorage.setItem('AUTHORIZATION', 'D9C8E6D3D66FDEE7239B26544E5A74F6');
                        localStorage.setItem('userInfo', document.cookie.match(/USER_INFO=([^;]+)/)?.[1] || '');
                    """)
                    # 重新加载失败的JS资源
                    driver.execute_script("""
                        // 重新加载可能失败的资源
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
                # 再次刷新
                driver.refresh()
                t.sleep(3)
                print("认证修复完成")
            # 刷新主窗口，更新进度
            driver.refresh()
            t.sleep(3)  
    except Exception as e:
        print(f"处理新窗口时出错: {e}")



    # ====== 跳过提示 =======
    for i in range(2):
        try:
            tip_skip_btn = driver.find_element(By.CLASS_NAME, 'operation').find_element(By.CLASS_NAME, 'close-btn')
            t.sleep(5)
            actions.click(tip_skip_btn).perform()
            #print("> 跳过所有提示")
        except:
            pass

    chapter_list = driver.find_element(By.CLASS_NAME, 'catalog-list').find_elements(By.CLASS_NAME, 'chapter-item')
    print(f"> 该部分有{len(chapter_list)}个专题")
    for chapter_item_count in range(index, len(chapter_list)):
        chapter_item = chapter_list[chapter_item_count]
        section_items = chapter_item.find_element(By.CLASS_NAME, 'section-list').find_elements(By.CLASS_NAME, 'section-item')
        print(f"> 当前专题:{chapter_item.find_element(By.CLASS_NAME, 'text').text}")
        print("-----------------------")
        t.sleep(1)

        for section_item in section_items:
            page_items = section_item.find_element(By.CLASS_NAME, 'page-list').find_elements(By.CLASS_NAME, 'page-item')
            t.sleep(1)

            for page_item in page_items:
                page_name = page_item.find_element(By.CLASS_NAME, 'page-name')
                driver.execute_script("arguments[0].scrollIntoView();", page_name)
                actions.click(page_name).perform()
                t.sleep(2)
                actions.click(page_name).perform()
                title = page_name.find_element(By.CLASS_NAME, 'text').find_element(By.XPATH, './span')
                print("\n-----------------------")
                print(f"> 当前项目:{title.text}")
                driver.save_screenshot("start.png")
                t.sleep(2)

                # ===== 先检测是否是视频 =====
                try:
                    is_video = driver.find_element(By.CLASS_NAME, 'page-container').find_element(By.CLASS_NAME, 'page-wrapper').find_element(By.CLASS_NAME, 'video-element')
                    video_elements = driver.find_elements(By.CLASS_NAME, 'video-element')
                    print("> 当前部分 : 视频")
                    print(f"> 数量: {len(video_elements)}")
                    video_count = 1

                    # ===== 遍历视频列表 =====
                    for video_element in video_elements:
                        print(f">   视频{video_count}")
                        video_count+=1
                        video = video_element.find_element(By.CLASS_NAME, 'mejs__container')
                        driver.execute_script("arguments[0].scrollIntoView();", video)
                        t.sleep(1)

                        # ===== 当前视频是否看完？ =====
                        video_check = video_element.find_element(By.CLASS_NAME, 'video-progress').find_element(By.CLASS_NAME, 'text').find_element(By.XPATH, './span')
                        if(video_check.text == "已看完"):
                            print(">   该视频已看完")
                            continue
                        t.sleep(1)
                        
                        # ===== 视频控制组件的获取 =====
                        video_control = video.find_element(By.CLASS_NAME, 'mejs__controls')
                        video_play_btn = video_control.find_element(By.CLASS_NAME, 'mejs__play').find_element(By.XPATH, './button')
                        video_volumn = video_control.find_element(By.CLASS_NAME, 'mejs__volume-button').find_element(By.XPATH, './button')
                        t.sleep(1)

                        # ===== 视频的自动静音与播放 =====
                        actions.click(video_volumn).perform()
                        actions.click(video_play_btn).perform()
                        print(">   已静音")
                        print(">   已自动播放")
                        t.sleep(5)

                        # ===== 视频的时间计算 =====
                        video_current_time = video_control.find_element(By.CLASS_NAME, 'mejs__currenttime-container').find_element(By.XPATH, './span').text
                        video_time = video_control.find_element(By.CLASS_NAME, 'mejs__duration-container').find_element(By.XPATH, './span').text
                        cost_time = (((int)(video_time.strip().split(':')[0])+1) - ((int)(video_current_time.strip().split(":")[0])))
                        print(f">   视频时长: {video_time}")
                        print(f">   已播放: {video_current_time}")
                        print(f">   消耗时间:{cost_time*60}")
                        t.sleep(1)

                        # ===== 每60s自动暂停一次视频 防止脚本/挂机检测 =====
                        for i in range(cost_time):
                            t.sleep(60)
                            actions.click(video_play_btn).perform()
                            print(f">   防挂机检测X{i+1}")
                            driver.save_screenshot("current.png")
                            t.sleep(1)
                            actions.click(video_play_btn).perform()
                        t.sleep(1)
                
                except:
                    # ===== 再检测是否是题目 =====
                    try:
                        is_qustion = driver.find_element(By.CLASS_NAME, 'question-view')
                        print(">    当前部分 : 小测")
                        
                        # ===== 获取必要的问题组件 =====
                        question_view = driver.find_element(By.CLASS_NAME, 'question-view')
                        submit_btn = driver.find_element(By.CLASS_NAME, 'question-operation-area').find_element(By.CLASS_NAME, 'btn-submit')
                        qustion_list = question_view.find_element(By.CLASS_NAME, 'question-element-node-list').find_elements(By.CLASS_NAME, 'question-element-node')

                        # ===== 遍历题目列表 =====
                        for question in qustion_list:
                            driver.execute_script("arguments[0].scrollIntoView();", question)
                            question_wrapper = question.find_element(By.CLASS_NAME, 'question-body-wrapper')
                            try:
                                answer_choice = question_wrapper.find_elements(By.CLASS_NAME, 'choice-item')[0]
                            except:
                                answer_choice = question_wrapper.find_elements(By.CLASS_NAME, 'choice-btn')[0]
                            actions.click(answer_choice).perform()
                            t.sleep(0.5)
                        
                        # ===== 提交题目 =====
                        print(">    题目已全完成")
                        driver.save_screenshot("current.png")
                        driver.execute_script("arguments[0].scrollIntoView();", submit_btn)
                        t.sleep(1)
                        actions.click(submit_btn).perform()
                        t.sleep(3)

                    except Exception as e:
                        pass
                
                print("-----------------------")
                driver.save_screenshot("end.png")
                t.sleep(1)


        # ===== 收起当前专题栏并展开下一个专题栏 =====
        actions.click(chapter_list[chapter_item_count].find_element(By.CLASS_NAME, 'chapter-name')).perform()
        t.sleep(1)
        if(chapter_item_count<(len(chapter_list)-1)):
            actions.click(chapter_list[chapter_item_count+1].find_element(By.CLASS_NAME, 'chapter-name')).perform()
        t.sleep(1)

    t.sleep(10)
    driver.close()
    t.sleep(1)
    driver.switch_to.window(handle)

t.sleep(600)
print("<程序已经运行结束>")
driver.quit()
quit()
#driver.execute_script("arguments[0].scrollIntoView();", answer_check)