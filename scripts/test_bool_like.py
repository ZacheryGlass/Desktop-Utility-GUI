import argparse
import json
import sys

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
    parser = argparse.ArgumentParser(description="Test: boolean-like via choices and numeric mix")
    # Use choices for reliable analyzer + UI combo and safe parsing
    parser.add_argument("--enabled", choices=["true", "false"], default="true",
                        help="Enable feature (true/false)")
    parser.add_argument("--count", type=int, default=1, help="Repeat count")
    args = parser.parse_args()

    msg = f"enabled={args.enabled}, count={args.count}"
    popup("Bool-like + Numeric", msg)
    print(json.dumps({"success": True, "message": msg}))


if __name__ == "__main__":
    main()

