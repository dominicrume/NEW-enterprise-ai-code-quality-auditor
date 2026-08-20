"""Flask app serving the live audit surface.

Design constraints, in priority order:
  1. One command, no arguments, no prior knowledge.
  2. Something on screen immediately — never a blank page waiting for a build.
  3. Every metric either shows a number or says plainly why it cannot.
  4. Streams over Server-Sent Events: no websocket dependency, and it
     reconnects on its own if the browser sleeps.
"""
from __future__ import annotations

import json
import queue
import threading
from dataclasses import asdict
from pathlib import Path

from urllib.parse import urlparse

from flask import Flask, Response, jsonify, render_template, request

from auditor.core.scan import ScanResult, scan_directory
from auditor.core.watch import watch_directory
from auditor.live.brief import build_spec, load_spec, save_spec


def _serialise(result: ScanResult, changed: list[str] | None = None) -> dict:
    return {
        "path": str(result.path),
        "name": result.path.name,
        "files": result.file_count,
        "loc": result.total_loc,
        "python_files": result.python_files,
        "spec": result.spec_name,
        "coverage_note": result.coverage_note,
        "worst_band": result.worst_band,
        "changed": changed or [],
        "metrics": [
            {
                "name": o.name, "label": o.label, "value": o.value,
                "unit": o.unit, "band": o.band, "skipped": o.skipped_reason,
            }
            for o in result.outcomes
        ],
    }


class LiveSession:
    """Owns the watch loop and fans events out to connected browsers."""

    def __init__(self, project: Path, interval: float = 1.0):
        self.project = Path(project).resolve()
        self.interval = interval
        self.spec: dict | None = load_spec(self.project)
        self._subscribers: list[queue.Queue] = []
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._restart = threading.Event()
        self.latest: ScanResult = scan_directory(self.project, self.spec)
        self._thread: threading.Thread | None = None

    # ---------------------------------------------------------------- pub/sub
    def subscribe(self) -> queue.Queue:
        q: queue.Queue = queue.Queue(maxsize=32)
        with self._lock:
            self._subscribers.append(q)
        return q

    def unsubscribe(self, q: queue.Queue) -> None:
        with self._lock:
            if q in self._subscribers:
                self._subscribers.remove(q)

    def publish(self, payload: dict) -> None:
        with self._lock:
            targets = list(self._subscribers)
        for q in targets:
            try:
                q.put_nowait(payload)
            except queue.Full:
                pass  # a stalled browser must never block the watcher

    # ----------------------------------------------------------------- watch
    def start(self) -> None:
        """Begin watching. Idempotent — a session serving a page is always live."""
        if self._thread is not None and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _loop(self) -> None:
        first = True
        while not self._stop.is_set():
            self._restart.clear()
            if not first:
                # The spec changed. Rescore from scratch: an in-flight event
                # may have been measured against the previous definition of
                # "what was asked for", and must not be trusted or published.
                self.latest = scan_directory(self.project, self.spec)
                self.publish({"type": "update", "report": _serialise(self.latest),
                              "deltas": [], "notable": False})
            first = False

            for event in watch_directory(
                self.project, self.spec, interval=self.interval,
                stop=lambda: self._stop.is_set() or self._restart.is_set(),
            ):
                if self._restart.is_set():
                    break  # scored with a stale spec — discard
                self.latest = event.result
                self.publish({
                    "type": "update",
                    "report": _serialise(event.result, event.changed_files),
                    "deltas": [
                        {**asdict(d),
                         "became_measurable": d.became_measurable,
                         "became_unmeasurable": d.became_unmeasurable,
                         "changed_band": d.changed_band,
                         "direction": d.direction}
                        for d in event.deltas
                    ],
                    "notable": event.notable,
                })
                if self._stop.is_set():
                    break

    def apply_brief(self, brief: str) -> dict:
        """Adopt a new brief: derive the spec, rescan, restart the watcher."""
        spec = build_spec(brief, name=self.project.name.replace("-", "_") or "live_session")
        path = save_spec(self.project, spec)
        self.spec = spec
        self.latest = scan_directory(self.project, spec)
        self._restart.set()  # the loop picks up the new spec on its next pass
        self.publish({"type": "update", "report": _serialise(self.latest), "deltas": [],
                      "notable": False})
        return {"spec_path": str(path), "features": len(spec["features"])}


def _same_origin(request) -> bool:
    """Reject state-changing requests that did not come from our own page.

    Binding to 127.0.0.1 keeps other machines out, but it does not keep out a
    web page the user has open in the same browser: any site can POST to
    localhost. Without this check such a page could silently rewrite the spec
    the audit is measured against. Browsers set Origin on cross-origin POSTs
    and will not let a page forge it, so comparing it to our own host is
    sufficient here.
    """
    origin = request.headers.get("Origin")
    if origin is None:                      # non-browser client (curl, tests)
        return request.headers.get("Sec-Fetch-Site") in (None, "same-origin")
    return urlparse(origin).netloc == request.host


def create_app(session: LiveSession) -> Flask:
    app = Flask(__name__, template_folder="templates")
    app.config["SESSION"] = session
    # Serving a page implies watching. Without this, forgetting start() gives
    # a page that renders once and then silently never updates.
    session.start()

    @app.get("/")
    def index():
        return render_template("live.html", project=session.project.name)

    @app.get("/api/state")
    def state():
        return jsonify({
            "report": _serialise(session.latest),
            "has_spec": session.spec is not None,
            "brief_features": [f["description"] for f in (session.spec or {}).get("features", [])],
        })

    @app.post("/api/brief")
    def brief():
        if not _same_origin(request):
            return jsonify({"error": "Cross-origin requests are not accepted."}), 403
        text = (request.get_json(silent=True) or {}).get("brief", "").strip()
        if not text:
            return jsonify({"error": "Type what you asked the agent to build."}), 400
        return jsonify(session.apply_brief(text))

    @app.get("/api/stream")
    def stream():
        q = session.subscribe()

        def gen():
            # Paint immediately — never show an empty page.
            yield f"data: {json.dumps({'type':'update','report':_serialise(session.latest),'deltas':[],'notable':False})}\n\n"
            try:
                while True:
                    try:
                        yield f"data: {json.dumps(q.get(timeout=20))}\n\n"
                    except queue.Empty:
                        yield ": keepalive\n\n"
            finally:
                session.unsubscribe(q)

        return Response(gen(), mimetype="text/event-stream",
                        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    return app
