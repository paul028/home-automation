import { useState, useEffect, useCallback } from "react";
import type { Camera, CameraCreate } from "../models/Camera";
import { cameraApi } from "../services/api";

export function useCameraController() {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCameras = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await cameraApi.getAll();
      setCameras(data);
    } catch (err) {
      setError("Failed to fetch cameras");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  const addCamera = useCallback(
    async (data: CameraCreate) => {
      try {
        setError(null);
        await cameraApi.create(data);
        await fetchCameras();
      } catch (err) {
        setError("Failed to add camera");
        throw err;
      }
    },
    [fetchCameras]
  );

  const deleteCamera = useCallback(
    async (id: number) => {
      try {
        setError(null);
        await cameraApi.delete(id);
        await fetchCameras();
      } catch (err) {
        setError("Failed to delete camera");
        throw err;
      }
    },
    [fetchCameras]
  );

  useEffect(() => {
    fetchCameras();
  }, [fetchCameras]);

  return { cameras, loading, error, fetchCameras, addCamera, deleteCamera };
}
