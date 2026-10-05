# 机械臂校准

本章完成主臂（leader）和从臂（follower）两台臂的**校准**。

校准的意义：让「主臂和从臂处在相同的物理姿态时，读出来的关节数值也一致」。没有校准，策略就无法准确控制机械臂，还可能带来危险。

:::{dropdown} 动手前你需要准备什么？
- 已完成[接线](02-setup.md)，主臂、从臂都通电并连到你的笔记本
- 已经设置好 `TELEOP_PORT / TELEOP_ID / ROBOT_PORT / ROBOT_ID` 这些变量
- 机械臂周围有足够的活动空间，线缆不会被钩住
:::

:::{note}
本章所有命令都在**客户端容器内**执行。先进入容器：`sudo docker exec -it so101-client bash`。`$TELEOP_PORT`、`$ROBOT_PORT` 等变量也要在容器里设置（每次新开容器终端后重新 `export`，方法见[第 2 章](02-setup.md)）。
:::

## 学习目标

在本章结束时，你将能够：

- 说出校准包含哪两步（中位偏移 + 完整运动范围）
- 正确地完成主臂、从臂的校准流程
- 判断校准结果是否合格

## 校准到底在做什么？

校准分为两步，脚本会一步步引导你：

1. **摆到中间位置**：把每个关节手动摆到行程中间，让脚本知道"中位"在哪。
2. **扫过完整行程**：把每个关节从一端转到另一端，让脚本记录下该关节的最小值和最大值。

:::{note}
校准**不等于**开机姿态，也不会改变仿真里的摆放。它的产物是一个「校准文件」，记录每个关节的数值范围和对应关系。
:::

## 校准主臂（leader）

1. 先托住主臂，避免它突然动。然后运行：

```bash
lerobot-calibrate \
    --teleop.type=so101_leader \
    --teleop.port=$TELEOP_PORT \
    --teleop.id=$TELEOP_ID
```

2. **如果弹出提示**，让你「沿用旧校准」或「输入 c 重新校准」，请输入 `c` 再回车（表示要重新校准）。只按回车会复用旧文件。

3. 看到关于「middle of its range」的提示后，**手动把每个关节摆到中间位置**。参考下面这张图：

:::{figure} images/teleop_arm_neutral_pose.jpg
:alt: 主臂校准姿态示例
:width: 350px

主臂（leader）校准姿态：大臂接近竖直、小臂向前接近水平。
:::

:::{important}
**特别注意腕旋转关节（wrist roll）。** 这个关节几乎用满了电机的整个转动范围，如果没摆正，后面可能出现编码器上溢/下溢。注意图中夹爪把手的朝向。摆好后再按回车确认。
:::

4. 出现 `Recording positions` 后，**依次移动每个关节，走过完整的机械行程**（转到底，再转回来）：

   - 底座 → 肩 → 肘 → 腕俯仰 → 腕旋转 → 夹爪
   - 每个轴可以来回走两次，轻触端点即可
   - **被线缆挡住的位置不是真正的端点**，一定要转到机械极限
   - 这一步不要提前回车

5. 六个关节都走完后，按回车，看到 `Calibration saved` 即成功。

:::{figure} images/teleop_calibration.gif
:alt: 主臂校准流程动画
:width: 350px

主臂校准流程：先摆中间位，再依次扫到各关节行程端点。
:::

## 校准从臂（follower）

流程和主臂一样，只是命令参数换成从臂：

```bash
lerobot-calibrate \
    --robot.type=so101_follower \
    --robot.port=$ROBOT_PORT \
    --robot.id=$ROBOT_ID
```

1. 先把从臂摆到中间位置，参考下图：

::::{grid} 2
:gutter: 3

:::{grid-item-card}
:img-top: images/calibration_pose.jpg

从臂校准姿态示例
:::

:::{grid-item-card}
:img-top: images/wrist_center.jpg

