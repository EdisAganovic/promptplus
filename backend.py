"""Local HTTP service and keyboard worker launched by the Electron desktop app."""

import json
import secrets
import sys
import threading

import uvicorn

from app.api import app
from app.replacer import RealtimeTextReplacer


class DesktopServer(uvicorn.Server):
    async def startup(self, sockets=None):
        await super().startup(sockets=sockets)
        if self.started:
            port = self.servers[0].sockets[0].getsockname()[1]
            print(json.dumps({"event": "ready", "port": port,
                              "token": app.state.desktop_token}), flush=True)


def read_desktop_commands(server, replacer):
    for line in sys.stdin:
        try:
            command = json.loads(line)
            if command.get("type") == "paste" and isinstance(command.get("keyword"), str):
                threading.Thread(target=replacer.paste_prompt,
                                 args=(command["keyword"],), daemon=True).start()
            elif command.get("type") == "shutdown":
                break
        except (ValueError, TypeError) as exc:
            print(f"Invalid desktop command: {exc}", file=sys.stderr, flush=True)
    server.should_exit = True
    replacer.stop_monitoring()


def main():
    app.state.desktop_token = secrets.token_urlsafe(32)
    replacer = RealtimeTextReplacer()
    monitor = threading.Thread(target=replacer.start_monitoring, daemon=True)
    monitor.start()

    config = uvicorn.Config(app, host="127.0.0.1", port=0, log_level="warning")
    server = DesktopServer(config)
    commands = threading.Thread(target=read_desktop_commands,
                                args=(server, replacer), daemon=True)
    commands.start()
    try:
        server.run()
    finally:
        replacer.stop_monitoring()


if __name__ == "__main__":
    main()
