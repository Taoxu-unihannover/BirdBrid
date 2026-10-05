# 仿真遥操作与数据采集

本章你在**仿真**里遥控机械臂：仿真程序跑在服务器上，你用浏览器看实时画面，用主臂给它下发动作。这也是采集训练数据的方式。

:::{dropdown} 动手前你需要准备什么？
- 已完成[主从遥操作](04-teleop.md)，熟悉用相机画面操作
- 主臂已连到你的笔记本（`leader_server.py` 读取它的串口）
- 在首页「配置你的实训场景」填好你的**工位 ID** 和**集中服务器 IP / 主机名**
- 你的**工位 ID**（首页配置的 `sz01`–`sz99`）就是 SSH 登录服务器的账号
:::

## 学习目标

在本章结束时，你将能够：

- 说清楚「你的主臂动作 → 服务器仿真」这条链路是怎么连起来的
- 启动本机的 leader 读取服务，SSH 登录服务器并连上你自己的仿真
- 自己启动只属于你的仿真容器和网页容器，通过浏览器观看、跟随和抓取
- 了解数据采集的步骤

## 这条链路长什么样？

仿真要"搬"到服务器上，是因为它太吃显卡。你的主臂动作要经过一段「中转」才能到仿真：

```
① 主臂动作 —— 你的笔记本
   leader_server.py 读主臂串口，监听 127.0.0.1:18765
        │
        │  SSH 隧道（服务器 ↔ 笔记本，端口按工位）
        ▼
② 仿真 —— 服务器（容器 so101-sim-<你的工位>）
   Isaac Sim 读 127.0.0.1:18765 的动作
        │
        │  WebRTC 视频流（默认信令 49100 / 媒体 47998）
        ▼
③ 网页查看器 —— 服务器（容器 so101-web-<你的工位>）
   浏览器打开 http://<服务器IP>:8210 看你的仿真画面
```

- 你的笔记本只负责**读主臂动作**和**看画面**，不跑仿真。
- 服务器上**每个工位一套** `so101-sim-<工位>` + `so101-web-<工位>` 容器，网页、隧道、信令、媒体端口全部**按你的工位 ID 自动错开**，互不干扰。

## 第一步：启动本机的 leader 读取服务

主臂动作的「读取服务」也跑在**客户端容器**里。先进入容器（`sudo docker exec -it so101-client bash`），再进入部署目录并启动读取服务（它会读主臂串口、释放主臂扭矩、把关节位置转发出去）：

```bash
cd ~/so101-lab/scripts   # 部署脚本目录（在第 2 章的 ~/so101-lab 下）
python3 -u leader_server.py \
    --serial /dev/ttyACM0 \
    --calibration R07252801.recalibrated.json
```

:::{note}
`--serial` 换成你第 2 章记录的主臂串口（`$TELEOP_PORT`），`--calibration` 换成你的主臂校准文件名。容器以 `--network host` 启动，所以它监听的 `127.0.0.1:18765` 就是笔记本本机的端口，服务器端的 SSH 隧道仍能照常连上。
:::

看到类似 `CALIBRATION_MATCH` 和 `LEADER_READY` 的输出，说明主臂已经被正确读取，等待仿真来取数据。

## 第二步：登录服务器宿主机

:::{important}
第一步的 `leader_server.py` 还在**前台运行**，别关它。请**新开一个终端**，再继续下面的操作。
:::

接下来的隧道和容器都要在**服务器宿主机**上执行。在新终端里 SSH 登录服务器：

```bash
ssh sz03@192.168.1.6
```

:::{note}
地址填首页「配置你的实训场景」里的**集中服务器 IP / 主机名**，用户名就是你在首页填的**工位 ID**（`sz03` 只是示例）。登录成功后再执行后面的命令。
:::

## 第三步：建立主臂隧道

这一步把「你笔记本的主臂读取端口」接到「服务器」。登录服务器成功后，在**服务器宿主机**上执行：

```bash
ssh -N -o ExitOnForwardFailure=yes \
  -o ServerAliveInterval=10 -o ServerAliveCountMax=3 \
  -L 127.0.0.1:18765:127.0.0.1:18765 你的账号@你的笔记本IP
```

:::{tip}
`18765` 是本页下方动态步骤里的**隧道端口**（按你的工位推导），两端同号。如果该端口已经在监听，先确认已有隧道，不要重复启动。账号密码不要写进任何文件。
:::

## 第四步：启动仿真容器

:::{important}
第三步的隧道 `ssh -N` 还在**前台运行**，占用了当前终端。请**再新开一个终端**，重新 SSH 登录服务器，再执行下面的命令。
:::

先在新终端里 SSH 登录服务器：

```bash
ssh sz03@192.168.1.6
```

登录后，启动只属于你的仿真容器（容器名按工位自动错开）：

