import argparse
import json
import os

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
    parser = argparse.ArgumentParser(description="Test: file and directory path arguments")
    parser.add_argument("--file", type=str, required=True, help="Path to a file (string path)")
    parser.add_argument("--dir", type=str, required=True, help="Path to a directory (string path)")
    args = parser.parse_args()

    # Basic validation (non-fatal): build a status summary
    validations = []
    validations.append(f"file_exists={'yes' if os.path.isfile(args.file) else 'no'}")
    validations.append(f"dir_exists={'yes' if os.path.isdir(args.dir) else 'no'}")

    msg = f"file={args.file}; dir={args.dir}; " + ", ".join(validations)
    popup("Path Args", msg)
    print(json.dumps({"success": True, "message": msg}))


if __name__ == "__main__":
    main()

