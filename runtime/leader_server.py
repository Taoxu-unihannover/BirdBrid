"""Read SO101 leader locally; return calibrated positions over localhost TCP/SSH.
Does not write calibration or goal positions. Disables leader torque at startup.
"""
import argparse
import json
import socket
import time
import types
from pathlib import Path
import scservo_sdk as scs

JOINTS = ('shoulder_pan', 'shoulder_lift', 'elbow_flex', 'wrist_flex', 'wrist_roll', 'gripper')

def decode_sign(value, bit):
    return -(value & ~(1 << bit)) if value & (1 << bit) else value

def normalize(value, entry, gripper=False):
    low, high = entry['range_min'], entry['range_max']
    if not 0 <= low < high <= 4095 or entry['drive_mode'] != 0:
        raise ValueError('Unsupported or invalid calibration')
    fraction = (min(high, max(low, value)) - low) / (high - low)
    return fraction * 100 if gripper else fraction * 200 - 100

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial', default='/dev/ttyACM0')
    parser.add_argument('--calibration', required=True)
    parser.add_argument('--port', type=int, default=18766)
    args = parser.parse_args()
    calibration = json.loads(Path(args.calibration).read_text())
    assert set(calibration) == set(JOINTS)
    p = scs.PortHandler(args.serial)
    def timeout(self, length):
        self.packet_start_time = self.getCurrentTime()
        self.packet_timeout = self.tx_time_per_byte * (length + 3) + 50
    p.setPacketTimeout = types.MethodType(timeout, p)
    assert p.openPort() and p.setBaudRate(1000000)
    h = scs.PacketHandler(0)
    def checked(result):
        value, comm, error = result
        if comm != 0 or error != 0:
            raise RuntimeError(f'Serial error: comm={comm}, motor_error={error}')
        return value
    try:
        for index, name in enumerate(JOINTS, 1):
            entry = calibration[name]
            assert entry['id'] == index
            normalize(entry['range_min'], entry, name == 'gripper')
            assert checked(h.ping(p, index)) == 777
            for key, address in [('range_min',9),('range_max',11),('homing_offset',31)]:
                value = checked(h.read2ByteTxRx(p,index,address))
                if key == 'homing_offset': value = decode_sign(value,11)
                if value != entry[key]: raise RuntimeError(f'Calibration mismatch: {name} {key} {value} != {entry[key]}')
            comm, error = h.write1ByteTxRx(p,index,40,0)
            if comm or error: raise RuntimeError(f'Cannot disable leader torque: {index}')
        print('CALIBRATION_MATCH all 6 motors; torque disabled; no goal writes',flush=True)
        reader = scs.GroupSyncRead(p,h,56,2)
        for index in range(1,7): reader.addParam(index)
        with socket.socket() as listener:
            listener.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            listener.bind(('127.0.0.1',args.port)); listener.listen(1)
            print(f'LEADER_READY localhost:{args.port}',flush=True)
            total=0
            while True:
                conn,_=listener.accept()
                conn.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
                conn.settimeout(10)
                with conn:
                    try:
                        while True:
                            command=conn.recv(1)
                            if not command: break
                            if command != b'R': raise ValueError('Invalid request')
                            started=time.perf_counter()
                            result=reader.txRxPacket()
                            if result != scs.COMM_SUCCESS: raise RuntimeError(f'Sync read failed: {result}')
                            action={}
                            for index,name in enumerate(JOINTS,1):
                                if not reader.isAvailable(index,56,2): raise RuntimeError(f'Missing motor {index}')
                                raw=decode_sign(reader.getData(index,56,2),15)
                                action[name+'.pos']=normalize(raw,calibration[name],name=='gripper')
                            total+=1
                            response={'seq':total,'action':action,'read_ms':(time.perf_counter()-started)*1000}
                            conn.sendall(json.dumps(response,allow_nan=False).encode()+b'\n')
                            if total%300==0: print(f'READ_OK count={total} read_ms={response["read_ms"]:.2f}',flush=True)
                    except (OSError,ValueError,RuntimeError) as exc:
                        print(f'CLIENT_CLOSED {exc}',flush=True)
    finally:
        p.closePort()

if __name__=='__main__': main()
