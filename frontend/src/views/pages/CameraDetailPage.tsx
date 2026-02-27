import { useEffect, useState, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { useStreamController } from "../../controllers/StreamController";
import { cameraApi } from "../../services/api";
import type { Camera } from "../../models/Camera";
import LivePlayer from "../components/LivePlayer";
import PTZControls from "../components/PTZControls";
import RecordingPlayer from "../components/RecordingPlayer";
import EditableField from "../components/EditableField";

export default function CameraDetailPage() {
  const { id } = useParams<{ id: string }>();
  const cameraId = Number(id);
  const { streamInfo, fetchStream } = useStreamController();
  const [camera, setCamera] = useState<Camera | null>(null);
  const [locations, setLocations] = useState<string[]>([]);
  const [playlist, setPlaylist] = useState<string[] | null>(null);
  const [playbackIndex, setPlaybackIndex] = useState(0);

  useEffect(() => {
    if (!cameraId) return;
    cameraApi.getById(cameraId).then(setCamera).catch(console.error);
    cameraApi.getLocations().then(setLocations).catch(() => {});
    fetchStream(cameraId);
  }, [cameraId, fetchStream]);

  const updateField = useCallback(
    async (field: string, value: string) => {
      if (!camera) return;
      const updated = await cameraApi.update(camera.id, {
        [field]: value || null,
      });
      setCamera(updated);
      if (field === "location") {
        cameraApi.getLocations().then(setLocations).catch(() => {});
      }
    },
    [camera]
  );

  if (!camera) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-600 border-t-blue-500" />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex items-center gap-4">
        <Link
          to="/"
          className="rounded-md p-1 text-gray-500 transition-colors hover:bg-gray-800 hover:text-white"
        >
          <svg
            className="h-5 w-5"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 19l-7-7 7-7"
            />
          </svg>
        </Link>
        <div>
          <h2 className="text-2xl font-bold text-white">{camera.name}</h2>
          <p className="text-sm text-gray-500">
            {camera.ip_address} · {camera.model || camera.brand}
          </p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          {playlist ? (
            <div className="relative">
              <video
                key={playlist[playbackIndex]}
                controls
                autoPlay
                className="aspect-video w-full rounded-lg bg-black object-contain"
                src={`/api/recordings/play/${playlist[playbackIndex]}`}
                onEnded={() => {
                  if (playbackIndex < playlist.length - 1) {
                    setPlaybackIndex(playbackIndex + 1);
                  }
                }}
              />
              <div className="absolute left-3 top-3 flex items-center gap-2">
                <button
                  onClick={() => { setPlaylist(null); setPlaybackIndex(0); }}
                  className="flex items-center gap-1.5 rounded-md bg-gray-900/80 px-3 py-1.5 text-xs font-medium text-white backdrop-blur transition-colors hover:bg-gray-800"
                >
                  <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                  Back to Live
                </button>
                <span className="rounded-md bg-gray-900/80 px-2.5 py-1.5 text-xs text-gray-300 backdrop-blur">
                  {playbackIndex + 1} / {playlist.length}
                </span>
              </div>
            </div>
          ) : streamInfo ? (
            <LivePlayer
              mseUrl={streamInfo.mse_url}
              className="aspect-video"
            />
          ) : (
            <div className="flex aspect-video items-center justify-center rounded-lg bg-gray-900">
              <p className="text-sm text-gray-500">Loading stream...</p>
            </div>
          )}
        </div>

        <div className="space-y-6">
          {camera.has_ptz && (
            <div className="flex justify-center rounded-lg border border-gray-800 bg-gray-900 p-4">
              <PTZControls cameraId={camera.id} />
            </div>
          )}

          <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
            <h3 className="mb-3 text-sm font-medium uppercase tracking-wider text-gray-500">
              Camera Info
            </h3>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-500">Status</dt>
                <dd className="flex items-center gap-1.5">
                  <span
                    className={`h-2 w-2 rounded-full ${
                      camera.is_active ? "bg-green-500" : "bg-red-500"
                    }`}
                  />
                  {camera.is_active ? "Online" : "Offline"}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Brand</dt>
                <dd>{camera.brand}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Model</dt>
                <dd>{camera.model || "—"}</dd>
              </div>
              <div className="flex items-center justify-between">
                <dt className="text-gray-500">Location</dt>
                <dd>
                  <EditableField
                    value={camera.location || ""}
                    placeholder="Set location"
                    onSave={(v) => updateField("location", v)}
                    suggestions={locations}
                  />
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">PTZ</dt>
                <dd>{camera.has_ptz ? "Yes" : "No"}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Recording</dt>
                <dd>{camera.has_recording ? "Yes" : "No"}</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>

      {camera.has_recording && (
        <div className="mt-6">
          <RecordingPlayer
            cameraId={camera.id}
            activeFileId={playlist?.[playbackIndex] ?? null}
            onPlay={(fileIds, startIndex) => {
              setPlaylist(fileIds);
              setPlaybackIndex(startIndex);
            }}
          />
        </div>
      )}
    </div>
  );
}
