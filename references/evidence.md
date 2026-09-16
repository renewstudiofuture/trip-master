# 状态与证据

事实状态：用户提供（文字）、截图可辨识（仅可见字段）、公开核实（有来源与适用条件）、估算、待确认。取消预订单独标记，不进入现行安排；不再使用“账号订单已核”。

`trip.json` 是唯一正式行程源；不再维护第二份可编辑的全文 Markdown 行程。必要的文字来源附录可从源数据生成。

状态文件 `build-state.json` 只保存：trip_id、revision、stage、source_hash、completed、pending、output_path、last_error。stage 采用 intake/outline/research/render/checked/published；状态是记录，不是证明。用户确认可写入简短当前确认摘要，不复制全部聊天。

证据记录：id、title、status、url（无公开链接可为空）、checked_at、applicable、note；`claims` 可按字段保存证据对应关系。看到图片或标题不能自动证明价格和早餐。只读取本阶段涉及的证据与缺口；来源未变也要判断日期适用性。

修改时依赖关系：活动引用 place_id；住宿引用 booking_id；费用可关联 booking_id；模块由地点 category 和每日引用派生。用户指定固定活动设置 locked，正式变更需符合用户明确要求。自由意见先转结构化改动，再计算影响；脚本只给初步范围。

构建完成、浏览器检查、部署成功、匿名访问、微信实测分开记录。正常内容小改只重验受影响范围；公共模板／交互变化需覆盖相关交互，不能复用旧检查记录冒充新版通过。

日志记录实际阶段耗时、搜索和原文调用、重复查询、阻断和介入次数。token 仅报告可用的本任务实际计量，没有则写未测。不要用字数或账号总额度变化估算节省比例。
