#!/usr/bin/env python3
"""工位推理前端壳（学员部署）。

学员在自己的工位上启动本服务，体验完整的「部署服务 → 监听端口 → 转发请求 → 返回动作」流程。
本进程不加载模型权重（模型由教师部署的后端批处理引擎统一持有），因此 8 个工位可同时各起一个前端壳，互不争抢 GPU。

用法：
    python station_server.py <station_id> <port> [backend]

示例（sz03 工位，对外 5603，后端在教师机）：
    python station_server.py sz03 5603 tcp://192.168.1.6:5500

链路：
    学员评估客户端(REQ，如 so101_eval.py) ──▶ 本服务(REP) ──▶ 后端批处理引擎(ROUTER)
        ◀──────────────────── 动作（仅本工位的那一份）────────────────────┘
"""

import sys

import zmq

# 复用 GR00T 的 msgpack 序列化协议，确保与服务端/客户端编码一致
sys.path.insert(0, "/Isaac-GR00T")
from gr00t.policy.server_client import MsgSerializer


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    station_id = sys.argv[1]        # 例如 sz03
    port = int(sys.argv[2])         # 本工位对外端口
    backend = sys.argv[3] if len(sys.argv) > 3 else "tcp://127.0.0.1:5500"

    ctx = zmq.Context()

    # 对外：学员的评估客户端用 REQ 连这里，故本侧必须用 REP 配对。
    front = ctx.socket(zmq.REP)
    front.bind(f"tcp://0.0.0.0:{port}")

    # 对内：连教师部署的后端批处理引擎（ROUTER），本侧用 REQ 配对。
    back = ctx.socket(zmq.REQ)
    back.connect(backend)

    print(f"[{station_id}] 前端壳已部署：监听 {port}，后端 {backend}")

    while True:
        # 1) 收学员发来的观测（已 msgpack 编码）
        observation = MsgSerializer.from_bytes(front.recv())

        # 2) 转发给后端批处理引擎；请求结构与服务端 get_action 端点一致
        back.send(MsgSerializer.to_bytes({
            "endpoint": "get_action",
            "data": {"observation": observation, "options": None},
        }))

        # 3) 收后端返回的、属于本工位的那一份动作
        response = MsgSerializer.from_bytes(back.recv())

        # 4) 回给学员客户端
        front.send(MsgSerializer.to_bytes(response))


if __name__ == "__main__":
    main()