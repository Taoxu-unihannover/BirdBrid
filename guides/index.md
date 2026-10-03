# SO-101 Sim-to-Real 集中算力实训

欢迎参加本次实训。你将亲手操作一台 SO-101 机械臂，经历一条完整的 **sim-to-real（仿真到真实）** 工作流：从接线、校准、遥操作，到连接服务器上的仿真与 AI 大模型，最终让机器人在真实世界里自动抓取试管、放入试管架。

:::{figure} images/so101_vial_to_rack_task.gif
:alt: SO-101 机器人自动完成「抓取试管放入试管架」
:width: 100%

SO-101 机器人自主完成「从桌面抓取试管到放入试管架」的任务。
:::


## 学习目标

完成这门课后，你将能够：

- **接线并校准**一台 SO-101 机械臂和它的遥操作臂
- 用遥操作臂**遥控**（主从跟随）机械臂，并正确配置两台相机
- 通过浏览器连接服务器上的**仿真环境**，进行遥操作和数据采集
- 理解 **GR00T 视觉-语言-动作模型**，并亲手「部署推理服务、调用接口」
- 在真实机械臂上运行**策略评估**，亲眼观察 sim-to-real 鸿沟
- 掌握常见故障的**排查方法**和安全操作规范

```{toctree}
:caption: 第一部分 · 认识任务
:maxdepth: 2
:hidden:

01-overview
```

```{toctree}
:caption: 第二部分 · 动手接线与操作
:maxdepth: 2
:hidden:

02-setup
03-calibration
04-teleop
```

```{toctree}
:caption: 第三部分 · 仿真、推理与真机评估
:maxdepth: 2
:hidden:

05-sim-teleop
06-inference
07-real-eval
```

```{toctree}
:caption: 参考资料
:maxdepth: 2
:hidden:

08-troubleshooting
09-server-deploy
appendix
```