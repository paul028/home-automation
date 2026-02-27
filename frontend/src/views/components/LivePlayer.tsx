import { useEffect, useRef, useState } from "react";

interface Props {
  mseUrl: string;
  className?: string;
}

export default function LivePlayer({ mseUrl, className = "" }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const [status, setStatus] = useState<"connecting" | "playing" | "error">(
    "connecting"
  );
  const [muted, setMuted] = useState(true);

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !mseUrl) return;

    // go2rtc MSE WebSocket connection
    const ws = new WebSocket(mseUrl);
    wsRef.current = ws;

    ws.binaryType = "arraybuffer";

    let mediaSource: MediaSource | null = null;
    let sourceBuffer: SourceBuffer | null = null;
    const bufferQueue: ArrayBuffer[] = [];

    ws.onopen = () => {
      mediaSource = new MediaSource();
      video.src = URL.createObjectURL(mediaSource);

      mediaSource.addEventListener("sourceopen", () => {
        // Send MSE codecs request to go2rtc
        ws.send(JSON.stringify({ type: "mse", value: "" }));
      });
    };

    ws.onmessage = (event) => {
      if (typeof event.data === "string") {
        const msg = JSON.parse(event.data);
        if (msg.type === "mse") {
          // Codec info received, create source buffer
          try {
            sourceBuffer = mediaSource!.addSourceBuffer(msg.value);
            sourceBuffer.mode = "segments";
            sourceBuffer.addEventListener("updateend", () => {
              if (bufferQueue.length > 0 && !sourceBuffer!.updating) {
                sourceBuffer!.appendBuffer(bufferQueue.shift()!);
              }
            });
          } catch (e) {
            console.error("Failed to create source buffer:", e);
            setStatus("error");
          }
        }
      } else {
        // Binary data - video segment
        if (sourceBuffer) {
          if (sourceBuffer.updating) {
            bufferQueue.push(event.data);
          } else {
            try {
              sourceBuffer.appendBuffer(event.data);
            } catch {
              bufferQueue.push(event.data);
            }
          }
        }
      }
    };

    ws.onerror = () => setStatus("error");
    ws.onclose = () => setStatus("error");

    video.onplaying = () => setStatus("playing");

    // Auto-play when ready
    video.oncanplay = () => {
      video.play().catch(() => {});
    };

    return () => {
      ws.close();
      if (mediaSource && mediaSource.readyState === "open") {
        try {
          mediaSource.endOfStream();
        } catch {
          // ignore
        }
      }
      video.src = "";
    };
  }, [mseUrl]);

  return (
    <div className={`relative overflow-hidden rounded-lg bg-black ${className}`}>
      <video
        ref={videoRef}
        autoPlay
        muted={muted}
        playsInline
        className="h-full w-full object-contain"
      />
      {status === "connecting" && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-900/80">
          <div className="text-center">
            <div className="mx-auto mb-2 h-8 w-8 animate-spin rounded-full border-2 border-gray-600 border-t-blue-500" />
            <p className="text-sm text-gray-400">Connecting to stream...</p>
          </div>
        </div>
      )}
      {status === "playing" && (
        <button
          onClick={() => {
            setMuted(!muted);
            if (videoRef.current) videoRef.current.muted = !muted;
          }}
          className="absolute bottom-3 right-3 rounded-md bg-gray-900/80 p-2 text-white backdrop-blur transition-colors hover:bg-gray-800"
        >
          {muted ? (
            <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
            </svg>
          ) : (
            <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072M18.364 5.636a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
            </svg>
          )}
        </button>
      )}
      {status === "error" && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-900/80">
          <div className="text-center">
            <p className="text-sm text-red-400">Stream unavailable</p>
            <p className="mt-1 text-xs text-gray-500">
              Check that go2rtc is running and the camera is accessible
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
