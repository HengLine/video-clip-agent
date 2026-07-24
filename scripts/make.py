"""
@FileName: make.py.py
@Description: Python 版本的构建脚本
@Author: HiPeng
@Time: 2026/4/26 22:12
"""
import subprocess
import sys


def run_command(cmd):
    print(f">>> {cmd}")
    subprocess.run(cmd, shell=True, check=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python make.py [install|test|format|clean]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "install-dev":
        run_command("pip install -e .[dev]")
    elif command == "test":
        run_command("pytest tests/ -v --cov=neoclip")
    elif command == "format":
        run_command("black src/ tests/")
        run_command("ruff check --fix src/ tests/")
    elif command == "clean":
        run_command("rmdir /s /q build dist 2>nul")
    else:
        print(f"未知命令: {command}")