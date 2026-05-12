# U-learning_AUTO

基于 **Python + Selenium** 的在线课程自动学习工具，支持 **U学院（东莞理工学院）** 和 **微伴（mycourse.cn）** 两大平台，自动完成视频播放、答题测试、章节导航等操作，实现无人值守的课程进度完成。

## 目录结构

```
U-learning_AUTO/
├── U-learning/                    # U学院 自动化脚本
│   ├── AUTO.py                    # 主程序 (源码)
│   ├── update_driver.py           # 自动更新 Edge 驱动的工具
│   ├── dist/                      # 打包好的可执行文件
│   │   ├── AUTO.exe
│   │   └── update_driver.exe
│   ├── msedgedriver.exe           # Edge 浏览器驱动
│   └── cookies.json               # 保存的登录Cookie（自动生成）
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
| **登录方式** | 首次有界面登录保存Cookie，后续无头自动登录 | 本地 Edge 用户目录持久化 (首次手动登录) |
| **浏览器模式** | 首次有界面 + 后续无头 (Headless) | 有界面模式 |
| **课程列表获取** | 自动扫描学习选项卡 | 自动展开并导出为 JSON |
| **视频自动播放** | ✅ 静音自动播放，60 秒轮询保活 | ✅ 模拟可信点击，检测播放完成 |
| **答题功能** | ✅ 选择题默认选A、简答题填"ROMIN"、章节测试直接提交 | ✅ 单选/多选/页面提交，支持穷举组合 |
| **栏目检测** | ✅ 识别当前栏目名，章节测试自动跳过答题 | ❌ |
| **已完成项跳过** | ✅ 检测 `complete` 类自动跳过 | ❌ |
| **黑名单课程** | ❌ | ✅ 可配置跳过指定课程 |
| **课程序列导航** | 从第一个未完成章节开始，自动切换专题 | 自动翻页 / 返回课程列表 |
| **异常恢复** | 401 时自动重新注入 Cookie | 检测登录失效 / 重复登录 |
| **防弹窗机制** | ✅ alertModal 自动移除 + 点击重试 | ❌ |
| **截图调试** | ✅ 生成 cur_start.png / cur_end.png / cur_vedio.png | ✅ |
| **全局异常捕获** | ✅ 捕获后打印错误并等待 Enter | ❌ |
| **防检测** | 自定义 UA、禁用自动化标志 | 自定义 UA、禁用自动化标志 |

---

## 使用方法

### 方式一：直接运行 `.exe`

进入 `U-learning/dist/` 或 `WeiBan-learning/dist/`，双击运行对应 exe 即可。

> 需将 `msedgedriver.exe` 放在 exe **同目录**下。

#### 首次使用（U-learning）

1. 运行 `AUTO.exe`
2. 程序自动弹出浏览器窗口，跳转到东莞理工学院统一身份认证页面
3. 手动完成登录后，在控制台按 Enter 键
4. Cookie 自动保存，提示"首次登录完成，请重新启动程序"
5. **重新运行** `AUTO.exe`，程序将以无头模式自动登录并开始刷课

#### 再次使用

直接运行 `AUTO.exe`，程序自动无头登录并从第一个未完成章节开始刷课。

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

首次运行会自动弹出浏览器窗口进行登录，流程与 exe 版本一致。

#### 微伴 (WeiBan)

```bash
cd WeiBan-learning
python weiban_exam.py
```

首次运行会弹出 Edge 浏览器窗口，手动登录微伴平台。之后的运行会自动复用登录会话。

---

## 主要逻辑说明

### U-learning AUTO

- **两阶段登录**：首次有界面浏览器登录保存 Cookie，后续无头模式自动注入 Cookie
- **Cookie 持久化**：保存到 `cookies.json`，过期自动删除并提示重新登录
- **自动检测进度**：从进度未满 100% 的章节开始
- **侧边栏导航**：自动展开/切换专题和栏目，检测 `complete` 类跳过已完成项
- **视频播放**：静音自动播放，每 60 秒防挂机检测
- **答题支持**：
  - 选择题：默认勾选第一个选项
  - 简答题：自动输入 "ROMIN" 并提交
  - 章节测试：检测栏目名，自动提交不答题
- **防弹窗**：自动关闭新手引导、视频引导弹窗，移除 `alertModal` 遮罩层
- **异常恢复**：遇到 401 / undefined 时自动尝试恢复
- **截图调试**：每个项目开始/结束时生成截图，视频防挂机时截图
- **全局异常捕获**：所有未捕获异常打印 traceback 并等待 Enter 退出

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
cd U-learning
python update_driver.py
```

---

## 注意事项

1. **仅供个人学习使用**，请勿滥用。
2. 程序运行时需要一定的 CPU 和内存资源。
3. 如平台页面结构更新导致脚本失效，可能需要更新对应的选择器逻辑。
4. U-learning 首次登录后**必须重启程序**才能开始刷课。
5. 如果 Cookie 过期，程序会自动删除 `cookies.json`，重新运行即可重新登录。
6. 微伴的 `projectId` 和黑名单课程为硬编码，如有需要请直接修改 `weiban_exam.py` 中的常量。

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

**现象**：启动 `AUTO.exe` 时提示"未检测到浏览器驱动"。

**解决**：运行 `update_driver.exe` 自动下载 `msedgedriver.exe` 到同目录下。

### 登录过期

**现象**：启动后提示 "Cookie已过期，请重新启动程序并重新登录"。

**原因**：平台会话过期。

**解决**：程序已自动删除过期 `cookies.json`，直接重新运行 `AUTO.exe`，会重新弹出浏览器窗口进行首次登录流程。

### 课程卡住 / 无法翻页

**现象**：长时间卡在某页面，控制台反复输出某些错误信息。

**原因**：平台页面结构更新，或该课程的特殊页面不在脚本的识别范围内。

**解决**：同目录下查看 `cur_start.png` / `cur_end.png` / `cur_vedio.png` 截图，确认当前页面状态。如果确认是页面结构变化，需要更新 `AUTO.py` 中的选择器逻辑。

### 程序闪退看不到错误

**现象**：双击 exe 后窗口一闪而过。

**原因**：程序出错但无法停留在控制台。

**解决**：在命令行中运行 exe（cmd 或 PowerShell）查看报错信息。新版已加入全局异常捕获，错误信息会显示并等待按 Enter 退出。

### 黑名单配置（微伴）

如需跳过某些课程，修改 `weiban_exam.py` 第 37-50 行的 `BLACKLIST_COURSES` 集合，添加或移除课程标题即可。

---

## License

MIT