```bash
sudo docker run -d --name so101-sim-sz03 \
  --privileged --network host --runtime nvidia \
  -v /dev:/dev -e PUBLIC_IP=192.168.1.6 \
  --entrypoint bash \
  so101-sim:network \
  -c "echo started && sleep infinity"
```

- **`-e PUBLIC_IP=192.168.1.6` 必须设**：Isaac Sim WebRTC 生成 SDP 时用它作为媒体流对外地址；不设的话远程浏览器拿到 SDP 后会去 `127.0.0.1` 取媒体流，表现为点连接后**黑屏**。把 `192.168.1.6` 换成你首页填的集中服务器 IP。
- 镜像 `so101-sim:network` 是「网络输入版」（主臂接在你笔记本上）。
- 若主臂**直接插在服务器 USB 上**，改用镜像 `so101-sim:usb`。
- 想让教师对仿真脚本的修复（如录制空帧保护）即时生效，可额外挂载宿主机源码目录：`-v /home/xutao/so101-lab/so-101/Sim-to-Real-SO-101-Workshop/source:/workspace/Sim-to-Real-SO-101-Workshop/source`（路径换成服务器上实际源码位置；挂载空目录会让容器内 `sim_to_real_so101` 模块丢失，sim 启动报 `ModuleNotFoundError`）。
- 多工位 WebRTC 信令 / 媒体端口隔离需要教师按工位构建仿真镜像，单工位测试时使用默认端口（49100 / 47998），参见[服务器部署与复现](09-server-deploy.md)。

## 第五步：启动网页容器

再启动只属于你的网页查看器容器，浏览器端口按工位自动推导（查看器镜像默认监听 8210，这里通过覆盖启动命令让它监听属于你的端口）：

```bash
sudo docker run -d --name so101-web-sz03 --network host \
  so101-viewer sh -c "./node_modules/.bin/vite preview --host --port 8210"
```

## 第六步：进入仿真容器并启动仿真

先进入属于你的仿真容器：

```bash
sudo docker exec -it so101-sim-sz03 bash
```

进入后，在容器里启动仿真（命令已带录制参数，启动后即可遥操作 + 按 S 录制；`sim_to_real_so101` 模块和 `/workspace` 目录只存在于此容器内，宿主机上没有）：

```bash
cd /workspace/Sim-to-Real-SO-101-Workshop
/isaac-sim/python.sh -m sim_to_real_so101.scripts.lerobot_agent \
    --task Lerobot-So101-Teleop-Vials-To-Rack --num_envs 1 \
    --robot_id R07252801 --livestream 1 \
    --leader_tcp_port 18765
```

启动后仿真会加载场景、等待主臂动作并串流画面。命令跑起来后，去下一步的浏览器链接看画面；日志里 `fresh actions received`、`network_actions` 持续增长，即说明主臂动作已进入仿真。

## 第七步：启动本机仿真

:::{important}
第一步的 `leader_server.py` 还在**前台运行**，别关它。请**新开一个终端**，进入本机仿真容器，再启动仿真。
:::

本机有 GPU 的场景跳过服务器：进入你本机的仿真容器后直接启动仿真（不需要 SSH 隧道）：

```bash
cd /workspace/Sim-to-Real-SO-101-Workshop
/isaac-sim/python.sh -m sim_to_real_so101.scripts.lerobot_agent \
    --task Lerobot-So101-Teleop-Vials-To-Rack --num_envs 1 \
    --robot_id R07252801 --livestream 1 \
    --leader_tcp_port 18765
```

## 第八步：观看与跟随检查

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

第六步的启动命令已带录制参数（`--repo_id` / `--repo_root` / `--task_name`），仿真跑起来后直接用下面的按键控制录制，无需停止重启。

录制控制的按键：

- **S**：开始/停止录制一条示范
- **C**：取消当前录制（录错了用）
- **R**：重置环境（同时停止录制）

## 下课：有序停止

按顺序停，不要乱 kill：

1. 先在**仿真容器里**按 Ctrl+C 停止遥操作。
2. 再关闭 SSH 隧道。
3. 最后停掉你笔记本上的 `leader_server.py`。
4. 需要时停掉属于你的两个容器：`sudo docker rm -f so101-sim-<你的工位> so101-web-<你的工位>`。

## 关键要点

- 链路：**主臂 → leader_server.py → SSH 隧道 → 服务器仿真 → 浏览器 WebRTC**。
- 你只负责读主臂和看画面，仿真吃显卡的部分全在服务器。
- 服务器上**每个工位一套** `so101-sim-<工位>` + `so101-web-<工位>` 容器；网页端口和隧道端口按工位自动错开。多工位 WebRTC 信令 / 媒体端口隔离需要教师按工位构建镜像，参见[服务器部署与复现](09-server-deploy.md)。
- 浏览器里按 **R** 重置、**S** 录制、**C** 取消。
- 停止时按「仿真 → 隧道 → 采集」的顺序，避免误杀进程。