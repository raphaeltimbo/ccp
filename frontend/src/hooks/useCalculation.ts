import { useMutation } from "@tanstack/react-query";
import { calculateStraightThrough } from "../lib/api/straightThrough";
import { useStraightThroughStore } from "../stores/straightThroughStore";

export function useCalculation() {
  const setResults = useStraightThroughStore((s) => s.setResults);
  const setIsCalculating = useStraightThroughStore((s) => s.setIsCalculating);

  return useMutation({
    mutationFn: calculateStraightThrough,
    onMutate: () => setIsCalculating(true),
    onSuccess: (data) => {
      setResults(data);
      setIsCalculating(false);
    },
    onError: () => setIsCalculating(false),
  });
}
