import argparse
import json

try:
    import ctypes
    def popup(title, message):
        try:
            ctypes.windll.user32.MessageBoxW(None, str(message), str(title), 0x40)
        except Exception:
            print(str(message))
except Exception:
    def popup(title, message):
        print(str(message))


def main():
    parser = argparse.ArgumentParser(description="Test: required string and number arguments")
    parser.add_argument("--label", type=str, required=True, help="A required string label")
    parser.add_argument("--count", type=int, required=True, help="A required integer count")
    parser.add_argument("--threshold", type=float, default=0.5, help="Optional float threshold")
    args = parser.parse_args()

    msg = f"label={args.label}, count={args.count}, threshold={args.threshold}"
    popup("Required Str+Num", msg)
    print(json.dumps({"success": True, "message": msg}))


if __name__ == "__main__":
    main()

