import axios from "axios";
import type { Camera, CameraDetail, CameraCreate, CameraUpdate } from "../models/Camera";
import type { StreamInfo } from "../models/Stream";
import type { RecordingSegment, RecordingDays } from "../models/Recording";

const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

export const cameraApi = {
  getAll: () => api.get<Camera[]>("/cameras").then((r) => r.data),

  getById: (id: number) =>
    api.get<CameraDetail>(`/cameras/${id}`).then((r) => r.data),

  create: (data: CameraCreate) =>
    api.post<Camera>("/cameras", data).then((r) => r.data),

  update: (id: number, data: CameraUpdate) =>
    api.put<Camera>(`/cameras/${id}`, data).then((r) => r.data),

  delete: (id: number) => api.delete(`/cameras/${id}`),

  ptz: (id: number, direction: string, action: string = "start") =>
    api.post(`/cameras/${id}/ptz`, { direction, action }),

  getPresets: (id: number) =>
    api
      .get<{ id: string; name: string }[]>(`/cameras/${id}/presets`)
      .then((r) => r.data),

  getLocations: () =>
    api.get<string[]>("/cameras/locations").then((r) => r.data),
};

export const streamApi = {
  getStreamInfo: (cameraId: number) =>
    api.get<StreamInfo>(`/streams/${cameraId}`).then((r) => r.data),

  getActiveStreams: () => api.get("/streams").then((r) => r.data),
};

export const recordingApi = {
  getRecordings: (cameraId: number, date: string) =>
    api
      .get<RecordingSegment[]>(`/recordings/${cameraId}`, {
        params: { recording_date: date },
      })
      .then((r) => r.data),

  getRecordingDays: (cameraId: number, year: number, month: number) =>
    api
      .get<RecordingDays>(`/recordings/${cameraId}/days`, {
        params: { year, month },
      })
      .then((r) => r.data),
};

export default api;
