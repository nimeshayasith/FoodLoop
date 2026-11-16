import { useEffect, useState } from "react";

const dt = new Intl.DateTimeFormat("en-GB", { timeZone: "Asia/Colombo", day: "numeric", month: "short", hour: "numeric", minute: "2-digit", hour12: true });
export const formatDateTime = (iso) => (iso ? dt.format(new Date(iso)) : "-");
export const lkr = (n) => `LKR ${Number(n || 0).toLocaleString("en-LK", { maximumFractionDigits: 2 })}`;

export function useCountdown(iso) {
  const [ms, setMs] = useState(() => new Date(iso) - Date.now());
  useEffect(() => {
    setMs(new Date(iso) - Date.now());
    const id = setInterval(() => setMs(new Date(iso) - Date.now()), 1000);
    return () => clearInterval(id);
  }, [iso]);
  return ms;
}

export function humanize(ms) {
  if (ms <= 0) return null;
  const s = Math.floor(ms / 1000), h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = s % 60;
  if (h >= 24) return `${Math.floor(h / 24)}d ${h % 24}h`;
  if (h > 0) return `${h}h ${String(m).padStart(2, "0")}m`;
  return `${m}m ${String(sec).padStart(2, "0")}s`;
}

// <input type="datetime-local"> value (browser local time) for "now + minutes"
export const localInputValue = (minutesFromNow) => {
  const d = new Date(Date.now() + minutesFromNow * 60000);
  d.setSeconds(0, 0);
  return new Date(d - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
};
export const localInputToIso = (value) => (value ? new Date(value).toISOString() : "");
