---
name: scraper-blueprint
description: 爬虫蓝图——接单后编写具体爬虫脚本时加载。DrissionPage 标准作业流、环境检查、频率纪律、脱敏交付、平台实测状态总表（B站/微博匿名通，京东半通，点评需登录）、模板00-04。
---

# 爬虫蓝图（scraper-blueprint）

## 环境检查（每台机器一次）

```bash
T:/python310/python.exe -m pip install DrissionPage openpyxl -q
T:/python310/python.exe -c "from DrissionPage import ChromiumPage; print('ok')"
```

## DrissionPage 标准作业流

1. **登录态**：用固定用户数据目录接管 Chrome（小号！不用主号）：
   `ChromiumPage(addr_or_opts=f'127.0.0.1:{port}', ...) `或直接指定 user_data_dir 启动。首次手动登录一次，cookie 落目录，之后免登录。
2. **页面等待**：用 `ele.located` / 显式等待目标元素，**禁用死等 sleep**；翻页用元素级等待 + 超时重试（最多 3 次退避）。
3. **频率纪律**：每次请求间 `random.uniform(2, 5)` 秒抖动；单账号连续运行不超 2 小时；遇到滑块/验证码立即停机人工处理，**不自动破解**（破解=红线）。
4. **字段抽取**：每个字段给选择器 + 兜底（`or None`），全空行记 warning 不中断；断点续爬：进度写 `state.json`（已处理 ID 集合），崩了从断点跑。
5. **导出**：openpyxl 出 xlsx，列宽自适应；交付前过一遍脱敏规则（见下）。

## 脱敏交付纪律

- 消费者数据：昵称/头像/用户ID/手机号一律不进交付表
- 商家数据：优先交付 公司名/固话/地址；个人手机号默认剔除，客户明确要求时提醒风险后以脱敏形态给
- 样本先行：全量跑之前先出 20 条样本给客户确认字段口径

## 实测状态总表（2026-10-24 匿名冒烟，测试脚本在 tests/）

| 平台 | 匿名可达性 | 结论 | 证据 |
|---|---|---|---|
| akshare 财务 | ✓ 全通 | 免登录 20 秒拉全量三表 | test-output/byd_financials.xlsx |
| B站 | ✓ 全通 | 排行/详情/评论 API 全匿名可用 | tests/test_bilibili.py → bili_smoke.json |
| 微博 | ✓ 浏览器路线 | m 站渲染匿名可抓博文；接口直连需浏览器签发的访客 token | tests/test_weibo_browser.py → weibo_smoke.json |
| 京东商品 | △ 半通 | 给 SKU 时标题/参数匿名可抓；**价格服务端打码（`1??9`）需登录 cookie**；匿名搜索被风控页拦 | tests/test_jd_product.py |
| 京东评论 | ✗ 匿名全堵 | club.jd.com 接口 444，渲染也空（风控在接口层）→ 需登录 cookie | - |
| 大众点评 | ✗ 匿名全墙 | PC 端安全检测页 + m 站错误页 → 需真浏览器过验证拿 cookie + 字体解码 | - |
| 淘宝/拼多多/抖音/小红书 | 未测 | 预期登录/签名墙；等真单输入（客户给链接/清单）再走 MediaCrawler 路线 | - |

无登录可接的单型：财务数据、B站内容/评论、微博舆情（浏览器路线）、京东标题类字段。
需登录态的单型（cookie 由客户提供或小号登录）：京东价格+评论、美团/点评商家、抖音、小红书、淘宝、拼多多。

## 模板 00：上市公司财务三表（akshare 路线，2026-10-22 实测通过）

论文类金融数据单的答案：**先 akshare 再谈爬**。东财接口免登录直连，比亚迪(SZ002594)实测 20 秒拉全量三表。

```python
# pip install akshare openpyxl -i https://mirrors.aliyun.com/pypi/simple/ （清华源拉不到 akshare，用阿里源）
import akshare as ak
bs = ak.stock_balance_sheet_by_report_em(symbol='SZ002594')   # 资产负债表 71期×319字段
pl = ak.stock_profit_sheet_by_report_em(symbol='SZ002594')    # 利润表 74期×203
cf = ak.stock_cash_flow_sheet_by_report_em(symbol='SZ002594') # 现金流量表 74期×254
# 三个 DataFrame 各写一个 sheet 到 xlsx，openpyxl 重新打开验证 sheet 名与报告期
```

