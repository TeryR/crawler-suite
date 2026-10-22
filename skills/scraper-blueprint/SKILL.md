---
name: scraper-blueprint
description: 爬虫蓝图——接单后编写具体爬虫脚本时加载。DrissionPage 标准作业流、环境检查、频率纪律、脱敏交付，含京东第一模板。
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

## 模板 01：京东商品+价格（h5 路线）

目标字段：sku_id / 标题 / 价格 / 店铺名 / 评论数（+评论明细走模板 02）。要点：
- 入口 `m.jd.com` 搜索关键词 → 商详 `item.m.jd.com/product/{sku}.html`
- 价格不在页面 DOM 里，走接口：商详页 Network 里找 `pingou`/`api.m.jd.com` 的 price 接口，带 sku 参数直接复用登录态请求
- 翻页/翻深度：搜索结果下滑加载，用 `page.scroll.to_bottom()` 循环直到无新商品
- 每单按实际字段调整选择器，本模板是骨架不是成品

## 模板 02：京东评论（接口路线）

- 评论走 `api.m.jd.com` 的 comment 列表接口（商详页 Network 抓一次真实请求，参数照抄，翻页改 page）
- 字段：评分/内容/时间/规格/是否追评。**不收用户身份字段**
- 排序参数切换（推荐/最新）各跑一遍注意去重（评论ID）

## 模板 03：商家信息（美团/点评类）

- 店铺页 → 商家信息区块；城市+品类遍历用 m 站搜索页
- 输出 公司名/地址/固话/品类/评分；个人号码剔除
- 地域翻页结构每个城市独立，state.json 按城市记进度

## 何时升级武器

- 页面结构三天一变 → 把选择器抽成配置文件
- 量级上万 → 上多账号轮换 + 代理（住宅代理），成本入报价
- Web 路线全灭 → 回 crawler-triage 的边缘试探协议
