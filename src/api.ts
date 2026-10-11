export async function request<T>(path: string, body?: unknown): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, {
      method: body === undefined ? "GET" : "POST",
      headers:
        body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new Error(
      "The planning service is not reachable. Check the connection and try again. Your inputs are still here.",
    );
  }
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = data?.detail ?? data?.message ?? data?.error;
    const text =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail
              .map(
                (e: { loc?: unknown[]; msg?: string }) =>
                  `${(e.loc ?? []).filter((x) => x !== "body").join(" › ")}: ${e.msg ?? "Invalid value"}`,
              )
              .join(" · ")
          : "The service could not complete this request. Please try again.";
    throw new Error(text);
  }
  if (!data)
    throw new Error(
      "The service returned an unreadable response. Please try again.",
    );
  return data as T;
}
export function minutes(time: string) {
  const [h, m] = time.split(":").map(Number);
  return h * 60 + m;
}
export function timeString(value: number) {
  return `${Math.floor(value / 60)
    .toString()
    .padStart(2, "0")}:${(value % 60).toString().padStart(2, "0")}`;
}
export function prettyDate(date: string) {
  return new Date(`${date}T12:00:00+05:30`).toLocaleDateString("en-IN", {
    weekday: "short",
    day: "numeric",
    month: "short",
  });
}
export function number(value: number | null | undefined, unit = "") {
  return typeof value === "number" && Number.isFinite(value)
    ? `${value.toFixed(1)}${unit}`
    : "—";
}
export function fingerprint(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(fingerprint).join(",")}]`;
  if (value && typeof value === "object")
    return `{${Object.entries(value)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([k, v]) => `${k}:${fingerprint(v)}`)
      .join(",")}}`;
  return JSON.stringify(value);
}
