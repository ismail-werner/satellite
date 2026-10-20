"""Simulated satellite + flight software. Stdlib only.

Run: python sat.py   (listens on 127.0.0.1:9000, 1 tick/sec, 1 tick = 60 s of sim time)
Protocol: newline-delimited JSON. Sat -> ground: {"type":"tm",...} / {"type":"ack",...}
          Ground -> sat: {"cmd":"SET_MODE","arg":"SAFE"}
"""
import json, math, socket, threading, time

DT = 60                 # sim seconds per tick
ORBIT_S = 5520          # ~92 min LEO
ECLIPSE_FRAC = 0.38     # fraction of orbit in Earth's shadow
BATT_WH = 100.0
SOLAR_W, BUS_W, PAYLOAD_W = 40.0, 15.0, 30.0
SAFE_BELOW, RECOVER_ABOVE = 20.0, 60.0   # battery % thresholds
MAX_TEMP = 45.0


class Sat:
    def __init__(self):
        self.t = 0.0
        self.batt = 100.0   # percent
        self.temp = 20.0
        self.mode = "NOMINAL"
        self.payload = True
        self.faults = []
        self.log = []

    # --- environment (the "physics" the flight software reacts to) ---
    def phase(self):
        return (self.t % ORBIT_S) / ORBIT_S

    def eclipse(self):
        return self.phase() > 1 - ECLIPSE_FRAC

    def position(self):
        ang = 2 * math.pi * self.phase()
        lat = 51.6 * math.sin(ang)
        lon = (math.degrees(ang) - self.t * 360 / 86164 + 180) % 360 - 180
        return lat, lon

    # --- flight software ---
    def event(self, msg):
        self.log.append(f"t+{int(self.t)}s {msg}")
        self.log = self.log[-50:]

    def set_mode(self, mode):
        if mode != self.mode:
            self.event(f"mode {self.mode} -> {mode}")
            self.mode = mode
        if mode == "SAFE":
            self.payload = False

    def step(self):
        self.t += DT
        sun = 0.0 if self.eclipse() else SOLAR_W
        load = BUS_W + (PAYLOAD_W if self.payload else 0)
        self.batt = max(0.0, min(100.0, self.batt + (sun - load) * (DT / 3600) / BATT_WH * 100))
        target = (-20 if self.eclipse() else 25) + (20 if self.payload else 0)
        self.temp += (target - self.temp) * 0.05
        # fault detection -> autonomous safing
        if self.batt < SAFE_BELOW and self.mode != "SAFE":
            self.faults.append("LOW_BATTERY")
            self.set_mode("SAFE")
        if self.temp > MAX_TEMP and self.mode != "SAFE":
            self.faults.append("OVERTEMP")
            self.set_mode("SAFE")
        if self.mode == "SAFE" and self.batt > RECOVER_ABOVE and not self.faults:
            self.set_mode("NOMINAL")
        self.sun, self.load = sun, load

    def command(self, cmd, arg=None):
        if cmd == "PING":
            return "PONG"
        if cmd == "SET_MODE" and arg in ("NOMINAL", "SAFE"):
            if arg == "NOMINAL" and self.batt < SAFE_BELOW:
                return "REJECTED: battery too low"
            self.set_mode(arg)
            return f"MODE={arg}"
        if cmd == "PAYLOAD" and arg in ("ON", "OFF"):
            if arg == "ON" and self.mode == "SAFE":
                return "REJECTED: in SAFE mode"
            self.payload = arg == "ON"
            self.event(f"payload {arg}")
            return f"PAYLOAD={arg}"
        if cmd == "CLEAR_FAULTS":
            self.faults.clear()
            return "FAULTS CLEARED"
        return f"REJECTED: unknown command {cmd} {arg}"

    def telemetry(self):
        lat, lon = self.position()
        return {"type": "tm", "t": self.t, "mode": self.mode, "battery": round(self.batt, 2),
                "temp": round(self.temp, 2), "solar_w": getattr(self, "sun", SOLAR_W),
                "load_w": getattr(self, "load", BUS_W + PAYLOAD_W), "eclipse": self.eclipse(),
                "payload": self.payload, "lat": round(lat, 2), "lon": round(lon, 2),
                "faults": self.faults, "log": self.log[-8:]}


def main(host="127.0.0.1", port=9000, tick=1.0):
    sat, lock, clients = Sat(), threading.Lock(), []

    def send(conn, obj):
        conn.sendall((json.dumps(obj) + "\n").encode())

    def serve(conn):
        for line in conn.makefile():
            try:
                c = json.loads(line)
                with lock:
                    reply = sat.command(c.get("cmd"), c.get("arg"))
                send(conn, {"type": "ack", "cmd": c.get("cmd"), "arg": c.get("arg"), "reply": reply})
            except Exception as e:
                send(conn, {"type": "ack", "reply": f"ERROR {e}"})
        clients.remove(conn)

    srv = socket.create_server((host, port))
    threading.Thread(target=lambda: [(lambda c: (clients.append(c), threading.Thread(target=serve, args=(c,), daemon=True).start()))(srv.accept()[0]) for _ in iter(int, 1)], daemon=True).start()
    print(f"satellite up on {host}:{port}")
    while True:
        with lock:
            sat.step()
            tm = sat.telemetry()
        for c in list(clients):
            try:
                send(c, tm)
            except OSError:
                clients.remove(c)
        time.sleep(tick)


if __name__ == "__main__":
    main()
