# 附录

## 四条 sim-to-real 策略速览

本课实操了**策略 1（域随机化）**。另外三条策略用于进一步缩小 sim-to-real 鸿沟，属于**扩展阅读，现场不做实操**：

| 策略 | 一句话说明 | 解决哪类鸿沟 |
|---|---|---|
| 1. 域随机化（DR） | 训练时随机化仿真参数（光照/颜色/物理），让策略对变化更鲁棒 | 感知、物理 |
| 2. 协同训练 | 把仿真数据和少量真实数据**混起来一起训练** | 感知、执行 |
| 3. Cosmos 增强 | 用生成式模型把真实/仿真数据**扩增**得更多样 | 感知 |
| 4. SAGE + GapONet | 显式**测量并补偿**仿真与真实的执行器（关节）差异 | 执行、建模 |

## 常用命令快查

```bash
# 进入客户端容器（先导入镜像并启动容器，见第 2 章）
sudo docker exec -it so101-client bash
cd ~/so101-lab/scripts   # 或你放部署脚本的目录

# 找串口 / 找相机
lerobot-find-port
lerobot-find-cameras opencv

# 校准主臂 / 从臂
lerobot-calibrate --teleop.type=so101_leader --teleop.port=$TELEOP_PORT --teleop.id=$TELEOP_ID
lerobot-calibrate --robot.type=so101_follower --robot.port=$ROBOT_PORT --robot.id=$ROBOT_ID

# 本机读取主臂动作（供仿真用）
python3 -u leader_server.py --serial /dev/ttyACM0 --calibration R07252801.recalibrated.json

# 部署你的前端壳（<工位号> <你的端口> <后端地址>）
python station_server.py s03 5582 tcp://192.168.1.6:5554

# 看端口监听
ss -lnt | grep 5582
```

## 术语表

| 术语 | 含义 |
|---|---|
| sim-to-real | 在仿真里训练策略，再部署到真实硬件的过程 |
| sim-to-real 鸿沟 | 策略在仿真与真实中的表现差异 |
| leader / teleop | 主臂（遥控器），人手操作 |
| follower / robot | 从臂，真正执行任务 |
| wrist / front | 腕部相机 / 外部相机 |
| LeRobot | Hugging Face 开源机器人库 |
| GR00T | NVIDIA 视觉-语言-动作（VLA）模型 |
| VLA | 视觉-语言-动作模型 |
| 动作分块 | 一次预测多步动作（本课 horizon=16） |
| 批处理 | 攒多个请求一次前向，吃满 GPU 吞吐 |
| 后端引擎 | 持模型的批处理服务（全组一份） |
| 前端壳 | 每工位一个的转发服务（不持模型） |
| WebRTC | 浏览器观看仿真画面的实时串流技术 |

## 参考资源

- [NVIDIA Isaac GR00T](https://developer.nvidia.com/isaac/gr00t)
- [LeRobot 文档](https://huggingface.co/docs/lerobot)
- [课程代码仓库（原版）](https://github.com/NV-DLI/Sim-to-Real-SO-101-Workshop)