#!/usr/bin/env python3
"""后端批处理推理引擎（教师部署，一份，真正持有模型）。

把多个工位前端壳转发的观测攒成一个 batch，一次前向服务多路，吃满 GPU。
用 ZeroMQ ROUTER 收多路请求，按连接身份回发各工位拆出的动作，天然不串台。

用法（在推理容器 real-robot:so101 内）：
    /Isaac-GR00T/.venv/bin/python run_batched_server.py \
        --model-path /workspace/models/<org>/<repo>/<checkpoint> [--port 5500] [--max-batch 8] [--wait-ms 6]

实测依据（5090 32GB，640×480 双相机，batch=1 前向 ~51ms）：
    batch=8 一次前向 ~149ms，均摊每路 18.7ms，吞吐从串行 ~19 req/s 提到 ~40 req/s，
    8 路并发 p95 从单副本串行的 ~436ms 降到 ~154ms（接近 150ms 验收线）。
"""

import time
from dataclasses import dataclass

import numpy as np
import tyro
import zmq

from gr00t.data.embodiment_tags import EmbodimentTag
from gr00t.policy.gr00t_policy import Gr00tPolicy
from gr00t.policy.server_client import MsgSerializer


@dataclass
class Config:
    model_path: str
    port: int = 5500
    host: str = "0.0.0.0"
    max_batch: int = 8      # 攒批上限；batch 越大吞吐越高，但也抬高单个请求的等待
    wait_ms: int = 6        # 攒批窗口毫秒数；越大越容易攒满，但增加边界等待
    device: str = "cuda"


def merge_observations(obs_list):
    """把 N 份 B=1 的观测沿 batch 维拼成 B=N 的一份。"""
    video = {k: np.concatenate([o["video"][k] for o in obs_list], axis=0) for k in obs_list[0]["video"]}
    state = {k: np.concatenate([o["state"][k] for o in obs_list], axis=0) for k in obs_list[0]["state"]}
    language = {k: [o["language"][k][0] for o in obs_list] for k in obs_list[0]["language"]}
    return {"video": video, "state": state, "language": language}


def main(cfg: Config):
    policy = Gr00tPolicy(
        embodiment_tag=EmbodimentTag.NEW_EMBODIMENT,
        model_path=cfg.model_path,
        device=cfg.device,
        strict=True,
    )

    ctx = zmq.Context()
    sock = ctx.socket(zmq.ROUTER)
    sock.bind(f"tcp://{cfg.host}:{cfg.port}")
    print(f"批处理引擎就绪: {cfg.host}:{cfg.port}  max_batch={cfg.max_batch}  wait={cfg.wait_ms}ms")

    while True:
        # 阻塞等第一个请求；前端壳用 REQ 发来，ROUTER 收 3 帧 [identity, empty, payload]
        parts = sock.recv_multipart()
        pending = [(parts[0], MsgSerializer.from_bytes(parts[2]))]

        # 攒批窗口：尽量攒满 max_batch，超时则用当前已收到的跑
        t0 = time.time()
        while len(pending) < cfg.max_batch and (time.time() - t0) * 1000 < cfg.wait_ms:
            if sock.poll(2):
                parts = sock.recv_multipart()
                pending.append((parts[0], MsgSerializer.from_bytes(parts[2])))

        # 一次前向处理整个 batch
        observations = [req["data"]["observation"] for _, req in pending]
        actions, info = policy.get_action(merge_observations(observations))

        # 按 batch 维拆回各工位，沿各自身份回发
        for j, (ident, _) in enumerate(pending):
            action_j = {k: v[j : j + 1] for k, v in actions.items()}
            sock.send_multipart([ident, b"", MsgSerializer.to_bytes([action_j, info])])


if __name__ == "__main__":
    main(tyro.cli(Config))