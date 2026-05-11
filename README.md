# U-learning_AUTO

基于 **Python + Selenium** 的在线课程自动学习工具，支持 **U学院（东莞理工学院）** 和 **微伴（mycourse.cn）** 两大平台，自动完成视频播放、答题测试、章节导航等操作，实现无人值守的课程进度完成。

## 目录结构

```
U-learning_AUTO/
├── U-learning/                    # U学院 自动化脚本
│   ├── AUTO.py                    # 主程序 (源码)
│   ├── AUTO.exe                   # 打包好的可执行文件
│   ├── msedgedriver.exe           # Edge 浏览器驱动
│   └── README.md
│
├── WeiBan-learning/               # 微伴 自动化脚本
│   ├── weiban_exam.py             # 主程序 (源码)
│   ├── update_driver.py           # 自动更新 Edge 驱动的工具
│   ├── click.png / end.png        # 调试截图
│   ├── msedgedriver.exe           # Edge 浏览器驱动
│   ├── dist/                      # 打包好的可执行文件
│   │   ├── weiban_exam.exe
│   │   ├── update_driver.exe
│   │   └── weiban_exam.zip
│   └── ...
│
└── README.md                      # 本文件
```

---

## 功能对比

| 功能 | U-learning | 微伴 (WeiBan) |
|------|-----------|---------------|
| **登录方式** | 手动粘贴 Cookie | 本地 Edge 用户目录持久化 (首次手动登录) |
| **浏览器模式** | 无头模式 (Headless) | 有界面模式 |
| **课程列表获取** | 自动扫描学习选项卡 | 自动展开并导出为 JSON |
| **视频自动播放** | ✅ 静音自动播放，60 秒轮询保活 | ✅ 模拟可信点击，检测播放完成 |
| **答题功能** | ✅ 自动选择第一个选项并提交 | ✅ 单选/多选/页面提交，支持穷举组合 |
| **黑名单课程** | ❌ | ✅ 可配置跳过指定课程 |
| **课程序列导航** | 从第一个未完成章节开始 | 自动翻页 / 返回课程列表 |
| **异常恢复** | 401 时自动重新注入 Cookie | 检测登录失效 / 重复登录 |
| **截图调试** | ❌ | ✅ |
| **防检测** | 自定义 UA、禁用自动化标志 | 自定义 UA、禁用自动化标志 |

---

## 使用方法

### 方式一：直接运行 `.exe`

进入对应子目录，双击运行 `AUTO.exe` 或 `weiban_exam.exe` 即可。

> 需将 `msedgedriver.exe` 放在同目录下。

### 方式二：运行 Python 源码

#### 环境要求

- Python 3.7+
- Microsoft Edge 浏览器
- 安装依赖：

```bash
pip install selenium
```

#### U学院 (U-learning)

```bash
cd U-learning
python AUTO.py
```

程序启动后会提示：
1. 粘贴 Cookie —— 在浏览器中登录 U学院后，按 `F12` → 控制台输入 `document.cookie` 复制结果
2. 输入课程页面 URL

#### 微伴 (WeiBan)

```bash
cd WeiBan-learning
python weiban_exam.py
```

首次运行会弹出 Edge 浏览器窗口，手动登录微伴平台。之后的运行会自动复用登录会话。

---

## 主要逻辑说明

### U-learning AUTO

- 通过 Cookie 进行身份认证
- 无头浏览器后台运行，不干扰前台操作
- 自动检测进度，从进度未满 100% 的章节开始
- 视频播放时静音，每 60 秒检测一次以防页面判定超时
- 遇到 401 / undefined 时自动尝试恢复

### 微伴 weiban_exam

- 使用 Edge 用户数据目录持久化登录状态，避免重复登录
- 支持配置 `BLACKLIST_COURSES` 跳过不需要的课程
- 多种策略查找「开始」按钮，适配不同页面结构
- 答题支持多种模式：
  - 标准单选 / 多选（按 `name` 属性分组）
  - 页面提交题（检测 `data-answer` / `data-all-answer`）
  - 多按钮页面（依次点击不同选项）
- 支持自动翻页、返回列表、失败重试
- 无合适按钮时自动尝试点击页面底部区域作为兜底

### update_driver

自动检测当前 Edge 浏览器版本，从 Microsoft 官方下载匹配的 WebDriver。
当 Edge 自动更新后驱动不兼容时，运行此工具即可修复。

```bash
cd WeiBan-learning
python update_driver.py
```

---

## 注意事项

1. **仅供个人学习使用**，请勿滥用。
2. 程序运行时需要一定的 CPU 和内存资源。
3. 如平台页面结构更新导致脚本失效，可能需要更新对应的选择器逻辑。
4. 微伴的 `projectId` 和黑名单课程为硬编码，如有需要请直接修改 `weiban_exam.py` 中的常量。

---

## 常见问题

### Edge 驱动版本不匹配

**现象**：启动时报错 `session not created: This version of Microsoft Edge WebDriver only supports Microsoft Edge version XX`。

**原因**：Edge 浏览器自动更新后，旧的 `msedgedriver.exe` 与新版本不兼容。

**解决**：运行 `update_driver.exe`（或 `python update_driver.py`）自动下载匹配的驱动。如果运行后仍不匹配，请检查 Edge 浏览器是否完全退出（任务管理器结束 Edge 进程），然后重启脚本。

### 读取到的 Edge 版本与真实版本不一致

**现象**：`update_driver` 输出的版本号比实际 Edge 版本新。

**原因**：Edge 自动更新会在后台下载新版文件，但尚未生效。脚本枚举安装目录文件夹时取到了新版的目录名。

**解决**：完全关闭所有 Edge 窗口 → 任务管理器确认 `msedge.exe` 已结束 → 重新打开 Edge 检查版本 → 再运行 `update_driver`。

### 驱动文件缺失

**现象**：报错 `[!] 未找到 Edge Driver` 或 `msedgedriver.exe 不存在`。

**解决**：运行 `update_driver.exe` 自动下载，或手动从 [Microsoft Edge WebDriver](https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/) 下载 `msedgedriver.exe` 放到 `WeiBan-learning/` 目录下。

> `.exe` 用户注意：`msedgedriver.exe` 必须和 `weiban_exam.exe` 放在同一目录下。

### 登录过期 / 重复登录

**现象**：程序提示 `[登录已过期] 请重新登录` 或 `检测到重复登录!`，然后退出。

**原因**：平台会话过期，或在其他设备上登录导致当前 Session 被踢。

**解决**：删除 `WeiBan-learning/edge_profile/` 目录（清除缓存的登录数据），重新运行程序，在弹出窗口中手动登录。

### 课程卡住 / 无法翻页

**现象**：长时间卡在某页面，控制台反复输出 `未找到翻页按钮` 或 `尝试底部区域逐点点击`。

**原因**：平台页面结构更新，或该课程的特殊页面不在脚本的识别范围内。

**解决**：截图 `click.png` 查看当前页面状态。如果确认是页面结构变化，需要更新 `weiban_exam.py` 中的选择器逻辑。

### 黑名单配置

如需跳过某些课程，修改 `weiban_exam.py` 第 37-50 行的 `BLACKLIST_COURSES` 集合，添加或移除课程标题即可。

---

## License

MIT
