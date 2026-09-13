const WEB_SOCKET_ROUTE = "/ws";
const COUNT_ROUTE = /^\/rooms\/([^/]+)\/count$/;

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function hasValidKey(request, env) {
  if (!env.SIGNALING_KEY) return true;
  const key = new URL(request.url).searchParams.get("key");
  return key === env.SIGNALING_KEY;
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    if (!hasValidKey(request, env)) {
      return json({ error: "unauthorized" }, 401);
    }

    if (url.pathname === "/") {
      return json({
        service: "meeet-signaling",
        ws: "/ws?room=NAME&peer=ID",
        count: "/rooms/NAME/count",
      });
    }

    const countMatch = url.pathname.match(COUNT_ROUTE);
    if (countMatch && request.headers.get("Upgrade") !== "websocket") {
      const stub = env.SIGNALING_ROOM.get(
        env.SIGNALING_ROOM.idFromName(countMatch[1])
      );
      return stub.fetch(request);
    }

    if (
      url.pathname === WEB_SOCKET_ROUTE &&
      request.headers.get("Upgrade") === "websocket"
    ) {
      const room = url.searchParams.get("room");
      if (!room || !room.trim()) {
        return json({ error: "room query param is required" }, 400);
      }
      const stub = env.SIGNALING_ROOM.get(env.SIGNALING_ROOM.idFromName(room));
      return stub.fetch(request);
    }

    return json({ error: "not found" }, 404);
  },
};

export class SignalingRoom {
  constructor(state, env) {
    this.state = state;
    this.connections = new Map();
  }

  async fetch(request) {
    const url = new URL(request.url);

    if (url.pathname.endsWith("/count")) {
      return json({
        room: url.pathname.split("/")[2],
        peers: [...this.connections.keys()],
      });
    }

    if (request.headers.get("Upgrade") !== "websocket") {
      return json({ error: "expected websocket upgrade" }, 426);
    }

    const peer =
      url.searchParams.get("peer") ||
      `peer-${crypto.randomUUID().slice(0, 8)}`;
    const [client, server] = Object.values(new WebSocketPair());

    server.accept();
    this.connections.set(peer, server);

    server.addEventListener("message", (event) => this.relay(peer, event.data));
    server.addEventListener("close", () => {
      this.connections.delete(peer);
      this.broadcast({ type: "peers", count: this.connections.size });
    });
    server.addEventListener("error", () => this.connections.delete(peer));

    this.broadcast({ type: "peers", count: this.connections.size });
    server.send(JSON.stringify({ type: "joined", peer }));

    return new Response(null, { status: 101, webSocket: client });
  }

  relay(fromPeer, data) {
    for (const [peerId, socket] of this.connections) {
      if (peerId === fromPeer) continue;
      try {
        socket.send(typeof data === "string" ? data : JSON.stringify(data));
      } catch (_) {
        this.connections.delete(peerId);
      }
    }
  }

  broadcast(message) {
    const encoded = JSON.stringify(message);
    for (const [peerId, socket] of this.connections) {
      try {
        socket.send(encoded);
      } catch (_) {
        this.connections.delete(peerId);
      }
    }
  }
}