- 年度/单季变体：`_by_yearly_em` / `_by_quarterly_em`；退市公司用 `_delisted_em`
- 验收口径：最新报告期是否到上季度、三表齐全、xlsx 能打开
- 这类单子工时≈10分钟（含核对），报价锚 50-150 元

## 模板 01：京东商品+价格（h5 路线，2026-10-24 实测）

目标字段：sku_id / 标题 / 价格 / 店铺名 / 评论数（+评论明细走模板 02）。实测结论修正要点：
- **SKU 来源**：h5/PC 搜索匿名都被风控页拦（`cfe.m.jd.com/privatedomain/risk_handler`）→ 单子里客户通常直接给商品链接/SKU 清单，没有就要登录态搜索
- **商详标题**：`item.m.jd.com/product/{sku}.html` curl_cffi 静态抓即可（impersonate=chrome + h5 UA + Referer），`<title>` 里就有，无需登录
- **价格**：静态 HTML 是 `jdPrice":"1??9"` **服务端打码**，无头渲染后 DOM 里仍是 `¥1??9`；p.3.cn/c0.3.cn 老价格接口已死（DNS 没了）→ 真价格必须登录 cookie（浏览器登录后渲染，或带 cookie 复用商详页 Network 里的价格接口）
- 测试脚本 `tests/test_jd_product.py`（含搜索失败时输出原始诊断）

## 模板 02：京东评论（接口路线，2026-10-24 实测：匿名全堵）

- `club.jd.com/comment/productPageComments.action` 匿名返回 **444**；评论页浏览器渲染也空（风控在接口层）
- 可行路线：登录态浏览器开商详页 Network 抓一次 comment 真实请求（参数照抄含 cookie/sign，翻页改 page）
- 字段：评分/内容/时间/规格/是否追评。**不收用户身份字段**
- 排序参数切换（推荐/最新）各跑一遍注意去重（评论ID）

## 模板 03：商家信息（美团/点评类，2026-10-24 实测：匿名全墙）

- PC 端 `www.dianping.com/{city}/ch10` 匿名 → 安全检测页（4.8KB）；m 站 `m.dianping.com` → error_page
- 可行路线：DrissionPage 真浏览器（带 user_data_dir 小号目录）首次**人工过一次验证码**，cookie 落目录后批量抓；评分/价格数字是**字体反爬**（PUA 私用区字符），需下载 woff 字体建码表映射（fontTools，脚本骨架待 cookie 实战时写）
- 输出 公司名/地址/固话/品类/评分；个人号码剔除
- 地域翻页结构每个城市独立，state.json 按城市记进度

## 模板 04：内容平台公开 API（B站 2026-10-24 实测通过；微博浏览器路线通过）

**B站（全匿名，首选接口直连）**：
```python
# 排行(拿bvid) -> 详情 -> 评论，Referer 带 bilibili.com，curl_cffi impersonate=chrome
rank = 'https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all'   # rid=分区号
view = 'https://api.bilibili.com/x/web-interface/view?bvid={bvid}'            # 标题/UP主/播放/弹幕
reply = 'https://api.bilibili.com/x/v2/reply?type=1&oid={aid}&sort=1&ps=20'   # aid 从 view 拿
# 用户维度：space.bilibili.com API；关键词搜索需 cookie，用浏览器路线
```
**微博（匿名=浏览器渲染，接口直连没访客 token）**：
- `m.weibo.cn/search?containerid=100103type%3D1%26q%3D{关键词}` DrissionPage 渲染 4 秒 → `.weibo-text` 节点即博文；提速：渲染成功后把浏览器 cookies 导出给 curl_cffi 复用
- 博文字段：user.screen_name / text / reposts_count / comments_count；**不收用户身份与定位**
- 完整测试：tests/test_weibo_browser.py
**抖音/小红书**：登录墙+请求签名，走 MediaCrawler 路线（cookie 登录），真单进来再实测。


## 何时升级武器

- 页面结构三天一变 → 把选择器抽成配置文件
- 量级上万 → 上多账号轮换 + 代理（住宅代理），成本入报价
- Web 路线全灭 → 回 crawler-triage 的边缘试探协议
