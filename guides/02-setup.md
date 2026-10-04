# 环境与接线

本章把设备和软件准备好。做完本章，你的笔记本能「看到」机械臂、遥操作臂和两台相机，为后面的校准、遥操作打基础。

:::{dropdown} 你在动手前需要准备什么？
- 你的东芝笔记本（Ubuntu 系统，已装好）
- SO-101 主臂（leader）、从臂（follower）各一台，配套电源、USB 线
- 两台 USB 相机（一个装在机械臂腕部 = wrist，一个固定在外侧 = front）
- 教师下发的**工位信息表**

工位信息表长这样（示例，值以你拿到的那张为准）：

| 项目 | 示例值 | 说明 |
|---|---|---|
| 服务器 IP | 192.168.1.6 | 仿真/推理都在这里 |
| 仿真网页地址 | http://192.168.1.6:8210 | 浏览器打开看仿真 |
| 你的工位号 | s03 | 用来命名端口 |
| 你的前端壳端口 | 5582 | 第 6 章部署推理服务用 |
:::

## 学习目标

在本章结束时，你将能够：

- 安全地**接好**所有电源和 USB 线，且不搞混
- 用命令**找到**主臂、从臂各自对应的串口
- 用命令**识别**两台相机，分清哪个是 wrist、哪个是 front
- 准备好本机的 LeRobot 客户端环境

## 第一步：接线（先断电接，再通电）

:::{warning}
**主臂用 5V 电源，从臂用 12V 电源。千万不要搞混！** 建议在线缆上贴标签或用不同颜色区分。搞混可能烧坏设备。
:::

按下面顺序来：

1. **先不接电**，把从臂（follower）和主臂（leader）用 USB 线接到你的笔记本上。
2. 把两台相机也插到笔记本的 USB 口。
3. 分别接上主臂、从臂的**各自电源**。
4. 确认机器人背面控制板上的**电源 LED 亮起**。

:::{tip}
USB 只负责「通信」，**电机需要单独的电源才有力气动**。如果后面运行时报"所有电机都找不到"（Missing motor IDs），八成是电源没接或没通电。
:::

## 第二步：准备本机 LeRobot 环境（容器）


:::{note}
如果 `docker` 还没装，请先按教师指引安装并确保能用 `sudo docker`。进入容器后 `lerobot-find-cameras`、`lerobot-calibrate` 等命令能跑，就说明环境就绪，无需再装任何包。
:::


```bash
# 1) 建一个工作目录，本课程所有内容都放这里，避免散落在 home 目录下
mkdir -p ~/so101-lab/scripts
cp ~/so101-lab/BridSimReal/runtime/* ~/so101-lab/scripts/

# 2) 启动客户端容器（每次开机后启动一次即可）
sudo docker run -d --name so101-client \
  --privileged --network host \
  -v ~/so101-lab:/root/so101-lab \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  so101-client:latest sleep infinity
```

- `--privileged --network host`：让容器能访问你的 USB 串口和相机。
- `-v ~/so101-lab:/root/so101-lab`：把你本机的工作目录挂进容器；容器里的 `~/so101-lab` 和本机是**同一个目录**。
- `-v ~/.cache/huggingface:/root/.cache/huggingface`：对齐校准文件的存放位置，容器内外校准结果一致。

### 进入容器

本节之后的命令，都在容器里执行

```bash
sudo docker exec -it so101-client bash
```

进入后提示符会变成容器里的 shell。敲 `lerobot --help` 或 `lerobot-find-cameras opencv` 验证一下环境可用。

## 第三步：找到主臂和从臂的串口

USB 设备每次插拔，系统分配给它的名字（如 `/dev/ttyACM0`）**可能会变**。所以每次开始前，都要重新确认。

1. 在**容器内**的终端执行：

```bash
ls -l /dev/ttyACM* /dev/ttyUSB*
```

会看到类似：

```
crw-rw---- 1 root dialout 166, 0  9月 28 10:00 /dev/ttyACM0
crw-rw---- 1 root dialout 166, 1  9月 28 10:00 /dev/ttyACM1
```

2. 有两台臂，通常会有两个串口。用下面这个工具确认哪个是主臂、哪个是从臂：

```bash
lerobot-find-port
```

它会让你**拔掉其中一条 USB 线再按回车**，从而判断哪条线对应哪个设备。跟着提示做，记下结果：

```bash
# 记住这两个值（示例，按你的实际输出改）
export TELEOP_PORT=/dev/ttyACM0   # 主臂（leader）
export TELEOP_ID=R07252801        # 主臂的校准 ID

export ROBOT_PORT=/dev/ttyACM1    # 从臂（follower）
export ROBOT_ID=R07252801         # 从臂的校准 ID（每台臂独立）
```

:::{tip}
`ID` 决定校准结果存在哪里。同一台臂每次用**同一个 ID**，校准结果就能在不同次启动间复用。如果换了一台臂，就换一个新 ID，别把别人的校准文件拿来用在自己的臂上。
:::

## 第四步：识别两台相机

策略靠两台相机看世界，**相机分配错了，策略一定会失败**（把腕部相机当成外部相机，或反过来，都会翻车）。

1. 在**容器内**的终端执行：

```bash
lerobot-find-cameras opencv
```

它会抓到所有相机的画面并保存下来，输出类似：

```
Found 3 cameras:
  Camera 0: /dev/video0 (USB 2.0 Camera)
  Camera 1: /dev/video2 (USB 2.0 Camera)
  Camera 2: /dev/video4 (Integrated Webcam)
```

2. 打开保存图片的目录，一张张看图，判断：
   - **wrist（腕部相机）**：装在机械臂夹爪旁边的那个，画面离夹爪很近。
   - **front（外部相机）**：固定在三脚架/外侧，看整个工作区全貌的那个。
   - 笔记本自带的摄像头（Integrated Webcam）不是我们要用的，排除掉。

```bash
# 记住这两个索引（示例，按你的实际输出改）
export CAMERA_WRIST=0     # 腕部相机索引
export CAMERA_FRONT=2     # 外部相机索引
```

:::{warning}
**相机索引在拔插后会变！** 每次采集数据或运行策略前，都要重新跑一次 `lerobot-find-cameras opencv` 确认。

如果你发现策略行为很怪（像在"瞎抓"），相机索引被重排是最常见的原因之一。
:::

## 第五步：确认你的输出

最后自查一遍：

```bash
echo "TELEOP_PORT=$TELEOP_PORT  TELEOP_ID=$TELEOP_ID"
echo "ROBOT_PORT=$ROBOT_PORT    ROBOT_ID=$ROBOT_ID"
echo "CAMERA_WRIST=$CAMERA_WRIST  CAMERA_FRONT=$CAMERA_FRONT"
```

:::{tip}
把这些值记在一张纸上或记事本里。关闭终端后环境变量会丢失，但你有了这些数字就能随时重新设置。
:::

## 关键要点

- **先断电接线，再通电**；主臂 5V、从臂 12V 绝不能混。
- 串口名（`/dev/ttyACM*`）会变，每次开始前用 `lerobot-find-port` 重新确认。
- 相机用 `lerobot-find-cameras opencv` 抓图识别，**wrist 和 front 别插反**。
- 本机只需要 LeRobot 客户端环境，不装模型、不需要显卡。