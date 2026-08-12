"use client";

import { useCallback, useEffect, useState } from "react";

export function useApiResource<T>(load: (signal: AbortSignal) => Promise<T>) {
  const [value, setValue] = useState<T>();
  const [error, setError] = useState<Error>();
  const [version, setVersion] = useState(0);
  const retry = useCallback(() => setVersion((current) => current + 1), []);

  useEffect(() => {
    const controller = new AbortController();
    setError(undefined);
    void load(controller.signal).then(setValue).catch((reason: unknown) => {
      if (!controller.signal.aborted) setError(reason instanceof Error ? reason : new Error("Unable to load"));
    });
    return () => controller.abort();
  }, [load, version]);

  return { value, error, retry, loading: value === undefined && error === undefined };
}
