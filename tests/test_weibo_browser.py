# -*- coding: utf-8 -*-
"""模板04实测：微博 m 站浏览器路线（无登录）. 搜索关键词->博文列表
关键点: 访客 XSRF token 由浏览器 JS 签发，接口直连拿不到 → 必须 DrissionPage 渲染。
提速法: 渲染后把 cookies 导出给 curl_cffi 复用（见 SKILL.md 模板04）。
产物: test-output/weibo_smoke.json
"""
import json, sys, urllib.parse
from pathlib import Path
from DrissionPage import ChromiumPage, ChromiumOptions

OUT = Path(__file__).resolve().parent.parent / "test-output" / "weibo_smoke.json"

def main(keyword="新能源汽车"):
    result = {"template": "04-weibo-browser", "keyword": keyword, "steps": {}, "ok": False}
    co = ChromiumOptions()
    co.headless()
    co.set_argument("--window-size=414,896")
    page = ChromiumPage(co)
    try:
        kw = urllib.parse.quote(keyword)
        page.get(f"https://m.weibo.cn/search?containerid=100103type%3D1%26q%3D{kw}")
        page.wait(4)
        posts = page.eles("css:.weibo-text")
        users = page.eles("css:[class*=name]")
        texts = [p.text.strip()[:60].replace("\n", " ") for p in posts[:5]]
        result["steps"]["search"] = {"title": page.title[:30], "posts": len(posts),
                                     "sample": texts[:2]}
        result["ok"] = len(posts) >= 3
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(("✓" if result["ok"] else "✗"), json.dumps(result["steps"], ensure_ascii=False)[:300])
        return 0 if result["ok"] else 1
    finally:
        page.quit()

if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "新能源汽车"))
