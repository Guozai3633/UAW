# MS-I2k 实际合同等待与前端接受

2026-10-10；实际后端运行源码4c3f159。实际办公Run：run-eb7af1282636488f99e6559898e0623f。原公开RunDeliveryView在ms-i2k-start已有，未增加endpoint/DTO。

## 准确来源

后台在原Agent/Completion流程形成固定proposal、contract、report、bundle，job在delivery/waiting等待合同接受。此时Run.status可以仍为running，因为proposal绑定Run版本；修改Run状态/版本会使原提案或Context失效。Run.status不是合同接受是否需要的唯一依据。

浏览器读当前RunDeliveryView：requires_acceptance=true、stale=false、尚无acceptance；真实Artifact/Report/Proposal/Contract/Bundle绑定全部有效。当前文本/UTF-8 hash/要求核验通过，已读取完整正文。前端按该视图及当前身份、原Run/Refs、安全条件显示合同接受。原Run非终态、尚未取消；决定前再读同一交付视图；原请求查阅/精确Refs/去重、不重发语义保持。

CompletionAcceptance只是实际接受回执。只有原Completion Controller重新复查frame、权限、预算、取消、unknown效果、真实报告及接受，提交completed后才显示任务完成。不能把接受当作自动通过报告或完成任务。

## B本包同一真实页面修复

Review.tsx不应只因run.status!=waiting_for_user禁用接受；按以上实际交付来源处理running与waiting_for_user的非终态等待，取消/终态/过时/缺源/未知决定仍拒绝。补实际RunDeliveryView回放及取消/终态/旧Refs/未知费用或效果不能越过控制器的回归。

原实际wire位于A自身tests/.artifacts/A/MS-I2k/m4-live-run-eb7af1282636488f99e6559898e0623f.json（delivery.result.payload），含正文、合同、报告、提案等，不含凭据。B只读参考，不修改A。

另一个实际UI现象记录：办公原提交尚待接受时，新建学术会话并写入草稿成功，但全局old Recovery使发送禁用。保留原查阅ID，不能删除缓存或改request_id绕过。此项需要按原会话恢复/独立任务语义修复，或明确导航到尚待核对的原运行；A先完成办公原接受再验学术，不隐藏这个限制。
