import { ApiConfig } from "@/shared/api/Config";
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
import {
  archiveMockAgent,
  createMockAgent,
  getMockAgentDetail,
  getMockAgentTemplates,
  getMockAgents,
  verifyMockAgent,
} from "./internal/mock-agent-api";

const useMockApi = ApiConfig.enableApiMock;

export interface AgentListQuery {
  includeArchived?: boolean;
  status?: string;
}

export const getAgentTemplates = async (): Promise<AgentTemplate[]> =>
  useMockApi ? getMockAgentTemplates() : getLiveAgentTemplates();

export const createAgent = async (
  payload: AgentCreatePayload,
): Promise<AgentCreateResponse> =>
  useMockApi ? createMockAgent(payload) : createLiveAgent(payload);

export const getAgents = async (
  query: AgentListQuery = {},
): Promise<AgentListItem[]> =>
  useMockApi ? getMockAgents(query) : getLiveAgents(query);

export const getAgentDetail = async (agentId: string): Promise<AgentDetail> =>
  useMockApi ? getMockAgentDetail(agentId) : getLiveAgentDetail(agentId);

export const verifyAgent = async (
  agentId: string,
): Promise<AgentVerifyResponse> =>
  useMockApi ? verifyMockAgent(agentId) : verifyLiveAgent(agentId);

export const archiveAgent = async (
  agentId: string,
): Promise<AgentArchiveResponse> =>
  useMockApi ? archiveMockAgent(agentId) : archiveLiveAgent(agentId);
