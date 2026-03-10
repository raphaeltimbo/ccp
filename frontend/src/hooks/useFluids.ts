import { useQuery } from "@tanstack/react-query";
import { getFluids, getUnits } from "../lib/api/fluids";

export function useFluids() {
  return useQuery({ queryKey: ["fluids"], queryFn: getFluids });
}

export function useUnits() {
  return useQuery({ queryKey: ["units"], queryFn: getUnits });
}
