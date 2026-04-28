import {
  createErrorEnvelope,
  createSuccessEnvelope,
  resolveMockEnvelope,
} from "@/shared/api/mock-api-utils";
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
import {
  createStoredMockAgent,
  getStoredMockAgentById,
  getStoredMockAgents,
  referenceAgentTemplates,
  toAgentListItem,
  updateStoredMockAgent,
  verifyStoredMockAgent,
} from "./mock-agent-store";

const MOCK_DELAY_MS = 360;

export const getMockAgentTemplates = async (): Promise<AgentTemplate[]> => {
  const result = await resolveMockEnvelope(
    createSuccessEnvelope(referenceAgentTemplates),
    { delay: MOCK_DELAY_MS },
  );

  return result.data;
};

export const createMockAgent = async (
  payload: AgentCreatePayload,
): Promise<AgentCreateResponse> => {
  const agent = createStoredMockAgent(payload);
  const result = await resolveMockEnvelope(
    createSuccessEnvelope({
      agentId: agent.agentId,
      name: agent.name,
      invokeMode: agent.invokeMode,
      status: agent.status,
      verifiedAt: agent.verifiedAt,
      lastVerificationPassed: agent.lastVerification?.passed ?? null,
      createdAt: agent.createdAt,
      updatedAt: agent.updatedAt,
    }),
    { delay: MOCK_DELAY_MS },
  );

  return result.data;
};

export const getMockAgents = async (
  query: AgentListQuery,
): Promise<AgentListItem[]> => {
  const status = query.status?.trim();
  const agents = getStoredMockAgents()
    .filter((agent) => query.includeArchived || agent.status !== "archived")
    .filter((agent) => !status || agent.status === status)
    .map(toAgentListItem);
  const result = await resolveMockEnvelope(createSuccessEnvelope(agents), {
    delay: MOCK_DELAY_MS,
  });

  return result.data;
};

export const getMockAgentDetail = async (
  agentId: string,
): Promise<AgentDetail> => {
  const agent = getStoredMockAgentById(agentId);
  if (!agent) {
    const result = await resolveMockEnvelope(
      createErrorEnvelope(40400, "Agent 不存在。", null),
      { delay: MOCK_DELAY_MS },
    );
    throw createAgentServiceError(result.message, result.code);
  }

  const result = await resolveMockEnvelope(createSuccessEnvelope(agent), {
    delay: MOCK_DELAY_MS,
  });

  return result.data;
};

export const verifyMockAgent = async (
  agentId: string,
): Promise<AgentVerifyResponse> => {
  try {
    const verification = verifyStoredMockAgent(agentId);
    const result = await resolveMockEnvelope(
      createSuccessEnvelope(verification),
      { delay: MOCK_DELAY_MS },
    );

    return result.data;
  } catch (error) {
    const result = await resolveMockEnvelope(
      createErrorEnvelope(
        40400,
        error instanceof Error ? error.message : "Agent 验证失败。",
        null,
      ),
      { delay: MOCK_DELAY_MS },
    );
    throw createAgentServiceError(result.message, result.code);
  }
};

export const archiveMockAgent = async (
  agentId: string,
): Promise<AgentArchiveResponse> => {
  const agent = getStoredMockAgentById(agentId);
  if (!agent) {
    const result = await resolveMockEnvelope(
      createErrorEnvelope(40400, "Agent 不存在。", null),
      { delay: MOCK_DELAY_MS },
    );
    throw createAgentServiceError(result.message, result.code);
  }

  if (agent.status === "archived") {
    const result = await resolveMockEnvelope(
      createErrorEnvelope(40901, "已归档 Agent 不能重复归档。", null),
      { delay: MOCK_DELAY_MS },
    );
    throw createAgentServiceError(result.message, result.code);
  }

  const updatedAt = new Date().toISOString();
  updateStoredMockAgent({
    ...agent,
    status: "archived",
    updatedAt,
  });

  const result = await resolveMockEnvelope(
    createSuccessEnvelope({
      agentId,
      status: "archived" as const,
      updatedAt,
    }),
    { delay: MOCK_DELAY_MS },
  );

  return result.data;
};
