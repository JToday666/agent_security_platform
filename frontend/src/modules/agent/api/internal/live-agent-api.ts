import { translateRuntimeMessage } from "@/app/i18n/runtime-translator";
import request from "@/shared/api/http-client";
import type {
  AgentArchiveResponse,
  AgentCreatePayload,
  AgentCreateResponse,
  AgentDetail,
  AgentListItem,
  AgentTemplate,
  AgentVerifyResponse,
} from "@/shared/types/agent-registry-types";
import type { AgentListQuery } from "../agent-api";
import { createAgentServiceError } from "./agent-service-shared";

const buildListParams = (query: AgentListQuery) => ({
  includeArchived: query.includeArchived ?? false,
  ...(query.status ? { status: query.status } : {}),
});

export const getLiveAgentTemplates = async (): Promise<AgentTemplate[]> => {
  const response = await request.get<AgentTemplate[]>("/agents/templates");

  if (!response.success || !response.data) {
    throw createAgentServiceError(
      response.message ||
        translateRuntimeMessage("agent.api.templateLoadFailed"),
      response.code,
    );
  }

  return response.data;
};

export const createLiveAgent = async (
  payload: AgentCreatePayload,
): Promise<AgentCreateResponse> => {
  const response = await request.post<AgentCreateResponse>("/agents", payload);

  if (!response.success || !response.data) {
    throw createAgentServiceError(
      response.message || translateRuntimeMessage("agent.api.createFailed"),
      response.code,
    );
  }

  return response.data;
};

export const getLiveAgents = async (
  query: AgentListQuery,
): Promise<AgentListItem[]> => {
  const response = await request.get<AgentListItem[]>("/agents", {
    params: buildListParams(query),
  });

  if (!response.success || !response.data) {
    throw createAgentServiceError(
      response.message || translateRuntimeMessage("agent.api.listLoadFailed"),
      response.code,
    );
  }

  return response.data;
};

export const getLiveAgentDetail = async (
  agentId: string,
): Promise<AgentDetail> => {
  const response = await request.get<AgentDetail>(`/agents/${agentId}`);

  if (!response.success || !response.data) {
    throw createAgentServiceError(
      response.message || translateRuntimeMessage("agent.api.detailLoadFailed"),
      response.code,
    );
  }

  return response.data;
};

export const verifyLiveAgent = async (
  agentId: string,
): Promise<AgentVerifyResponse> => {
  const response = await request.post<AgentVerifyResponse>(
    `/agents/${agentId}/verify`,
    { timeoutSeconds: 90 },
  );

  if (!response.success || !response.data) {
    throw createAgentServiceError(
      response.message || translateRuntimeMessage("agent.api.verifyFailed"),
      response.code,
    );
  }

  return response.data;
};

export const archiveLiveAgent = async (
  agentId: string,
): Promise<AgentArchiveResponse> => {
  const response = await request.post<AgentArchiveResponse>(
    `/agents/${agentId}/archive`,
  );

  if (!response.success || !response.data) {
    throw createAgentServiceError(
      response.message || translateRuntimeMessage("agent.api.archiveFailed"),
      response.code,
    );
  }

  return response.data;
};
