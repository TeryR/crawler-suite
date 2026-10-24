# -*- coding: utf-8 -*-
"""模板01实测（浏览器渲染路线）：京东 h5 搜索 -> 详情 -> 真实价格.
DrissionPage 无头 Chromium；产物 test-output/jd_smoke_browser.json
"""
import json, sys, time
from pathlib import Path
from DrissionPage import ChromiumPage, ChromiumOptions

OUT = Path(__file__).resolve().parent.parent / "test-output" / "jd_smoke_browser.json"

def main(keyword="无线鼠标"):
    result = {"template": "01-browser", "keyword": keyword, "steps": {}, "ok": False}
    co = ChromiumOptions()
    co.headless()
    co.set_argument("--no-sandbox")
    co.set_argument("--window-size=414,896")
    page = ChromiumPage(co)
    try:
        UA = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"}
        # ① 搜索
        page.get(f"https://so.m.jd.com/ware/search.action?keyword={keyword}")
        page.wait(2.5)
        result["steps"]["search"] = {"url": page.url[:80], "title": page.title[:40]}
        items = page.eles("css:.search_pricing, css:.goods-item-v2, css:[data-sku]")
        skus = []
        for it in items[:6]:
            sku = it.attr("data-sku") or (it.link.split("/product/")[-1].split(".")[0] if it.link and "/product/" in (it.link or "") else None)
            if sku and sku.isdigit():
                skus.append(sku)
        skus = list(dict.fromkeys(skus))[:3]
        result["steps"]["search"]["skus"] = skus

        if not skus:
            # 兜底：链接里解析
            links = [e.attr("href") or "" for e in page.eles("tag:a")][:200]
            skus = list(dict.fromkeys([l.split("/product/")[-1].split(".")[0] for l in links if "/product/" in l and l.split("/product/")[-1].split(".")[0].isdigit()]))[:3]
            result["steps"]["search"]["skus_fallback"] = skus
            skus = skus

        if not skus:
            result["steps"]["search"]["error"] = "rendered page still no sku"
            OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            return 1

        sku = skus[0]
        # ② 详情 + 真实价格
        page.get(f"https://item.m.jd.com/product/{sku}.html")
        page.wait(3)
        title = page.title.split("【")[0].strip() if page.title else None
        price = None
        for sel in [".price-selector .price", ".summary-price .price", "css:.p-price", "css:[class*=jdPrice]", "css:.price"]:
            el = page.ele(sel, timeout=1.5)
            if el and el.text and any(c.isdigit() for c in el.text):
                price = el.text.strip(); break
        result["steps"]["item"] = {"sku": sku, "title": (title or "")[:50], "price": price}
        result["ok"] = bool(title and price)
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(("✓" if result["ok"] else "✗"), json.dumps(result["steps"], ensure_ascii=False)[:400])
        return 0 if result["ok"] else 1
    finally:
        page.quit()

if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "无线鼠标"))
