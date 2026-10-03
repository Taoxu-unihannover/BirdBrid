# 维护课程配方

每节课程由 `recipes/<课程系列>/<id>.yaml` 和 `guides/<id>.md` 组成。新增配方将自动加入首页，无需修改页面组件。

```yaml
id: 10-example
title: 新课程
order: 11
category: 动手操作
description: 一句话说明这节课的目标。
duration: 30 分钟
guide: guides/10-example.md
steps:
  - title: 启动工位服务
    where: '{compute} · 推理容器 /workspace/deploy'
    note: 先确认后端已启动，另开终端运行本步骤。
    command: |
      /Isaac-GR00T/.venv/bin/python station_server.py {{station}} {{port}} tcp://127.0.0.1:{{backend}}
  - title: 集中模式的额外步骤
    where: 集中服务器 · 宿主机
    modes: [remote]
    note: 只有集中算力模式展示。
```

`id` 唯一，仅小写字母、数字、连字符；`order` 控制排序。支持 `remote` 和 `local` 场景，省略 `modes` 表示两种场景都展示。

`command` 的 `{{变量名}}` 由 `src/scenario.js` 统一进行 Shell 单引号转义。**不要再给占位符套一层引号**。变量可作为单独参数或参数的一部分（如 `tcp://127.0.0.1:{{backend}}`）。不支持在变量里加入 Shell 表达式；模型 / 校准路径必须是绝对路径，不会展开 `~`。

变量列表：`station, mode, server, client, user, teleop, robot, teleopId, robotId, wrist, front, modelRoot, model, calibration, viewer, tunnel, backend`；派生变量 `port, host, compute, cameras`。`where` 中的 `{compute}` 表示本机 GPU 或集中服务器。

不要让同一条命令混合宿主机和容器操作。需要另开终端、保持进程运行或先修改路径时，在 `note` 明确说明。页面将命令输出为文本，绝不自动执行。

正文支持标准 Markdown、表格，以及现有课程使用的 MyST `figure`、`dropdown`、`note`、`tip`、`warning`、`important`、`admonition`、`grid`、`grid-item-card`。复杂的新指令需先扩展 `scripts/build.py` 并补充内容完整性检查。正文中 `images/xxx` 的 MyST 图片从 `assets/images/` 读取；课程链接写成 `03-calibration.md` 即可。

修改步骤后运行 `npm run build && npm test`。若改变机器人行为，应单独进行硬件验收并记录环境、镜像版本和结果；不要把网站单元测试描述为真实设备验证。原始示例和动态命令不同的原因应在配方说明中写明。
