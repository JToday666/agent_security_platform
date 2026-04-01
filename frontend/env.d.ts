/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_BACKEND_TARGET?: string;
  readonly VITE_USE_LIVE_REFERENCE_API?: string;
  readonly VITE_USE_LIVE_SUBMISSION_API?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
