# 服务器部署与复现（教师 / 复现者）

本章面向**教师 / 复现者**，讲清服务器端怎么从离线镜像把整套环境跑起来。学员按第 2～7 章操作即可，无需读本章。

## 一、镜像与离线存档

正式培训用到 4 个 Docker 镜像，均已按**易理解的规范名**导出为离线 tar（位于 `training-class/镜像存档/`）：

| 规范镜像名 | 用途 | 大小 | 离线文件 |
|---|---|---|---|
| `so101-sim:network` | 仿真（主臂接学员笔记本，网络输入） | 69.4GB | `so101-sim-network.tar` |
| `so101-sim:usb` | 仿真（主臂直连服务器 USB） | 69.2GB | `so101-sim-usb.tar` |
| `so101-viewer` | 网页查看器（串流到 8210） | 619MB | `so101-viewer.tar` |
| `so101-infer` | GR00T 推理 | 80.5GB | `so101-infer.tar` |

## 二、加载镜像

在（新的）服务器上，把 tar 加载进 Docker。tar 已按规范名导出，加载后即为规范名，无需再改名：

```bash
sudo docker load -i 镜像存档/so101-sim-network.tar
sudo docker load -i 镜像存档/so101-sim-usb.tar
sudo docker load -i 镜像存档/so101-viewer.tar
sudo docker load -i 镜像存档/so101-infer.tar
```

加载后执行 `docker images`，应能看到 `so101-sim`、`so101-viewer`、`so101-infer` 这几个规范名。

## 三、启动容器（统一命名）

| 容器名 | 镜像 | 作用 |
|---|---|---|
| `so101-sim` | `so101-sim:network` | 仿真主程序（Isaac Sim） |
| `so101-web` | `so101-viewer` | 网页串流（浏览器 8210） |
| `so101-infer` | `so101-infer` | GR00T 推理（第 6 章） |

### 仿真容器

```bash
sudo docker run -d --name so101-sim \
  --privileged --network host --runtime nvidia \
  -v /dev:/dev \
  --entrypoint bash \
  so101-sim:network \
  -c "echo started && sleep infinity"
```

- 主臂接**学员笔记本**（网络输入）用 `so101-sim:network`。
- 主臂**直连服务器 USB** 时，把镜像换成 `so101-sim:usb`。

### 网页查看器容器

```bash
sudo docker run -d --name so101-web \
  --network host \
  -e WEB_VIEWER_PORT=8210 \
  -e ISAACSIM_HOST=127.0.0.1 \
  -e ISAACSIM_SIGNAL_PORT=49100 \
  -e ISAACSIM_STREAM_PORT=47998 \
  so101-viewer
```

### 推理容器

```bash
sudo docker run -d --name so101-infer \
  --network host --gpus all --ipc=host \
  -v /home/xutao/sim2real/models:/workspace/models \
  so101-infer \
  -c "sleep infinity"
```

进入容器后启动**批处理推理引擎**（监听 5554，攒批上限 8、窗口 6ms）：

```bash
sudo docker exec -it so101-infer bash
/Isaac-GR00T/.venv/bin/python run_batched_server.py \
    --model-path /workspace/models/aravindhs-NV/grootn16-finetune_sreetz-so101_teleop_vials_rack_left/checkpoint-10000 \
    --port 5554 --max-batch 8 --wait-ms 6
```

:::{note}
`run_batched_server.py`、`station_server.py`（工位前端壳）位于 `poc-course/deploy/`；模型 checkpoint 路径按实际存在的为准。推理的完整用法见[第 6 章](06-inference.md)。
:::

## 四、启动顺序与验证

1. 先起 `so101-web`，再起 `so101-sim`。
2. 进仿真容器启动仿真（见[第 5 章第三步](05-sim-teleop.md)）。
3. 浏览器打开 `http://<服务器IP>:8210`，看到仿真画面即「仿真 + 网页」链路通。
4. 需要真机推理时，再起 `so101-infer` 并跑 `run_batched_server.py`（见[第 6 章](06-inference.md)）。

## 五、端口规划

| 端口 | 用途 |
|---|---|
| 8210 | 网页查看器（浏览器访问） |
| 49100 | 仿真信令（WebRTC） |
| 47998 | 仿真媒体流 |
| 18765 | 主臂动作（SSH 隧道接学员端 18766） |
| 5554 | 批处理推理引擎 |
| 5555 | 单副本推理（旧串行版，仅部分场景用） |

多工位并发时，每个工位的信令/媒体端口要**错开**（如 49100-49102、47998-48000），前端壳端口也各自不同，以教师下发的工位信息表为准。