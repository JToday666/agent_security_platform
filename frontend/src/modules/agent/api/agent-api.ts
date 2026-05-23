import type {
  AgentArchiveResponse,
  AgentCreatePayload,
  AgentCreateResponse,
  AgentDetail,
  AgentListItem,
  AgentTemplate,
  AgentVerifyResponse,
} from "@/shared/types/agent-registry-types";
import {
  archiveLiveAgent,
  createLiveAgent,
  getLiveAgentDetail,
  getLiveAgentTemplates,
  getLiveAgents,
  verifyLiveAgent,
} from "./internal/live-agent-api";

export interface AgentListQuery {
  includeArchived?: boolean;
  status?: string;
}

export const getAgentTemplates = async (): Promise<AgentTemplate[]> =>
  getLiveAgentTemplates();

export const createAgent = async (
  payload: AgentCreatePayload,
): Promise<AgentCreateResponse> =>
  createLiveAgent(payload);

export const getAgents = async (
  query: AgentListQuery = {},
): Promise<AgentListItem[]> =>
  getLiveAgents(query);

export const getAgentDetail = async (agentId: string): Promise<AgentDetail> =>
  getLiveAgentDetail(agentId);

export const verifyAgent = async (
  agentId: string,
): Promise<AgentVerifyResponse> =>
  verifyLiveAgent(agentId);

export const archiveAgent = async (
  agentId: string,
): Promise<AgentArchiveResponse> =>
  archiveLiveAgent(agentId);
