# -*- coding: utf-8 -*-
"""模板04实测：B站公开API链（无登录）. 排行->详情->评论
产物: test-output/bili_smoke.json
"""
import json, sys
from pathlib import Path
from curl_cffi import requests as creq

OUT = Path(__file__).resolve().parent.parent / "test-output" / "bili_smoke.json"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

def main():
    result = {"template": "04-bilibili", "steps": {}, "ok": False}
    s = creq.Session(impersonate="chrome")
    h = {"User-Agent": UA, "Referer": "https://www.bilibili.com/"}

    r = s.get("https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all", headers=h, timeout=10)
    lst = r.json().get("data", {}).get("list", [])
    result["steps"]["rank"] = {"code": r.json().get("code"), "videos": len(lst)}

    v = lst[0] if lst else None
    if not v:
        OUT.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8"); return 1
    bvid = v["bvid"]
    r2 = s.get(f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}", headers=h, timeout=10)
    d2 = r2.json().get("data", {})
    result["steps"]["view"] = {"bvid": bvid, "title": d2.get("title", "")[:40],
                               "owner": d2.get("owner", {}).get("name"), "play": d2.get("stat", {}).get("view")}

    aid = d2.get("aid")
    r3 = s.get(f"https://api.bilibili.com/x/v2/reply?type=1&oid={aid}&sort=1&ps=5",
               headers={**h, "Referer": f"https://www.bilibili.com/video/{bvid}/"}, timeout=10)
    reps = r3.json().get("data", {}).get("replies") or []
    result["steps"]["reply"] = {"count": len(reps),
                                "sample": (reps[0]["content"]["message"][:40] if reps else None)}

    result["ok"] = bool(lst and d2.get("aid") and reps)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(("✓" if result["ok"] else "✗"), json.dumps(result["steps"], ensure_ascii=False)[:300])
    return 0 if result["ok"] else 1

if __name__ == "__main__":
    sys.exit(main())
