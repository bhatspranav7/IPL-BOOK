import { useEffect, useRef, useState } from "react";
import { wsUrl } from "./api";

export interface LiveEvent {
  event: string;
  match_id: number;
  seats: string[];
  user_id: number;
  [key: string]: unknown;
}

/** Subscribes to backend booking events with automatic reconnect. */
export function useEvents(onEvent: (e: LiveEvent) => void) {
  const [connected, setConnected] = useState(false);
  const handler = useRef(onEvent);
  handler.current = onEvent;

  useEffect(() => {
    let ws: WebSocket | null = null;
    let retry: number | undefined;
    let delay = 1000;
    let closed = false;

    const connect = () => {
      ws = new WebSocket(wsUrl("/ws/events"));
      ws.onopen = () => {
        delay = 1000;
        setConnected(true);
      };
      ws.onmessage = (msg) => {
        try {
          handler.current(JSON.parse(msg.data));
        } catch {
          /* ignore malformed frames */
        }
      };
      ws.onclose = () => {
        setConnected(false);
        if (closed) return;
        retry = window.setTimeout(connect, delay);
        delay = Math.min(delay * 2, 15000);
      };
      ws.onerror = () => ws?.close();
    };

    connect();
    return () => {
      closed = true;
      window.clearTimeout(retry);
      ws?.close();
    };
  }, []);

  return connected;
}
