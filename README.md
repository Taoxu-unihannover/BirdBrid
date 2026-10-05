# BirdBrid

面向机器人实训的场景化 Recipes 项目。现有 SO-101 课程已经迁为 10 个课程卡片：选择工位、算力部署方式、串口和相机后，为当前场景生成可复制的操作命令。

## 本地启动

需要 Python 3.10+；Node.js 20+ 用于测试和 npm 快捷命令。网站本身不需要 Node 服务，不使用 CDN、在线字体或数据库。

```bash
cd BirdBrid
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
npm run dev
```

打开 <http://127.0.0.1:4173>。修改 YAML、Markdown 或前端后，重新运行 `npm run build` 并刷新页面即可。也可以完全不用 npm：

```bash
python scripts/build.py
python -m http.server 4173 --bind 127.0.0.1 --directory dist
```

网站不会连接机器人或执行命令；复制命令后在标注的终端运行。首次使用先确认设备、校准 ID、校准文件及模型路径。

## 已实现

- 10 个课程卡片，支持分类、关键词搜索和课程深链接。
- 课前准备标签、场景配置、单步切换的详细课程、命令复制、完成状态和操作清单导出。
- 两种算力场景：无 GPU 端侧接集中服务器；兼容 NVIDIA GPU 的端侧在本机运行服务。
- 工位 `sz01`–`sz99` 自动映射推理前端端口 `5600 + 工位序号`，例如 `sz03 → 5603`。
- 可配置服务器、客户端 IP、串口、两台相机、校准 ID / 路径、模型路径、网页 / 隧道 / 后端端口。
- 配置和进度保存在当前浏览器 localStorage；进度按课程、工位、场景区分。
- 详细课程正文按章节合并为唯一操作流程，保留图片、提示框与安全说明，以及静态 `recipes.json` 数据接口。
- 所有网站资源本地化；构建后可部署在离线教室网络或 GitHub Pages 的项目子路径。

## 项目结构

```text
recipes/so101/*.yaml   # 一课一配方：元信息、步骤、执行位置、场景和命令模板
guides/*.md          # 完整课程正文，保留原课程示例与 MyST 指令
assets/images/       # 课文图片
src/                 # 页面、样式、场景校验和命令渲染
runtime/             # 实训辅助脚本，不是网站依赖
scripts/build.py     # YAML 校验、MyST 转换、静态构建
tests/               # 工位映射、场景命令、模板及内容完整性检查
dist/                # 生成结果，不提交 Git
```

维护方法见 [CONTRIBUTING.md](CONTRIBUTING.md)。本项目借鉴 [vLLM Recipes](https://recipes.vllm.ai/) 的“结构化配方 → 场景选项 → 命令”交互方式；采用轻量静态前端和 Python 构建，适合离线实训。没有复制 vLLM 的模型目录或命令引擎。

## 端口与部署约定

| 项目 | 默认 / 规则 | 说明 |
|---|---|---|
| 推理前端壳 | 5600 + n | 每工位一个；`sz03 = 5603` |
| 批处理后端 | 5500 | 同一推理主机共享一个后端 |
| 主臂读取 / SSH 隧道 | 18700 + n | 两端同号，按工位推导 |
| 仿真网页（查看器） | 8200 + n | 每工位一个；`sz03 = 8203` |
| WebRTC 信令 | 49100 + (n−1)×10 | 每工位一个，仅仿真实例与查看器可见 |
| WebRTC 媒体 | 47998 + (n−1)×10 | 每工位一个，UDP，与信令端口成套 |

多工位时每个工位启动一套 `so101-sim-<工位>` + `so101-web-<工位>` 容器，网页 / 隧道 / 信令 / 媒体端口全部按工位序号推导而错开。信令 / 媒体端口能否按工位绑定，取决于 `so101-sim` 影像版本与查看器镜像的构建方式，需教师先在真实服务器验证（见第 9 章「五、端口规划」）。

本机 GPU 场景复用同一 GR00T 后端和前端壳架构，把计算位置改到本机；它是由课程命令推导出的部署场景，尚未在本次工作中连接 GPU 或机器人验证。端侧无 GPU 时，客户端不加载模型。

`runtime/` 提供课程引用的辅助脚本及 `so101_eval.py` 的配套 `so101_control.py`。这些脚本需要教师提供的 LeRobot / GR00T / Isaac Sim 镜像及相应依赖；网站的 `requirements.txt` 不安装机器人运行环境。镜像、权重和个人校准文件不随仓库分发。原课文固定示例仅作讲解，执行时优先使用上方动态步骤。

## 验证

```bash
npm run build
npm test
```

测试覆盖所有课程的两种场景、工位端口唯一性、输入拒绝、Shell 引号及图片 / 内部课程链接完整性。网页测试不代表机器人实机验收。原课程只验证过遥操作观看和跟随，批量采集到训练的闭环仍需单独验收。

## 后续发布 GitHub

本地目录已初始化为独立 Git 仓库，当前没有远程仓库，也没有推送。确定公开范围与素材授权后，在 GitHub 创建名为 `BirdBrid` 的仓库并添加 remote 即可。

仓库自带 CI 构建测试，以及手动触发的 Pages 工作流。启用仓库 Settings → Pages → Source: GitHub Actions 后，在 Actions 中运行 `Deploy Pages`。本阶段不会自动公开网站。

来源与授权说明见 [THIRD_PARTY.md](THIRD_PARTY.md)。
