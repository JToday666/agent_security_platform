import { isValidHttpUrl } from "@/modules/submission/model/parameter-validator";
import type {
  AgentAuthType,
  AgentCreatePayload,
} from "@/shared/types/agent-registry-types";
import {
  buildAgentCustomRequestBody,
  cloneAgentRegistrationJson,
  parseAgentStatusText,
  type AgentRegisterForm,
} from "./agent-registration-form";

export interface AgentRegisterFieldErrors {
  templateId?: string;
  name?: string;
  baseUrl?: string;
  invokePath?: string;
  resultPathTemplate?: string;
  taskMapping?: string;
  customRequestBody?: string;
  outputMapping?: string;
  terminalStatuses?: string;
  successStatuses?: string;
  authSecret?: string;
}

export interface AgentCreatePayloadResult {
  valid: boolean;
  errors: string[];
  fieldErrors: AgentRegisterFieldErrors;
  payload: AgentCreatePayload | null;
}

const buildAuthConfig = (
  form: AgentRegisterForm,
): { type: AgentAuthType; config: Record<string, string> } => {
  if (form.auth.type === "none") {
    return { type: "none", config: {} };
  }

  if (form.auth.type === "bearer") {
    return {
      type: "bearer",
      config: {
        token: form.auth.token.trim(),
      },
    };
  }

  return {
    type: form.auth.type,
    config: {
      headerName: form.auth.headerName.trim(),
      secret: form.auth.secret.trim(),
    },
  };
};

export const buildAgentCreatePayload = (
  form: AgentRegisterForm,
): AgentCreatePayloadResult => {
  const errors: string[] = [];
  const fieldErrors: AgentRegisterFieldErrors = {};
  const name = form.name.trim();

  if (!form.templateId.trim()) {
    errors.push("请选择注册模板。");
    fieldErrors.templateId = "请选择注册模板";
  }

  if (!name) {
    errors.push("请填写 Agent 名称。");
    fieldErrors.name = "请填写 Agent 名称";
  }

  if (!form.connection.baseUrl.trim()) {
    errors.push("请填写服务根地址。");
    fieldErrors.baseUrl = "请填写服务根地址";
  } else if (!isValidHttpUrl(form.connection.baseUrl.trim())) {
    errors.push("服务根地址格式不正确。");
    fieldErrors.baseUrl = "服务根地址格式不正确";
  }

  if (!form.connection.invokePath.trim()) {
    errors.push("请填写提交任务路径。");
    fieldErrors.invokePath = "请填写提交任务路径";
  }

  if (
    form.invokeMode === "submit_poll" &&
    !form.connection.resultPathTemplate?.trim()
  ) {
    errors.push("轮询模式下必须填写结果路径模板。");
    fieldErrors.resultPathTemplate = "请填写结果路径模板";
  }

  if (!form.platformInputMapping.task.trim()) {
    errors.push("平台任务字段映射不能为空。");
    fieldErrors.taskMapping = "请填写 task 对应字段名";
  }

  const customBodyResult = buildAgentCustomRequestBody(
    form.customRequestFields,
  );
  if (customBodyResult.errors.length) {
    errors.push(...customBodyResult.errors);
    fieldErrors.customRequestBody = customBodyResult.errors[0];
  }

  const mappedFieldNames = Object.values(form.platformInputMapping)
    .map((value) => value?.trim())
    .filter((value): value is string => Boolean(value));
  const mappedFieldNameSet = new Set(mappedFieldNames);
  const conflictField = Object.keys(customBodyResult.body).find((key) =>
    mappedFieldNameSet.has(key),
  );
  if (conflictField) {
    const message = `字段 ${conflictField} 已被平台输入映射使用，不能作为自定义固定字段。`;
    errors.push(message);
    fieldErrors.customRequestBody = message;
  }

  const terminalStatuses = parseAgentStatusText(form.terminalStatusesText);
  const successStatuses = parseAgentStatusText(form.successStatusesText);
  if (terminalStatuses.length === 0) {
    errors.push("请至少填写一个终态。");
    fieldErrors.terminalStatuses = "请至少填写一个终态";
  }

  const terminalStatusSet = new Set(terminalStatuses);
  const invalidSuccess = successStatuses.find(
    (item) => !terminalStatusSet.has(item),
  );
  if (invalidSuccess) {
    errors.push("成功态必须属于终态集合。");
    fieldErrors.successStatuses = "成功态必须属于终态集合";
  }

  if (
    form.invokeMode === "submit_poll" &&
    (!form.platformOutputMapping.externalRunId?.trim() ||
      !form.platformOutputMapping.status?.trim())
  ) {
    const message = "轮询模式下必须配置运行 ID 和状态输出路径。";
    errors.push(message);
    fieldErrors.outputMapping = message;
  }

  if (form.auth.type === "bearer" && !form.auth.token.trim()) {
    errors.push("请填写 Bearer Token。");
    fieldErrors.authSecret = "请填写 Bearer Token";
  }

  if (
    (form.auth.type === "api_key_header" ||
      form.auth.type === "custom_header") &&
    (!form.auth.headerName.trim() || !form.auth.secret.trim())
  ) {
    errors.push("请填写 Header 名称和密钥。");
    fieldErrors.authSecret = "请填写 Header 名称和密钥";
  }

  if (errors.length) {
    return {
      valid: false,
      errors,
      fieldErrors,
      payload: null,
    };
  }

  return {
    valid: true,
    errors: [],
    fieldErrors: {},
    payload: {
      templateId: form.templateId.trim(),
      name,
      description: form.description.trim(),
      invokeMode: form.invokeMode,
      connection: {
        ...form.connection,
        baseUrl: form.connection.baseUrl.trim(),
        invokePath: form.connection.invokePath.trim(),
        resultPathTemplate: form.connection.resultPathTemplate?.trim(),
      },
      auth: buildAuthConfig(form),
      platformInputMapping: cloneAgentRegistrationJson(
        form.platformInputMapping,
      ),
      taskRenderMode: "goal_only",
      customRequestBody: customBodyResult.body,
      requestOptions: cloneAgentRegistrationJson(form.requestOptions),
      platformOutputMapping: cloneAgentRegistrationJson(
        form.platformOutputMapping,
      ),
      terminalStatuses,
      successStatuses,
    },
  };
};
