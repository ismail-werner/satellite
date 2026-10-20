from sat import Sat


def test_safe_mode_and_recovery():
    s = Sat()
    for _ in range(600):
        s.step()
        if s.mode == "SAFE":
            break
    assert s.mode == "SAFE" and not s.payload and "LOW_BATTERY" in s.faults
    assert s.command("PAYLOAD", "ON").startswith("REJECTED")
    s.command("CLEAR_FAULTS")
    for _ in range(600):
        s.step()
    assert s.mode == "NOMINAL" and s.batt > 60


if __name__ == "__main__":
    test_safe_mode_and_recovery()
    print("ok")
