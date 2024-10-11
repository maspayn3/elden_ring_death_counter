from mss import mss

def print_monitor_specs():
    with mss() as sct:
        for i, monitor in enumerate(sct.monitors):
            print(f"Monitor {i}:")
            print(f"  Top: {monitor['top']}")
            print(f"  Left: {monitor['left']}")
            print(f"  Width:{monitor['width']}")
            print(f"  Height: {monitor['height']}")
            print()

        print("Note: Monitor 0 typically represents the entire virtual screen.")

if __name__ == "__main__":
    print_monitor_specs()
