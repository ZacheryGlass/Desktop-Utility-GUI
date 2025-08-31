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
    parser = argparse.ArgumentParser(description="Test: single choices argument")
    parser.add_argument("--device", choices=["speakers", "headphones", "hdmi"],
                        help="Output device to route audio to")
    parser.add_argument("--volume", type=int, default=50,
                        help="Volume percent (0-100)")
    args = parser.parse_args()

    msg = f"device={args.device}, volume={args.volume}"
    popup("Choices Single", msg)
    print(json.dumps({"success": True, "message": msg}))


if __name__ == "__main__":
    main()

