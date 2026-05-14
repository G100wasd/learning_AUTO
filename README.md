# learning-AUTO 自动学习脚本

东莞理工学院 U 学习平台和微伴平台的自动刷课脚本。

---

## 目录

- [U-learning 刷课脚本 (AUTO.py)](#u-learning-刷课脚本-autopy)
- ~~[微伴刷课脚本 (weiban_exam.py)](#微伴刷课脚本-weiban_exampy)~~ （已过时）
- [驱动下载程序 (update_driver.py)](#驱动下载程序-update_driverpy)

---

## U-learning 刷课脚本 (AUTO.py)

适用于 DGUT 统一认证登录的 U 学习平台。

### 功能

- 自动登录（Cookie 保存 / 复用 / 多账号管理）
- 自动遍历课件章节，完成视频播放和答题
- 视频静音自动播放 + 防挂机检测
- 简答题自动填写 + 选择题自动作答
- 章节测试直接提交
- 多开支持（截图按账号隔离存放）

### Cookie 管理

- **首次使用**：有界面浏览器弹出 → 在 DGUT 统一登录页完成认证 → 自动保存 Cookie
- **Cookie 文件名格式**：`{userId}_{name}_{userNo}.json`（从 USERINFO cookie 解码提取）
- **Cookie 存储位置**：程序同目录下的 `cookies/` 文件夹
- **支持多账号**：多个 Cookie 文件并存，启动时选择使用哪个
- **注入方式**：导航到目标域后通过标准 Selenium API 逐条注入，确保 domain 正确关联

### 截图目录结构

```
程序目录/
├── cur_photo/
│   └── {userId}_{name}_{userNo}/
│       ├── cur_vedio.png
│       ├── cur_start.png
│       └── cur_end.png
```

### 支持的题目类型

| 类型 | 处理方式 |
|------|---------|
| 选择题 | 自动选择第一个选项 |
| 简答题 | 自动填写预设内容并提交 |
| 章节测试 | 直接提交跳过 |

### 注意事项

- 需要 Edge 浏览器驱动（`msedgedriver.exe`）放在程序同目录下
- 仅支持 DGUT 统一认证登录（`auth.dgut.edu.cn`）
- 不支持 `.ulearning.cn` 本站登录

---

## ~~微伴刷课脚本 (weiban_exam.py)~~（已过时）

> 当前版本基于纯 DOM 操作实现，对不同课程页面结构的泛用性不足，**计划重构为 DOM + OCR 混合架构**，改造完成前标记为过时。

### 改造计划

**目标**：将 `weiban_exam.py` 从纯 DOM 操作改为 DOM + OCR 混合架构，提高对不同课程页面结构的泛用性。

**已确定的架构分层**：

| 模块 | 方案 | 说明 |
|------|------|------|
| 课程列表（主页 DOM） | 保留现有逻辑 | 获取课程列表、展开分类、点击课程标题 |
| 课程内容（iframe 内 OCR） | 截图 + PaddleOCR | 识别文字坐标，定位并点击"开始学习"/"下一页"/"返回列表" |
| 视频检测 | 保留 DOM | `document.querySelector('video')` 检测时长、播放状态 |
| 小测答题 | 保留 DOM | radio/checkbox/data-answer 遍历组合 |

**需改造的函数**（约 200 行替换）：

| 现有函数 | 改造方案 |
|---------|---------|
| `wait_for_start_button(driver)` | → OCR 识别"开始学习"坐标，ActionChains 点击 |
| `click_next_or_btn(driver)` | → OCR 识别"下一页"/"返回列表"坐标 |
| `click_return_or_back(driver)` | → OCR 识别"返回"坐标 |
| 新增 `ocr_click(driver, keywords)` | 通用函数：截图 → 识别 → 点击坐标 |

**iframe 注意事项**：截图前需 `switch_to.frame(content_iframe)`，坐标回主 frame 后需偏移换算。

**依赖变更**：接入 PaddleOCR（或 EasyOCR），`pip install paddleocr` 或等效方案。

---

## 驱动下载程序 (update_driver.py)

独立的 Edge 浏览器驱动下载工具，用于自动获取与当前 Edge 浏览器版本匹配的 `msedgedriver.exe`。

### 使用方式

```bash
python update_driver.py
# 或直接运行 exe 版本
```

### 说明

- 自动检测本机 Edge 浏览器版本
- 从 Microsoft CDN 下载对应版本的 EdgeDriver
- 下载完成后放在程序同目录下即可被 AUTO.py 识别
- 可脱离主程序独立运行，打包为 `update_driver.exe`
