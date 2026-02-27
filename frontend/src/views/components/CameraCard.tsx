import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { Camera } from "../../models/Camera";
import type { StreamInfo } from "../../models/Stream";
import { streamApi } from "../../services/api";
import LivePlayer from "./LivePlayer";
import EditableField from "./EditableField";

interface Props {
  camera: Camera;
  onDelete: (id: number) => void;
  onUpdateLocation: (id: number, location: string) => void;
  locations: string[];
}

export default function CameraCard({
  camera,
  onDelete,
  onUpdateLocation,
  locations,
}: Props) {
  const [streamInfo, setStreamInfo] = useState<StreamInfo | null>(null);

  useEffect(() => {
    streamApi.getStreamInfo(camera.id).then(setStreamInfo).catch(() => {});
  }, [camera.id]);

  return (
    <div className="overflow-hidden rounded-lg border border-gray-800 bg-gray-900 transition-colors hover:border-gray-700">
      <Link to={`/camera/${camera.id}`}>
        <div className="relative aspect-video bg-gray-800">
          {streamInfo ? (
            <LivePlayer mseUrl={streamInfo.mse_url} className="h-full w-full" />
          ) : (
            <div className="flex h-full items-center justify-center text-gray-500">
              <div className="text-center">
                <div className="mx-auto mb-2 h-6 w-6 animate-spin rounded-full border-2 border-gray-600 border-t-blue-500" />
                <p className="text-xs text-gray-500">Loading stream...</p>
              </div>
            </div>
          )}
          <div className="absolute bottom-2 left-2 z-10 flex gap-1">
            {camera.has_ptz && (
              <span className="rounded bg-blue-600/80 px-1.5 py-0.5 text-xs font-medium">
                PTZ
              </span>
            )}
            {camera.has_recording && (
              <span className="rounded bg-red-600/80 px-1.5 py-0.5 text-xs font-medium">
                REC
              </span>
            )}
          </div>
          <div
            className={`absolute right-2 top-2 z-10 h-2.5 w-2.5 rounded-full ${
              camera.is_active ? "bg-green-500" : "bg-red-500"
            }`}
          />
        </div>
      </Link>
      <div className="p-3">
        <div className="flex items-center justify-between">
          <h3 className="font-medium text-white">{camera.name}</h3>
          <button
            onClick={() => onDelete(camera.id)}
            className="rounded p-1 text-gray-500 transition-colors hover:bg-red-900/30 hover:text-red-400"
            title="Delete camera"
          >
            <svg
              className="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              />
            </svg>
          </button>
        </div>
        <p className="text-xs text-gray-500">
          {camera.ip_address} · {camera.model || camera.brand}
        </p>
        <div className="mt-1.5 text-xs text-gray-400">
          <EditableField
            value={camera.location || ""}
            placeholder="Set location"
            onSave={(v) => onUpdateLocation(camera.id, v)}
            suggestions={locations}
          />
        </div>
      </div>
    </div>
  );
}
