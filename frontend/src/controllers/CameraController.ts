import { useState, useEffect, useCallback } from "react";
import type { Camera, CameraCreate } from "../models/Camera";
import { cameraApi } from "../services/api";

export function useCameraController() {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [locations, setLocations] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchLocations = useCallback(async () => {
    try {
      const data = await cameraApi.getLocations();
      setLocations(data);
    } catch {
      // Non-critical, ignore
    }
  }, []);

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

  const updateCameraLocation = useCallback(
    async (id: number, location: string) => {
      try {
        setError(null);
        await cameraApi.update(id, { location: location || null });
        await fetchCameras();
        await fetchLocations();
      } catch (err) {
        setError("Failed to update location");
        console.error(err);
      }
    },
    [fetchCameras, fetchLocations]
  );

  useEffect(() => {
    fetchCameras();
    fetchLocations();
  }, [fetchCameras, fetchLocations]);

  return { cameras, locations, loading, error, fetchCameras, addCamera, deleteCamera, updateCameraLocation };
}
