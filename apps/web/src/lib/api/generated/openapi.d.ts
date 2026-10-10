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
        Acknowledgement: {
            operation_id: components["schemas"]["ID"];
            /** @enum {string} */
            status: "accepted" | "unchanged" | "completed" | "pending";
            related_refs?: components["schemas"]["Ref"][];
        };
        AgentInstance: {
            id: components["schemas"]["ID"];
            run_id: components["schemas"]["ID"];
            parent_agent_ref?: components["schemas"]["Ref"];
            definition_ref?: components["schemas"]["Ref"];
            delegation_ref?: components["schemas"]["Ref"];
            status: components["schemas"]["State"];
            model_policy_ref: components["schemas"]["Ref"];
            capability_policy_ref: components["schemas"]["Ref"];
            context_epoch: components["schemas"]["Revision"];
            workspace_ref?: components["schemas"]["Ref"];
            result_ref?: components["schemas"]["Ref"];
            revision: components["schemas"]["Revision"];
        };
        AgentResult: {
            agent_ref: components["schemas"]["Ref"];
            outcome: components["schemas"]["Outcome"];
            summary: components["schemas"]["Text"];
            output_refs: components["schemas"]["Ref"][];
            verification_refs: components["schemas"]["Ref"][];
            limitations: components["schemas"]["NonEmptyText"][];
            usage_ref: components["schemas"]["Ref"];
        };
        ApprovalDecision: {
            decision: components["schemas"]["ApprovalDecisionKind"];
            expected_arguments_hash: components["schemas"]["Hash"];
            expected_resource_refs: components["schemas"]["Ref"][];
            scope_selector?: components["schemas"]["ScopeSelector"];
            expires_at?: components["schemas"]["Timestamp"];
            reason: components["schemas"]["Text"];
        };
        /** @enum {string} */
        ApprovalDecisionKind: "approve_once" | "approve_scoped" | "decline" | "cancel";
        ApprovalGrant: {
            id: components["schemas"]["ID"];
            approval_ref: components["schemas"]["Ref"];
            actor: components["schemas"]["Principal"];
            decision: components["schemas"]["ApprovalDecision"];
            issued_at: components["schemas"]["Timestamp"];
        };
        /** @enum {string} */
        ApprovalMode: "assisted" | "manual" | "automatic";
        ApprovalRequest: {
            id: components["schemas"]["ID"];
            revision: components["schemas"]["Revision"];
            action_id: components["schemas"]["ID"];
            arguments_hash: components["schemas"]["Hash"];
            resource_refs: components["schemas"]["Ref"][];
            effect: components["schemas"]["EffectKind"];
            summary: components["schemas"]["NonEmptyText"];
            mode: components["schemas"]["ApprovalMode"];
            status: components["schemas"]["ApprovalStatus"];
            expires_at: components["schemas"]["Timestamp"];
        };
        /** @enum {string} */
        ApprovalStatus: "pending" | "approved" | "declined" | "expired" | "cancelled" | "stale";
        ApprovalsDecideRequest: {
            approval_id: components["schemas"]["ID"];
            decision: components["schemas"]["ApprovalDecision"];
        };
        ApprovalsGetRequest: {
            approval_id: components["schemas"]["ID"];
        };
        ArtifactContentView: {
            artifact: components["schemas"]["ArtifactRecord"];
            content: components["schemas"]["ArtifactPreviewText"];
        };
        ArtifactPreviewText: string;
        ArtifactRecord: {
            id: components["schemas"]["ID"];
            version: components["schemas"]["Version"];
            title: components["schemas"]["NonEmptyText"];
            format_kind: components["schemas"]["NonEmptyText"];
            media_type: components["schemas"]["NonEmptyText"];
            content_ref: components["schemas"]["Ref"];
            size_bytes: components["schemas"]["Count"];
            content_hash: components["schemas"]["Hash"];
            provenance_refs: components["schemas"]["Ref"][];
            verification_refs: components["schemas"]["Ref"][];
            created_at: components["schemas"]["Timestamp"];
        };
        ArtifactsContentRequest: {
            artifact_id: components["schemas"]["ID"];
            version: components["schemas"]["Version"];
            content_hash: components["schemas"]["Hash"];
        };
        ArtifactsGetRequest: {
            artifact_id: components["schemas"]["ID"];
            version?: components["schemas"]["Version"];
        };
        AuthenticationFailure: {
            /** @constant */
            code: components["schemas"]["ID"];
            message: components["schemas"]["Text"];
            request_id: components["schemas"]["ID"];
        };
        Bool: boolean;
        Budget: {
            limits: components["schemas"]["ResourceVector"];
            max_steps: components["schemas"]["Count"];
            max_depth: components["schemas"]["Count"];
            deadline: components["schemas"]["Timestamp"];
            parent_reservation_ref?: components["schemas"]["Ref"];
        };
        BudgetReservation: {
            id: components["schemas"]["ID"];
            parent_ref?: components["schemas"]["Ref"];
            estimates: components["schemas"]["ResourceVector"];
            settled_usage_refs: components["schemas"]["Ref"][];
            status: components["schemas"]["ReservationState"];
            revision: components["schemas"]["Revision"];
        };
        /** @enum {string} */
        ChangeKind: "add" | "modify" | "delete" | "rename";
        ChangeSet: {
            id: components["schemas"]["ID"];
            base_ref: components["schemas"]["Ref"];
            target_ref: components["schemas"]["Ref"];
            units: components["schemas"]["ChangeUnit"][];
            provenance_refs: components["schemas"]["Ref"][];
            revision: components["schemas"]["Revision"];
        };
        ChangeUnit: {
            id: components["schemas"]["ID"];
            path: components["schemas"]["RelativePath"];
            kind: components["schemas"]["ChangeKind"];
            before_ref?: components["schemas"]["Ref"];
            after_ref?: components["schemas"]["Ref"];
            location?: components["schemas"]["Location"];
            patch_ref?: components["schemas"]["Ref"];
            binary: components["schemas"]["Bool"];
        };
        /** @enum {string} */
        CheckState: "passed" | "failed" | "not_run" | "blocked";
        Checkpoint: {
            id: components["schemas"]["ID"];
            run_ref: components["schemas"]["Ref"];
            schema_version: components["schemas"]["Version"];
            committed_event_seq: components["schemas"]["Revision"];
            domains: components["schemas"]["DomainCheckpoint"][];
            pending_action_refs: components["schemas"]["Ref"][];
            created_at: components["schemas"]["Timestamp"];
        };
        CompletionAcceptance: {
            bundle_ref: components["schemas"]["Ref"];
            principal: components["schemas"]["Principal"];
            decision: components["schemas"]["DeliveryDecision"];
            created_at: components["schemas"]["Timestamp"];
        };
        ConfigurationVersion: {
            id: components["schemas"]["ID"];
            revision: components["schemas"]["Revision"];
            model_refs: components["schemas"]["ModelRef"][];
            provider_refs: components["schemas"]["Ref"][];
            environment_template_refs: components["schemas"]["Ref"][];
            feature_flags: components["schemas"]["FeatureFlag"][];
            approval_policy_ref: components["schemas"]["Ref"];
            storage_policy_ref: components["schemas"]["Ref"];
            state: components["schemas"]["ProviderState"];
        };
        Constraint: components["schemas"]["Requirement"];
        Contract: {
            goal: components["schemas"]["NonEmptyText"];
            requirements: components["schemas"]["Requirement"][];
            outputs: components["schemas"]["OutputSpec"][];
            version: components["schemas"]["Version"];
            /** @default false */
            acceptance_required: components["schemas"]["Bool"];
        };
        /** @enum {string} */
        ControlMode: "steer" | "enqueue" | "replace" | "cancel" | "deliver_partial";
        Conversation: {
            id: components["schemas"]["ID"];
            owner_id: components["schemas"]["ID"];
            title: components["schemas"]["NonEmptyText"];
            revision: components["schemas"]["Revision"];
            project_ref?: components["schemas"]["Ref"];
            model_policy_ref: components["schemas"]["Ref"];
            memory_policy: components["schemas"]["MemoryPolicy"];
            created_at: components["schemas"]["Timestamp"];
            updated_at: components["schemas"]["Timestamp"];
            /** @default manual */
            approval_mode: components["schemas"]["ApprovalMode"];
        };
        ConversationModelChoice: {
            mode: components["schemas"]["ConversationModelMode"];
            model_id?: components["schemas"]["ID"];
            allowed_model_ids?: components["schemas"]["ID"][];
        };
        /** @enum {string} */
        ConversationModelMode: "explicit" | "auto";
        ConversationPage: {
            items: components["schemas"]["Conversation"][];
            next_cursor?: components["schemas"]["Cursor"];
            snapshot_revision: components["schemas"]["Revision"];
        };
        ConversationsCreateRequest: {
            title: components["schemas"]["NonEmptyText"];
            model_choice: components["schemas"]["ConversationModelChoice"];
            project_ref?: components["schemas"]["Ref"];
            memory_policy: components["schemas"]["MemoryPolicy"];
            /** @default manual */
            approval_mode: components["schemas"]["ApprovalMode"];
        };
        ConversationsGetRequest: {
            conversation_id: components["schemas"]["ID"];
        };
        ConversationsItemsRequest: {
            conversation_id: components["schemas"]["ID"];
            cursor?: components["schemas"]["Cursor"];
            limit?: components["schemas"]["PageLimit"];
        };
        ConversationsListRequest: {
            cursor?: components["schemas"]["Cursor"];
            limit?: components["schemas"]["PageLimit"];
        };
        Count: number;
        Cursor: string;
        Decimal: string;
        DeletionReceipt: {
            deletion_id: components["schemas"]["ID"];
            deleted_refs: components["schemas"]["Ref"][];
            invalidated_refs: components["schemas"]["Ref"][];
            physical_cleanup_pending: components["schemas"]["Bool"];
        };
        /** @enum {string} */
        DeliveryDecision: "accept" | "reject" | "revise" | "partial_accept";
        DeliveryProposal: {
            run_ref: components["schemas"]["Ref"];
            contract_ref: components["schemas"]["Ref"];
            outcome: components["schemas"]["Outcome"];
            artifact_refs: components["schemas"]["Ref"][];
            report_ref: components["schemas"]["Ref"];
            unresolved_effect_refs: components["schemas"]["Ref"][];
            created_at: components["schemas"]["Timestamp"];
        };
        DomainCheckpoint: {
            domain: components["schemas"]["ID"];
            resource_ref: components["schemas"]["Ref"];
            lease_ref?: components["schemas"]["Ref"];
        };
        DraftPreview: {
            draft_revision: components["schemas"]["Revision"];
            interpretation: components["schemas"]["Interpretation"];
            model_config_ref: components["schemas"]["Ref"];
            expires_at: components["schemas"]["Timestamp"];
        };
        Duration: number;
        /** @enum {string} */
        EffectKind: "read" | "internal_write" | "workspace_write" | "external_write" | "process" | "credential";
        /** @enum {string} */
        EffectState: "confirmed" | "pending" | "unknown";
        EnvVar: {
            name: components["schemas"]["NonEmptyText"];
            value: components["schemas"]["Text"];
        };
        EventEnvelope: {
            event_id: components["schemas"]["ID"];
            stream_id: components["schemas"]["ID"];
            seq: components["schemas"]["Revision"];
            type: components["schemas"]["EventType"];
            schema_version: components["schemas"]["Version"];
            occurred_at: components["schemas"]["Timestamp"];
            item_ref?: components["schemas"]["Ref"];
            payload_ref: components["schemas"]["Ref"];
            base_revision?: components["schemas"]["Revision"];
            result_revision?: components["schemas"]["Revision"];
        };
        EventPage: {
            items: components["schemas"]["EventEnvelope"][];
            next_cursor?: components["schemas"]["Cursor"];
            snapshot_revision: components["schemas"]["Revision"];
        };
        EventPayload: components["schemas"]["EventPayloadInput.committed"] | components["schemas"]["EventPayloadUnderstanding.preview"] | components["schemas"]["EventPayloadTask.frame.committed"] | components["schemas"]["EventPayloadPlan.committed"] | components["schemas"]["EventPayloadAgent.updated"] | components["schemas"]["EventPayloadAgent.result"] | components["schemas"]["EventPayloadTool.started"] | components["schemas"]["EventPayloadTool.completed"] | components["schemas"]["EventPayloadProcess.updated"] | components["schemas"]["EventPayloadChanges.committed"] | components["schemas"]["EventPayloadArtifact.registered"] | components["schemas"]["EventPayloadApproval.required"] | components["schemas"]["EventPayloadApproval.decided"] | components["schemas"]["EventPayloadItem.delta"] | components["schemas"]["EventPayloadItem.updated"] | components["schemas"]["EventPayloadRun.updated"] | components["schemas"]["EventPayloadVerification.completed"] | components["schemas"]["EventPayloadControl.accepted"] | components["schemas"]["EventPayloadMemory.deleted"] | components["schemas"]["EventPayloadConfiguration.activated"] | components["schemas"]["EventPayloadCheckpoint.committed"] | components["schemas"]["EventPayloadBudget.updated"];
        "EventPayloadAgent.result": {
            /** @constant */
            action: "agent.result";
            parameters: components["schemas"]["AgentResult"];
        };
        "EventPayloadAgent.updated": {
            /** @constant */
            action: "agent.updated";
            parameters: components["schemas"]["AgentInstance"];
        };
        "EventPayloadApproval.decided": {
            /** @constant */
            action: "approval.decided";
            parameters: components["schemas"]["ApprovalGrant"];
        };
        "EventPayloadApproval.required": {
            /** @constant */
            action: "approval.required";
            parameters: components["schemas"]["ApprovalRequest"];
        };
        "EventPayloadArtifact.registered": {
            /** @constant */
            action: "artifact.registered";
            parameters: components["schemas"]["ArtifactRecord"];
        };
        "EventPayloadBudget.updated": {
            /** @constant */
            action: "budget.updated";
            parameters: components["schemas"]["BudgetReservation"];
        };
        "EventPayloadChanges.committed": {
            /** @constant */
            action: "changes.committed";
            parameters: components["schemas"]["ChangeSet"];
        };
        "EventPayloadCheckpoint.committed": {
            /** @constant */
            action: "checkpoint.committed";
            parameters: components["schemas"]["Checkpoint"];
        };
        "EventPayloadConfiguration.activated": {
            /** @constant */
            action: "configuration.activated";
            parameters: components["schemas"]["ConfigurationVersion"];
        };
        "EventPayloadControl.accepted": {
            /** @constant */
            action: "control.accepted";
            parameters: components["schemas"]["Acknowledgement"];
        };
        "EventPayloadInput.committed": {
            /** @constant */
            action: "input.committed";
            parameters: components["schemas"]["InputRecord"];
        };
        "EventPayloadItem.delta": {
            /** @constant */
            action: "item.delta";
            parameters: components["schemas"]["ItemPatch"];
        };
        "EventPayloadItem.updated": {
            /** @constant */
            action: "item.updated";
            parameters: components["schemas"]["InteractionItem"];
        };
        "EventPayloadMemory.deleted": {
            /** @constant */
            action: "memory.deleted";
            parameters: components["schemas"]["DeletionReceipt"];
        };
        "EventPayloadPlan.committed": {
            /** @constant */
            action: "plan.committed";
            parameters: components["schemas"]["TaskGraph"];
        };
        "EventPayloadProcess.updated": {
            /** @constant */
            action: "process.updated";
            parameters: components["schemas"]["ProcessRecord"];
        };
        "EventPayloadRun.updated": {
            /** @constant */
            action: "run.updated";
            parameters: components["schemas"]["RunRecord"];
        };
        "EventPayloadTask.frame.committed": {
            /** @constant */
            action: "task.frame.committed";
            parameters: components["schemas"]["TaskFrame"];
        };
        "EventPayloadTool.completed": {
            /** @constant */
            action: "tool.completed";
            parameters: components["schemas"]["ToolResult"];
        };
        "EventPayloadTool.started": {
            /** @constant */
            action: "tool.started";
            parameters: components["schemas"]["ValidatedCall"];
        };
        "EventPayloadUnderstanding.preview": {
            /** @constant */
            action: "understanding.preview";
            parameters: components["schemas"]["DraftPreview"];
        };
        "EventPayloadVerification.completed": {
            /** @constant */
            action: "verification.completed";
            parameters: components["schemas"]["VerificationReport"];
        };
        /** @enum {string} */
        EventType: "input.committed" | "understanding.preview" | "task.frame.committed" | "plan.committed" | "agent.updated" | "agent.result" | "tool.started" | "tool.completed" | "process.updated" | "changes.committed" | "artifact.registered" | "approval.required" | "approval.decided" | "item.delta" | "item.updated" | "run.updated" | "verification.completed" | "control.accepted" | "memory.deleted" | "configuration.activated" | "checkpoint.committed" | "budget.updated";
        EventsPayloadRequest: {
            event_id: components["schemas"]["ID"];
        };
        EventsReadRequest: {
            conversation_id: components["schemas"]["ID"];
            cursor?: components["schemas"]["Cursor"];
            limit?: components["schemas"]["PageLimit"];
        };
        ExitCode: number;
        Failure: {
            code: components["schemas"]["ID"];
            category: components["schemas"]["FailureCategory"];
            message: components["schemas"]["NonEmptyText"];
            retryable: components["schemas"]["Bool"];
            failed_phase: components["schemas"]["NonEmptyText"];
            recover_hint?: components["schemas"]["Text"];
            evidence_refs?: components["schemas"]["Ref"][];
            side_effect_state?: components["schemas"]["EffectState"];
            retry_after_ms?: components["schemas"]["Duration"];
        };
        /** @enum {string} */
        FailureCategory: "arguments" | "authorization" | "policy" | "dependency" | "conflict" | "model_protocol" | "tool_business" | "infrastructure" | "budget" | "timeout" | "cancelled" | "unknown_effect";
        FeatureFlag: {
            id: components["schemas"]["ID"];
            enabled: components["schemas"]["Bool"];
            scope: components["schemas"]["ScopeSelector"];
            reason: components["schemas"]["Text"];
        };
        Hash: string;
        HttpApprovalsDecideResult: {
            /** @enum {string} */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            payload?: components["schemas"]["ApprovalGrant"];
            output_refs: components["schemas"]["Ref"][];
            revision?: components["schemas"]["Revision"];
            failure?: components["schemas"]["Failure"];
            wait_ref?: components["schemas"]["Ref"];
            usage_ref?: components["schemas"]["Ref"];
        };
        HttpApprovalsGetResult: {
            /** @enum {string} */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            payload?: components["schemas"]["ApprovalRequest"];
            output_refs: components["schemas"]["Ref"][];
            revision?: components["schemas"]["Revision"];
            failure?: components["schemas"]["Failure"];
            wait_ref?: components["schemas"]["Ref"];
            usage_ref?: components["schemas"]["Ref"];
        };
        HttpArtifactsContentResult: {
            /** @enum {string} */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            payload?: components["schemas"]["ArtifactContentView"];
            output_refs: components["schemas"]["Ref"][];
            revision?: components["schemas"]["Revision"];
            failure?: components["schemas"]["Failure"];
            wait_ref?: components["schemas"]["Ref"];
            usage_ref?: components["schemas"]["Ref"];
        };
        HttpArtifactsGetResult: {
            /** @enum {string} */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            payload?: components["schemas"]["ArtifactRecord"];
            output_refs: components["schemas"]["Ref"][];
            revision?: components["schemas"]["Revision"];
            failure?: components["schemas"]["Failure"];
            wait_ref?: components["schemas"]["Ref"];
            usage_ref?: components["schemas"]["Ref"];
        };
        HttpConversationsCreateResult: {
            /** @enum {string} */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            payload?: components["schemas"]["Conversation"];
            output_refs: components["schemas"]["Ref"][];
            revision?: components["schemas"]["Revision"];
            failure?: components["schemas"]["Failure"];
            wait_ref?: components["schemas"]["Ref"];
            usage_ref?: components["schemas"]["Ref"];
        };
        HttpConversationsGetResult: {
            /** @enum {string} */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            payload?: components["schemas"]["Conversation"];
            output_refs: components["schemas"]["Ref"][];
            revision?: components["schemas"]["Revision"];
            failure?: components["schemas"]["Failure"];
            wait_ref?: components["schemas"]["Ref"];
            usage_ref?: components["schemas"]["Ref"];
        };
        HttpConversationsItemsResult: {
            /** @enum {string} */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            payload?: components["schemas"]["ItemPage"];
            output_refs: components["schemas"]["Ref"][];
            revision?: components["schemas"]["Revision"];
            failure?: components["schemas"]["Failure"];
            wait_ref?: components["schemas"]["Ref"];
            usage_ref?: components["schemas"]["Ref"];
        };
        HttpConversationsListResult: {
            /** @enum {string} */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            payload?: components["schemas"]["ConversationPage"];
            output_refs: components["schemas"]["Ref"][];
            revision?: components["schemas"]["Revision"];
            failure?: components["schemas"]["Failure"];
            wait_ref?: components["schemas"]["Ref"];
            usage_ref?: components["schemas"]["Ref"];
        };
        HttpEventsPayloadResult: {
            /** @enum {string} */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            payload?: components["schemas"]["EventPayload"];
            output_refs: components["schemas"]["Ref"][];
            revision?: components["schemas"]["Revision"];
            failure?: components["schemas"]["Failure"];
            wait_ref?: components["schemas"]["Ref"];
            usage_ref?: components["schemas"]["Ref"];
        };
        HttpEventsReadResult: {
            /** @enum {string} */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            payload?: components["schemas"]["EventPage"];
            output_refs: components["schemas"]["Ref"][];
            revision?: components["schemas"]["Revision"];
            failure?: components["schemas"]["Failure"];
            wait_ref?: components["schemas"]["Ref"];
            usage_ref?: components["schemas"]["Ref"];
        };
        HttpModelsListResult: {
            /** @enum {string} */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            payload?: components["schemas"]["ModelPage"];
            output_refs: components["schemas"]["Ref"][];
            revision?: components["schemas"]["Revision"];
            failure?: components["schemas"]["Failure"];
            wait_ref?: components["schemas"]["Ref"];
            usage_ref?: components["schemas"]["Ref"];
        };
        HttpRunsControlResult: {
            /** @enum {string} */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            payload?: components["schemas"]["Acknowledgement"];
            output_refs: components["schemas"]["Ref"][];
            revision?: components["schemas"]["Revision"];
            failure?: components["schemas"]["Failure"];
            wait_ref?: components["schemas"]["Ref"];
            usage_ref?: components["schemas"]["Ref"];
        };
        HttpRunsDeliveryAcceptResult: {
            /** @enum {string} */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            payload?: components["schemas"]["CompletionAcceptance"];
            output_refs: components["schemas"]["Ref"][];
            revision?: components["schemas"]["Revision"];
            failure?: components["schemas"]["Failure"];
            wait_ref?: components["schemas"]["Ref"];
            usage_ref?: components["schemas"]["Ref"];
        };
        HttpRunsDeliveryResult: {
            /** @enum {string} */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            payload?: components["schemas"]["RunDeliveryView"];
            output_refs: components["schemas"]["Ref"][];
            revision?: components["schemas"]["Revision"];
            failure?: components["schemas"]["Failure"];
            wait_ref?: components["schemas"]["Ref"];
            usage_ref?: components["schemas"]["Ref"];
        };
        HttpRunsGetResult: {
            /** @enum {string} */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            payload?: components["schemas"]["RunRecord"];
            output_refs: components["schemas"]["Ref"][];
            revision?: components["schemas"]["Revision"];
            failure?: components["schemas"]["Failure"];
            wait_ref?: components["schemas"]["Ref"];
            usage_ref?: components["schemas"]["Ref"];
        };
        HttpTasksFrameResult: {
            /** @enum {string} */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            payload?: components["schemas"]["TaskFrame"];
            output_refs: components["schemas"]["Ref"][];
            revision?: components["schemas"]["Revision"];
            failure?: components["schemas"]["Failure"];
            wait_ref?: components["schemas"]["Ref"];
            usage_ref?: components["schemas"]["Ref"];
        };
        HttpTurnsLookupResult: {
            /** @enum {string} */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            payload?: components["schemas"]["RunRecord"];
            output_refs: components["schemas"]["Ref"][];
            revision?: components["schemas"]["Revision"];
            failure?: components["schemas"]["Failure"];
            wait_ref?: components["schemas"]["Ref"];
            usage_ref?: components["schemas"]["Ref"];
        };
        HttpTurnsSubmitResult: {
            /** @enum {string} */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            payload?: components["schemas"]["RunRecord"];
            output_refs: components["schemas"]["Ref"][];
            revision?: components["schemas"]["Revision"];
            failure?: components["schemas"]["Failure"];
            wait_ref?: components["schemas"]["Ref"];
            usage_ref?: components["schemas"]["Ref"];
        };
        HttpWebSessionExchangeResult: {
            /** @enum {string} */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            payload?: components["schemas"]["WebSession"];
            output_refs: components["schemas"]["Ref"][];
            revision?: components["schemas"]["Revision"];
            failure?: components["schemas"]["Failure"];
            wait_ref?: components["schemas"]["Ref"];
            usage_ref?: components["schemas"]["Ref"];
        };
        HttpWebSessionGetResult: {
            /** @enum {string} */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            payload?: components["schemas"]["WebSession"];
            output_refs: components["schemas"]["Ref"][];
            revision?: components["schemas"]["Revision"];
            failure?: components["schemas"]["Failure"];
            wait_ref?: components["schemas"]["Ref"];
            usage_ref?: components["schemas"]["Ref"];
        };
        HttpWebSessionLogoutResult: {
            /** @enum {string} */
            kind: "ok" | "waiting" | "missing" | "denied" | "conflict" | "stale" | "failed" | "cancelled";
            payload?: components["schemas"]["Acknowledgement"];
            output_refs: components["schemas"]["Ref"][];
            revision?: components["schemas"]["Revision"];
            failure?: components["schemas"]["Failure"];
            wait_ref?: components["schemas"]["Ref"];
            usage_ref?: components["schemas"]["Ref"];
        };
        ID: string;
        InputRecord: {
            id: components["schemas"]["ID"];
            conversation_id: components["schemas"]["ID"];
            turn_id: components["schemas"]["ID"];
            text: components["schemas"]["Text"];
            attachment_refs: components["schemas"]["Ref"][];
            created_at: components["schemas"]["Timestamp"];
        };
        InteractionItem: {
            id: components["schemas"]["ID"];
            conversation_id: components["schemas"]["ID"];
            run_id?: components["schemas"]["ID"];
            type: components["schemas"]["ItemType"];
            status: components["schemas"]["ItemStatus"];
            revision: components["schemas"]["Revision"];
            text: components["schemas"]["Text"];
            resource_refs: components["schemas"]["Ref"][];
            created_at: components["schemas"]["Timestamp"];
            updated_at: components["schemas"]["Timestamp"];
        };
        Interpretation: {
            goal: components["schemas"]["NonEmptyText"];
            assumptions: components["schemas"]["NonEmptyText"][];
            source_refs: components["schemas"]["Ref"][];
            missing_facts: components["schemas"]["NonEmptyText"][];
        };
        ItemPage: {
            items: components["schemas"]["InteractionItem"][];
            next_cursor?: components["schemas"]["Cursor"];
            snapshot_revision: components["schemas"]["Revision"];
        };
        ItemPatch: {
            item_id: components["schemas"]["ID"];
            base_revision: components["schemas"]["Revision"];
            status?: components["schemas"]["ItemStatus"];
            text_delta?: components["schemas"]["Text"];
            replacement_text?: components["schemas"]["Text"];
            resource_refs?: components["schemas"]["Ref"][];
        };
        /** @enum {string} */
        ItemStatus: "pending" | "in_progress" | "waiting" | "completed" | "failed" | "declined" | "cancelled";
        /** @enum {string} */
        ItemType: "user_message" | "understanding" | "agent_message" | "plan" | "tool_call" | "command" | "file_change" | "approval" | "user_control" | "artifact" | "review" | "context_compression";
        JsonValue: null | boolean | number | string | components["schemas"]["JsonValue"][] | {
            [key: string]: components["schemas"]["JsonValue"];
        };
        Location: {
            /** @enum {string} */
            kind: "whole" | "page" | "lines" | "paragraph" | "json_pointer" | "cell_range" | "text_span";
            start?: components["schemas"]["Count"];
            end?: components["schemas"]["Count"];
            anchor?: components["schemas"]["Text"];
            relative_path?: components["schemas"]["RelativePath"];
        };
        MemoryPolicy: {
            revision: components["schemas"]["Revision"];
            read_enabled: components["schemas"]["Bool"];
            contribute_enabled: components["schemas"]["Bool"];
            scope: components["schemas"]["ScopeSelector"];
            retention_ms?: components["schemas"]["Duration"];
        };
        ModelCatalogEntry: {
            id: components["schemas"]["ID"];
            provider_ref: components["schemas"]["Ref"];
            display_name: components["schemas"]["NonEmptyText"];
            context_limit_tokens: components["schemas"]["Count"];
            output_limit_tokens: components["schemas"]["Count"];
            capabilities: components["schemas"]["ID"][];
            status: components["schemas"]["ProviderState"];
            revision: components["schemas"]["Revision"];
            pricing_ref?: components["schemas"]["Ref"];
        };
        ModelPage: {
            items: components["schemas"]["ModelCatalogEntry"][];
            next_cursor?: components["schemas"]["Cursor"];
            snapshot_revision: components["schemas"]["Revision"];
        };
        ModelRef: components["schemas"]["Ref"] & {
            /** @constant */
            kind?: "model";
        };
        ModelsListRequest: {
            cursor?: components["schemas"]["Cursor"];
            limit?: components["schemas"]["PageLimit"];
        };
        NodeSpec: {
            id: components["schemas"]["ID"];
            goal: components["schemas"]["NonEmptyText"];
            depends_on: components["schemas"]["ID"][];
            input_refs: components["schemas"]["Ref"][];
            output_contract: components["schemas"]["Contract"];
            agent_definition_ref?: components["schemas"]["Ref"];
            read_refs: components["schemas"]["Ref"][];
            write_refs: components["schemas"]["Ref"][];
            budget: components["schemas"]["Budget"];
        };
        NonEmptyText: string;
        Object: {
            [key: string]: components["schemas"]["JsonValue"];
        };
        /** @enum {string} */
        Outcome: "succeeded" | "partial" | "blocked" | "failed" | "cancelled";
        OutputSpec: {
            id: components["schemas"]["ID"];
            kind: components["schemas"]["NonEmptyText"];
            required: components["schemas"]["Bool"];
            schema_ref?: components["schemas"]["Ref"];
        };
        /** @default 20 */
        PageLimit: number;
        Principal: {
            id: components["schemas"]["ID"];
            /** @enum {string} */
            kind: "user" | "admin" | "service" | "runner";
            auth_session_id: components["schemas"]["ID"];
            delegated_by?: components["schemas"]["ID"];
        };
        ProcessRecord: {
            id: components["schemas"]["ID"];
            spec: components["schemas"]["ProcessSpec"];
            status: components["schemas"]["ProcessState"];
            started_at: components["schemas"]["Timestamp"];
            ended_at?: components["schemas"]["Timestamp"];
            exit_code?: components["schemas"]["ExitCode"];
            stdout_ref?: components["schemas"]["Ref"];
            stderr_ref?: components["schemas"]["Ref"];
            output_cursor?: components["schemas"]["Cursor"];
            change_set_ref?: components["schemas"]["Ref"];
            failure?: components["schemas"]["Failure"];
        };
        ProcessSpec: {
            workspace_ref: components["schemas"]["Ref"];
            executable: components["schemas"]["NonEmptyText"];
            argv: components["schemas"]["Text"][];
            cwd: components["schemas"]["RelativePath"];
            environment: components["schemas"]["EnvVar"][];
            timeout_ms: components["schemas"]["Duration"];
            shell_command?: components["schemas"]["NonEmptyText"];
            shell_profile_ref?: components["schemas"]["Ref"];
        };
        /** @enum {string} */
        ProcessState: "starting" | "running" | "exited" | "stopping" | "stopped" | "lost" | "failed";
        /** @enum {string} */
        ProviderState: "draft" | "validated" | "active" | "disabled" | "revoked";
        Ref: {
            kind: components["schemas"]["RefKind"];
            id: components["schemas"]["ID"];
            version: components["schemas"]["Version"];
            location?: components["schemas"]["Location"];
            content_hash?: components["schemas"]["Hash"];
            access_scope?: components["schemas"]["Scope"];
        };
        /** @enum {string} */
        RefKind: "web" | "asset" | "content" | "artifact" | "workspace" | "verification" | "local" | "input" | "task" | "task_frame" | "semantic_parse" | "plan" | "agent_definition" | "agent_instance" | "skill" | "memory" | "context" | "tool_call" | "policy" | "environment" | "process" | "configuration" | "checkpoint" | "usage" | "trace" | "evaluation" | "review" | "changeset" | "conversation" | "run" | "source" | "rule" | "role_profile" | "template" | "corpus" | "chunk" | "check" | "board" | "provider" | "connection" | "extension" | "blob" | "item" | "event" | "upload" | "reservation" | "budget" | "lease" | "approval" | "trigger" | "device" | "project" | "model" | "provider_profile";
        RelativePath: string;
        RequestMeta: {
            request_id: components["schemas"]["ID"];
            /** @constant */
            schema_version: components["schemas"]["Version"];
            expected_revision?: components["schemas"]["Revision"] | null;
        };
        Requirement: {
            id: components["schemas"]["ID"];
            text: components["schemas"]["NonEmptyText"];
            mandatory: components["schemas"]["Bool"];
            source_refs: components["schemas"]["Ref"][];
            evidence_kinds?: components["schemas"]["NonEmptyText"][];
        };
        RequirementVerdict: {
            requirement_id: components["schemas"]["ID"];
            state: components["schemas"]["CheckState"];
            evidence_refs: components["schemas"]["Ref"][];
            reason: components["schemas"]["NonEmptyText"];
            limitations: components["schemas"]["NonEmptyText"][];
        };
        /** @enum {string} */
        ReservationState: "reserved" | "partially_settled" | "settled" | "released";
        ResourceVector: {
            input_tokens: components["schemas"]["Count"];
            output_tokens: components["schemas"]["Count"];
            model_calls: components["schemas"]["Count"];
            tool_calls: components["schemas"]["Count"];
            child_agents: components["schemas"]["Count"];
            wall_time_ms: components["schemas"]["Duration"];
            money: components["schemas"]["Decimal"];
            currency: string;
        };
        Revision: number;
        RunDeliveryView: {
            run_id: components["schemas"]["ID"];
            bundle_ref: components["schemas"]["Ref"];
            artifact_ref: components["schemas"]["Ref"];
            artifact: components["schemas"]["ArtifactRecord"];
            content: components["schemas"]["ArtifactPreviewText"];
            contract_ref: components["schemas"]["Ref"];
            contract: components["schemas"]["Contract"];
            report_ref: components["schemas"]["Ref"];
            report: components["schemas"]["VerificationReport"];
            proposal_ref: components["schemas"]["Ref"];
            proposal: components["schemas"]["DeliveryProposal"];
            requires_acceptance: components["schemas"]["Bool"];
            stale: components["schemas"]["Bool"];
            acceptance?: components["schemas"]["CompletionAcceptance"];
        };
        RunRecord: {
            id: components["schemas"]["ID"];
            task_id: components["schemas"]["ID"];
            conversation_id: components["schemas"]["ID"];
            revision: components["schemas"]["Revision"];
            status: components["schemas"]["RunStatus"];
            root_agent_ref?: components["schemas"]["Ref"];
            frame_ref?: components["schemas"]["Ref"];
            plan_ref?: components["schemas"]["Ref"];
            budget: components["schemas"]["Budget"];
            outcome?: components["schemas"]["Outcome"];
            created_at: components["schemas"]["Timestamp"];
            ended_at?: components["schemas"]["Timestamp"];
        };
        /** @enum {string} */
        RunStatus: "queued" | "preparing" | "running" | "verifying" | "waiting_for_user" | "waiting_for_merge" | "completed" | "failed" | "cancelled";
        RunsControlRequest: {
            run_id: components["schemas"]["ID"];
            control: components["schemas"]["UserControl"];
        };
        RunsDeliveryAcceptRequest: {
            run_id: components["schemas"]["ID"];
            bundle_ref: components["schemas"]["Ref"];
            artifact_ref: components["schemas"]["Ref"];
            /** @enum {string} */
            decision: "accept" | "reject";
        };
        RunsDeliveryRequest: {
            run_id: components["schemas"]["ID"];
        };
        RunsGetRequest: {
            run_id: components["schemas"]["ID"];
        };
        Scope: {
            principal_id: components["schemas"]["ID"];
            conversation_id?: components["schemas"]["ID"];
            task_id?: components["schemas"]["ID"];
            project_id?: components["schemas"]["ID"];
            resource_refs?: components["schemas"]["Ref"][];
            capabilities?: components["schemas"]["NonEmptyText"][];
        };
        ScopeSelector: {
            conversation_id?: components["schemas"]["ID"];
            task_id?: components["schemas"]["ID"];
            project_id?: components["schemas"]["ID"];
            resource_refs?: components["schemas"]["Ref"][];
        };
        /** @enum {string} */
        State: "pending" | "ready" | "running" | "waiting" | "completed" | "failed" | "stale" | "cancelled";
        TaskFrame: {
            task_id: components["schemas"]["ID"];
            revision: components["schemas"]["Revision"];
            original_input_ref: components["schemas"]["UserInputRef"];
            patch_refs: components["schemas"]["Ref"][];
            goal: string;
            constraints: components["schemas"]["Constraint"][];
            output_specs: components["schemas"]["OutputSpec"][];
            assumptions: components["schemas"]["NonEmptyText"][];
            unresolved: components["schemas"]["NonEmptyText"][];
            evidence_refs: components["schemas"]["Ref"][];
            created_at: components["schemas"]["Timestamp"];
            summary?: components["schemas"]["NonEmptyText"];
            input_revision?: components["schemas"]["Revision"];
            semantic_parse_ref?: components["schemas"]["Ref"];
        };
        TaskGraph: {
            task_id: components["schemas"]["ID"];
            revision: components["schemas"]["Revision"];
            /** @enum {string} */
            planning: "steps" | "dag";
            nodes: components["schemas"]["NodeSpec"][];
            source_frame_ref: components["schemas"]["Ref"];
            created_at: components["schemas"]["Timestamp"];
        };
        TasksFrameRequest: {
            task_id: components["schemas"]["ID"];
        };
        Text: string;
        /** Format: date-time */
        Timestamp: string;
        ToolResult: {
            call_ref: components["schemas"]["Ref"];
            status: components["schemas"]["ToolStatus"];
            data?: components["schemas"]["Object"];
            output_refs: components["schemas"]["Ref"][];
            failure?: components["schemas"]["Failure"];
            effect_state: components["schemas"]["EffectState"];
            usage_ref: components["schemas"]["Ref"];
            next_cursor?: components["schemas"]["Cursor"];
        };
        /** @enum {string} */
        ToolStatus: "succeeded" | "failed" | "waiting" | "cancelled" | "unknown";
        TurnsLookupRequest: {
            conversation_id: components["schemas"]["ID"];
            request_id: components["schemas"]["ID"];
        };
        TurnsSubmitRequest: {
            conversation_id: components["schemas"]["ID"];
            text: components["schemas"]["Text"];
            attachment_refs: components["schemas"]["Ref"][];
            task_id?: components["schemas"]["ID"];
            expected_task_revision?: components["schemas"]["Revision"];
            budget?: components["schemas"]["Budget"];
        };
        UserControl: {
            mode: components["schemas"]["ControlMode"];
            input_ref?: components["schemas"]["Ref"];
            preserve_refs: components["schemas"]["Ref"][];
            reason: components["schemas"]["Text"];
        };
        UserInputRef: components["schemas"]["Ref"] & {
            /** @constant */
            kind?: "input";
        };
        ValidatedCall: {
            tool_ref: components["schemas"]["Ref"];
            arguments: components["schemas"]["Object"];
            arguments_hash: components["schemas"]["Hash"];
            action_id: components["schemas"]["ID"];
        };
        VerificationCheck: {
            id: components["schemas"]["ID"];
            kind: components["schemas"]["VerificationKind"];
            requirement_ids: components["schemas"]["ID"][];
            state: components["schemas"]["CheckState"];
            target_refs: components["schemas"]["Ref"][];
            process_ref?: components["schemas"]["Ref"];
            evidence_refs: components["schemas"]["Ref"][];
            summary: components["schemas"]["Text"];
        };
        /** @enum {string} */
        VerificationKind: "command" | "structure" | "reference" | "semantic" | "manual";
        VerificationReport: {
            id: components["schemas"]["ID"];
            contract_ref: components["schemas"]["Ref"];
            target_refs: components["schemas"]["Ref"][];
            checks: components["schemas"]["VerificationCheck"][];
            verdicts: components["schemas"]["RequirementVerdict"][];
            outcome: components["schemas"]["Outcome"];
            limitations: components["schemas"]["NonEmptyText"][];
            reviewer_model_config_ref?: components["schemas"]["Ref"];
            created_at: components["schemas"]["Timestamp"];
        };
        Version: string;
        WebSession: {
            principal: components["schemas"]["Principal"];
            expires_at: components["schemas"]["Timestamp"];
            csrf_token: components["schemas"]["Hash"];
        };
        WebSessionExchangeRequest: {
            launch_code: components["schemas"]["NonEmptyText"];
        };
        WebSessionGetRequest: Record<string, never>;
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
