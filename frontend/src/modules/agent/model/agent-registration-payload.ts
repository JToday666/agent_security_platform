import type { AgentCreatePayload } from "@/shared/types/agent-registry-types";
import {
  cloneAgentRegistrationJson,
  type AgentRegisterForm,
} from "./agent-registration-form";
import {
  validateAgentRegistration,
  type AgentRegisterFieldErrors,
} from "./agent-registration-validation";

export interface AgentCreatePayloadResult {
  valid: boolean;
  errors: string[];
  fieldErrors: AgentRegisterFieldErrors;
  payload: AgentCreatePayload | null;
}

export const buildAgentCreatePayload = (
  form: AgentRegisterForm,
): AgentCreatePayloadResult => {
  const result = validateAgentRegistration(form);
  if (!result.valid) {
    return {
      valid: false,
      errors: result.errors,
      fieldErrors: result.fieldErrors,
      payload: null,
    };
  }

  const normalized = result.normalized;
  return {
    valid: true,
    errors: [],
    fieldErrors: {},
    payload: {
      templateId: normalized.templateId,
      name: normalized.name,
      description: normalized.description,
      invokeMode: form.invokeMode,
      connection: cloneAgentRegistrationJson(normalized.connection),
      auth: cloneAgentRegistrationJson(normalized.auth),
      platformInputMapping: cloneAgentRegistrationJson(
        normalized.platformInputMapping,
      ),
      taskRenderMode: "goal_only",
      customRequestBody: cloneAgentRegistrationJson(
        normalized.customRequestBody,
      ),
      requestOptions: cloneAgentRegistrationJson(normalized.requestOptions),
      platformOutputMapping: cloneAgentRegistrationJson(
        normalized.platformOutputMapping,
      ),
      terminalStatuses: normalized.terminalStatuses,
      successStatuses: normalized.successStatuses,
    },
  };
};
