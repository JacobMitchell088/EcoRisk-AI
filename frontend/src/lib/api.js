export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";
export const TURNSTILE_SITE_KEY = import.meta.env.VITE_TURNSTILE_SITE_KEY || "";
export const backendUrl = API_BASE_URL ? API_BASE_URL.replace(/\/$/, "") : "";

// Pull a readable message out of a FastAPI error response ({detail} or {message}).
export async function readErrorMessage(response, fallback) {
  const text = await response.text();
  try {
    const json = JSON.parse(text);
    if (typeof json.detail === "string") return json.detail;
    if (typeof json.message === "string") return json.message;
    return fallback;
  } catch {
    return text || fallback;
  }
}

export function isNetworkError(err) {
  return (
    err instanceof TypeError &&
    /failed to fetch|networkerror|load failed|network request failed/i.test(err.message)
  );
}
