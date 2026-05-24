# learning-AUTO 自动学习脚本

东莞理工学院 U 学习平台的自动刷课脚本。

---

## 目录

- [U-learning 刷课脚本 (AUTO.py)](#u-learning-刷课脚本-autopy)
- [驱动下载程序 (update_driver.py)](#驱动下载程序-update_driverpy)

---

## U-learning 刷课脚本 (AUTO.py)

适用于 DGUT 统一认证登录的 U 学习平台。

### 功能

- 自动登录（Cookie 保存 / 复用 / 多账号管理）
- **多课程批量刷课**：输入课程编号（空格分隔），按顺序依次完成
- 自动遍历课程列表分页，获取完整课程清单
- 自动遍历所有学习界面和课件章节，完成视频播放和答题
- 视频静音自动播放 + 防挂机检测
- 简答题自动填写 + 选择题自动作答
- 章节测试直接提交
- 多开支持（截图按账号隔离存放）
- WebDriverWait 显式等待，适配网络波动

### Cookie 管理

- **首次使用**：有界面浏览器弹出 → 在 DGUT 统一登录页完成认证 → 自动保存 Cookie
- **Cookie 文件名格式**：`{userId}_{name}_{userNo}.json`（从 USERINFO cookie 解码提取）
- **Cookie 存储位置**：程序同目录下的 `cookies/` 文件夹
- **支持多账号**：多个 Cookie 文件并存，启动时选择使用哪个
- **注入方式**：导航到目标域后通过标准 Selenium API 逐条注入，确保 domain 正确关联

### 截图目录结构

```
U-learning/
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

- 需要 Edge 浏览器驱动（`msedgedriver.exe`）放在 `U-learning/` 目录下
- 仅支持 DGUT 统一认证登录（`auth.dgut.edu.cn`）
- 不支持 `.ulearning.cn` 本站登录

---

## 驱动下载程序 (update_driver.py)

独立的 Edge 浏览器驱动下载工具，用于自动获取与当前 Edge 浏览器版本匹配的 `msedgedriver.exe`。

### 使用方式

```bash
cd U-learning
python update_driver.py
# 或直接运行 dist/update_driver.exe
```

### 说明

- 自动检测本机 Edge 浏览器版本
- 从 Microsoft CDN 下载对应版本的 EdgeDriver
- 下载完成后放在 `U-learning/` 目录下即可被 AUTO.py 识别
- 可脱离主程序独立运行，打包为 `update_driver.exe`
