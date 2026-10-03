# 仿真遥操作与数据采集

本章你在**仿真**里遥控机械臂：仿真程序跑在服务器上，你用浏览器看实时画面，用主臂给它下发动作。这也是采集训练数据的方式。

:::{dropdown} 动手前你需要准备什么？
- 已完成[主从遥操作](04-teleop.md)，熟悉用相机画面操作
- 主臂已连到你的笔记本（`leader_server.py` 读取它的串口）
- 教师已在服务器端准备好仿真容器和网页入口
- 拿到服务器 IP 和网页地址（在工位信息表里）
:::

## 学习目标

在本章结束时，你将能够：

- 说清楚「你的主臂动作 → 服务器仿真」这条链路是怎么连起来的
- 启动本机的 leader 读取服务，连上服务器仿真
- 通过浏览器观看仿真，并完成跟随检查和抓取练习
- 了解数据采集的步骤

## 这条链路长什么样？

仿真要"搬"到服务器上，是因为它太吃显卡。你的主臂动作要经过一段「中转」才能到仿真：

```
你的笔记本                                    服务器
  ├─ leader_server.py 读主臂串口                ├─ Isaac Sim 仿真程序
  │   （监听 localhost:18766）  ◀──SSH 隧道──       （读 localhost:18765 的动作）
  └─ 浏览器：看仿真实时画面  ◀──── WebRTC ────  └─ 网页串流 http://<server>:8210
```

- 你的笔记本只负责**读主臂动作**和**看画面**，不跑仿真。
- 中间那条 SSH 隧道，把「你笔记本上的 18766」接到「服务器上的 18765」。

## 第一步：启动本机的 leader 读取服务

主臂动作的「读取服务」也跑在**客户端容器**里。先进入容器（`sudo docker exec -it so101-client bash`），再进入部署目录并启动读取服务（它会读主臂串口、释放主臂扭矩、把关节位置转发出去）：

```bash
cd ~/so101-lab/scripts   # 部署脚本目录（在第 2 章的 ~/so101-lab 下）
python3 -u leader_server.py \
    --serial /dev/ttyACM0 \
    --calibration R07252801.recalibrated.json
```

:::{note}
`--serial` 换成你第 2 章记录的主臂串口（`$TELEOP_PORT`），`--calibration` 换成你的主臂校准文件名。容器以 `--network host` 启动，所以它监听的 `localhost:18766` 就是笔记本本机的端口，服务器端的 SSH 隧道仍能照常连上。
:::

看到类似 `CALIBRATION_MATCH` 和 `LEADER_READY` 的输出，说明主臂已经被正确读取，等待仿真来取数据。

## 第二步：建立 SSH 隧道

这一步把「你笔记本的 18766」接到「服务器」。通常由**教师统一建立**，或在教师的指导下执行（因为需要服务器的登录权限）：

```bash
# 以下在服务器端执行（示例，不要照抄 IP/账号）
ssh -N -o ExitOnForwardFailure=yes \
  -o ServerAliveInterval=10 -o ServerAliveCountMax=3 \
  -L 127.0.0.1:18765:127.0.0.1:18766 你的账号@你的笔记本IP
```

:::{tip}
如果 `18765` 已经在监听，先确认已有隧道，不要重复启动。账号密码不要写进任何文件。
:::

## 第三步：启动仿真并观看

仿真需**服务器上的容器**（这一步由教师/服务器操作，若教师已帮你起好，可直接跳到浏览器）：

| 组件 | 作用 | 名称 |
|---|---|---|
| 仿真容器 | 跑 Isaac Sim + `lerobot_agent` | `so101-sim` |
| 网页服务 | 把仿真画面串流到浏览器 8210（在**宿主机直跑**，不起容器） | — |

:::{note}
这些命令**不是在你笔记本上执行**。`sim_to_real_so101` 模块和 `/workspace` 目录只存在于**仿真容器里**（靠镜像自带 `/isaac-sim/python.sh` 提供），宿主机上是没有的。
:::

### 1）启动仿真容器（服务器）

```bash
sudo docker run -d --name so101-sim \
  --privileged --network host --runtime nvidia \
  -v /dev:/dev \
  --entrypoint bash \
  so101-sim:network \
  -c "echo started && sleep infinity"
```

- 镜像 `so101-sim:network` 是「网络输入版」（主臂接在学员笔记本上）。
- 若主臂**直接插在服务器 USB 上**，改用镜像 `so101-sim:usb`。

### 2）进入仿真容器，启动仿真

```bash
sudo docker exec -it so101-sim bash

cd /workspace/Sim-to-Real-SO-101-Workshop
/isaac-sim/python.sh -m sim_to_real_so101.scripts.lerobot_agent \
    --task Lerobot-So101-Teleop-Vials-To-Rack --num_envs 1 \
    --robot_id R07252801 --headless --livestream 1 \
    --leader_tcp_port 18765
```

:::{note}
网页查看器**不在容器里跑**，而是作为宿主机上的一个 Node 静态服务（占 8210 端口）直接运行。教师在宿主机上启动该网页服务的方式见[第 9 章「web-viewer 宿主机直跑」](09-server-deploy.md)。
:::

然后在**你的浏览器**打开：

```
http://<服务器IP>:8210
```

你应该看到仿真画面。日志里出现 `fresh actions received`、`network_actions` 持续增长，说明你的主臂动作已经传进仿真了。

## 第四步：跟随检查与操作练习

1. 保持主臂静止，确认场景完整。**不要为了调视角去拖动仿真实体**（灯箱之类），只看相机视角。
2. 六个关节逐个**小幅移动**，检查方向、幅度是否一致。
3. 点击画面让窗口获得键盘焦点，按 **R** 重置环境三次。
4. 连续操作至少两分钟，观察是否卡顿或断连。
5. 抓试管放进试管架，反复几次，记录成功/失败原因。

:::{figure} images/teleop_in_sim.gif
:alt: 仿真中的遥操作
:width: 80%

在仿真中进行遥操作。
:::

## 采集训练数据（理解即可，现场按教师指引）

在仿真里，每按一次 **S** 就录一条示范（episode）。录到的示范就是将来训练 AI 模型的数据。

:::{warning}
**诚实说明：** 下面这套「录制」步骤沿用原课件命令，本项目的 POC 实测**只完整验证了遥操作观看和跟随**，尚未完整跑通「批量录制 → 转数据集 → 训练」的闭环。正式培训中若启用录制环节，需按教师现场指引执行，并以实际输出为准。
:::

原课件的录制命令长这样（供理解）：

```bash
lerobot_agent --task Lerobot-So101-Teleop-Vials-To-Rack-DR \
    --repo_id 你的用户名/so101_teleop_vials \
    --repo_root "$(pwd)/datasets/recorded/so101_teleop_vials" \
    --task_name "Pick up the vial and place it in the rack"
```

录制控制的按键：

- **S**：开始/停止录制一条示范
- **C**：取消当前录制（录错了用）
- **R**：重置环境（同时停止录制）

## 下课：有序停止

按顺序停，不要乱 kill：

1. 先在**仿真/服务器端**按 Ctrl+C 停止遥操作。
2. 再关闭 SSH 隧道。
3. 最后停掉你笔记本上的 `leader_server.py`。

## 关键要点

- 链路：**主臂 → leader_server.py → SSH 隧道 → 服务器仿真 → 浏览器 WebRTC**。
- 你只负责读主臂和看画面，仿真吃显卡的部分全在服务器。
- 浏览器里按 **R** 重置、**S** 录制、**C** 取消。
- 停止时按「仿真 → 隧道 → 采集」的顺序，避免误杀进程。