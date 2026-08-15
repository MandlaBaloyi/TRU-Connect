import { useMutation, useQuery } from "@tanstack/react-query";

import { getSubscription, requestUpgrade } from "../services/subscriptionService";

export function useSubscription() {
  const query = useQuery({
    queryKey: ["supplierMyAccount", "subscription"],
    queryFn: getSubscription,
  });

  const upgrade = useMutation({
    mutationFn: requestUpgrade,
  });

  return {
    subscription: query.data ?? null,
    isLoading: query.isLoading,
    requestUpgrade: upgrade.mutateAsync,
    isUpgrading: upgrade.isPending,
    upgradeError: upgrade.error,
  };
}
