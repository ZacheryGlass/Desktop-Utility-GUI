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
    parser = argparse.ArgumentParser(description="Test: numeric range validation")
    parser.add_argument("--level", type=int, default=5, help="Integer level (0-10)")
    parser.add_argument("--ratio", type=float, default=0.5, help="Float ratio (0.0-1.0)")
    args = parser.parse_args()

    # Validate ranges (demonstrate failure JSON when out of bounds)
    errors = []
    if not (0 <= args.level <= 10):
        errors.append("level must be between 0 and 10")
    if not (0.0 <= args.ratio <= 1.0):
        errors.append("ratio must be between 0.0 and 1.0")

    if errors:
        msg = "; ".join(errors)
        popup("Numeric Range Error", msg)
        print(json.dumps({"success": False, "message": msg}))
        sys.exit(2)

    msg = f"level={args.level}, ratio={args.ratio}"
    popup("Numeric Ranges", msg)
    print(json.dumps({"success": True, "message": msg}))


if __name__ == "__main__":
    main()

