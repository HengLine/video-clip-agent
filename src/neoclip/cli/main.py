"""CLI entry point — argparse-based command routing."""

import argparse
from neoclip.cli.commands import handle_command
from neoclip.cli.renderer import render_response
from neoclip.logger import info


def main():
    parser = argparse.ArgumentParser(description="NeoClip — Video Mix Clip Agent CLI")
    parser.add_argument("command", nargs="?", default="help", help="Command to execute")
    parser.add_argument("--session", "-s", type=str, help="Session ID")
    parser.add_argument("--input", "-i", type=str, help="Input text or file path")
    args = parser.parse_args()

    info(f"CLI command: {args.command}")
    response = handle_command(args.command, session_id=args.session, user_input=args.input)
    render_response(response)


if __name__ == "__main__":
    main()
