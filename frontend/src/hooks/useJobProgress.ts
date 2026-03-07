import { useQuery } from "@tanstack/react-query";
import * as api from "@/lib/api";

export function useJobProgress(jobId: string | null) {
  return useQuery({
    queryKey: ["jobs", jobId],
    queryFn: () => api.getJobStatus(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      // Stop polling when job is done or failed
      if (status === "completed" || status === "failed") return false;
      return 1000; // Poll every second
    },
  });
}
