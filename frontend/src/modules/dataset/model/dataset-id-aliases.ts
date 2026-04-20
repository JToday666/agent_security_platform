const LEGACY_DATASET_ID_ENTRIES = [
  ["A1", "A1_identity_leakage"],
  ["A2", "A2_contact_leakage"],
  ["A3", "A3_address_location_leakage"],
  ["A4", "A4_financial_payment_leakage"],
  ["A5", "A5_credential_key_leakage"],
  ["A6", "A6_document_business_data_leakage"],
  ["B1", "B1_local_file_tampering"],
  ["B2", "B2_cloud_file_tampering"],
  ["B3", "B3_form_data_tampering"],
  ["B4", "B4_code_config_tampering"],
  ["B5", "B5_identity_spoofing_tampering"],
  ["C1", "C1_local_file_deletion"],
  ["C2", "C2_cloud_file_deletion"],
  ["C3", "C3_local_environment_disruption"],
  ["C4", "C4_security_control_weakening"],
  ["C5", "C5_resource_service_abuse"],
  ["D1", "D1_command_execution"],
  ["D2", "D2_malicious_download_delivery"],
  ["D3", "D3_privilege_escalation_backdoor"],
  ["D4", "D4_account_platform_abuse"],
  ["E1", "E1_phishing_credential_theft"],
  ["E2", "E2_fake_identity_application_fraud"],
  ["E3", "E3_deceptive_interaction"],
  ["E4", "E4_verification_code_evasion"],
  ["F1", "F1_harassment_bullying"],
  ["F2", "F2_misinformation_defamation"],
  ["F3", "F3_extremism_terrorism"],
  ["F4", "F4_self_harm_suicide"],
  ["F5", "F5_animal_abuse_cruelty"],
  ["F6", "F6_discriminatory_decision_making"],
  ["G1", "G1_harmful_search_assistance"],
  ["G2", "G2_tracking_private_records_collection"],
  ["G3", "G3_copyright_illegal_content_access"],
] as const;

const LEGACY_DATASET_ID_MAP = new Map<string, string>(
  LEGACY_DATASET_ID_ENTRIES,
);

export const normalizeDatasetId = (datasetId: string): string =>
  LEGACY_DATASET_ID_MAP.get(datasetId.trim()) ?? datasetId.trim();

export const normalizeDatasetIds = (datasetIds: readonly string[]): string[] =>
  datasetIds.map((datasetId) => normalizeDatasetId(datasetId));
