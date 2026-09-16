# 生成与验收

主交付为手机 HTML；需要时另给资料摘要和 PDF。输入统一为 trip.json，不在成品HTML里手改事实。

1. 运行 trip_model.py validate，修复 errors，warnings 保持可见并说明缺什么。自动校验涵盖已知时间、转场、用户预订日期、住宿容量／已引用晚数、币种和关联费用重复；不代表地图实测或外部预约成功。
2. build_mobile_html.py 输出独立文件；检查没有用户原始凭证、真实订单号、签名URL或源码占位符。正文仍须人工核对来源与适用日期。
3. 首次或改公共模板后测试320/390/768/桌面宽度、日期锚点、无JS基础阅读、真实外链、图片失败、本地行程增删改移与跨版本保护、助手重规划复制、预算联动及多币种、金额解析、编辑删除、备份重复／冲突导入、存储失败和同一trip_id版本更新。
4. 小范围行程内容改动只验证受影响日期、卡片和链接；不重做无关研究和全部交互。线上分享未授权时停在本地成果。

PDF按需：先运行 `python scripts/build_pdf_cards.py trip.json cards.json`，再 `python scripts/build_cards_pdf.py cards.json trip.pdf --font <中文TrueType字体>`。按实际字体和页面长度拆分卡片，导出器溢出时不要缩字号强塞。运行当前可用PDF技能的渲染与文本检查；PDF不是手机微信交互的替代保证。本次没有生成PDF就不声称PDF版已验收。

代码回归：`python scripts/test_trip_model.py`。仅用合成数据测试，不拿旧用户订单冒充新核实。

涉及换肤时按 [视觉风格](visual-style.md) 检查两套主题、封面、刷新记忆与数据不变；只改技能规则时不得把模板尚未实现的功能当成已交付。
