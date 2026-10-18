export interface paths {
    "/v1/conversations": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 查询自己的会话。 */
        get: operations["http_conversations_list"];
        put?: never;
        /** 创建会话。 */
        post: operations["http_conversations_create"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/conversations/{conversation_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 读取会话。 */
        get: operations["http_conversations_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/conversations/{conversation_id}/items": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 可见交互记录。 */
        get: operations["http_conversations_items"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/conversations/{conversation_id}/turns": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** 提交原文并受理Run。 */
        post: operations["http_turns_submit"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/runs/{run_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 运行状态。 */
        get: operations["http_runs_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/runs/{run_id}/control": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** 用户干预。 */
        post: operations["http_runs_control"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/tasks/{task_id}/frame": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 读取当前任务理解。 */
        get: operations["http_tasks_frame"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/approvals/{approval_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 审批详情。 */
        get: operations["http_approvals_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/approvals/{approval_id}/decisions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** 用户审批。 */
        post: operations["http_approvals_decide"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/conversations/{conversation_id}/events": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 分页读取历史事件。 */
        get: operations["http_events_read"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/events/{event_id}/payload": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 读取同主体持久事件的严格分支载荷。 */
        get: operations["http_events_payload"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/conversations/{conversation_id}/turn-requests/{request_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 按原提交request_id查询当前Run；没有记录返回missing，不发送新任务。 */
        get: operations["http_turns_lookup"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/runs/{run_id}/delivery": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 读取本人Run的最新真实固定交付；无交付返回missing。 */
        get: operations["http_runs_delivery"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/runs/{run_id}/delivery/acceptance": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** 实际用户决定整份合同交付；不直接设置completed。 */
        post: operations["http_runs_delivery_accept"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/artifacts/{artifact_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 成果版本。 */
        get: operations["http_artifacts_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/artifacts/{artifact_id}/content": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 读取完整文本/Markdown；固定版本与hash必需。 */
        get: operations["http_artifacts_content"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/runner/enrollments": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** 当前Web用户请求独立候选的首次登记；不授予目录权限。 */
        post: operations["http_runner_enrollments_begin"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/runner/enrollments/{enrollment_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 当前原Web会话读取准确当前登记；不授予执行。 */
        get: operations["http_runner_enrollments_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/runner/enrollments/{enrollment_id}/confirmation": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** 读取独立本机本人确认和双方签名证明后CAS登记。 */
        post: operations["http_runner_enrollments_complete"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/runner/enrollments/{enrollment_id}/revocation": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** 原当前Web用户撤销登记。 */
        post: operations["http_runner_enrollments_revoke"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/runner/local": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** 当前Web用户请求本机本人确认；异步返回原启动状态。 */
        post: operations["http_runner_local_begin"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/runner/local/{launch_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 查询原本机启动；当前主体/通道/原根复查，后端重启标unavailable，不重发。 */
        get: operations["http_runner_local_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/runner/local/{launch_id}/stop": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** 原Web用户停止并drain自己本机实例，保留原历史。 */
        post: operations["http_runner_local_stop"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/runs/{run_id}/presentation": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 运行状态。 */
        get: operations["http_runs_presentation_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/runs/{run_id}/conversation": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 运行状态。 */
        get: operations["http_runs_conversation_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/runs/{run_id}/clarifications/{question_item_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 读取原Run特定问题，不猜最新问题。 */
        get: operations["http_runs_clarification_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/runs/{run_id}/clarifications/{question_item_id}/answers": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** 原Run回答；身份和expected_run_revision来自meta。 */
        post: operations["http_runs_clarification_answer"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/runs/{run_id}/corrections": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** 当前Run纠正，不让客户端指定任意执行节点或权限。 */
        post: operations["http_runs_correction_create"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/runs/{run_id}/continuations/{request_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 原提交响应丢失或刷新后的受理/生效查询。 */
        get: operations["http_runs_continuation_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/quality/reviews": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 认证网页质量审阅/反馈入口。 */
        get: operations["http_quality_reviews_list"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/quality/reviews/{review_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 认证网页质量审阅/反馈入口。 */
        get: operations["http_quality_reviews_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/quality/reviews/{review_id}/draft": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** 认证网页质量审阅写入；要求 CAS 和原目标绑定。 */
        post: operations["http_quality_reviews_save"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/quality/reviews/{review_id}/submission": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** 认证网页质量审阅写入；要求 CAS 和原目标绑定。 */
        post: operations["http_quality_reviews_submit"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/quality/reviews/{review_id}/export": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 认证网页质量审阅/反馈入口。 */
        get: operations["http_quality_reviews_export"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/runs/{run_id}/feedback": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 认证网页质量审阅/反馈入口。 */
        get: operations["http_quality_feedback_list"];
        put?: never;
        /** 认证网页质量审阅写入；要求 CAS 和原目标绑定。 */
        post: operations["http_quality_feedback_save"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/models": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 用户可用模型目录。 */
        get: operations["http_models_list"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/v1/web/session": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 读取当前浏览器用户会话。 */
        get: operations["http_web_session_get"];
        put?: never;
        /** 精确Origin消费一次启动code。 */
        post: operations["http_web_session_exchange"];
        /** 撤销当前浏览器会话并清cookie。 */
        delete: operations["http_web_session_logout"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /** @description 确认受理，不证明整个任务已完成。 */
        Acknowledgement: {
            /** @description 受理ID */
            operation_id: components["schemas"]["ID"];
            /**
             * @description 确认状态
             * @enum {string}
             */
            status: "accepted" | "unchanged" | "completed" | "pending";
            /** @description 相关资源 */
            related_refs?: components["schemas"]["Ref"][];
        };
        /** @description 运行实例与持久定义分离。 */
        AgentInstance: {
            /** @description 实例ID */
            id: components["schemas"]["ID"];
            /** @description 所属运行 */
            run_id: components["schemas"]["ID"];
            /** @description 根实例无父 */
            parent_agent_ref?: components["schemas"]["Ref"];
            /** @description 使用的角色版本 */
            definition_ref?: components["schemas"]["Ref"];
            /** @description 子实例的委派契约 */
            delegation_ref?: components["schemas"]["Ref"];
            /** @description 实例状态 */
            status: components["schemas"]["State"];
            /** @description 实际继承或覆盖政策 */
            model_policy_ref: components["schemas"]["Ref"];
            /** @description 有效权限交集 */
            capability_policy_ref: components["schemas"]["Ref"];
            /** @description 上下文纪元 */
            context_epoch: components["schemas"]["Revision"];
            /** @description 需要文件操作时绑定 */
            workspace_ref?: components["schemas"]["Ref"];
            /** @description 终态结果 */
            result_ref?: components["schemas"]["Ref"];
            /** @description 实例版本 */
            revision: components["schemas"]["Revision"];
        };
        /** @description 子Agent返回候选成果，父Agent仍需核验。 */
        AgentResult: {
            /** @description 完成实例版本 */
            agent_ref: components["schemas"]["Ref"];
            /** @description 真实结果 */
            outcome: components["schemas"]["Outcome"];
            /** @description 结果摘要 */
            summary: components["schemas"]["Text"];
            /** @description 交付引用 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 核验证据 */
            verification_refs: components["schemas"]["Ref"][];
            /** @description 未完成项 */
            limitations: components["schemas"]["NonEmptyText"][];
            /** @description 真实累计用量 */
            usage_ref: components["schemas"]["Ref"];
        };
        /** @description 由用户或批准的审查服务签发，LLM工具参数不含批准结果。 */
        ApprovalDecision: {
            /** @description 单次/限定持续/拒绝/取消 */
            decision: components["schemas"]["ApprovalDecisionKind"];
            /** @description 对应动作参数 */
            expected_arguments_hash: components["schemas"]["Hash"];
            /** @description 对应版本 */
            expected_resource_refs: components["schemas"]["Ref"][];
            /** @description 限定持续范围 */
            scope_selector?: components["schemas"]["ScopeSelector"];
            /** @description 持续授权截止 */
            expires_at?: components["schemas"]["Timestamp"];
            /** @description 理由 */
            reason: components["schemas"]["Text"];
        };
        /**
         * @description 取值含义见字段及协议约束。
         * @enum {string}
         */
        ApprovalDecisionKind: "approve_once" | "approve_scoped" | "decline" | "cancel";
        /** @description 授权结果不是无限期全局允许。 */
        ApprovalGrant: {
            /** @description 授权 */
            id: components["schemas"]["ID"];
            /** @description 审批版本 */
            approval_ref: components["schemas"]["Ref"];
            /** @description 真实批准者 */
            actor: components["schemas"]["Principal"];
            /** @description 用户决定 */
            decision: components["schemas"]["ApprovalDecision"];
            /** @description 签发时间 */
            issued_at: components["schemas"]["Timestamp"];
        };
        /**
         * @description 取值含义见字段及协议约束。
         * @enum {string}
         */
        ApprovalMode: "assisted" | "manual" | "automatic";
        /** @description 审批绑定动作、参数与资源版本。 */
        ApprovalRequest: {
            /** @description 审批 */
            id: components["schemas"]["ID"];
            /** @description 审批版本 */
            revision: components["schemas"]["Revision"];
            /** @description 动作 */
            action_id: components["schemas"]["ID"];
            /** @description 规范参数 */
            arguments_hash: components["schemas"]["Hash"];
            /** @description 预期目标版本 */
            resource_refs: components["schemas"]["Ref"][];
            /** @description 效果 */
            effect: components["schemas"]["EffectKind"];
            /** @description 用户可读动作 */
            summary: components["schemas"]["NonEmptyText"];
            /** @description 当前政策 */
            mode: components["schemas"]["ApprovalMode"];
            /** @description 等待/批准等 */
            status: components["schemas"]["ApprovalStatus"];
            /** @description 有效期 */
            expires_at: components["schemas"]["Timestamp"];
        };
        /**
         * @description 取值含义见字段及协议约束。
         * @enum {string}
         */
        ApprovalStatus: "pending" | "approved" | "declined" | "expired" | "cancelled" | "stale";
        /** @description 用户审批。 */
        ApprovalsDecideRequest: {
            /** @description 审批 */
            approval_id: components["schemas"]["ID"];
            /** @description 批准范围 */
            decision: components["schemas"]["ApprovalDecision"];
        };
        /** @description 审批详情。 */
        ApprovalsGetRequest: {
            /** @description 审批 */
            approval_id: components["schemas"]["ID"];
        };
        /** @description 实际文本或Markdown成果正文。 */
        ArtifactContentView: {
            /** @description 不可变成果元数据 */
            artifact: components["schemas"]["ArtifactRecord"];
            /** @description 完整正文 */
            content: components["schemas"]["ArtifactPreviewText"];
        };
        /** @description 完整UTF-8文本预览；服务再检查最大65536字节和SHA256，不截断。 */
        ArtifactPreviewText: string;
        /** @description 用户可编辑、预览、导出的版本化成果。 */
        ArtifactRecord: {
            /** @description 成果 */
            id: components["schemas"]["ID"];
            /** @description 内容版本 */
            version: components["schemas"]["Version"];
            /** @description 展示名 */
            title: components["schemas"]["NonEmptyText"];
            /** @description 例如markdown/csv/source_code */
            format_kind: components["schemas"]["NonEmptyText"];
            /** @description MIME */
            media_type: components["schemas"]["NonEmptyText"];
            /** @description 实际内容 */
            content_ref: components["schemas"]["Ref"];
            /** @description 字节数 */
            size_bytes: components["schemas"]["Count"];
            /** @description 摘要 */
            content_hash: components["schemas"]["Hash"];
            /** @description 生成/数据来源 */
            provenance_refs: components["schemas"]["Ref"][];
            /** @description 该版本证据 */
            verification_refs: components["schemas"]["Ref"][];
            /** @description 登记时间 */
            created_at: components["schemas"]["Timestamp"];
        };
        /** @description 读取完整文本/Markdown；固定版本与hash必需。 */
        ArtifactsContentRequest: {
            /** @description 成果 */
            artifact_id: components["schemas"]["ID"];
            /** @description 精确版本 */
            version: components["schemas"]["Version"];
            /** @description 预期SHA256 */
            content_hash: components["schemas"]["Hash"];
        };
        /** @description 成果版本。 */
        ArtifactsGetRequest: {
            /** @description 成果 */
            artifact_id: components["schemas"]["ID"];
            /** @description 不指定返回当前版本 */
            version?: components["schemas"]["Version"];
        };
        /** @description 认证失败不透露受保护资源存在性。 */
        AuthenticationFailure: {
            /**
             * @description 稳定认证错误码
             * @constant
             */
            code: components["schemas"]["ID"];
            /** @description 安全提示 */
            message: components["schemas"]["Text"];
            /** @description 关联 */
            request_id: components["schemas"]["ID"];
        };
        /** @description 布尔值，不能用字符串true或整数替代。 */
        Bool: boolean;
        /** @description 运行总预算/子预算请求。 */
        Budget: {
            /** @description 总上限 */
            limits: components["schemas"]["ResourceVector"];
            /** @description 动作循环次数上限 */
            max_steps: components["schemas"]["Count"];
            /** @description 委派最大深度 */
            max_depth: components["schemas"]["Count"];
            /** @description 绝对截止 */
            deadline: components["schemas"]["Timestamp"];
            /** @description 父预留引用 */
            parent_reservation_ref?: components["schemas"]["Ref"];
        };
        /** @description 所有重试和子Agent共享父预算账本。 */
        BudgetReservation: {
            /** @description 预留 */
            id: components["schemas"]["ID"];
            /** @description 父预留 */
            parent_ref?: components["schemas"]["Ref"];
            /** @description 预留量 */
            estimates: components["schemas"]["ResourceVector"];
            /** @description 尝试账单 */
            settled_usage_refs: components["schemas"]["Ref"][];
            /** @description 预留状态 */
            status: components["schemas"]["ReservationState"];
            /** @description 账本版本 */
            revision: components["schemas"]["Revision"];
        };
        /**
         * @description 取值含义见字段及协议约束。
         * @enum {string}
         */
        ChangeKind: "add" | "modify" | "delete" | "rename";
        /** @description Diff绑定具体输入版本；不能覆盖用户之后的编辑。 */
        ChangeSet: {
            /** @description 变更集 */
            id: components["schemas"]["ID"];
            /** @description 基础文件树 */
            base_ref: components["schemas"]["Ref"];
            /** @description 修改后文件树 */
            target_ref: components["schemas"]["Ref"];
            /** @description 可选择改动 */
            units: components["schemas"]["ChangeUnit"][];
            /** @description 命令/模型动作来源 */
            provenance_refs: components["schemas"]["Ref"][];
            /** @description 登记版本 */
            revision: components["schemas"]["Revision"];
        };
        /** @description 可审阅与选择的改动单位。 */
        ChangeUnit: {
            /** @description 改动块ID */
            id: components["schemas"]["ID"];
            /** @description 文件 */
            path: components["schemas"]["RelativePath"];
            /** @description 修改/新增/删除/改名 */
            kind: components["schemas"]["ChangeKind"];
            /** @description 改前版本 */
            before_ref?: components["schemas"]["Ref"];
            /** @description 改后版本 */
            after_ref?: components["schemas"]["Ref"];
            /** @description 文本改动位置 */
            location?: components["schemas"]["Location"];
            /** @description 差异内容 */
            patch_ref?: components["schemas"]["Ref"];
            /** @description 二进制不能行级合并 */
            binary: components["schemas"]["Bool"];
        };
        /**
         * @description 取值含义见字段及协议约束。
         * @enum {string}
         */
        CheckState: "passed" | "failed" | "not_run" | "blocked";
        /** @description 引用跨模块已提交版本，不能声称撤销外部动作。 */
        Checkpoint: {
            /** @description 检查点 */
            id: components["schemas"]["ID"];
            /** @description 运行版本 */
            run_ref: components["schemas"]["Ref"];
            /** @description 快照格式 */
            schema_version: components["schemas"]["Version"];
            /** @description 最后提交事件 */
            committed_event_seq: components["schemas"]["Revision"];
            /** @description 各域固定版本 */
            domains: components["schemas"]["DomainCheckpoint"][];
            /** @description 待对账动作 */
            pending_action_refs: components["schemas"]["Ref"][];
            /** @description 提交时间 */
            created_at: components["schemas"]["Timestamp"];
        };
        /** @description 模型的必要补充问题；不是审批请求。 */
        ClarificationPrompt: {
            /** @description 自包含问题 */
            text: components["schemas"]["NonEmptyText"];
            /** @description 缺什么和为什么需要 */
            reason: components["schemas"]["NonEmptyText"];
            /** @description 可选候选，空数组表示自由答复 */
            options: components["schemas"]["NonEmptyText"][];
        };
        /** @description 原问题的持久权威关联，用稳定Item表达，无新RefKind。 */
        ClarificationQuestion: {
            /**
             * @description 协议
             * @constant
             */
            protocol: "conversation-v1";
            /** @description 原Run */
            run_id: components["schemas"]["ID"];
            /** @description 所属会话 */
            conversation_id: components["schemas"]["ID"];
            /** @description agent_message问题Item */
            item_id: components["schemas"]["ID"];
            /** @description 问题CAS版本 */
            revision: components["schemas"]["Revision"];
            /** @description 提问时有效原文版本 */
            input_revision: components["schemas"]["Revision"];
            /** @description 用户看到的问题 */
            prompt: components["schemas"]["ClarificationPrompt"];
            /** @description 原ask动作的实际模型记录 */
            decision_record_ref: components["schemas"]["Ref"];
            /**
             * @description 问题状态
             * @enum {string}
             */
            state: "open" | "answered" | "stale" | "cancelled";
            /** @description 问题提交时间 */
            created_at: components["schemas"]["Timestamp"];
            /** @description 实际受理答复，answered时必需 */
            answer_input_ref?: components["schemas"]["UserInputRef"];
        };
        /** @description UI同源读取原问题与Run，刷新不创建新launch或会话。 */
        ClarificationView: {
            /** @description 当前实际问题 */
            question: components["schemas"]["ClarificationQuestion"];
            /** @description 当前Run版本，用于提交CAS */
            run_revision: components["schemas"]["Revision"];
            /** @description 当前Run真实状态 */
            run_status: components["schemas"]["RunStatus"];
            /** @description 当前有效输入版本 */
            input_revision: components["schemas"]["Revision"];
        };
        /** @description 独立认证用户对确切成果版本的审阅记录。 */
        CompletionAcceptance: {
            /** @description 确切不可变交付Bundle */
            bundle_ref: components["schemas"]["Ref"];
            /** @description 真实认证用户 */
            principal: components["schemas"]["Principal"];
            /** @description 用户决定 */
            decision: components["schemas"]["DeliveryDecision"];
            /** @description 实际登记时间 */
            created_at: components["schemas"]["Timestamp"];
        };
        /** @description 管理员配置发布经过校验后成为有效版本。 */
        ConfigurationVersion: {
            /** @description 配置域 */
            id: components["schemas"]["ID"];
            /** @description 版本 */
            revision: components["schemas"]["Revision"];
            /** @description 模型目录 */
            model_refs: components["schemas"]["ModelRef"][];
            /** @description 工具/搜索绑定 */
            provider_refs: components["schemas"]["Ref"][];
            /** @description 环境模板 */
            environment_template_refs: components["schemas"]["Ref"][];
            /** @description 能力开关 */
            feature_flags: components["schemas"]["FeatureFlag"][];
            /** @description 审批政策 */
            approval_policy_ref: components["schemas"]["Ref"];
            /** @description 存储部署政策 */
            storage_policy_ref: components["schemas"]["Ref"];
            /** @description 发布状态 */
            state: components["schemas"]["ProviderState"];
        };
        /** @description 命名兼容别名，结构以 Requirement 为准。 */
        Constraint: components["schemas"]["Requirement"];
        /** @description 语义目标+结构+证据契约，不写死行业字段。 */
        Contract: {
            /** @description 目标 */
            goal: components["schemas"]["NonEmptyText"];
            /** @description 验收条件 */
            requirements: components["schemas"]["Requirement"][];
            /** @description 交付物要求 */
            outputs: components["schemas"]["OutputSpec"][];
            /** @description 契约版本 */
            version: components["schemas"]["Version"];
            /**
             * @description Task结束是否需用户接受
             * @default false
             */
            acceptance_required: components["schemas"]["Bool"];
        };
        /**
         * @description 取值含义见字段及协议约束。
         * @enum {string}
         */
        ControlMode: "steer" | "enqueue" | "replace" | "cancel" | "deliver_partial";
        /** @description 会话不等于Task；首期单用户仍有独立主体。 */
        Conversation: {
            /** @description 会话 */
            id: components["schemas"]["ID"];
            /** @description 服务注入用户 */
            owner_id: components["schemas"]["ID"];
            /** @description 标题 */
            title: components["schemas"]["NonEmptyText"];
            /** @description 会话版本 */
            revision: components["schemas"]["Revision"];
            /** @description 可选本地/云项目绑定 */
            project_ref?: components["schemas"]["Ref"];
            /** @description 会话模型选择 */
            model_policy_ref: components["schemas"]["Ref"];
            /** @description 独立读写开关 */
            memory_policy: components["schemas"]["MemoryPolicy"];
            /** @description 创建时间 */
            created_at: components["schemas"]["Timestamp"];
            /** @description 修改时间 */
            updated_at: components["schemas"]["Timestamp"];
            /**
             * @description 用户选择；不能扩大管理员政策与本机权限。
             * @default manual
             */
            approval_mode: components["schemas"]["ApprovalMode"];
        };
        /** @description 用户选择当前会话模型；无法选inherit。 */
        ConversationModelChoice: {
            /** @description explicit或auto */
            mode: components["schemas"]["ConversationModelMode"];
            /** @description 固定模型ID */
            model_id?: components["schemas"]["ID"];
            /** @description Auto授权范围 */
            allowed_model_ids?: components["schemas"]["ID"][];
        };
        /**
         * @description 取值含义见字段及协议约束。
         * @enum {string}
         */
        ConversationModelMode: "explicit" | "auto";
        /** @description 稳定筛选条件的分页结果。 */
        ConversationPage: {
            /** @description 本页 */
            items: components["schemas"]["Conversation"][];
            /** @description 续页 */
            next_cursor?: components["schemas"]["Cursor"];
            /** @description 读取版本 */
            snapshot_revision: components["schemas"]["Revision"];
        };
        /** @description 新对话控制专用元信息；不能提交给旧0.1入口。 */
        ConversationRequestMeta: {
            /** @description 同一逻辑补充提交保持不变 */
            request_id: components["schemas"]["ID"];
            /**
             * @description 新控制HTTP版本
             * @constant
             */
            schema_version: "0.2";
            /** @description 原Run预期修订，必需且从1开始 */
            expected_revision: components["schemas"]["Revision"];
        };
        /** @description 首次调用中的可选理解提示，不是额外调用或权限。 */
        ConversationUnderstanding: {
            /** @description 理解摘要 */
            summary: components["schemas"]["NonEmptyText"];
            /** @description 明确的少量假设 */
            assumptions: components["schemas"]["NonEmptyText"][];
        };
        /** @description 创建会话。 */
        ConversationsCreateRequest: {
            /** @description 标题 */
            title: components["schemas"]["NonEmptyText"];
            /** @description 用户选定模型 */
            model_choice: components["schemas"]["ConversationModelChoice"];
            /** @description 获准项目 */
            project_ref?: components["schemas"]["Ref"];
            /** @description 记忆控制 */
            memory_policy: components["schemas"]["MemoryPolicy"];
            /**
             * @description 用户选择；不能扩大管理员政策与本机权限。
             * @default manual
             */
            approval_mode: components["schemas"]["ApprovalMode"];
        };
        /** @description 读取会话。 */
        ConversationsGetRequest: {
            /** @description 路径会话 */
            conversation_id: components["schemas"]["ID"];
        };
        /** @description 可见交互记录。 */
        ConversationsItemsRequest: {
            /** @description 会话 */
            conversation_id: components["schemas"]["ID"];
            /** @description 续页 */
            cursor?: components["schemas"]["Cursor"];
            /** @description 页大小 */
            limit?: components["schemas"]["PageLimit"];
        };
        /** @description 查询自己的会话。 */
        ConversationsListRequest: {
            /** @description 续页 */
            cursor?: components["schemas"]["Cursor"];
            /** @description 页大小 */
            limit?: components["schemas"]["PageLimit"];
        };
        /** @description 非负计数。 */
        Count: number;
        /** @description 不透明分页/事件位置；主体与过滤范围绑定，过期需快照。 */
        Cursor: string;
        /** @description 精确非负十进制字符串，用于金额，不以二进制float计账。 */
        Decimal: string;
        /** @description 删除回执含派生失效，不掩盖异步物理清除。 */
        DeletionReceipt: {
            /** @description 删除事务 */
            deletion_id: components["schemas"]["ID"];
            /** @description 逻辑删除 */
            deleted_refs: components["schemas"]["Ref"][];
            /** @description 索引/缓存失效 */
            invalidated_refs: components["schemas"]["Ref"][];
            /** @description 物理回收状态 */
            physical_cleanup_pending: components["schemas"]["Bool"];
        };
        /**
         * @description 取值含义见字段及协议约束。
         * @enum {string}
         */
        DeliveryDecision: "accept" | "reject" | "revise" | "partial_accept";
        /** @description 候选完成提案，不能由模型直接置Run为completed。 */
        DeliveryProposal: {
            /** @description 目标运行版本 */
            run_ref: components["schemas"]["Ref"];
            /** @description 交付标准 */
            contract_ref: components["schemas"]["Ref"];
            /** @description 建议终态 */
            outcome: components["schemas"]["Outcome"];
            /** @description 成果版本 */
            artifact_refs: components["schemas"]["Ref"][];
            /** @description 语义及执行证据报告 */
            report_ref: components["schemas"]["Ref"];
            /** @description 未确认外部效果 */
            unresolved_effect_refs: components["schemas"]["Ref"][];
            /** @description 提案时间 */
            created_at: components["schemas"]["Timestamp"];
        };
        /** @description 一个域的恢复指针。 */
        DomainCheckpoint: {
            /** @description 域名 */
            domain: components["schemas"]["ID"];
            /** @description 固定版本 */
            resource_ref: components["schemas"]["Ref"];
            /** @description 可选控制租约 */
            lease_ref?: components["schemas"]["Ref"];
        };
        /** @description 发送前只读理解提示；发送后不得冒充已执行。 */
        DraftPreview: {
            /** @description 对应草稿 */
            draft_revision: components["schemas"]["Revision"];
            /** @description 提示 */
            interpretation: components["schemas"]["Interpretation"];
            /** @description 实际模型 */
            model_config_ref: components["schemas"]["Ref"];
            /** @description 提示有效期 */
            expires_at: components["schemas"]["Timestamp"];
        };
        /** @description 毫秒；0仅在明确支持非阻塞查询的接口允许。 */
        Duration: number;
        /**
         * @description 取值含义见字段及协议约束。
         * @enum {string}
         */
        EffectKind: "read" | "internal_write" | "workspace_write" | "external_write" | "process" | "credential";
        /**
         * @description 取值含义见字段及协议约束。
         * @enum {string}
         */
        EffectState: "confirmed" | "pending" | "unknown";
        /** @description 显式环境变量；秘密值只由Runner/服务注入。 */
        EnvVar: {
            /** @description 变量名 */
            name: components["schemas"]["NonEmptyText"];
            /** @description 非秘密值 */
            value: components["schemas"]["Text"];
        };
        /** @description 持久事件有序号、版本与可追溯项。 */
        EventEnvelope: {
            /** @description 事件去重键 */
            event_id: components["schemas"]["ID"];
            /** @description 作用域流 */
            stream_id: components["schemas"]["ID"];
            /** @description 单调流序号 */
            seq: components["schemas"]["Revision"];
            /** @description 注册事件类型；payload_ref解引用后按EventPayload分支校验。 */
            type: components["schemas"]["EventType"];
            /** @description 事件协议版本 */
            schema_version: components["schemas"]["Version"];
            /** @description 提交时间 */
            occurred_at: components["schemas"]["Timestamp"];
            /** @description 交互项 */
            item_ref?: components["schemas"]["Ref"];
            /** @description 固定类型的事件payload */
            payload_ref: components["schemas"]["Ref"];
            /** @description 应用前版本 */
            base_revision?: components["schemas"]["Revision"];
            /** @description 应用后版本 */
            result_revision?: components["schemas"]["Revision"];
        };
        /** @description 稳定筛选条件的分页结果。 */
        EventPage: {
            /** @description 本页 */
            items: components["schemas"]["EventEnvelope"][];
            /** @description 续页 */
            next_cursor?: components["schemas"]["Cursor"];
            /** @description 读取版本 */
            snapshot_revision: components["schemas"]["Revision"];
        };
        /** @description 互斥分支；所有字段须匹配所选action。 */
        EventPayload: components["schemas"]["EventPayloadInput.committed"] | components["schemas"]["EventPayloadUnderstanding.preview"] | components["schemas"]["EventPayloadTask.frame.committed"] | components["schemas"]["EventPayloadPlan.committed"] | components["schemas"]["EventPayloadAgent.updated"] | components["schemas"]["EventPayloadAgent.result"] | components["schemas"]["EventPayloadTool.started"] | components["schemas"]["EventPayloadTool.completed"] | components["schemas"]["EventPayloadProcess.updated"] | components["schemas"]["EventPayloadChanges.committed"] | components["schemas"]["EventPayloadArtifact.registered"] | components["schemas"]["EventPayloadApproval.required"] | components["schemas"]["EventPayloadApproval.decided"] | components["schemas"]["EventPayloadItem.delta"] | components["schemas"]["EventPayloadItem.updated"] | components["schemas"]["EventPayloadRun.updated"] | components["schemas"]["EventPayloadVerification.completed"] | components["schemas"]["EventPayloadControl.accepted"] | components["schemas"]["EventPayloadMemory.deleted"] | components["schemas"]["EventPayloadConfiguration.activated"] | components["schemas"]["EventPayloadCheckpoint.committed"] | components["schemas"]["EventPayloadBudget.updated"] | components["schemas"]["EventPayloadQualityRegistered"] | components["schemas"]["EventPayloadQualitySaved"] | components["schemas"]["EventPayloadQualitySubmitted"] | components["schemas"]["EventPayloadQualityFeedbackSaved"];
        /** @description 按action选择的独立参数/结果分支。 */
        "EventPayloadAgent.result": {
            /**
             * @description 分支标识
             * @constant
             */
            action: "agent.result";
            /** @description 该分支的明确结构 */
            parameters: components["schemas"]["AgentResult"];
        };
        /** @description 按action选择的独立参数/结果分支。 */
        "EventPayloadAgent.updated": {
            /**
             * @description 分支标识
             * @constant
             */
            action: "agent.updated";
            /** @description 该分支的明确结构 */
            parameters: components["schemas"]["AgentInstance"];
        };
        /** @description 按action选择的独立参数/结果分支。 */
        "EventPayloadApproval.decided": {
            /**
             * @description 分支标识
             * @constant
             */
            action: "approval.decided";
            /** @description 该分支的明确结构 */
            parameters: components["schemas"]["ApprovalGrant"];
        };
        /** @description 按action选择的独立参数/结果分支。 */
        "EventPayloadApproval.required": {
            /**
             * @description 分支标识
             * @constant
             */
            action: "approval.required";
            /** @description 该分支的明确结构 */
            parameters: components["schemas"]["ApprovalRequest"];
        };
        /** @description 按action选择的独立参数/结果分支。 */
        "EventPayloadArtifact.registered": {
            /**
             * @description 分支标识
             * @constant
             */
            action: "artifact.registered";
            /** @description 该分支的明确结构 */
            parameters: components["schemas"]["ArtifactRecord"];
        };
        /** @description 按action选择的独立参数/结果分支。 */
        "EventPayloadBudget.updated": {
            /**
             * @description 分支标识
             * @constant
             */
            action: "budget.updated";
            /** @description 该分支的明确结构 */
            parameters: components["schemas"]["BudgetReservation"];
        };
        /** @description 按action选择的独立参数/结果分支。 */
        "EventPayloadChanges.committed": {
            /**
             * @description 分支标识
             * @constant
             */
            action: "changes.committed";
            /** @description 该分支的明确结构 */
            parameters: components["schemas"]["ChangeSet"];
        };
        /** @description 按action选择的独立参数/结果分支。 */
        "EventPayloadCheckpoint.committed": {
            /**
             * @description 分支标识
             * @constant
             */
            action: "checkpoint.committed";
            /** @description 该分支的明确结构 */
            parameters: components["schemas"]["Checkpoint"];
        };
        /** @description 按action选择的独立参数/结果分支。 */
        "EventPayloadConfiguration.activated": {
            /**
             * @description 分支标识
             * @constant
             */
            action: "configuration.activated";
            /** @description 该分支的明确结构 */
            parameters: components["schemas"]["ConfigurationVersion"];
        };
        /** @description 按action选择的独立参数/结果分支。 */
        "EventPayloadControl.accepted": {
            /**
             * @description 分支标识
             * @constant
             */
            action: "control.accepted";
            /** @description 该分支的明确结构 */
            parameters: components["schemas"]["Acknowledgement"];
        };
        /** @description 按action选择的独立参数/结果分支。 */
        "EventPayloadInput.committed": {
            /**
             * @description 分支标识
             * @constant
             */
            action: "input.committed";
            /** @description 该分支的明确结构 */
            parameters: components["schemas"]["InputRecord"];
        };
        /** @description 按action选择的独立参数/结果分支。 */
        "EventPayloadItem.delta": {
            /**
             * @description 分支标识
             * @constant
             */
            action: "item.delta";
            /** @description 该分支的明确结构 */
            parameters: components["schemas"]["ItemPatch"];
        };
        /** @description 按action选择的独立参数/结果分支。 */
        "EventPayloadItem.updated": {
            /**
             * @description 分支标识
             * @constant
             */
            action: "item.updated";
            /** @description 该分支的明确结构 */
            parameters: components["schemas"]["InteractionItem"];
        };
        /** @description 按action选择的独立参数/结果分支。 */
        "EventPayloadMemory.deleted": {
            /**
             * @description 分支标识
             * @constant
             */
            action: "memory.deleted";
            /** @description 该分支的明确结构 */
            parameters: components["schemas"]["DeletionReceipt"];
        };
        /** @description 按action选择的独立参数/结果分支。 */
        "EventPayloadPlan.committed": {
            /**
             * @description 分支标识
             * @constant
             */
            action: "plan.committed";
            /** @description 该分支的明确结构 */
            parameters: components["schemas"]["TaskGraph"];
        };
        /** @description 按action选择的独立参数/结果分支。 */
        "EventPayloadProcess.updated": {
            /**
             * @description 分支标识
             * @constant
             */
            action: "process.updated";
            /** @description 该分支的明确结构 */
            parameters: components["schemas"]["ProcessRecord"];
        };
        /** @description 注册的质量审计分支。 */
        EventPayloadQualityFeedbackSaved: {
            /**
             * @description 事件
             * @constant
             */
            action: "quality.feedback.saved";
            /** @description 审计元数据，不含凭据 */
            parameters: components["schemas"]["QualityFeedbackSavedEvent"];
        };
        /** @description 注册的质量审计分支。 */
        EventPayloadQualityRegistered: {
            /**
             * @description 事件
             * @constant
             */
            action: "quality.registered";
            /** @description 审计元数据，不含凭据 */
            parameters: components["schemas"]["QualityRegisteredEvent"];
        };
        /** @description 注册的质量审计分支。 */
        EventPayloadQualitySaved: {
            /**
             * @description 事件
             * @constant
             */
            action: "quality.saved";
            /** @description 审计元数据，不含凭据 */
            parameters: components["schemas"]["QualitySavedEvent"];
        };
        /** @description 注册的质量审计分支。 */
        EventPayloadQualitySubmitted: {
            /**
             * @description 事件
             * @constant
             */
            action: "quality.submitted";
            /** @description 审计元数据，不含凭据 */
            parameters: components["schemas"]["QualitySubmittedEvent"];
        };
        /** @description 按action选择的独立参数/结果分支。 */
        "EventPayloadRun.updated": {
            /**
             * @description 分支标识
             * @constant
             */
            action: "run.updated";
            /** @description 该分支的明确结构 */
            parameters: components["schemas"]["RunRecord"];
        };
        /** @description 按action选择的独立参数/结果分支。 */
        "EventPayloadTask.frame.committed": {
            /**
             * @description 分支标识
             * @constant
             */
            action: "task.frame.committed";
            /** @description 该分支的明确结构 */
            parameters: components["schemas"]["TaskFrame"];
        };
        /** @description 按action选择的独立参数/结果分支。 */
        "EventPayloadTool.completed": {
            /**
             * @description 分支标识
             * @constant
             */
            action: "tool.completed";
            /** @description 该分支的明确结构 */
            parameters: components["schemas"]["ToolResult"];
        };
        /** @description 按action选择的独立参数/结果分支。 */
        "EventPayloadTool.started": {
            /**
             * @description 分支标识
             * @constant
             */
            action: "tool.started";
            /** @description 该分支的明确结构 */
            parameters: components["schemas"]["ValidatedCall"];
        };
        /** @description 按action选择的独立参数/结果分支。 */
        "EventPayloadUnderstanding.preview": {
            /**
             * @description 分支标识
             * @constant
             */
            action: "understanding.preview";
            /** @description 该分支的明确结构 */
            parameters: components["schemas"]["DraftPreview"];
        };
        /** @description 按action选择的独立参数/结果分支。 */
        "EventPayloadVerification.completed": {
            /**
             * @description 分支标识
             * @constant
             */
            action: "verification.completed";
            /** @description 该分支的明确结构 */
            parameters: components["schemas"]["VerificationReport"];
        };
        /**
         * @description 取值含义见字段及协议约束。
         * @enum {string}
         */
        EventType: "input.committed" | "understanding.preview" | "task.frame.committed" | "plan.committed" | "agent.updated" | "agent.result" | "tool.started" | "tool.completed" | "process.updated" | "changes.committed" | "artifact.registered" | "approval.required" | "approval.decided" | "item.delta" | "item.updated" | "run.updated" | "verification.completed" | "control.accepted" | "memory.deleted" | "configuration.activated" | "checkpoint.committed" | "budget.updated" | "quality.registered" | "quality.saved" | "quality.submitted" | "quality.feedback.saved";
        /** @description 读取同主体持久事件的严格分支载荷。 */
        EventsPayloadRequest: {
            /** @description 事件 */
            event_id: components["schemas"]["ID"];
        };
        /** @description 分页读取历史事件。 */
        EventsReadRequest: {
            /** @description 会话 */
            conversation_id: components["schemas"]["ID"];
            /** @description 续页 */
            cursor?: components["schemas"]["Cursor"];
            /** @description 页大小 */
            limit?: components["schemas"]["PageLimit"];
            /** @description 仅返回此序号之后的新事件，分页期间固定 */
            after_seq?: components["schemas"]["Count"];
        };
        /** @description 真实进程退出码；不能用缺省0表示成功。 */
        ExitCode: number;
        /** @description 类型化失败，不携带秘密与隐藏思维。 */
        Failure: {
            /** @description 稳定错误码 */
            code: components["schemas"]["ID"];
            /** @description 错误类别 */
            category: components["schemas"]["FailureCategory"];
            /** @description 面向用户的明确失败原因；不得为空。 */
            message: components["schemas"]["NonEmptyText"];
            /** @description 是否允许按原契约恢复 */
            retryable: components["schemas"]["Bool"];
            /** @description 失败阶段 */
            failed_phase: components["schemas"]["NonEmptyText"];
            /** @description 可允许的修复建议 */
            recover_hint?: components["schemas"]["Text"];
            /** @description 受控诊断证据 */
            evidence_refs?: components["schemas"]["Ref"][];
            /** @description 实际副作用状态 */
            side_effect_state?: components["schemas"]["EffectState"];
            /** @description 可选退避 */
            retry_after_ms?: components["schemas"]["Duration"];
        };
        /**
         * @description 取值含义见字段及协议约束。
         * @enum {string}
         */
        FailureCategory: "arguments" | "authorization" | "policy" | "dependency" | "conflict" | "model_protocol" | "tool_business" | "infrastructure" | "budget" | "timeout" | "cancelled" | "unknown_effect";
        /** @description 关闭能力在发现、调用、恢复和子Agent处均执行。 */
        FeatureFlag: {
            /** @description 能力旗标 */
            id: components["schemas"]["ID"];
            /** @description 当前允许 */
            enabled: components["schemas"]["Bool"];
            /** @description 适用产品范围 */
            scope: components["schemas"]["ScopeSelector"];
            /** @description 说明 */
            reason: components["schemas"]["Text"];
        };
        /** @description SHA-256内容/规范参数摘要；不是匿名化。 */
        Hash: string;
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpApprovalsDecideResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["ApprovalGrant"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpApprovalsGetResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["ApprovalRequest"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpArtifactsContentResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["ArtifactContentView"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpArtifactsGetResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["ArtifactRecord"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpConversationsCreateResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["Conversation"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpConversationsGetResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["Conversation"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpConversationsItemsResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["ItemPage"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpConversationsListResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["ConversationPage"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpEventsPayloadResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["EventPayload"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpEventsReadResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["EventPage"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpModelsListResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["ModelPage"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpQualityFeedbackListResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["QualityFeedbackPage"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpQualityFeedbackSaveResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["QualityFeedback"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpQualityReviewsExportResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["QualityExport"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpQualityReviewsGetResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["QualityReviewView"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpQualityReviewsListResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["QualityReviewPage"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpQualityReviewsSaveResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["QualityReviewView"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpQualityReviewsSubmitResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["QualityReviewView"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpRunnerEnrollmentsBeginResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["RunnerEnrollmentRecord"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpRunnerEnrollmentsCompleteResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["RunnerEnrollmentRecord"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpRunnerEnrollmentsGetResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["RunnerEnrollmentRecord"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpRunnerEnrollmentsRevokeResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["RunnerEnrollmentRecord"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpRunnerLocalBeginResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["InstalledLaunchView"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpRunnerLocalGetResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["InstalledLaunchView"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpRunnerLocalStopResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["InstalledLaunchView"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpRunsClarificationAnswerResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["RunContinuationReceipt"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpRunsClarificationGetResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["ClarificationView"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpRunsContinuationGetResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["RunContinuationReceipt"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpRunsControlResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["Acknowledgement"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpRunsConversationGetResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["RunConversationView"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpRunsCorrectionCreateResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["RunContinuationReceipt"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpRunsDeliveryAcceptResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["CompletionAcceptance"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpRunsDeliveryResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["RunDeliveryView"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpRunsGetResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["RunRecord"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpRunsPresentationGetResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["RunPresentationView"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpTasksFrameResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["TaskFrame"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpTurnsLookupResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["RunRecord"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpTurnsSubmitResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["RunRecord"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpWebSessionExchangeResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["WebSession"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpWebSessionGetResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["WebSession"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 该接口的状态结果；ok才携带完整业务payload。 */
        HttpWebSessionLogoutResult: {
            /**
             * @description 接口状态
             * @enum {string}
             */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            /** @description ok的业务结果 */
            payload?: components["schemas"]["Acknowledgement"];
            /** @description 关联真实资源 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 本次提交/读取的域版本 */
            revision?: components["schemas"]["Revision"];
            /** @description 失败状态的明确原因 */
            failure?: components["schemas"]["Failure"];
            /** @description waiting时审批/进程/用户问题引用 */
            wait_ref?: components["schemas"]["Ref"];
            /** @description 发生消耗时真实统计 */
            usage_ref?: components["schemas"]["Ref"];
        };
        /** @description 域内不透明标识，不能推断主体或访问权限。 */
        ID: string;
        /** @description 原文追加保存，不覆盖已有输入。 */
        InputRecord: {
            /** @description 输入 */
            id: components["schemas"]["ID"];
            /** @description 会话 */
            conversation_id: components["schemas"]["ID"];
            /** @description 轮次 */
            turn_id: components["schemas"]["ID"];
            /** @description 用户原文 */
            text: components["schemas"]["Text"];
            /** @description 获准附件 */
            attachment_refs: components["schemas"]["Ref"][];
            /** @description 提交时间 */
            created_at: components["schemas"]["Timestamp"];
        };
        /** @description 原网页会话拥有的本机实例进度；ready只表示原生回调与当前根来源完成，不授予文件工具权限。 */
        InstalledLaunchView: {
            /** @description 原启动身份 */
            id: components["schemas"]["ID"];
            /** @description 原RequestMeta.request_id */
            request_id: components["schemas"]["ID"];
            /** @description 状态持久CAS版本 */
            revision: components["schemas"]["Revision"];
            /**
             * @description 实际生命周期
             * @enum {string}
             */
            state: "starting" | "waiting_device" | "connecting" | "selecting_directory" | "ready" | "closed" | "failed" | "unavailable";
            /** @description 管理员安装配置中的逻辑工作区；不是本机路径 */
            workspace_ref: components["schemas"]["Ref"];
            /** @description 原启动时间 */
            created_at: components["schemas"]["Timestamp"];
            /** @description 本次状态时间 */
            updated_at: components["schemas"]["Timestamp"];
            /** @description 原设备登记 */
            enrollment_id?: components["schemas"]["ID"];
            /** @description 当前实际通道绑定的设备版本与摘要 */
            device_ref?: components["schemas"]["Ref"];
            /** @description 原通道期限，不从轮询重新计时 */
            expires_at?: components["schemas"]["Timestamp"];
            /** @description 有界错误码；不输出路径/proof/凭据 */
            failure_code?: components["schemas"]["ID"];
        };
        /** @description 稳定前端交互对象，不依赖猜模型文本。 */
        InteractionItem: {
            /** @description 交互项 */
            id: components["schemas"]["ID"];
            /** @description 会话 */
            conversation_id: components["schemas"]["ID"];
            /** @description 运行 */
            run_id?: components["schemas"]["ID"];
            /** @description 消息/工具/文件/审批等 */
            type: components["schemas"]["ItemType"];
            /** @description 交互状态 */
            status: components["schemas"]["ItemStatus"];
            /** @description 项版本 */
            revision: components["schemas"]["Revision"];
            /** @description 可见内容 */
            text: components["schemas"]["Text"];
            /** @description 关联真实资源 */
            resource_refs: components["schemas"]["Ref"][];
            /** @description 开始 */
            created_at: components["schemas"]["Timestamp"];
            /** @description 最近更新 */
            updated_at: components["schemas"]["Timestamp"];
        };
        /** @description 一个有来源的理解候选。 */
        Interpretation: {
            /** @description 候选目标 */
            goal: components["schemas"]["NonEmptyText"];
            /** @description 未获用户确认的假设 */
            assumptions: components["schemas"]["NonEmptyText"][];
            /** @description 原文与补充来源 */
            source_refs: components["schemas"]["Ref"][];
            /** @description 缺少的信息 */
            missing_facts: components["schemas"]["NonEmptyText"][];
        };
        /** @description 稳定筛选条件的分页结果。 */
        ItemPage: {
            /** @description 本页 */
            items: components["schemas"]["InteractionItem"][];
            /** @description 续页 */
            next_cursor?: components["schemas"]["Cursor"];
            /** @description 读取版本 */
            snapshot_revision: components["schemas"]["Revision"];
        };
        /** @description 增量文本不可与整段替换混淆。 */
        ItemPatch: {
            /** @description 项 */
            item_id: components["schemas"]["ID"];
            /** @description 原版本 */
            base_revision: components["schemas"]["Revision"];
            /** @description 新状态 */
            status?: components["schemas"]["ItemStatus"];
            /** @description 追加文本 */
            text_delta?: components["schemas"]["Text"];
            /** @description 完整替换 */
            replacement_text?: components["schemas"]["Text"];
            /** @description 替换资源 */
            resource_refs?: components["schemas"]["Ref"][];
        };
        /**
         * @description 取值含义见字段及协议约束。
         * @enum {string}
         */
        ItemStatus: "pending" | "in_progress" | "waiting" | "completed" | "failed" | "declined" | "cancelled";
        /**
         * @description 取值含义见字段及协议约束。
         * @enum {string}
         */
        ItemType: "user_message" | "understanding" | "agent_message" | "plan" | "tool_call" | "command" | "file_change" | "approval" | "user_control" | "artifact" | "review" | "context_compression";
        /** @description 仅用于显式扩展载荷/工具动态参数；必须再按关联schema验证，非可信权限。 */
        JsonValue: null | boolean | number | string | components["schemas"]["JsonValue"][] | {
            [key: string]: components["schemas"]["JsonValue"];
        };
        /** @description 引用定位器，kind对应字段由Runtime交叉检查。 */
        Location: {
            /**
             * @description 定位种类
             * @enum {string}
             */
            kind: "whole" | "page" | "lines" | "paragraph" | "json_pointer" | "cell_range" | "text_span";
            /** @description 起点：页/行从1，字符offset从0 */
            start?: components["schemas"]["Count"];
            /** @description 含义随kind，字符end为排他 */
            end?: components["schemas"]["Count"];
            /** @description 段落ID/JSON Pointer/单元格范围 */
            anchor?: components["schemas"]["Text"];
            /** @description 工作区内文件位置 */
            relative_path?: components["schemas"]["RelativePath"];
        };
        /** @description 读写独立开关，关闭后不能继续使用派生缓存。 */
        MemoryPolicy: {
            /** @description 政策版本 */
            revision: components["schemas"]["Revision"];
            /** @description 允许读 */
            read_enabled: components["schemas"]["Bool"];
            /** @description 允许贡献 */
            contribute_enabled: components["schemas"]["Bool"];
            /** @description 生效范围 */
            scope: components["schemas"]["ScopeSelector"];
            /** @description 保留时间 */
            retention_ms?: components["schemas"]["Duration"];
        };
        /** @description 管理员模型目录，不返回密钥。 */
        ModelCatalogEntry: {
            /** @description 稳定目录ID */
            id: components["schemas"]["ID"];
            /** @description 提供方 */
            provider_ref: components["schemas"]["Ref"];
            /** @description 展示名 */
            display_name: components["schemas"]["NonEmptyText"];
            /** @description 上下文窗口 */
            context_limit_tokens: components["schemas"]["Count"];
            /** @description 输出上限 */
            output_limit_tokens: components["schemas"]["Count"];
            /** @description 协议能力 */
            capabilities: components["schemas"]["ID"][];
            /** @description 启停状态 */
            status: components["schemas"]["ProviderState"];
            /** @description 目录版本 */
            revision: components["schemas"]["Revision"];
            /** @description 可选固定价格；缺少时账单显式pending/estimated，不填0。 */
            pricing_ref?: components["schemas"]["Ref"];
        };
        /** @description 稳定筛选条件的分页结果。 */
        ModelPage: {
            /** @description 本页 */
            items: components["schemas"]["ModelCatalogEntry"][];
            /** @description 续页 */
            next_cursor?: components["schemas"]["Cursor"];
            /** @description 读取版本 */
            snapshot_revision: components["schemas"]["Revision"];
        };
        ModelRef: components["schemas"]["Ref"] & {
            /** @constant */
            kind?: "model";
        };
        /** @description 用户可用模型目录。 */
        ModelsListRequest: {
            /** @description 续页 */
            cursor?: components["schemas"]["Cursor"];
            /** @description 页大小 */
            limit?: components["schemas"]["PageLimit"];
        };
        /** @description 任务图节点，与Agent实例不是一一对应。 */
        NodeSpec: {
            /** @description 图内稳定ID */
            id: components["schemas"]["ID"];
            /** @description 节点目标 */
            goal: components["schemas"]["NonEmptyText"];
            /** @description 前置节点ID */
            depends_on: components["schemas"]["ID"][];
            /** @description 固定输入 */
            input_refs: components["schemas"]["Ref"][];
            /** @description 节点交付标准 */
            output_contract: components["schemas"]["Contract"];
            /** @description 可选指定角色 */
            agent_definition_ref?: components["schemas"]["Ref"];
            /** @description 预计读集 */
            read_refs: components["schemas"]["Ref"][];
            /** @description 预计写集 */
            write_refs: components["schemas"]["Ref"][];
            /** @description 节点预算上限 */
            budget: components["schemas"]["Budget"];
        };
        /** @description 非空业务文本。 */
        NonEmptyText: string;
        /** @description 动态工具参数或注册扩展配置；必须有具体ToolSpec/config schema约束。 */
        Object: {
            [key: string]: components["schemas"]["JsonValue"];
        };
        /**
         * @description 取值含义见字段及协议约束。
         * @enum {string}
         */
        Outcome: "succeeded" | "partial" | "blocked" | "failed" | "cancelled";
        /** @description 一个可交付结果要求。 */
        OutputSpec: {
            /** @description 成果要求ID */
            id: components["schemas"]["ID"];
            /** @description 成果类型 */
            kind: components["schemas"]["NonEmptyText"];
            /** @description 内容/用途 */
            description: components["schemas"]["NonEmptyText"];
            /** @description 必需 */
            required: components["schemas"]["Bool"];
            /** @description 结构检查schema */
            schema_ref?: components["schemas"]["Ref"];
        };
        /**
         * @description 每页数量。
         * @default 20
         */
        PageLimit: number;
        /** @description 可信身份摘要，不包含凭据。 */
        Principal: {
            /** @description 身份ID */
            id: components["schemas"]["ID"];
            /**
             * @description 身份类别
             * @enum {string}
             */
            kind: "user" | "admin" | "service" | "runner";
            /** @description 已认证会话/设备绑定 */
            auth_session_id: components["schemas"]["ID"];
            /** @description 委托来源 */
            delegated_by?: components["schemas"]["ID"];
        };
        /** @description 启动返回进程句柄，实际结果使用poll。 */
        ProcessRecord: {
            /** @description 进程 */
            id: components["schemas"]["ID"];
            /** @description 实际配置 */
            spec: components["schemas"]["ProcessSpec"];
            /** @description 进程状态 */
            status: components["schemas"]["ProcessState"];
            /** @description 启动时间 */
            started_at: components["schemas"]["Timestamp"];
            /** @description 结束时间 */
            ended_at?: components["schemas"]["Timestamp"];
            /** @description 真实退出码；未结束缺省 */
            exit_code?: components["schemas"]["ExitCode"];
            /** @description 输出内容 */
            stdout_ref?: components["schemas"]["Ref"];
            /** @description 错误输出 */
            stderr_ref?: components["schemas"]["Ref"];
            /** @description 未读日志 */
            output_cursor?: components["schemas"]["Cursor"];
            /** @description 命令造成的改动 */
            change_set_ref?: components["schemas"]["Ref"];
            /** @description 启动/终止失败 */
            failure?: components["schemas"]["Failure"];
        };
        /** @description argv模式优先；shell模式是单独能力。 */
        ProcessSpec: {
            /** @description 工作区版本 */
            workspace_ref: components["schemas"]["Ref"];
            /** @description 可执行文件或批准句柄 */
            executable: components["schemas"]["NonEmptyText"];
            /** @description 独立参数数组 */
            argv: components["schemas"]["Text"][];
            /** @description 根内工作目录，.表示根 */
            cwd: components["schemas"]["RelativePath"];
            /** @description 额外非秘密环境变量 */
            environment: components["schemas"]["EnvVar"][];
            /** @description 最大运行时间 */
            timeout_ms: components["schemas"]["Duration"];
            /** @description shell模式命令 */
            shell_command?: components["schemas"]["NonEmptyText"];
            /** @description 获准shell配置 */
            shell_profile_ref?: components["schemas"]["Ref"];
        };
        /**
         * @description 取值含义见字段及协议约束。
         * @enum {string}
         */
        ProcessState: "starting" | "running" | "exited" | "stopping" | "stopped" | "lost" | "failed";
        /**
         * @description 取值含义见字段及协议约束。
         * @enum {string}
         */
        ProviderState: "draft" | "validated" | "active" | "disabled" | "revoked";
        /** Answer */
        QualityAnswer: {
            /**
             * Decision
             * @enum {string}
             */
            decision: "reply" | "ask" | "tool" | "deliver" | "blocked" | "none";
            /** Text */
            text: string;
            /** Evidence */
            evidence: components["schemas"]["QualityOutputEvidence"][];
        };
        /** Case */
        QualityCase: {
            /** Id */
            id: string;
            /** Version */
            version: string;
            /**
             * Split
             * @enum {string}
             */
            split: "revision" | "holdout";
            /**
             * Category
             * @enum {string}
             */
            category: "office" | "academic" | "technical" | "missing_material" | "reasonable_ambiguity" | "correction";
            /** Prompt */
            prompt: string;
            rubric: components["schemas"]["QualityRubric"];
            /** Evidence */
            evidence: components["schemas"]["QualityEvidence"][];
            /**
             * Review Status
             * @enum {string}
             */
            review_status: "needs_human_review" | "human_verified";
            human_verification: components["schemas"]["QualityHumanVerification"] | null;
        };
        /** Evidence */
        QualityEvidence: {
            /** Id */
            id: string;
            /**
             * Kind
             * @enum {string}
             */
            kind: "provided_material" | "primary_source";
            /** Locator */
            locator: string;
            /** Captured At */
            captured_at: string;
            /** Text */
            text: string;
            /** Sha256 */
            sha256: string;
            /**
             * Url
             * @default null
             */
            url: string | null;
        };
        /** QualityExport */
        QualityExport: {
            /** Review Id */
            review_id: string;
            /** Revision */
            revision: number;
            /** Packet Sha256 */
            packet_sha256: string;
            /** Submission Sha256 */
            submission_sha256: string;
            /** Authenticated Reviewer Id */
            authenticated_reviewer_id: string;
            /**
             * Basis
             * @enum {string}
             */
            basis: "human_evidence_review" | "controlled_test";
            files: components["schemas"]["QualityFiles"];
        };
        /** QualityFeedback */
        QualityFeedback: {
            /** Id */
            id: string;
            /** Revision */
            revision: number;
            /** Run Id */
            run_id: string;
            /** Run Revision */
            run_revision: number;
            /** Input Revision */
            input_revision: number;
            /**
             * Category
             * @enum {string}
             */
            category: "latency" | "clarification" | "correction" | "presentation" | "content" | "other";
            /** Notes */
            notes: string;
            /** Created At */
            created_at: string;
            /** Updated At */
            updated_at: string;
        };
        /** QualityFeedbackPage */
        QualityFeedbackPage: {
            /** Items */
            items: components["schemas"]["QualityFeedback"][];
        };
        /**
         * QualityFeedbackSave
         * @description 认证网页质量审阅写入；要求 CAS 和原目标绑定。
         */
        QualityFeedbackSaveRequest: {
            /** Run Id */
            run_id: string;
            /** Feedback Id */
            feedback_id: string;
            /** Run Revision */
            run_revision: number;
            /** Input Revision */
            input_revision: number;
            /**
             * Category
             * @enum {string}
             */
            category: "latency" | "clarification" | "correction" | "presentation" | "content" | "other";
            /** Notes */
            notes: string;
        };
        /** @description 独立质量记录的事务审计，不是任务完成事件。 */
        QualityFeedbackSavedEvent: {
            /** @description 反馈 */
            feedback_id: components["schemas"]["ID"];
            /** @description 原任务 */
            run_id: components["schemas"]["ID"];
            /** @description 认证会话 */
            auth_session_id: components["schemas"]["ID"];
        };
        /** QualityFiles */
        QualityFiles: {
            /** Suite */
            suite: string;
            /** Manifest */
            manifest: string;
            /** Observations */
            observations: string;
            /** Reviews */
            reviews: string;
        };
        /** HumanVerification */
        QualityHumanVerification: {
            /** Reviewer Id */
            reviewer_id: string;
            /** Reviewed At */
            reviewed_at: string;
            /** Rubric Sha256 */
            rubric_sha256: string;
            /** Evidence Sha256 */
            evidence_sha256: string[];
            /** Record Locator */
            record_locator: string;
        };
        /** QualityJudgment */
        QualityJudgment: {
            /** Case Id */
            case_id: string;
            /** Attempt Id */
            attempt_id: string;
            /** Case Review */
            case_review: ("verified" | "needs_revision") | null;
            /** Evidence Reviewed */
            evidence_reviewed: boolean | null;
            /** Answer Correct */
            answer_correct: boolean | null;
            /** Unnecessary Block */
            unnecessary_block: boolean | null;
            /** Unsupported Execution */
            unsupported_execution: boolean | null;
            /** Requirements Preserved */
            requirements_preserved: boolean | null;
            /** Acceptable */
            acceptable: boolean | null;
            /** Critical Error */
            critical_error: boolean | null;
            /** Fabricated Evidence */
            fabricated_evidence: boolean | null;
            /** Notes */
            notes: string;
        };
        /** Labels */
        QualityLabels: {
            /** Answer Correct */
            answer_correct: boolean | null;
            /** Unnecessary Block */
            unnecessary_block: boolean | null;
            /** Unsupported Execution */
            unsupported_execution: boolean | null;
            /** Requirements Preserved */
            requirements_preserved: boolean | null;
            /** Acceptable */
            acceptable: boolean | null;
            /** Critical Error */
            critical_error: boolean;
        };
        /** NamedHash */
        QualityNamedHash: {
            /** Name */
            name: string;
            /** Sha256 */
            sha256: string;
        };
        /** Observation */
        QualityObservation: {
            /**
             * Schema Version
             * @constant
             */
            schema_version: "ms-e1.v1";
            /** Manifest Id */
            manifest_id: string;
            /** Case Id */
            case_id: string;
            /** Case Version */
            case_version: string;
            /** Attempt Id */
            attempt_id: string;
            /** Logical Request Id */
            logical_request_id: string;
            /** Attempt Number */
            attempt_number: number;
            /**
             * Phase
             * @enum {string}
             */
            phase: "answer" | "reviewer" | "tool" | "preparation";
            /**
             * Status
             * @enum {string}
             */
            status: "succeeded" | "failed" | "cancelled" | "unknown";
            /** Started At */
            started_at: string;
            /** Finished At */
            finished_at: string;
            /** Active Ms */
            active_ms: number;
            /** Wall Ms */
            wall_ms: number;
            usage: components["schemas"]["QualityUsage"];
            output: components["schemas"]["QualityAnswer"] | null;
            reviewer: components["schemas"]["QualityReviewerObservation"] | null;
            /** Failure Code */
            failure_code: string | null;
        };
        /** QualityOrigin */
        QualityOrigin: {
            /**
             * Kind
             * @enum {string}
             */
            kind: "actual_run" | "controlled_test";
            /** Principal Id */
            principal_id: string;
            /** Run Id */
            run_id: string;
            /** Run Revision */
            run_revision: number;
            /** Input Revision */
            input_revision: number;
            /** Source Commit */
            source_commit: string;
        };
        /** OutputEvidence */
        QualityOutputEvidence: {
            /**
             * Kind
             * @enum {string}
             */
            kind: "content" | "artifact" | "tool_call" | "tool_result" | "receipt";
            /** Id */
            id: string;
            /** Version */
            version: string;
            /** Sha256 */
            sha256: string;
        };
        /** @description 独立质量记录的事务审计，不是任务完成事件。 */
        QualityRegisteredEvent: {
            /** @description 审阅包 */
            review_id: components["schemas"]["ID"];
            /** @description 可信登记来源 */
            operator_id: components["schemas"]["ID"];
        };
        /** ReviewPacket */
        QualityReviewPacket: {
            /**
             * Schema Version
             * @constant
             */
            schema_version: "uaw.human-review-packet.v1";
            /** Created At */
            created_at: string;
            /** Input Sha256 */
            input_sha256: components["schemas"]["QualityNamedHash"][];
            /** Targets */
            targets: components["schemas"]["QualityReviewTarget"][];
        };
        /** QualityReviewPage */
        QualityReviewPage: {
            /** Items */
            items: components["schemas"]["QualityReviewSummary"][];
            /** Next Cursor */
            next_cursor: string | null;
        };
        /** ReviewSubmission */
        QualityReviewSubmission: {
            /**
             * Schema Version
             * @constant
             */
            schema_version: "uaw.human-review-submission.v1";
            /** Packet Sha256 */
            packet_sha256: string;
            /** Reviewer Id */
            reviewer_id: string;
            /** Reviewed At */
            reviewed_at: string;
            /** Human Attested */
            human_attested: boolean;
            /** Items */
            items: components["schemas"]["QualitySubmittedReview"][];
        };
        /** QualityReviewSummary */
        QualityReviewSummary: {
            /** Id */
            id: string;
            /** Revision */
            revision: number;
            /** Title */
            title: string;
            /**
             * Status
             * @enum {string}
             */
            status: "draft" | "submitted";
            /** Updated At */
            updated_at: string;
            origin: components["schemas"]["QualityOrigin"];
        };
        /** ReviewTarget */
        QualityReviewTarget: {
            /** Case Id */
            case_id: string;
            /** Case Version */
            case_version: string;
            /** Case Sha256 */
            case_sha256: string;
            /** Manifest Id */
            manifest_id: string;
            /** Attempt Id */
            attempt_id: string;
            /** Output Sha256 */
            output_sha256: string;
        };
        /** QualityReviewView */
        QualityReviewView: {
            /** Id */
            id: string;
            /** Revision */
            revision: number;
            /** Title */
            title: string;
            /** Created At */
            created_at: string;
            /** Updated At */
            updated_at: string;
            origin: components["schemas"]["QualityOrigin"];
            packet: components["schemas"]["QualityReviewPacket"];
            /** Packet Sha256 */
            packet_sha256: string;
            /** Targets */
            targets: components["schemas"]["QualityTarget"][];
            /**
             * Status
             * @enum {string}
             */
            status: "draft" | "submitted";
            /** Judgments */
            judgments: components["schemas"]["QualityJudgment"][];
            submission: components["schemas"]["QualityReviewSubmission"] | null;
        };
        /** ReviewerObservation */
        QualityReviewerObservation: {
            /** Target Attempt Id */
            target_attempt_id: string;
            /** Target Output Sha256 */
            target_output_sha256: string;
            /**
             * Verdict
             * @enum {string}
             */
            verdict: "passed" | "failed" | "not_applicable" | "unavailable";
        };
        /**
         * QualitySave
         * @description 认证网页质量审阅写入；要求 CAS 和原目标绑定。
         */
        QualityReviewsSaveRequest: {
            /** Review Id */
            review_id: string;
            /** Packet Sha256 */
            packet_sha256: string;
            /** Judgments */
            judgments: components["schemas"]["QualityJudgment"][];
        };
        /**
         * QualitySubmit
         * @description 认证网页质量审阅写入；要求 CAS 和原目标绑定。
         */
        QualityReviewsSubmitRequest: {
            /** Review Id */
            review_id: string;
            /** Packet Sha256 */
            packet_sha256: string;
            /** Judgments */
            judgments: components["schemas"]["QualityJudgment"][];
            /** Human Attested */
            human_attested: boolean;
        };
        /** Rubric */
        QualityRubric: {
            /**
             * Expected Behavior
             * @enum {string}
             */
            expected_behavior: "answer" | "clarify" | "decline" | "deliver" | "tool";
            /** Required Facts */
            required_facts: string[];
            /** Allowed Assumptions */
            allowed_assumptions: string[];
            /** Retained Requirements */
            retained_requirements: string[];
            /** Critical */
            critical: boolean;
        };
        /** QualitySave */
        QualitySave: {
            /** Review Id */
            review_id: string;
            /** Packet Sha256 */
            packet_sha256: string;
            /** Judgments */
            judgments: components["schemas"]["QualityJudgment"][];
        };
        /** @description 独立质量记录的事务审计，不是任务完成事件。 */
        QualitySavedEvent: {
            /** @description 审阅包 */
            review_id: components["schemas"]["ID"];
            /** @description 审阅修订 */
            revision: components["schemas"]["Revision"];
            /** @description 认证会话 */
            auth_session_id: components["schemas"]["ID"];
            /**
             * @description 判断来源
             * @enum {unknown}
             */
            basis: "human_evidence_review" | "controlled_test";
        };
        /** QualitySubmit */
        QualitySubmit: {
            /** Review Id */
            review_id: string;
            /** Packet Sha256 */
            packet_sha256: string;
            /** Judgments */
            judgments: components["schemas"]["QualityJudgment"][];
            /** Human Attested */
            human_attested: boolean;
        };
        /** @description 独立质量记录的事务审计，不是任务完成事件。 */
        QualitySubmittedEvent: {
            /** @description 审阅包 */
            review_id: components["schemas"]["ID"];
            /** @description 审阅修订 */
            revision: components["schemas"]["Revision"];
            /** @description 认证会话 */
            auth_session_id: components["schemas"]["ID"];
            /**
             * @description 判断来源
             * @enum {unknown}
             */
            basis: "human_evidence_review" | "controlled_test";
        };
        /** SubmittedReview */
        QualitySubmittedReview: {
            /** Case Id */
            case_id: string;
            /** Attempt Id */
            attempt_id: string;
            /**
             * Case Review
             * @enum {string}
             */
            case_review: "verified" | "needs_revision";
            /** Evidence Reviewed */
            evidence_reviewed: boolean;
            labels: components["schemas"]["QualityLabels"];
            /** Notes */
            notes: string;
        };
        /** QualityTarget */
        QualityTarget: {
            binding: components["schemas"]["QualityReviewTarget"];
            case: components["schemas"]["QualityCase"];
            answer: components["schemas"]["QualityAnswer"];
            /** Verifications */
            verifications: components["schemas"]["QualityObservation"][];
            /**
             * Verification Outputs
             * @default []
             */
            verification_outputs: components["schemas"]["QualityVerificationOutput"][];
        };
        /** Usage */
        QualityUsage: {
            /** Input Tokens */
            input_tokens: number | null;
            /** Output Tokens */
            output_tokens: number | null;
            /** Model Calls */
            model_calls: number | null;
            /** Tool Calls */
            tool_calls: number | null;
            /** Money */
            money: string | null;
            /** Currency */
            currency: string;
            /**
             * Billing State
             * @enum {string}
             */
            billing_state: "confirmed" | "pending" | "unknown";
        };
        /** QualityVerificationOutput */
        QualityVerificationOutput: {
            /** Attempt Id */
            attempt_id: string;
            /** Output Sha256 */
            output_sha256: string;
            /** Text */
            text: string;
        };
        /** @description 跨域资源引用；资源本体/权限归所属领域。 */
        Ref: {
            /** @description 来源类型 */
            kind: components["schemas"]["RefKind"];
            /** @description 资源ID */
            id: components["schemas"]["ID"];
            /** @description 实际来源版本 */
            version: components["schemas"]["Version"];
            /** @description 可选定位 */
            location?: components["schemas"]["Location"];
            /** @description 取得内容摘要 */
            content_hash?: components["schemas"]["Hash"];
            /** @description 可见范围，由来源域确认 */
            access_scope?: components["schemas"]["Scope"];
        };
        /**
         * @description 取值含义见字段及协议约束。
         * @enum {string}
         */
        RefKind: "web" | "asset" | "content" | "artifact" | "workspace" | "verification" | "local" | "input" | "task" | "task_frame" | "semantic_parse" | "plan" | "agent_definition" | "agent_instance" | "skill" | "memory" | "context" | "tool_call" | "policy" | "environment" | "process" | "configuration" | "checkpoint" | "usage" | "trace" | "evaluation" | "review" | "changeset" | "conversation" | "run" | "source" | "rule" | "role_profile" | "template" | "corpus" | "chunk" | "check" | "board" | "provider" | "connection" | "extension" | "blob" | "item" | "event" | "upload" | "reservation" | "budget" | "lease" | "approval" | "trigger" | "device" | "project" | "model" | "provider_profile";
        /** @description 项目内相对路径；机器还须解析真实路径/链接并核验授权根。 */
        RelativePath: string;
        /** @description 所有服务端操作的关联与幂等元数据。 */
        RequestMeta: {
            /** @description 同逻辑请求重试不变 */
            request_id: components["schemas"]["ID"];
            /**
             * @description 契约版本
             * @constant
             */
            schema_version: components["schemas"]["Version"];
            /** @description 修改时的CAS版本，创建可为0 */
            expected_revision?: components["schemas"]["Revision"] | null;
        };
        /** @description 用户/政策验收要求。 */
        Requirement: {
            /** @description 要求ID */
            id: components["schemas"]["ID"];
            /** @description 语义内容 */
            text: components["schemas"]["NonEmptyText"];
            /** @description 是否必需 */
            mandatory: components["schemas"]["Bool"];
            /** @description 用户或政策来源 */
            source_refs: components["schemas"]["Ref"][];
            /** @description 可接受证据类别 */
            evidence_kinds?: components["schemas"]["NonEmptyText"][];
        };
        /** @description 语义核验逐条覆盖要求。 */
        RequirementVerdict: {
            /** @description 要求 */
            requirement_id: components["schemas"]["ID"];
            /** @description 判定 */
            state: components["schemas"]["CheckState"];
            /** @description 实际证据 */
            evidence_refs: components["schemas"]["Ref"][];
            /** @description 判定依据 */
            reason: components["schemas"]["NonEmptyText"];
            /** @description 缺口 */
            limitations: components["schemas"]["NonEmptyText"][];
        };
        /**
         * @description 取值含义见字段及协议约束。
         * @enum {string}
         */
        ReservationState: "reserved" | "partially_settled" | "settled" | "released";
        /** @description 多维资源额度/估计/已用量；字段单位不混用。 */
        ResourceVector: {
            /** @description 输入token */
            input_tokens: components["schemas"]["Count"];
            /** @description 输出token */
            output_tokens: components["schemas"]["Count"];
            /** @description 模型调用 */
            model_calls: components["schemas"]["Count"];
            /** @description 工具调用 */
            tool_calls: components["schemas"]["Count"];
            /** @description 子实例数 */
            child_agents: components["schemas"]["Count"];
            /** @description 任务墙钟时间 */
            wall_time_ms: components["schemas"]["Duration"];
            /** @description 金额 */
            money: components["schemas"]["Decimal"];
            /** @description 币种 */
            currency: string;
        };
        /** @description CAS单调修订号；0仅表示对象尚不存在，已有版本从1开始。 */
        Revision: number;
        /** @description 原Run回答；身份和expected_run_revision来自meta。 */
        RunClarificationAnswerRequest: {
            /** @description 路径中的原Run */
            run_id: components["schemas"]["ID"];
            /** @description 路径中原问题稳定Item */
            question_item_id: components["schemas"]["ID"];
            /** @description 问题预期CAS版本 */
            expected_question_revision: components["schemas"]["Revision"];
            /** @description 原有效输入版本 */
            expected_input_revision: components["schemas"]["Revision"];
            /** @description 用户真实回答 */
            text: components["schemas"]["Text"];
            /** @description 本人获准材料，真实权限另查 */
            attachment_refs: components["schemas"]["Ref"][];
        };
        /** @description 读取原Run特定问题，不猜最新问题。 */
        RunClarificationGetRequest: {
            /** @description 路径原Run */
            run_id: components["schemas"]["ID"];
            /** @description 路径原问题 */
            question_item_id: components["schemas"]["ID"];
        };
        /** @description 原提交响应丢失或刷新后的受理/生效查询。 */
        RunContinuationGetRequest: {
            /** @description 路径原Run */
            run_id: components["schemas"]["ID"];
            /** @description 路径原逻辑提交ID */
            request_id: components["schemas"]["ID"];
        };
        /** @description 补充受理和实际生效回执，不等于最终成果完成。 */
        RunContinuationReceipt: {
            /**
             * @description 协议
             * @constant
             */
            protocol: "conversation-v1";
            /** @description 当前原Run；允许受理后又取消的查询结果 */
            run: components["schemas"]["RunRecord"];
            /** @description 原请求受理及生效状态 */
            patch: components["schemas"]["RunInputPatch"];
            /** @description 最后可续持久事件序号 */
            event_seq: components["schemas"]["Revision"];
        };
        /** @description 当前Run对话控制读图；问题ID来自持久来源，不猜消息文本。 */
        RunConversationView: {
            /**
             * @description 对话协议
             * @constant
             */
            protocol: "conversation-v1";
            /** @description 当前原Run及CAS修订 */
            run: components["schemas"]["RunRecord"];
            /** @description 当前有效输入版本 */
            input_revision: components["schemas"]["Revision"];
            /** @description 当前仍开放的具体问题；没有时省略，不传null */
            question?: components["schemas"]["ClarificationView"];
            /** @description 按输入版本排序的既有补充request_id；查询原回执用 */
            continuation_request_ids: components["schemas"]["ID"][];
        };
        /** @description 当前Run纠正，不让客户端指定任意执行节点或权限。 */
        RunCorrectionRequest: {
            /** @description 路径中的原Run */
            run_id: components["schemas"]["ID"];
            /** @description 原有效输入版本 */
            expected_input_revision: components["schemas"]["Revision"];
            /** @description 明确用户纠正 */
            text: components["schemas"]["Text"];
            /** @description 本人获准材料 */
            attachment_refs: components["schemas"]["Ref"][];
        };
        /** @description 真实成果、合同、逐项核验、完成提案的固定视图；不返回执行上下文。 */
        RunDeliveryView: {
            /** @description 所属Run */
            run_id: components["schemas"]["ID"];
            /** @description 固定Bundle */
            bundle_ref: components["schemas"]["Ref"];
            /** @description 固定成果 */
            artifact_ref: components["schemas"]["Ref"];
            /** @description 成果记录 */
            artifact: components["schemas"]["ArtifactRecord"];
            /** @description 实际正文 */
            content: components["schemas"]["ArtifactPreviewText"];
            /** @description 固定合同 */
            contract_ref: components["schemas"]["Ref"];
            /** @description 原要求合同 */
            contract: components["schemas"]["Contract"];
            /** @description 固定报告 */
            report_ref: components["schemas"]["Ref"];
            /** @description 逐项报告 */
            report: components["schemas"]["VerificationReport"];
            /** @description 固定提案 */
            proposal_ref: components["schemas"]["Ref"];
            /** @description 候选提案 */
            proposal: components["schemas"]["DeliveryProposal"];
            /** @description 合同要求用户接受 */
            requires_acceptance: components["schemas"]["Bool"];
            /** @description 相对于当前任务版本过时 */
            stale: components["schemas"]["Bool"];
            /** @description 实际用户决定 */
            acceptance?: components["schemas"]["CompletionAcceptance"];
        };
        /** @description 追加输入关联，InputRecord结构不变；受理与生效区分。 */
        RunInputPatch: {
            /**
             * @description 协议
             * @constant
             */
            protocol: "conversation-v1";
            /** @description 原Run */
            run_id: components["schemas"]["ID"];
            /** @description 会话 */
            conversation_id: components["schemas"]["ID"];
            /** @description 原用户逻辑请求 */
            request_id: components["schemas"]["ID"];
            /** @description 原子追加的实际InputRecord */
            input_ref: components["schemas"]["UserInputRef"];
            /**
             * @description 来源类型
             * @enum {string}
             */
            kind: "clarification_answer" | "correction";
            /** @description 原有效输入版本 */
            base_input_revision: components["schemas"]["Revision"];
            /** @description 受理后有效输入版本 */
            input_revision: components["schemas"]["Revision"];
            /** @description 澄清时必需；纠正时不允许 */
            question_item_id?: components["schemas"]["ID"];
            /** @description 原提问版本，与Item关联 */
            question_revision?: components["schemas"]["Revision"];
            /**
             * @description 受理/真实生效
             * @enum {string}
             */
            state: "accepted" | "applied" | "superseded" | "cancelled";
            /** @description 受理时间 */
            created_at: components["schemas"]["Timestamp"];
            /** @description 实际安全边界生效时刻 */
            applied_at?: components["schemas"]["Timestamp"];
        };
        /** @description 当前输入和Run修订的完整已登记成果引用；不是接受授权。 */
        RunPresentationDelivery: {
            /** @description 原完整成果包 */
            bundle_ref: components["schemas"]["Ref"];
            /** @description 原成果版本 */
            artifact_ref: components["schemas"]["Ref"];
            /** @description 原逐项核验 */
            report_ref: components["schemas"]["Ref"];
            /** @description 原交付提案 */
            proposal_ref: components["schemas"]["Ref"];
            /** @description 交付提案绑定的当前Run修订 */
            run_revision: components["schemas"]["Revision"];
            /** @description 原执行帧绑定的当前输入版本 */
            input_revision: components["schemas"]["Revision"];
            /** @description 真实核验结果，不代表独立事实质量 */
            outcome: components["schemas"]["Outcome"];
            /** @description 原合同是否要求本人接受 */
            requires_acceptance: components["schemas"]["Bool"];
        };
        /** @description 同次真实模型决策的理解提示，独立于不可变执行帧。 */
        RunPresentationUnderstanding: {
            /**
             * @description 尚未得到决策、有原理解或本次未提供
             * @enum {string}
             */
            state: "pending" | "available" | "not_provided";
            /** @description 本次读取的当前输入版本 */
            input_revision: components["schemas"]["Revision"];
            /** @description 真实模型摘要和假设；没有时省略 */
            value?: components["schemas"]["ConversationUnderstanding"];
            /** @description 原FirstDecisionRecord及摘要 */
            decision_record_ref?: components["schemas"]["Ref"];
            /** @description 原ModelOutput版本 */
            model_output_ref?: components["schemas"]["Ref"];
        };
        /** @description 同一只读数据库快照中的显示阶段、真实理解及当前成果；不授权执行或完成。 */
        RunPresentationView: {
            /**
             * @description 协议
             * @constant
             */
            protocol: "conversation-v1";
            /** @description 权威原Run，保持原CAS修订和状态 */
            run: components["schemas"]["RunRecord"];
            /** @description 当前有效输入版本 */
            input_revision: components["schemas"]["Revision"];
            /**
             * @description 显示阶段，不替代Run.status；取消受理尚未终态为stopping
             * @enum {string}
             */
            phase: "preparing" | "working" | "verifying" | "waiting_for_user" | "awaiting_acceptance" | "finalizing" | "needs_revision" | "stopping" | "completed" | "failed" | "cancelled" | "unavailable";
            /** @description 真实理解状态与来源 */
            understanding: components["schemas"]["RunPresentationUnderstanding"];
            /** @description 仅返回同一当前Run修订和输入的成果 */
            delivery?: components["schemas"]["RunPresentationDelivery"];
            /** @description 原普通回复与调用已停止的证据；仅释放本地发送查询，不结算Run/费用或授权续跑 */
            stopped_reply_ref?: components["schemas"]["Ref"];
            /** @description 一致性快照读取时间 */
            captured_at: components["schemas"]["Timestamp"];
        };
        /** @description 调度执行实体；任务历史有多个Run。 */
        RunRecord: {
            /** @description Run */
            id: components["schemas"]["ID"];
            /** @description 任务 */
            task_id: components["schemas"]["ID"];
            /** @description 入口会话 */
            conversation_id: components["schemas"]["ID"];
            /** @description 状态版本 */
            revision: components["schemas"]["Revision"];
            /** @description 当前状态 */
            status: components["schemas"]["RunStatus"];
            /** @description 根实例 */
            root_agent_ref?: components["schemas"]["Ref"];
            /** @description 当前任务理解 */
            frame_ref?: components["schemas"]["Ref"];
            /** @description 可选图 */
            plan_ref?: components["schemas"]["Ref"];
            /** @description 上限 */
            budget: components["schemas"]["Budget"];
            /** @description 终态 */
            outcome?: components["schemas"]["Outcome"];
            /** @description 受理时间 */
            created_at: components["schemas"]["Timestamp"];
            /** @description 实际结束 */
            ended_at?: components["schemas"]["Timestamp"];
        };
        /**
         * @description 取值含义见字段及协议约束。
         * @enum {string}
         */
        RunStatus: "queued" | "preparing" | "running" | "verifying" | "waiting_for_user" | "waiting_for_merge" | "completed" | "failed" | "cancelled";
        /** @description 独立控制源捕获的候选进程与角色key。 */
        RunnerEnrollmentPeer: {
            /** @description 独立OS观察 */
            identity: components["schemas"]["RunnerProcessIdentity"];
            /** @description 精确角色主体 */
            actor: components["schemas"]["Principal"];
            /**
             * @description 签名角色
             * @enum {string}
             */
            role: "control" | "device";
            /** @description 原key身份 */
            key_id: components["schemas"]["ID"];
            /** @description 原key版本与摘要 */
            key_ref: components["schemas"]["Ref"];
            /** @description 32字节Ed25519公钥标准base64；不是私钥 */
            public_key: string;
        };
        /** @description 双方持有证明签署的同一原账号设备挑战。 */
        RunnerEnrollmentProofDocument: {
            /**
             * @description 内部协议
             * @constant
             */
            protocol: "uaw-enrollment-v1";
            /** @description 本次操作 */
            enrollment_id: components["schemas"]["ID"];
            /** @description 准确候选快照 */
            candidate_ref: components["schemas"]["Ref"];
            /** @description 实际原Web会话 */
            owner: components["schemas"]["Principal"];
            /** @description 原设备 */
            device_id: components["schemas"]["ID"];
            /** @description 控制实例/key */
            control: components["schemas"]["RunnerEnrollmentPeer"];
            /** @description 设备实例/key */
            device: components["schemas"]["RunnerEnrollmentPeer"];
            /** @description 原随机nonce */
            nonce: string;
            /** @description 不超过Web会话及候选期限 */
            expires_at: components["schemas"]["Timestamp"];
        };
        /** @description 平台持久的首次设备登记状态；active仍不含目录授权。 */
        RunnerEnrollmentRecord: {
            /** @description 原操作 */
            id: components["schemas"]["ID"];
            /** @description CAS版本 */
            revision: components["schemas"]["Revision"];
            /**
             * @description 登记状态
             * @enum {string}
             */
            state: "pending" | "active" | "revoked" | "expired";
            /** @description 固定原挑战 */
            proof_document: components["schemas"]["RunnerEnrollmentProofDocument"];
            /** @description 登记时间 */
            created_at: components["schemas"]["Timestamp"];
            /** @description 独立本机决定记录 */
            confirmation_ref?: components["schemas"]["Ref"];
            /** @description 正式完整登记的固定摘要 */
            pairing_ref?: components["schemas"]["Ref"];
            /** @description 原设备持有签名 */
            device_proof?: string;
            /** @description 原控制持有签名 */
            control_proof?: string;
        };
        /** @description 当前Web用户请求独立候选的首次登记；不授予目录权限。 */
        RunnerEnrollmentsBeginRequest: {
            /** @description 已有受保护候选 */
            candidate_id: components["schemas"]["ID"];
        };
        /** @description 读取独立本机本人确认和双方签名证明后CAS登记。 */
        RunnerEnrollmentsCompleteRequest: {
            /** @description 原登记 */
            enrollment_id: components["schemas"]["ID"];
        };
        /** @description 当前原Web会话读取准确当前登记；不授予执行。 */
        RunnerEnrollmentsGetRequest: {
            /** @description 原登记 */
            enrollment_id: components["schemas"]["ID"];
        };
        /** @description 原当前Web用户撤销登记。 */
        RunnerEnrollmentsRevokeRequest: {
            /** @description 原登记 */
            enrollment_id: components["schemas"]["ID"];
        };
        /** @description 当前Web用户请求本机本人确认；异步返回原启动状态。 */
        RunnerLocalBeginRequest: Record<string, never>;
        /** @description 查询原本机启动；当前主体/通道/原根复查，后端重启标unavailable，不重发。 */
        RunnerLocalGetRequest: {
            /** @description 原启动 */
            launch_id: components["schemas"]["ID"];
        };
        /** @description 原Web用户停止并drain自己本机实例，保留原历史。 */
        RunnerLocalStopRequest: {
            /** @description 原启动 */
            launch_id: components["schemas"]["ID"];
        };
        /** @description 独立OS观察的进程实例；不是UAW账号。 */
        RunnerProcessIdentity: {
            /** @description 实际进程ID */
            pid: number;
            /** @description Windows FILETIME十进制字符串，避免签名JSON数值精度丢失 */
            created: string;
            /** @description 实际用户SID */
            user_sid: components["schemas"]["ID"];
            /** @description 实际本机登录SID */
            logon_sid: components["schemas"]["ID"];
        };
        /** @description 用户干预。 */
        RunsControlRequest: {
            /** @description 运行 */
            run_id: components["schemas"]["ID"];
            /** @description 控制指令 */
            control: components["schemas"]["UserControl"];
        };
        /** @description 实际用户决定整份合同交付；不直接设置completed。 */
        RunsDeliveryAcceptRequest: {
            /** @description 运行 */
            run_id: components["schemas"]["ID"];
            /** @description 精确Bundle */
            bundle_ref: components["schemas"]["Ref"];
            /** @description 精确成果 */
            artifact_ref: components["schemas"]["Ref"];
            /**
             * @description 现有DeliveryDecision的整份接受/拒绝子集。
             * @enum {string}
             */
            decision: "accept" | "reject";
        };
        /** @description 读取本人Run的最新真实固定交付；无交付返回missing。 */
        RunsDeliveryRequest: {
            /** @description 运行 */
            run_id: components["schemas"]["ID"];
        };
        /** @description 运行状态。 */
        RunsGetRequest: {
            /** @description 运行 */
            run_id: components["schemas"]["ID"];
        };
        /** @description 资源域选择器，不是授权凭证。 */
        Scope: {
            /** @description 有效主体，由可信通道提供 */
            principal_id: components["schemas"]["ID"];
            /** @description 会话范围 */
            conversation_id?: components["schemas"]["ID"];
            /** @description 任务范围 */
            task_id?: components["schemas"]["ID"];
            /** @description 已绑定项目范围 */
            project_id?: components["schemas"]["ID"];
            /** @description 进一步收窄资源 */
            resource_refs?: components["schemas"]["Ref"][];
            /** @description 请求/有效能力标签，服务端求交集 */
            capabilities?: components["schemas"]["NonEmptyText"][];
        };
        /** @description 客户端请求缩小可读范围，不能自行指定主体或授予能力。 */
        ScopeSelector: {
            /** @description 会话筛选 */
            conversation_id?: components["schemas"]["ID"];
            /** @description 任务筛选 */
            task_id?: components["schemas"]["ID"];
            /** @description 项目筛选 */
            project_id?: components["schemas"]["ID"];
            /** @description 指定材料 */
            resource_refs?: components["schemas"]["Ref"][];
        };
        /**
         * @description 取值含义见字段及协议约束。
         * @enum {string}
         */
        State: "pending" | "ready" | "running" | "waiting" | "completed" | "failed" | "stale" | "cancelled";
        /** @description 版本化任务理解。原文保持独立，理解不能覆盖原文。 */
        TaskFrame: {
            /** @description 关联任务 */
            task_id: components["schemas"]["ID"];
            /** @description 当前理解版本 */
            revision: components["schemas"]["Revision"];
            /** @description 原始用户输入 */
            original_input_ref: components["schemas"]["UserInputRef"];
            /** @description 运行中追加要求 */
            patch_refs: components["schemas"]["Ref"][];
            /** @description 本轮以完整原文及追加要求作为任务基准；AI摘要单独放summary。 */
            goal: string;
            /** @description 约束及来源 */
            constraints: components["schemas"]["Constraint"][];
            /** @description 成果要求 */
            output_specs: components["schemas"]["OutputSpec"][];
            /** @description 明确标记的假设 */
            assumptions: components["schemas"]["NonEmptyText"][];
            /** @description 未解问题 */
            unresolved: components["schemas"]["NonEmptyText"][];
            /** @description 已读取材料 */
            evidence_refs: components["schemas"]["Ref"][];
            /** @description 版本提交时间 */
            created_at: components["schemas"]["Timestamp"];
            /** @description AI理解的提示摘要，不授权动作、不替代完整原文。 */
            summary?: components["schemas"]["NonEmptyText"];
            /** @description 生成时的Run输入集合版本；旧理解不得覆盖新输入。 */
            input_revision?: components["schemas"]["Revision"];
            /** @description 有界模型提案及来源位置，保留模型回执。 */
            semantic_parse_ref?: components["schemas"]["Ref"];
        };
        /** @description 图修订不可变，执行状态另存。 */
        TaskGraph: {
            /** @description 所属任务 */
            task_id: components["schemas"]["ID"];
            /** @description 计划版本 */
            revision: components["schemas"]["Revision"];
            /**
             * @description 图仅用于步骤清单或DAG。
             * @enum {string}
             */
            planning: "steps" | "dag";
            /** @description 完整节点集合 */
            nodes: components["schemas"]["NodeSpec"][];
            /** @description 目标理解版本 */
            source_frame_ref: components["schemas"]["Ref"];
            /** @description 提交时间 */
            created_at: components["schemas"]["Timestamp"];
        };
        /** @description 读取当前任务理解。 */
        TasksFrameRequest: {
            /** @description 任务 */
            task_id: components["schemas"]["ID"];
        };
        /** @description 普通短文本；大正文使用Blob/Ref，限额为实验默认可配置。 */
        Text: string;
        /**
         * Format: date-time
         * @description UTC RFC3339时间；实现必须校验时间与时钟偏差。
         */
        Timestamp: string;
        /** @description 基础设施响应成功和业务成功分别表达。 */
        ToolResult: {
            /** @description 真实调用 */
            call_ref: components["schemas"]["Ref"];
            /** @description 成功/失败/等待/未知效果 */
            status: components["schemas"]["ToolStatus"];
            /** @description 由该工具output_schema约束的业务数据 */
            data?: components["schemas"]["Object"];
            /** @description 大结果/文件/证据 */
            output_refs: components["schemas"]["Ref"][];
            /** @description 失败 */
            failure?: components["schemas"]["Failure"];
            /** @description 副作用确定性 */
            effect_state: components["schemas"]["EffectState"];
            /** @description 调用用量 */
            usage_ref: components["schemas"]["Ref"];
            /** @description 分页 */
            next_cursor?: components["schemas"]["Cursor"];
        };
        /**
         * @description 取值含义见字段及协议约束。
         * @enum {string}
         */
        ToolStatus: "succeeded" | "failed" | "waiting" | "cancelled" | "unknown";
        /** @description 按原提交request_id查询当前Run；没有记录返回missing，不发送新任务。 */
        TurnsLookupRequest: {
            /** @description 原会话 */
            conversation_id: components["schemas"]["ID"];
            /** @description 原RequestMeta.request_id */
            request_id: components["schemas"]["ID"];
        };
        /** @description 提交原文并受理Run。 */
        TurnsSubmitRequest: {
            /** @description 会话 */
            conversation_id: components["schemas"]["ID"];
            /** @description 用户原文 */
            text: components["schemas"]["Text"];
            /** @description 附件 */
            attachment_refs: components["schemas"]["Ref"][];
            /** @description 继续已有任务 */
            task_id?: components["schemas"]["ID"];
            /** @description 继续任务必需 */
            expected_task_revision?: components["schemas"]["Revision"];
            /** @description 用户预算上限 */
            budget?: components["schemas"]["Budget"];
        };
        /** @description 补充、排队、替换、取消、先交现有成果语义明确。 */
        UserControl: {
            /** @description 干预方式 */
            mode: components["schemas"]["ControlMode"];
            /** @description 新要求；steer/enqueue/replace必需 */
            input_ref?: components["schemas"]["Ref"];
            /** @description 明确保留的成果 */
            preserve_refs: components["schemas"]["Ref"][];
            /** @description 解释 */
            reason: components["schemas"]["Text"];
        };
        /** @description 真实用户输入或已认证用户配置动作的引用；结构限制为input，来源真实性仍由Run核验。 */
        UserInputRef: components["schemas"]["Ref"] & {
            /** @constant */
            kind?: "input";
        };
        /** @description 参数schema通过的固定工具版本。 */
        ValidatedCall: {
            /** @description 固定契约 */
            tool_ref: components["schemas"]["Ref"];
            /** @description 规范参数 */
            arguments: components["schemas"]["Object"];
            /** @description 规范摘要 */
            arguments_hash: components["schemas"]["Hash"];
            /** @description 动作 */
            action_id: components["schemas"]["ID"];
        };
        /** @description 实际执行/资料核验的证据，不能伪造运行。 */
        VerificationCheck: {
            /** @description 检查 */
            id: components["schemas"]["ID"];
            /** @description 命令/结构/引用/语义 */
            kind: components["schemas"]["VerificationKind"];
            /** @description 覆盖要求 */
            requirement_ids: components["schemas"]["ID"][];
            /** @description passed/failed/not_run/blocked */
            state: components["schemas"]["CheckState"];
            /** @description 核验版本 */
            target_refs: components["schemas"]["Ref"][];
            /** @description 命令检查必需 */
            process_ref?: components["schemas"]["Ref"];
            /** @description 真实证据 */
            evidence_refs: components["schemas"]["Ref"][];
            /** @description 解释及限制 */
            summary: components["schemas"]["Text"];
        };
        /**
         * @description 取值含义见字段及协议约束。
         * @enum {string}
         */
        VerificationKind: "command" | "structure" | "reference" | "semantic" | "manual";
        /** @description 结构检查+真实执行+语义判定，不替代用户审阅。 */
        VerificationReport: {
            /** @description 报告 */
            id: components["schemas"]["ID"];
            /** @description 交付要求 */
            contract_ref: components["schemas"]["Ref"];
            /** @description 成果版本 */
            target_refs: components["schemas"]["Ref"][];
            /** @description 具体检查 */
            checks: components["schemas"]["VerificationCheck"][];
            /** @description 逐要求结果 */
            verdicts: components["schemas"]["RequirementVerdict"][];
            /** @description 总体结果 */
            outcome: components["schemas"]["Outcome"];
            /** @description 缺口 */
            limitations: components["schemas"]["NonEmptyText"][];
            /** @description 语义评审模型 */
            reviewer_model_config_ref?: components["schemas"]["Ref"];
            /** @description 生成时间 */
            created_at: components["schemas"]["Timestamp"];
        };
        /** @description 不可变内容/协议版本，不可用显示名替代。 */
        Version: string;
        /** @description 浏览器用户身份和CSRF；会话凭据只在HttpOnly cookie中。 */
        WebSession: {
            /** @description 服务器签发的用户和Web session */
            principal: components["schemas"]["Principal"];
            /** @description 固定会话截止 */
            expires_at: components["schemas"]["Timestamp"];
            /** @description 内存保留，修改请求X-UAW-CSRF */
            csrf_token: components["schemas"]["Hash"];
        };
        /** @description 精确Origin消费一次启动code。 */
        WebSessionExchangeRequest: {
            /** @description 原启动fragment凭据 */
            launch_code: components["schemas"]["NonEmptyText"];
        };
        /** @description 读取当前浏览器用户会话。 */
        WebSessionGetRequest: Record<string, never>;
        /** @description 撤销当前浏览器会话并清cookie。 */
        WebSessionLogoutRequest: Record<string, never>;
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    http_conversations_list: {
        parameters: {
            query?: {
                cursor?: components["schemas"]["Cursor"];
                limit?: components["schemas"]["PageLimit"];
            };
            header?: {
                "X-Request-Id"?: components["schemas"]["ID"];
                "X-UAW-Schema-Version"?: "0.1";
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsListResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsListResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsListResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsListResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsListResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsListResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsListResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsListResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsListResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsListResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsListResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_conversations_create: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    meta: components["schemas"]["RequestMeta"];
                    /** @description 创建会话。 */
                    payload: {
                        /** @description 标题 */
                        title: components["schemas"]["NonEmptyText"];
                        /** @description 用户选定模型 */
                        model_choice: components["schemas"]["ConversationModelChoice"];
                        /** @description 获准项目 */
                        project_ref?: components["schemas"]["Ref"];
                        /** @description 记忆控制 */
                        memory_policy: components["schemas"]["MemoryPolicy"];
                        /**
                         * @description 用户选择；不能扩大管理员政策与本机权限。
                         * @default manual
                         */
                        approval_mode?: components["schemas"]["ApprovalMode"];
                    };
                };
            };
        };
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsCreateResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsCreateResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsCreateResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsCreateResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsCreateResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsCreateResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsCreateResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsCreateResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsCreateResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsCreateResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsCreateResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_conversations_get: {
        parameters: {
            query?: never;
            header?: {
                "X-Request-Id"?: components["schemas"]["ID"];
                "X-UAW-Schema-Version"?: "0.1";
            };
            path: {
                conversation_id: components["schemas"]["ID"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsGetResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsGetResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsGetResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsGetResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsGetResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsGetResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_conversations_items: {
        parameters: {
            query?: {
                cursor?: components["schemas"]["Cursor"];
                limit?: components["schemas"]["PageLimit"];
            };
            header?: {
                "X-Request-Id"?: components["schemas"]["ID"];
                "X-UAW-Schema-Version"?: "0.1";
            };
            path: {
                conversation_id: components["schemas"]["ID"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsItemsResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsItemsResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsItemsResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsItemsResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsItemsResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsItemsResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsItemsResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsItemsResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsItemsResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsItemsResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpConversationsItemsResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_turns_submit: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                conversation_id: components["schemas"]["ID"];
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    meta: components["schemas"]["RequestMeta"];
                    /** @description 提交原文并受理Run。 */
                    payload: ({
                        /** @description 用户原文 */
                        text: components["schemas"]["Text"];
                        /** @description 附件 */
                        attachment_refs: components["schemas"]["Ref"][];
                        /** @description 继续已有任务 */
                        task_id?: components["schemas"]["ID"];
                        /** @description 继续任务必需 */
                        expected_task_revision?: components["schemas"]["Revision"];
                        /** @description 用户预算上限 */
                        budget?: components["schemas"]["Budget"];
                    } & unknown) | {
                        text?: unknown;
                    } | {
                        attachment_refs?: unknown;
                    };
                };
            };
        };
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpTurnsSubmitResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpTurnsSubmitResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpTurnsSubmitResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpTurnsSubmitResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpTurnsSubmitResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpTurnsSubmitResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpTurnsSubmitResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpTurnsSubmitResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpTurnsSubmitResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpTurnsSubmitResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpTurnsSubmitResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_runs_get: {
        parameters: {
            query?: never;
            header?: {
                "X-Request-Id"?: components["schemas"]["ID"];
                "X-UAW-Schema-Version"?: "0.1";
            };
            path: {
                run_id: components["schemas"]["ID"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsGetResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsGetResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsGetResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsGetResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsGetResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsGetResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_runs_control: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                run_id: components["schemas"]["ID"];
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    meta: components["schemas"]["RequestMeta"] & {
                        expected_revision: number;
                    };
                    /** @description 用户干预。 */
                    payload: {
                        /** @description 控制指令 */
                        control: components["schemas"]["UserControl"];
                    };
                };
            };
        };
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsControlResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsControlResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsControlResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsControlResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsControlResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsControlResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsControlResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsControlResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsControlResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsControlResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsControlResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_tasks_frame: {
        parameters: {
            query?: never;
            header?: {
                "X-Request-Id"?: components["schemas"]["ID"];
                "X-UAW-Schema-Version"?: "0.1";
            };
            path: {
                task_id: components["schemas"]["ID"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpTasksFrameResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpTasksFrameResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpTasksFrameResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpTasksFrameResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpTasksFrameResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpTasksFrameResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpTasksFrameResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpTasksFrameResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpTasksFrameResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpTasksFrameResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpTasksFrameResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_approvals_get: {
        parameters: {
            query?: never;
            header?: {
                "X-Request-Id"?: components["schemas"]["ID"];
                "X-UAW-Schema-Version"?: "0.1";
            };
            path: {
                approval_id: components["schemas"]["ID"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpApprovalsGetResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpApprovalsGetResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpApprovalsGetResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpApprovalsGetResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpApprovalsGetResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpApprovalsGetResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpApprovalsGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpApprovalsGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpApprovalsGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpApprovalsGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpApprovalsGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_approvals_decide: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                approval_id: components["schemas"]["ID"];
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    meta: components["schemas"]["RequestMeta"] & {
                        expected_revision: number;
                    };
                    /** @description 用户审批。 */
                    payload: {
                        /** @description 批准范围 */
                        decision: components["schemas"]["ApprovalDecision"];
                    };
                };
            };
        };
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpApprovalsDecideResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpApprovalsDecideResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpApprovalsDecideResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpApprovalsDecideResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpApprovalsDecideResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpApprovalsDecideResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpApprovalsDecideResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpApprovalsDecideResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpApprovalsDecideResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpApprovalsDecideResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpApprovalsDecideResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_events_read: {
        parameters: {
            query?: {
                cursor?: components["schemas"]["Cursor"];
                limit?: components["schemas"]["PageLimit"];
                after_seq?: components["schemas"]["Count"];
            };
            header?: {
                "X-Request-Id"?: components["schemas"]["ID"];
                "X-UAW-Schema-Version"?: "0.1";
            };
            path: {
                conversation_id: components["schemas"]["ID"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpEventsReadResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpEventsReadResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpEventsReadResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpEventsReadResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpEventsReadResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpEventsReadResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpEventsReadResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpEventsReadResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpEventsReadResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpEventsReadResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpEventsReadResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_events_payload: {
        parameters: {
            query?: never;
            header?: {
                "X-Request-Id"?: components["schemas"]["ID"];
                "X-UAW-Schema-Version"?: "0.1";
            };
            path: {
                event_id: components["schemas"]["ID"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpEventsPayloadResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpEventsPayloadResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpEventsPayloadResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpEventsPayloadResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpEventsPayloadResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpEventsPayloadResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpEventsPayloadResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpEventsPayloadResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpEventsPayloadResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpEventsPayloadResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpEventsPayloadResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_turns_lookup: {
        parameters: {
            query?: never;
            header?: {
                "X-Request-Id"?: components["schemas"]["ID"];
                "X-UAW-Schema-Version"?: "0.1";
            };
            path: {
                conversation_id: components["schemas"]["ID"];
                request_id: components["schemas"]["ID"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpTurnsLookupResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpTurnsLookupResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpTurnsLookupResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpTurnsLookupResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpTurnsLookupResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpTurnsLookupResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpTurnsLookupResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpTurnsLookupResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpTurnsLookupResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpTurnsLookupResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpTurnsLookupResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_runs_delivery: {
        parameters: {
            query?: never;
            header?: {
                "X-Request-Id"?: components["schemas"]["ID"];
                "X-UAW-Schema-Version"?: "0.1";
            };
            path: {
                run_id: components["schemas"]["ID"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsDeliveryResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsDeliveryResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsDeliveryResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsDeliveryResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsDeliveryResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsDeliveryResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsDeliveryResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsDeliveryResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsDeliveryResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsDeliveryResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsDeliveryResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_runs_delivery_accept: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                run_id: components["schemas"]["ID"];
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    meta: components["schemas"]["RequestMeta"];
                    /** @description 实际用户决定整份合同交付；不直接设置completed。 */
                    payload: {
                        /** @description 精确Bundle */
                        bundle_ref: components["schemas"]["Ref"];
                        /** @description 精确成果 */
                        artifact_ref: components["schemas"]["Ref"];
                        /**
                         * @description 现有DeliveryDecision的整份接受/拒绝子集。
                         * @enum {string}
                         */
                        decision: "accept" | "reject";
                    };
                };
            };
        };
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsDeliveryAcceptResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsDeliveryAcceptResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsDeliveryAcceptResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsDeliveryAcceptResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsDeliveryAcceptResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsDeliveryAcceptResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsDeliveryAcceptResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsDeliveryAcceptResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsDeliveryAcceptResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsDeliveryAcceptResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsDeliveryAcceptResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_artifacts_get: {
        parameters: {
            query?: {
                version?: components["schemas"]["Version"];
            };
            header?: {
                "X-Request-Id"?: components["schemas"]["ID"];
                "X-UAW-Schema-Version"?: "0.1";
            };
            path: {
                artifact_id: components["schemas"]["ID"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpArtifactsGetResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpArtifactsGetResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpArtifactsGetResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpArtifactsGetResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpArtifactsGetResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpArtifactsGetResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpArtifactsGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpArtifactsGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpArtifactsGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpArtifactsGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpArtifactsGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_artifacts_content: {
        parameters: {
            query: {
                version: components["schemas"]["Version"];
                content_hash: components["schemas"]["Hash"];
            };
            header?: {
                "X-Request-Id"?: components["schemas"]["ID"];
                "X-UAW-Schema-Version"?: "0.1";
            };
            path: {
                artifact_id: components["schemas"]["ID"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpArtifactsContentResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpArtifactsContentResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpArtifactsContentResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpArtifactsContentResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpArtifactsContentResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpArtifactsContentResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpArtifactsContentResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpArtifactsContentResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpArtifactsContentResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpArtifactsContentResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpArtifactsContentResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_runner_enrollments_begin: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    meta: components["schemas"]["RequestMeta"];
                    /** @description 当前Web用户请求独立候选的首次登记；不授予目录权限。 */
                    payload: {
                        /** @description 已有受保护候选 */
                        candidate_id: components["schemas"]["ID"];
                    };
                };
            };
        };
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsBeginResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsBeginResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsBeginResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsBeginResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsBeginResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsBeginResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsBeginResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsBeginResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsBeginResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsBeginResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsBeginResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_runner_enrollments_get: {
        parameters: {
            query?: never;
            header?: {
                "X-Request-Id"?: components["schemas"]["ID"];
                "X-UAW-Schema-Version"?: "0.1";
            };
            path: {
                enrollment_id: components["schemas"]["ID"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsGetResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsGetResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsGetResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsGetResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsGetResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsGetResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_runner_enrollments_complete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                enrollment_id: components["schemas"]["ID"];
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    meta: components["schemas"]["RequestMeta"];
                    /** @description 读取独立本机本人确认和双方签名证明后CAS登记。 */
                    payload: Record<string, never>;
                };
            };
        };
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsCompleteResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsCompleteResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsCompleteResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsCompleteResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsCompleteResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsCompleteResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsCompleteResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsCompleteResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsCompleteResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsCompleteResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsCompleteResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_runner_enrollments_revoke: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                enrollment_id: components["schemas"]["ID"];
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    meta: components["schemas"]["RequestMeta"];
                    /** @description 原当前Web用户撤销登记。 */
                    payload: Record<string, never>;
                };
            };
        };
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsRevokeResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsRevokeResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsRevokeResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsRevokeResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsRevokeResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsRevokeResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsRevokeResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsRevokeResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsRevokeResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsRevokeResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerEnrollmentsRevokeResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_runner_local_begin: {
        parameters: {
            query?: never;
            header: {
                Origin: string;
                "X-UAW-CSRF": components["schemas"]["Hash"];
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    meta: components["schemas"]["RequestMeta"];
                    /** @description 当前Web用户请求本机本人确认；异步返回原启动状态。 */
                    payload: Record<string, never>;
                };
            };
        };
        responses: {
            /** @description 原启动已登记，payload是实际生命周期状态；不是批准或文件权限。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerLocalBeginResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerLocalBeginResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerLocalBeginResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerLocalBeginResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerLocalBeginResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerLocalBeginResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerLocalBeginResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerLocalBeginResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerLocalBeginResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description 实际部署或当前来源不可用；不产生隐式授权。 */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerLocalBeginResult"];
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerLocalBeginResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_runner_local_get: {
        parameters: {
            query?: never;
            header?: {
                "X-Request-Id"?: components["schemas"]["ID"];
                "X-UAW-Schema-Version"?: "0.1";
                Origin?: string;
            };
            path: {
                launch_id: components["schemas"]["ID"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerLocalGetResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerLocalGetResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerLocalGetResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerLocalGetResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerLocalGetResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerLocalGetResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerLocalGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerLocalGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerLocalGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerLocalGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description 实际部署或当前来源不可用；不产生隐式授权。 */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerLocalGetResult"];
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerLocalGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_runner_local_stop: {
        parameters: {
            query?: never;
            header: {
                Origin: string;
                "X-UAW-CSRF": components["schemas"]["Hash"];
            };
            path: {
                launch_id: components["schemas"]["ID"];
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    meta: components["schemas"]["RequestMeta"];
                    /** @description 原Web用户停止并drain自己本机实例，保留原历史。 */
                    payload: Record<string, never>;
                };
            };
        };
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerLocalStopResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerLocalStopResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerLocalStopResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerLocalStopResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerLocalStopResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerLocalStopResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerLocalStopResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerLocalStopResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerLocalStopResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerLocalStopResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description 实际部署或当前来源不可用；不产生隐式授权。 */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerLocalStopResult"];
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunnerLocalStopResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_runs_presentation_get: {
        parameters: {
            query?: never;
            header?: {
                "X-Request-Id"?: components["schemas"]["ID"];
                "X-UAW-Schema-Version"?: "0.2";
                /** @description cookie写请求必需且精确匹配已发布同源配置；bearer遵守原CLI认证规则。 */
                Origin?: string;
            };
            path: {
                run_id: components["schemas"]["ID"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsPresentationGetResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsPresentationGetResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsPresentationGetResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsPresentationGetResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsPresentationGetResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsPresentationGetResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsPresentationGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsPresentationGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsPresentationGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsPresentationGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description 新handler或当前可信来源未装配，明确不可用；不续跑旧Run。 */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsPresentationGetResult"];
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsPresentationGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_runs_conversation_get: {
        parameters: {
            query?: never;
            header?: {
                "X-Request-Id"?: components["schemas"]["ID"];
                "X-UAW-Schema-Version"?: "0.2";
                /** @description cookie写请求必需且精确匹配已发布同源配置；bearer遵守原CLI认证规则。 */
                Origin?: string;
            };
            path: {
                run_id: components["schemas"]["ID"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsConversationGetResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsConversationGetResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsConversationGetResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsConversationGetResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsConversationGetResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsConversationGetResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsConversationGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsConversationGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsConversationGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsConversationGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description 新handler或当前可信来源未装配，明确不可用；不续跑旧Run。 */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsConversationGetResult"];
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsConversationGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_runs_clarification_get: {
        parameters: {
            query?: never;
            header?: {
                "X-Request-Id"?: components["schemas"]["ID"];
                "X-UAW-Schema-Version"?: "0.2";
                /** @description cookie写请求必需且精确匹配已发布同源配置；bearer遵守原CLI认证规则。 */
                Origin?: string;
            };
            path: {
                run_id: components["schemas"]["ID"];
                question_item_id: components["schemas"]["ID"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsClarificationGetResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsClarificationGetResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsClarificationGetResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsClarificationGetResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsClarificationGetResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsClarificationGetResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsClarificationGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsClarificationGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsClarificationGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsClarificationGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description 新handler或当前可信来源未装配，明确不可用；不续跑旧Run。 */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsClarificationGetResult"];
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsClarificationGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_runs_clarification_answer: {
        parameters: {
            query?: never;
            header?: {
                /** @description cookie写请求必需且精确匹配已发布同源配置；bearer遵守原CLI认证规则。 */
                Origin?: string;
                /** @description 使用cookie会话写请求时必需；缺失不得执行。 */
                "X-UAW-CSRF"?: components["schemas"]["Hash"];
            };
            path: {
                run_id: components["schemas"]["ID"];
                question_item_id: components["schemas"]["ID"];
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    meta: components["schemas"]["ConversationRequestMeta"] & {
                        expected_revision: number;
                    };
                    /** @description 原Run回答；身份和expected_run_revision来自meta。 */
                    payload: {
                        /** @description 问题预期CAS版本 */
                        expected_question_revision: components["schemas"]["Revision"];
                        /** @description 原有效输入版本 */
                        expected_input_revision: components["schemas"]["Revision"];
                        /** @description 用户真实回答 */
                        text: components["schemas"]["Text"];
                        /** @description 本人获准材料，真实权限另查 */
                        attachment_refs: components["schemas"]["Ref"][];
                    } | {
                        text: unknown;
                    } | {
                        attachment_refs: unknown;
                    };
                };
            };
        };
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsClarificationAnswerResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsClarificationAnswerResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsClarificationAnswerResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsClarificationAnswerResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsClarificationAnswerResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsClarificationAnswerResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsClarificationAnswerResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsClarificationAnswerResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsClarificationAnswerResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsClarificationAnswerResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description 新handler或当前可信来源未装配，明确不可用；不续跑旧Run。 */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsClarificationAnswerResult"];
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsClarificationAnswerResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_runs_correction_create: {
        parameters: {
            query?: never;
            header?: {
                /** @description cookie写请求必需且精确匹配已发布同源配置；bearer遵守原CLI认证规则。 */
                Origin?: string;
                /** @description 使用cookie会话写请求时必需；缺失不得执行。 */
                "X-UAW-CSRF"?: components["schemas"]["Hash"];
            };
            path: {
                run_id: components["schemas"]["ID"];
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    meta: components["schemas"]["ConversationRequestMeta"] & {
                        expected_revision: number;
                    };
                    /** @description 当前Run纠正，不让客户端指定任意执行节点或权限。 */
                    payload: {
                        /** @description 原有效输入版本 */
                        expected_input_revision: components["schemas"]["Revision"];
                        /** @description 明确用户纠正 */
                        text: components["schemas"]["Text"];
                        /** @description 本人获准材料 */
                        attachment_refs: components["schemas"]["Ref"][];
                    } | {
                        text: unknown;
                    } | {
                        attachment_refs: unknown;
                    };
                };
            };
        };
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsCorrectionCreateResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsCorrectionCreateResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsCorrectionCreateResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsCorrectionCreateResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsCorrectionCreateResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsCorrectionCreateResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsCorrectionCreateResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsCorrectionCreateResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsCorrectionCreateResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsCorrectionCreateResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description 新handler或当前可信来源未装配，明确不可用；不续跑旧Run。 */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsCorrectionCreateResult"];
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsCorrectionCreateResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_runs_continuation_get: {
        parameters: {
            query?: never;
            header?: {
                "X-Request-Id"?: components["schemas"]["ID"];
                "X-UAW-Schema-Version"?: "0.2";
                /** @description cookie写请求必需且精确匹配已发布同源配置；bearer遵守原CLI认证规则。 */
                Origin?: string;
            };
            path: {
                run_id: components["schemas"]["ID"];
                request_id: components["schemas"]["ID"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsContinuationGetResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsContinuationGetResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsContinuationGetResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsContinuationGetResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsContinuationGetResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsContinuationGetResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsContinuationGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsContinuationGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsContinuationGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsContinuationGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description 新handler或当前可信来源未装配，明确不可用；不续跑旧Run。 */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsContinuationGetResult"];
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpRunsContinuationGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_quality_reviews_list: {
        parameters: {
            query?: {
                cursor?: components["schemas"]["ID"];
            };
            header?: {
                "X-Request-Id"?: components["schemas"]["ID"];
                "X-UAW-Schema-Version"?: "0.1";
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsListResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsListResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsListResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsListResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsListResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsListResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsListResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsListResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsListResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsListResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsListResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_quality_reviews_get: {
        parameters: {
            query?: never;
            header?: {
                "X-Request-Id"?: components["schemas"]["ID"];
                "X-UAW-Schema-Version"?: "0.1";
            };
            path: {
                review_id: components["schemas"]["ID"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsGetResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsGetResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsGetResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsGetResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsGetResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsGetResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_quality_reviews_save: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                review_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    meta: components["schemas"]["RequestMeta"];
                    /**
                     * QualitySave
                     * @description 认证网页质量审阅写入；要求 CAS 和原目标绑定。
                     */
                    payload: {
                        /** Packet Sha256 */
                        packet_sha256: string;
                        /** Judgments */
                        judgments: components["schemas"]["QualityJudgment"][];
                    };
                };
            };
        };
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsSaveResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsSaveResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsSaveResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsSaveResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsSaveResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsSaveResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsSaveResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsSaveResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsSaveResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsSaveResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsSaveResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_quality_reviews_submit: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                review_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    meta: components["schemas"]["RequestMeta"];
                    /**
                     * QualitySubmit
                     * @description 认证网页质量审阅写入；要求 CAS 和原目标绑定。
                     */
                    payload: {
                        /** Packet Sha256 */
                        packet_sha256: string;
                        /** Judgments */
                        judgments: components["schemas"]["QualityJudgment"][];
                        /** Human Attested */
                        human_attested: boolean;
                    };
                };
            };
        };
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsSubmitResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsSubmitResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsSubmitResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsSubmitResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsSubmitResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsSubmitResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsSubmitResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsSubmitResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsSubmitResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsSubmitResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsSubmitResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_quality_reviews_export: {
        parameters: {
            query?: never;
            header?: {
                "X-Request-Id"?: components["schemas"]["ID"];
                "X-UAW-Schema-Version"?: "0.1";
            };
            path: {
                review_id: components["schemas"]["ID"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsExportResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsExportResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsExportResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsExportResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsExportResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsExportResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsExportResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsExportResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsExportResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsExportResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityReviewsExportResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_quality_feedback_list: {
        parameters: {
            query?: never;
            header?: {
                "X-Request-Id"?: components["schemas"]["ID"];
                "X-UAW-Schema-Version"?: "0.1";
            };
            path: {
                run_id: components["schemas"]["ID"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityFeedbackListResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityFeedbackListResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityFeedbackListResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityFeedbackListResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityFeedbackListResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityFeedbackListResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityFeedbackListResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityFeedbackListResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityFeedbackListResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityFeedbackListResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityFeedbackListResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_quality_feedback_save: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                run_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    meta: components["schemas"]["RequestMeta"];
                    /**
                     * QualityFeedbackSave
                     * @description 认证网页质量审阅写入；要求 CAS 和原目标绑定。
                     */
                    payload: {
                        /** Feedback Id */
                        feedback_id: string;
                        /** Run Revision */
                        run_revision: number;
                        /** Input Revision */
                        input_revision: number;
                        /**
                         * Category
                         * @enum {string}
                         */
                        category: "latency" | "clarification" | "correction" | "presentation" | "content" | "other";
                        /** Notes */
                        notes: string;
                    };
                };
            };
        };
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityFeedbackSaveResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityFeedbackSaveResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityFeedbackSaveResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityFeedbackSaveResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityFeedbackSaveResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityFeedbackSaveResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityFeedbackSaveResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityFeedbackSaveResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityFeedbackSaveResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityFeedbackSaveResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpQualityFeedbackSaveResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_models_list: {
        parameters: {
            query?: {
                cursor?: components["schemas"]["Cursor"];
                limit?: components["schemas"]["PageLimit"];
            };
            header?: {
                "X-Request-Id"?: components["schemas"]["ID"];
                "X-UAW-Schema-Version"?: "0.1";
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpModelsListResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpModelsListResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpModelsListResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpModelsListResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpModelsListResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpModelsListResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpModelsListResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpModelsListResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpModelsListResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpModelsListResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpModelsListResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_web_session_get: {
        parameters: {
            query?: never;
            header?: {
                /** @description Configured exact localhost origin; GET may use exact Referer. */
                Origin?: string;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpWebSessionGetResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpWebSessionGetResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpWebSessionGetResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpWebSessionGetResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpWebSessionGetResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpWebSessionGetResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpWebSessionGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpWebSessionGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpWebSessionGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpWebSessionGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpWebSessionGetResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_web_session_exchange: {
        parameters: {
            query?: never;
            header: {
                /** @description Configured exact localhost origin; GET may use exact Referer. */
                Origin: string;
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    meta: components["schemas"]["RequestMeta"];
                    /** @description 精确Origin消费一次启动code。 */
                    payload: {
                        /** @description 原启动fragment凭据 */
                        launch_code: components["schemas"]["NonEmptyText"];
                    };
                };
            };
        };
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpWebSessionExchangeResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpWebSessionExchangeResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpWebSessionExchangeResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpWebSessionExchangeResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpWebSessionExchangeResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpWebSessionExchangeResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpWebSessionExchangeResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpWebSessionExchangeResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpWebSessionExchangeResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpWebSessionExchangeResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpWebSessionExchangeResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
    http_web_session_logout: {
        parameters: {
            query?: never;
            header: {
                /** @description Configured exact localhost origin; GET may use exact Referer. */
                Origin: string;
                "X-UAW-CSRF": components["schemas"]["Hash"];
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    meta: components["schemas"]["RequestMeta"];
                    /** @description 撤销当前浏览器会话并清cookie。 */
                    payload: Record<string, never>;
                };
            };
        };
        responses: {
            /** @description 本接口成功；Run/作业可能仍在执行。 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpWebSessionLogoutResult"] & {
                        /** @constant */
                        kind?: "ok";
                    };
                };
            };
            /** @description waiting；failure.code区分原因，waiting含wait_ref。 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpWebSessionLogoutResult"] & {
                        /** @constant */
                        kind?: "waiting";
                    };
                };
            };
            /** @description 认证失败；不进入业务接口。 */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthenticationFailure"];
                };
            };
            /** @description denied；failure.code区分原因，waiting含wait_ref。 */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpWebSessionLogoutResult"] & {
                        /** @constant */
                        kind?: "denied";
                    };
                };
            };
            /** @description missing；failure.code区分原因，waiting含wait_ref。 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpWebSessionLogoutResult"] & {
                        /** @constant */
                        kind?: "missing";
                    };
                };
            };
            /** @description conflict；failure.code区分原因，waiting含wait_ref。 */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpWebSessionLogoutResult"] & {
                        /** @constant */
                        kind?: "conflict";
                    };
                };
            };
            /** @description stale；failure.code区分原因，waiting含wait_ref。 */
            412: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpWebSessionLogoutResult"] & {
                        /** @constant */
                        kind?: "stale";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpWebSessionLogoutResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpWebSessionLogoutResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            500: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpWebSessionLogoutResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            502: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpWebSessionLogoutResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
            /** @description failed；failure.code区分原因，waiting含wait_ref。 */
            504: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HttpWebSessionLogoutResult"] & {
                        /** @constant */
                        kind?: "failed";
                    };
                };
            };
        };
    };
}
