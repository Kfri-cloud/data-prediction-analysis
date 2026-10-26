"""Download only public research inputs; no model execution or remote code."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import urllib.request

ROOT = Path(__file__).resolve().parent
COMMIT = "00281e2d86058286d5548b15a7670e8eda57ef62"
BASE = f"https://raw.githubusercontent.com/AdityaLab/Time-MMD/{COMMIT}/"
SOURCES = {
    "Economy.csv": BASE + "numerical/Economy/Economy.csv",
    "Economy_report.csv": BASE + "textual/Economy/Economy_report.csv",
    "Economy_search.csv": BASE + "textual/Economy/Economy_search.csv",
    "upstream_readme.txt": BASE + "readme.MD",
    "timesx_paper.html": "https://arxiv.org/html/2607.06973v1",
    "timemmd_paper.html": "https://arxiv.org/html/2406.08627v3",
    "nsw_paper.html": "https://arxiv.org/html/2506.11050v1",
}


def main():
    folder = ROOT / "data"
    folder.mkdir(exist_ok=True)
    files = []
    for name, url in SOURCES.items():
        request = urllib.request.Request(url, headers={"User-Agent": "news-evidence-lab/0.1"})
        with urllib.request.urlopen(request, timeout=45) as response:
            payload = response.read()
        (folder / name).write_bytes(payload)
        files.append({"file": name, "url": url, "bytes": len(payload),
                      "sha256": hashlib.sha256(payload).hexdigest()})
        print(f"Downloaded {name}: {len(payload)} bytes")
    manifest = {"retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                "repository_commit": COMMIT, "files": files,
                "purpose": "Local provenance audit, not a forecasting reproduction"}
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
