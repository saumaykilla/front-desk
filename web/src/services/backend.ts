export type HealthResponse = { status: string; service: string };

const backendUrl = process.env.NEXT_PUBLIC_BACKEND_API_URL ?? "http://127.0.0.1:8000";

export async function getBackendHealth(): Promise<HealthResponse> {
  const response = await fetch(`${backendUrl.replace(/\/$/, "")}/health`, {
    headers: { Accept: "application/json" },
    cache: "no-store",
  });
  if (!response.ok) throw new Error(`Backend health request failed (${response.status})`);
  return (await response.json()) as HealthResponse;
}
