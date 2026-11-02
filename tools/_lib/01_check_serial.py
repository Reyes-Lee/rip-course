"""01_check_serial：量電腦和 Nano 之間的 serial 來回延遲（作者的 measure_serial_rtt.py）。"""
from __future__ import annotations

from _common import banner, finish, get_port, info, run_policy_script, wait_enter


def main() -> int:
    banner("01 Serial 延遲測試", "firmware/TestSerial", needs_rig=True)
    port = get_port()
    info(f"序列埠：{port}")
    wait_enter()
    code, _ = run_policy_script(["measure_serial_rtt.py", "--port", port])
    print()
    info("參考值：來回約 2.5 ms。明顯更慢通常是 USB 集線器或線材的問題，換一個 USB 孔或換線再試。")
    return code


if __name__ == "__main__":
    finish(main())
