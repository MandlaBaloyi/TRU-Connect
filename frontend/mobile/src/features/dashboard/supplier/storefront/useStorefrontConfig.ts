import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiGet, apiPut } from "@/services/api/apiClient";
import type { StorefrontConfig, StorefrontConfigSection } from "./types";

const storefrontConfigKey = ["supplierStorefront", "config"] as const;

/**
 * The supplier's own storefront configuration.
 *
 * ONE WRITE FOR THE WHOLE THING, mirroring the backend's PUT. That is
 * not laziness: reordering is inherently about the whole set --
 * moving one section changes every position after it -- so a
 * per-section save would have the screen firing several requests that
 * are only correct together, and a failure halfway through would leave
 * a storefront in a state the supplier never asked for.
 *
 * NO MOCK PATH. Unlike the business-facing storefront, this has a real
 * endpoint from the start and nothing to design against a fixture --
 * the whole screen is the supplier's own data or it is nothing.
 *
 * INVALIDATES THE BUSINESS-FACING FEED TOO. A supplier who switches a
 * section off and then previews their own profile must see it gone;
 * without this the cached business-side storefront would keep showing
 * it until that query happened to refetch.
 */
export function useStorefrontConfig() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: storefrontConfigKey,
    queryFn: () => apiGet<StorefrontConfig>("/supplier-discovery/my-profile/storefront"),
  });

  const save = useMutation({
    mutationFn: (sections: StorefrontConfigSection[]) =>
      apiPut<StorefrontConfig>("/supplier-discovery/my-profile/storefront", {
        // POSITION IS SENT AS THE ARRAY ORDER, not as whatever number
        // each section happens to be carrying. The backend re-derives
        // position from the list index anyway; sending stale numbers
        // alongside a reordered list is how the two disagree.
        sections: sections.map((section) => ({
          type: section.type,
          isEnabled: section.isEnabled,
          title: section.title,
          productIds: section.productIds,
        })),
      }),
    onSuccess: (saved) => {
      queryClient.setQueryData(storefrontConfigKey, saved);
      queryClient.invalidateQueries({ queryKey: ["findSupplier", "storefront"] });
    },
  });

  return {
    sections: query.data?.sections ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
    save: save.mutateAsync,
    isSaving: save.isPending,
    saveError: save.error,
  };
}
