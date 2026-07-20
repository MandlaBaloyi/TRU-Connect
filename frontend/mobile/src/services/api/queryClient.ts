import { QueryClient } from "@tanstack/react-query";

/**
 * Shared React Query client. Ref: docs/03_FRONTEND_COMPONENT_SPECIFICATION.txt
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 0,
    },
  },
});
