import { useState, useCallback } from "react";
import type { StreamInfo } from "../models/Stream";
import { streamApi } from "../services/api";

export function useStreamController() {
  const [streamInfo, setStreamInfo] = useState<StreamInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStream = useCallback(async (cameraId: number) => {
    try {
      setLoading(true);
      setError(null);
      const data = await streamApi.getStreamInfo(cameraId);
      setStreamInfo(data);
      return data;
    } catch (err) {
      setError("Failed to fetch stream info");
      console.error(err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { streamInfo, loading, error, fetchStream };
}
