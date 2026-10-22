# crawler-suite

爬虫接单工作台：skills-only DSH 插件（无运行时代码）。

- `skills/crawler-triage/` — 接单分诊：红线判定表（商家经营信息=低风险档 / 消费者PII=拒 / 破解=拒）、边缘试探协议（抓包先行→JS限时试解→不行动态调试）、武器矩阵、报价参考
- `skills/scraper-blueprint/` — DrissionPage 标准作业流、频率纪律、脱敏交付、京东商品/评论/商家信息三模板骨架

开发：ZCode 在本目录写，DSH 挂载运行。单子来了按真单调模板，固化进本仓库。
