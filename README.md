# Trip Master

搜索优先的国内旅行规划技能：围绕已有交通、酒店、门票续排行程，输出简洁、可核实的手机攻略。

## 特点

- 公开信息直接搜索；仅在读取携程私人订单时使用登录浏览器。
- 保留用户固定日期，区分历史订单、用户确认、已核实与待办。
- 用户已打开页面而工具看不到时，只做有限连接恢复，不要求反复登录导航。
- 包豪斯风格单文件手机网页：日期切换、交通住宿卡片、预算和待办；PDF作为离线选择。
- 需要分享时支持按授权使用免费静态托管，检查真实访问结果。

## 安装到 Codex

克隆或下载本仓库，把完整文件夹放到 `~/.codex/skills/trip-master/`，确保入口为 `~/.codex/skills/trip-master/SKILL.md`。在下一轮对话使用 `$trip-master`。

示例：`使用 $trip-master 为三人规划七天旅行，先读取已订订单，公开搜索补齐余下安排，输出手机行程。`

## 导出

需要Python 3。HTML导出不需要第三方依赖；PDF需要reportlab和可嵌入的中文TrueType字体。具体数据格式见 `references/pdf-design.md` 和 `references/mobile-web.md`。

```sh
python scripts/build_mobile_html.py trip-cards.json index.html
python scripts/build_cards_pdf.py trip-cards.json trip.pdf --font /path/to/chinese-font.ttf
```

本仓库不包含任何个人行程、订单、账号或部署凭据。不会代为付款、退改或发送消息。网页登录与实时库存可能受平台限制；输出必须标明未核实项。HTML需托管成HTTPS网址才能作为微信分享入口，PDF内链兼容性取决于阅读器。

## 来源与许可

基于 [TianhaoWu66/trip-planner](https://github.com/TianhaoWu66/trip-planner) 改写，保留原MIT许可与版权声明。行程组织参考圆周旅迹公开产品说明，不隶属于携程或圆周旅迹，也不包含其私有接口。
