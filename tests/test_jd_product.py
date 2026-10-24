# -*- coding: utf-8 -*-
"""模板01实测：京东 h5 商品+价格（无登录公开数据）.
链路: so.m.jd.com 搜索 -> item.m.jd.com 详情 -> p.3.cn 价格接口
产物: test-output/jd_smoke.json
"""
import json, re, sys, time
from pathlib import Path
from curl_cffi import requests as creq

OUT = Path(__file__).resolve().parent.parent / "test-output" / "jd_smoke.json"
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"

def log(*a):
    print(*a, flush=True)

def main(keyword="无线鼠标"):
    result = {"template": "01", "keyword": keyword, "steps": {}, "ok": False}
    s = creq.Session(impersonate="chrome")

    # ① 搜索页拿 SKU
    r = s.get(f"https://so.m.jd.com/ware/search.action?keyword={keyword}",
              headers={"User-Agent": UA, "Referer": "https://m.jd.com/"}, timeout=15)
    result["steps"]["search"] = {"status": r.status_code, "len": len(r.text)}
    skus = re.findall(r'wareid["\']?\s*[:=]\s*["\']?(\d{6,15})', r.text)
    if not skus:
        skus = re.findall(r'product/(\d{6,15})\.html', r.text)
    skus = list(dict.fromkeys(skus))[:3]
    result["steps"]["search"]["skus"] = skus

    if not skus:
        log("✗ 搜索页未解析出 SKU，需转 DrissionPage 渲染路线")
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return 1

    sku = skus[0]
    # ② h5 商品详情
    r2 = s.get(f"https://item.m.jd.com/product/{sku}.html",
               headers={"User-Agent": UA, "Referer": "https://so.m.jd.com/"}, timeout=15)
    t = r2.text
    title_m = re.search(r'<title>([^<]+)</title>', t) or re.search(r'"name"\s*:\s*"([^"]{5,80})"', t)
    result["steps"]["item"] = {"status": r2.status_code, "sku": sku,
                               "title": (title_m.group(1).strip() if title_m else None)[:60]}
    # ③ 价格接口（经典公开接口）
    r3 = s.get(f"https://p.3.cn/prices/mgets?skuIds=J_{sku}",
               headers={"User-Agent": UA, "Referer": f"https://item.m.jd.com/product/{sku}.html"}, timeout=10)
    try:
        price = r3.json()
    except Exception:
        price = {"raw": r3.text[:120]}
    result["steps"]["price"] = {"status": r3.status_code, "data": price}

    ok = bool(result["steps"]["item"].get("title")) and isinstance(price, list) and price
    result["ok"] = ok
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    log(("✓" if ok else "✗"), json.dumps(result["steps"], ensure_ascii=False)[:400])
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "无线鼠标"))
