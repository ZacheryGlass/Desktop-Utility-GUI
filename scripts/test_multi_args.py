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
    parser = argparse.ArgumentParser(description="Test: multiple argument types")
    parser.add_argument("--name", type=str, required=True, help="Your name")
    parser.add_argument("--age", type=int, default=30, help="Age in years")
    parser.add_argument("--ratio", type=float, default=0.75, help="A float ratio")
    parser.add_argument("--confirm", choices=["yes", "no"], default="yes", help="Confirmation choice")
    args = parser.parse_args()

    msg = f"name={args.name}, age={args.age}, ratio={args.ratio}, confirm={args.confirm}"
    popup("Multi Args", msg)
    print(json.dumps({"success": True, "message": msg}))


if __name__ == "__main__":
    main()

