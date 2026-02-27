import { useState, useCallback } from "react";
import type { RecordingSegment } from "../models/Recording";
import { recordingApi } from "../services/api";

export function useRecordingController() {
  const [recordings, setRecordings] = useState<RecordingSegment[]>([]);
  const [recordingDays, setRecordingDays] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchRecordings = useCallback(
    async (cameraId: number, date: string) => {
      try {
        setLoading(true);
        setError(null);
        const data = await recordingApi.getRecordings(cameraId, date);
        setRecordings(data);
      } catch (err) {
        setError("Failed to fetch recordings");
        console.error(err);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const fetchRecordingDays = useCallback(
    async (cameraId: number, year: number, month: number) => {
      try {
        const data = await recordingApi.getRecordingDays(
          cameraId,
          year,
          month
        );
        setRecordingDays(data.days);
      } catch (err) {
        console.error(err);
      }
    },
    []
  );

  return {
    recordings,
    recordingDays,
    loading,
    error,
    fetchRecordings,
    fetchRecordingDays,
  };
}
