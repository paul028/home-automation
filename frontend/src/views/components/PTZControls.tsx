import { useState } from "react";
import { cameraApi } from "../../services/api";

interface Props {
  cameraId: number;
}

export default function PTZControls({ cameraId }: Props) {
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const move = async (direction: string) => {
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      await cameraApi.ptz(cameraId, direction, "start");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || "PTZ command failed";
      setError(msg);
    } finally {
      setBusy(false);
    }
  };

  const btnClass = busy
    ? "flex h-10 w-10 items-center justify-center rounded-md bg-gray-800/50 text-gray-600 cursor-not-allowed"
    : "flex h-10 w-10 items-center justify-center rounded-md bg-gray-800 text-gray-300 transition-colors hover:bg-gray-700 hover:text-white active:bg-gray-600";

  return (
    <div className="inline-flex flex-col items-center gap-1">
      <p className="mb-1 text-xs font-medium uppercase tracking-wider text-gray-500">
        PTZ Controls
      </p>
      {error && (
        <p className="mb-1 max-w-[140px] text-center text-xs text-red-400">
          {error}
        </p>
      )}
      <div className="grid grid-cols-3 gap-1">
        <div />
        <button onClick={() => move("up")} className={btnClass} disabled={busy} title="Pan Up">
          <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
          </svg>
        </button>
        <div />
        <button onClick={() => move("left")} className={btnClass} disabled={busy} title="Pan Left">
          <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <div className="flex h-10 w-10 items-center justify-center rounded-md bg-gray-800/50">
          <div className="h-2 w-2 rounded-full bg-gray-600" />
        </div>
        <button onClick={() => move("right")} className={btnClass} disabled={busy} title="Pan Right">
          <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
        <div />
        <button onClick={() => move("down")} className={btnClass} disabled={busy} title="Pan Down">
          <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        <div />
      </div>
    </div>
  );
}
