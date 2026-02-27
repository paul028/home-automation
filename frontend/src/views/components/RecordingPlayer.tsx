import { useState } from "react";
import { useRecordingController } from "../../controllers/RecordingController";
import type { RecordingSegment } from "../../models/Recording";

interface Props {
  cameraId: number;
}

export default function RecordingPlayer({ cameraId }: Props) {
  const { recordings, loading, fetchRecordings } = useRecordingController();
  const [selectedDate, setSelectedDate] = useState(
    new Date().toISOString().split("T")[0]
  );

  const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const date = e.target.value;
    setSelectedDate(date);
    fetchRecordings(cameraId, date);
  };

  const formatTime = (timeStr: string) => {
    if (!timeStr) return "--:--";
    // Try to parse various time formats
    const parts = timeStr.match(/(\d{2}):?(\d{2}):?(\d{2})/);
    if (parts) return `${parts[1]}:${parts[2]}:${parts[3]}`;
    return timeStr;
  };

  const formatDuration = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    if (h > 0) return `${h}h ${m}m`;
    if (m > 0) return `${m}m ${s}s`;
    return `${s}s`;
  };

  return (
    <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-medium uppercase tracking-wider text-gray-500">
          Recordings
        </h3>
        <input
          type="date"
          value={selectedDate}
          onChange={handleDateChange}
          className="rounded-md border border-gray-700 bg-gray-800 px-3 py-1.5 text-sm text-white focus:border-blue-500 focus:outline-none"
        />
      </div>

      {loading && (
        <div className="py-8 text-center text-sm text-gray-500">
          Loading recordings...
        </div>
      )}

      {!loading && recordings.length === 0 && (
        <div className="py-8 text-center text-sm text-gray-500">
          No recordings found for this date
        </div>
      )}

      {!loading && recordings.length > 0 && (
        <div className="space-y-2">
          {recordings.map((rec: RecordingSegment, i: number) => (
            <div
              key={i}
              className="flex items-center justify-between rounded-md border border-gray-800 bg-gray-800/50 px-3 py-2"
            >
              <div className="flex items-center gap-3">
                <svg
                  className="h-4 w-4 text-red-400"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                >
                  <circle cx="12" cy="12" r="6" />
                </svg>
                <span className="text-sm text-white">
                  {formatTime(rec.start_time)} - {formatTime(rec.end_time)}
                </span>
              </div>
              <span className="text-xs text-gray-500">
                {formatDuration(rec.duration)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