特别注意腕旋转轴居中（避免编码器上溢/下溢）
:::

::::

2. 按回车开始，然后让每个关节走完完整行程（转到机械极限，别被线缆卡住）。

3. 走完后按回车，看到保存提示即成功。

:::{figure} images/full_so101_calibration.gif
:alt: 完整 SO-101 校准流程
:width: 60%

从臂完整校准流程示例：所有关节走完全部行程。
:::

## 检查校准结果

校准文件会保存在缓存目录里（如 `~/.cache/huggingface/lerobot/calibration/`）。我们提供了一个检查脚本，能把**主臂（leader）**或**从臂（follower）**的校准结果与参考数据作对比，并读取当前关节位置验证是否在合法范围内。

- 检查**从臂**：读的是 `ROBOT_PORT` / `ROBOT_ID`，请先把从臂接好并用上面的步骤校准；
- 检查**主臂**：读的是 `TELEOP_PORT` / `TELEOP_ID`，请先把主臂接好并用上面的步骤校准。

1. 设置好环境变量后运行（按你要检查的臂二选一）：

```bash
# 检查主臂（leader）
python3 ~/so101-lab/scripts/so101_check_calibration.py --arm leader

# 检查从臂（follower）
python3 ~/so101-lab/scripts/so101_check_calibration.py --arm follower
```

2. 看到输出类似（检查主臂时 `File:` 指向 `.../calibration/teleoperators/so101_leader/leader-sz03.json`；检查从臂时指向 `.../calibration/robots/so101_follower/follower-sz03.json`，其余结构相同）：

```
============================================================================
  SO101 CALIBRATION CHECK REPORT
  File:  .../calibration/robots/so101_follower/follower-sz03.json
  Stats: .../so101-lab/scripts/calibration_stats.json
============================================================================

[1] Motion Range vs Stats (threshold ±2.0σ, gripper ±8.0σ)

  Joint               Range     Mean    Std  Deviation    Offset  Status
  --------------------------------------------------------------------------
  shoulder_pan         2718     2725     32     -0.23σ      -174  ✓ PASS
  shoulder_lift        2353     2350     77     +0.04σ       710  ✓ PASS
  elbow_flex           2230     2222      9     +0.90σ     -1659  ✓ PASS
  wrist_flex           2331     2329     17     +0.11σ      -330  ✓ PASS
  wrist_roll           3857     4026    114     -1.48σ      -555  ✓ PASS
  gripper              1483     1475     33     +0.23σ      -845  ✓ PASS

[2] Live Encoder Positions

  Joint               Position    Calibrated Range     In Range
  --------------------------------------------------------------------------
  shoulder_pan            2174       857 – 3575       ✓ OK
  ...

============================================================================
  Overall: ✓ PASS — calibration looks good.
============================================================================
```

3. **确认**看到 `Overall: ✓ PASS`。如果有 `⚠ WARN`，检查对应关节的提示，必要时重新校准。

:::{tip}
如果你拿不准校准对没对，最简单的办法是：**再跑一次**。校准流程可以随时重跑，不会损坏设备。
:::

## 避坑清单

:::{warning}
- **腕旋转必须转满行程**：这是最容易出错的关节，它是 6 个关节里行程最接近满量程的一个。
- **只按回车 = 不重校**：看到"沿用旧校准"提示要输入 `c` 才真正校准。
- **别把别人的校准文件复制到自己这台臂上用**：每台臂的校准是它自己的，ID 也别混。
- **找的是机械端点，不是线缆卡住的位置**：线缆挡住会记录出错误的最小/最大值。
:::

## 关键要点

- 校准 = **中位偏移 + 完整运动范围**两步。
- 主臂用 `--teleop.type=so101_leader`，从臂用 `--robot.type=so101_follower`，两台臂独立校准。
- 腕旋转关节要特别小心，转满行程、摆正中位。
- 文件只能查明显问题，最终要靠小幅移动实测确认。