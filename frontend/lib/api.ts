const BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ??
  "http://localhost:8000";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init);
  const json = await res.json();
  if (!res.ok) throw new Error(json.error ?? "Request failed");
  return json as T;
}

export async function analyzeFunds(files: File[], freq: string) {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  form.append("freq", freq);
  return req("/api/analyze", { method: "POST", body: form });
}

export async function analyzeDefaults(freq: string) {
  const form = new FormData();
  form.append("freq", freq);
  return req("/api/analyze", { method: "POST", body: form });
}

export async function computeFrontier(
  mu: number[],
  sigma: number[][],
  allow_short: boolean
) {
  return req("/api/frontier", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mu, sigma, allow_short }),
  });
}

export async function fetchQuestions() {
  return req("/api/questions");
}

export async function computeProfile(total_score: number) {
  return req("/api/profile", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ total_score }),
  });
}

export async function computeOptimal(
  mu: number[],
  sigma: number[][],
  A: number,
  allow_short: boolean,
  fund_names: string[]
) {
  return req("/api/optimal", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mu, sigma, A, allow_short, fund_names }),
  });
}
