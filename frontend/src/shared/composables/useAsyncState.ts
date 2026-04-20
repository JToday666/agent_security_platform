import { ref } from "vue";

export const getErrorMessage = (error: unknown, fallback: string): string =>
  error instanceof Error ? error.message : fallback;

export const useAsyncState = <T>(initialValue: T | null = null) => {
  const data = ref<T | null>(initialValue);
  const loading = ref(false);
  const error = ref("");

  const startLoading = () => {
    loading.value = true;
    error.value = "";
  };

  const stopLoading = () => {
    loading.value = false;
  };

  const setError = (err: unknown, fallback: string) => {
    error.value = getErrorMessage(err, fallback);
  };

  return {
    data,
    loading,
    error,
    startLoading,
    stopLoading,
    setError,
  };
};
