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

在（新的）服务器上，把 tar 加载进 Docker：

```bash
sudo docker load -i 镜像存档/so101-sim-network.tar
sudo docker load -i 镜像存档/so101-sim-usb.tar
sudo docker load -i 镜像存档/so101-viewer.tar
sudo docker load -i 镜像存档/so101-infer.tar
```

加载后执行 `docker images`，应能看到 `so101-sim`、`so101-viewer`、`so101-infer` 这几个规范名。

## 三、启动容器（每工位一套）

| 容器名 | 镜像 | 作用 | 启动者 |
|---|---|---|---|
| `so101-sim-<工位>` | `so101-sim:network` 或 `:usb` | 每工位一个仿真主程序（Isaac Sim） | 学员（第 5 章） |
| `so101-web-<工位>` | `so101-viewer` | 每工位一个网页串流查看器 | 学员（第 5 章） |
| `so101-infer` | `so101-infer` | GR00T 推理（全体共用） | 教师（下方） |

:::{important}
仿真容器和网页容器**已改为由学员在第 5 章自己启动**：每个工位一套 `so101-sim-<工位>` + `so101-web-<工位>`，容器名、网页端口、隧道端口、WebRTC 信令 / 媒体端口都按工位自动错开。教师只需保证镜像已按上一章（二、加载镜像）加载好、查看器镜像按工位构建（见「五、端口规划」）。学员侧完整命令见[第 5 章](05-sim-teleop.md)。
:::

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

1. 教师先起 `so101-infer` 并跑 `run_batched_server.py`（见[第 6 章](06-inference.md)）。
2. 每个学员按[第 5 章](05-sim-teleop.md)自己启动属于本工位的 `so101-sim-<工位>` 与 `so101-web-<工位>`，并进仿真容器启动仿真。
3. 学员浏览器打开 `http://<服务器IP>:<工位网页端口>`，看到仿真画面即「仿真 + 网页」链路通。

## 五、端口规划（多工位）

以工位序号 `n`（`sz01` 即 `n=1`）推导，每工位一套独立端口：

| 类别 | 规则 | 例：sz03（n=3） |
|---|---|---|
| 推理前端壳 | `5600 + n` | 5603 |
| 网页查看器（浏览器） | `8200 + n` | 8203 |
| 服务器主臂隧道 | `18700 + n` | 18703 |
| WebRTC 信令（TCP） | `49100 + (n−1)×10` | 49120 |
| WebRTC 媒体（UDP） | `47998 + (n−1)×10` | 48018 |
| 批处理推理后端 | `5500`（全体共用） | 5500 |

:::{warning}
**多工位是否成立，取决于每个仿真实例能否绑定到各自的 WebRTC 信令 / 媒体端口。** 官方 Isaac Sim 6.0 影像通过 `ISAACSIM_SIGNAL_PORT` / `ISAACSIM_STREAM_PORT` 环境变量支持（映射到 `omni.kit.livestream.app` 的 `primaryStream/signalPort`、`streamPort`）。请在真实服务器上确认本项目 `so101-sim` 影像的版本与端口机制：若影像为 Isaac Sim 5.0，其原生 livestream（`--/app/livestream/port`）是否支持改端口需另行验证，否则 8 工位并发的串流隔离无法成立。

另需注意：每个 Isaac Sim 实例同一时刻只服务**一个**浏览器连接；每个工位的查看器也必须对准本工位的信令 / 媒体端口。若查看器镜像在**构建期**固化了信令 / 媒体端口（而非运行时用 `-e` 读取），则需为每个工位预先构建一份对应端口的查看器镜像，再让学员按工位启动对应镜像。
:::