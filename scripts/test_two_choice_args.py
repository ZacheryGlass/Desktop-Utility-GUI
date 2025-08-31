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
    parser = argparse.ArgumentParser(description="Test: two choices arguments for autogen")
    parser.add_argument("--theme", choices=["light", "dark", "system"], default="system",
                        help="Theme preference")
    parser.add_argument("--quality", choices=["low", "medium", "high"], default="medium",
                        help="Quality preset")
    args = parser.parse_args()

    msg = f"theme={args.theme}, quality={args.quality}"
    popup("Two Choice Args", msg)
    print(json.dumps({"success": True, "message": msg}))


if __name__ == "__main__":
    main()

