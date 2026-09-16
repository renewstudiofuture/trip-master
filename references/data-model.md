# trip.json v2：唯一行程事实源

从 `assets/example-trip.json` 的结构开始，用真实来源替换合成内容。它只是字段范例，不是可复用目的地事实。所有对象使用稳定英文 ID，不能以数组序号当长期身份。

顶层：`schema_version:2`、`trip_id`、`revision`正整数、`title`、IANA `timezone`、`travelers`整数或null；`brief`可保留已确认的需求，渲染不直接公开它。

- `budget`：可空；`amount_minor`整数最小货币单位、`currency`、`scope:total|per_person`。CNY/USD/EUR/GBP/HKD/TWD/SGD/THB用两位，JPY/KRW用零位。新增币种要显式定义精度并测试，不能默认100。
- `places`：id、name、category（sights/shopping/food/other）、status、reason；可选address/hours/reservation/price_note/lat/lon/coordinate_system/map_url/url/image_url/image_source/rating/rating_source/evidence_ids。坐标系明确；评分需来源；图片需核对主体与使用条件，缺图留文字卡。支持 image_asset（受限 assets/ 文件名）、image_caption、image_credit、image_license_url、highlights（字符串列表）和 visit_plan。
- `days`：id、date（YYYY-MM-DD或null）、title、note、stay_ids、stops。日期顺序排列，不用“第1天”代替已知实际日期。
- `stops`：id、place_id或title、status、note、locked、booking_id；start/end为含日期和偏移的ISO时间，如2026-11-02T10:00:00+08:00。transfer_minutes指进入此活动所需交通加缓冲；只能按明确依据填写，未知null，不能默认0。跨日活动用真实结束日期。
- `bookings`：id为自定引用编号；title、kind（stay/transport/ticket）、status、date或check_in/check_out、capacity_total、note、cancelled。状态只允许用户提供／截图可辨识／待确认；不记录真实订单号。非住宿的定日有效预订须在日程里引用一次；未确认的日期留空。
- `costs`：规划费用id/title/amount_minor（未知null）/paid_minor/currency/basis（用户提供/报价/估算）；可关联booking_id以防重复。实付记录不自动填入浏览器账本。
- `tasks`：id/title/note/priority。内容实质改变会使旧勾选需要重新确认。
- `evidence`：id/title/status/url/checked_at/applicable/note；可附 `claims` 说明证据支持哪些具体字段。

公共事实状态：用户提供、截图可辨识、公开核实、估算、待确认。字段确定性不能被整条卡片的状态掩盖：混合状态在note或字段级claims明确说明。

校验器检查结构和可计算冲突，不能自动判断商家真实可订，也不证明所有未填住宿都已覆盖。未知时间、未知预订字段需在正文注明。公开渲染使用字段白名单，但允许字段的文字仍需脱敏检查，不能仅凭白名单断言无隐私。

`request`检查为无副作用操作：只输出受影响日、相邻衔接和语义审查需求；不自动执行修改。新地点需先研究，旧申请需对照当前revision，锁定变更需用户明确授权后由Agent更新源数据。

浏览器个人记录包是另一个格式：schema_version:1、trip_id、expenses、tasks。账本记录整数最小单位和币种、日期、分类、备注、稳定id、updated_at；不在公共trip.json中维护它。未知格式不静默迁移覆盖。

来源、缓存和构建状态可保存用户工作目录，不写入安装技能模板；不同旅行不能串用缓存结果或个人存储ID。

顶层可选 introduction 为行程导语，delivery_stage 为 review/accepted/published，渲染对应下一步提示。个人行程包：schema_version:1、trip_id、base_revision、days；与个人账本包分开，不覆盖公共 trip.json。

## 展示时间与主题图片

活动可附 `time_label`（最多100字），用于“09:00–12:00 · 建议”等弹性时段，不代替带时区的真实 start/end，也不参与真实班次衔接校验。已知时间与建议时间须区分；跨天移动清除旧时间说明，用户可重填。

地点可附 `illustration_asset`（与 image_asset 同样的 assets/ 安全路径）和 `illustration_caption`，首页按主题选择实景/艺术封面，沿用该地点 image_source、image_credit 和许可，注明转绘。无可嵌入图片时可附 `image_gallery_url` 与 `image_gallery_note` 展示历史实景入口，不能宣称已补齐图片。
