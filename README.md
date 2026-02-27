# 📸 含子截图 - Screenshot Tool

一个功能完善的跨平台桌面截图工具，支持 Windows、macOS 和 Linux 系统。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](https://github.com/panda-like-bamboo/hanzi-screenshot)

## 📥 快速下载

### Windows 用户（推荐）

**直接下载可执行文件，无需安装 Python 环境：**

👉 [下载 ScreenshotTool.exe](https://github.com/panda-like-bamboo/hanzi-screenshot/releases/latest)

下载后双击运行即可使用！

### 其他平台

前往 [Releases](https://github.com/panda-like-bamboo/hanzi-screenshot/releases) 页面下载对应平台的版本。

---

## ✨ 功能特性

### 🎯 核心功能
- **全局快捷键**: 默认 `Ctrl+Shift+A` 快速截图
- **区域选择**: 鼠标拖拽自由选择截图区域
- **放大镜**: 精确选择时显示放大镜辅助
- **实时尺寸**: 显示选择区域的像素尺寸

### 🎨 绘图工具
| 工具 | 说明 |
|------|------|
| 矩形 | 绘制矩形框 |
| 椭圆 | 绘制椭圆/圆形 |
| 箭头 | 绘制指示箭头 |
| 直线 | 绘制直线 |
| 虚线 | 绘制虚线 |
| 画笔 | 自由绘制 |
| 文字 | 添加文字标注 |
| 马赛克 | 模糊敏感信息 |

### 💾 保存功能
- 保存为 PNG/JPG 格式
- 一键复制到剪贴板
- 截图历史记录管理
- 自定义保存路径

### ⚙️ 系统功能
- **系统托盘**: 最小化到托盘，后台运行
- **开机自启**: 可选开机自动启动
- **自定义设置**: 快捷键、颜色、线宽等

---

## 🎮 使用方法

### 快捷键
| 快捷键 | 功能 |
|--------|------|
| `Ctrl+Shift+A` | 开始截图 |
| `ESC` | 取消截图 |
| `Ctrl+Z` | 撤销 |
| `Ctrl+Y` | 重做 |
| `Ctrl+S` | 保存到文件 |
| `Enter` | 复制到剪贴板 |

### 操作流程
1. 双击运行 `ScreenshotTool.exe`（或按 `Ctrl+Shift+A`）
2. 鼠标拖拽选择截图区域
3. 使用绘图工具进行标注
4. 点击 **Save** 保存文件，或 **Copy** 复制到剪贴板

### 托盘菜单
右键点击系统托盘图标可访问：
- 📷 截图
- 📜 历史记录
- ⚙️ 设置
- 🚪 退出

---

## 🔧 从源码构建

### 环境要求
- Python 3.8+
- PyQt5
- Pillow

### 运行源码
```bash
# 克隆仓库
git clone https://github.com/panda-like-bamboo/hanzi-screenshot.git
cd hanzi-screenshot

# 安装依赖
pip install -r requirements.txt

# 运行程序
python screenshot_tool.py
```

### 打包可执行文件
```bash
# 安装打包工具
pip install pyinstaller

# 打包
pyinstaller --clean --noconfirm screenshot_tool.spec

# 生成的文件在 dist/ 目录
```

---

## 📁 项目结构

```
hanzi-screenshot/
├── screenshot_tool.py    # 主程序
├── screenshot_tool.spec  # PyInstaller配置
├── installer.iss         # Inno Setup安装程序脚本
├── requirements.txt      # Python依赖
├── app-icon.ico          # 应用图标
├── tray-icon.png         # 托盘图标
├── LICENSE.txt           # 许可证
└── README.md             # 项目说明
```

---

## 🛠️ 技术栈

- **GUI框架**: PyQt5
- **图像处理**: Pillow
- **打包工具**: PyInstaller
- **安装程序**: Inno Setup
- **快捷键**: Windows Native API

---

## 🌍 跨平台支持

| 平台 | 自启动方式 |
|------|-----------|
| Windows | 注册表 Run 键 |
| macOS | LaunchAgent plist |
| Linux | XDG autostart |

---

## 📝 更新日志

### v0.1 (2025-02-26)
- ✅ 基础截图功能
- ✅ 绘图工具（矩形、椭圆、箭头、直线、虚线、画笔、文字、马赛克）
- ✅ 颜色选择和线宽调整
- ✅ 撤销/重做功能
- ✅ 系统托盘集成
- ✅ 开机自启功能
- ✅ Windows 可执行文件发布

---

## 📄 许可证

[MIT License](LICENSE.txt)

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📮 联系方式

- GitHub: [@panda-like-bamboo](https://github.com/panda-like-bamboo)
- 项目地址: [hanzi-screenshot](https://github.com/panda-like-bamboo/hanzi-screenshot)
