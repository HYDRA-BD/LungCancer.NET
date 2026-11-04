/**
 * lib/api.ts — Typed API helpers for LungCancer.NET FastAPI backend.
 */
import { toast } from "sonner";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ─── Interfaces ──────────────────────────────────────────────────────────────

export interface User {
  id: number;
  name: string;
  email: string;
  role: "clinician" | "auditor";
}

export interface AuthResponse {
  token: string;
  user: User;
}

export interface StateAQI {
  name: string;
  aqi_5yr: number | null;
  pm25_5yr: number | null;
  aqi_category: number | null;
}

export interface PatientInputData {
  age: number;
  bmi: number;
  pack_years: number;
  resp_burden: boolean;
  chronic_burden: boolean;
  low_access: boolean;
  sex: number; // 1 = Male, 2 = Female
  state: string;
  patient_id?: string;
  packs_per_day?: number;
  years_smoked?: number;
  asthma?: boolean;
  copd?: boolean;
  heart_attack?: boolean;
  chd?: boolean;
  stroke?: boolean;
  diabetes?: boolean;
  height_weight?: string;
}

export interface ShapItem {
  feature: string;
  value: number;
  contribution: number;
  direction?: string;
}

export interface PredictionData {
  tier: "REFER" | "REVIEW" | "RULE-OUT";
  risk_score: number;
  ci_lower: number;
  ci_upper: number;
  recommendation: string;
  shap_items: ShapItem[];
  contributing_factors?: string[];
}

export interface GuidelineItem {
  text: string;
  page?: number | string;
}

export interface AnalyzeResponse {
  prediction: PredictionData;
  guidelines: GuidelineItem[];
  summary: string;
  aqi: {
    aqi_5yr: number | null;
    pm25_5yr: number | null;
    aqi_category: number | null;
  };
  patient: Record<string, unknown>;
}

// ─── Token & Auth Helpers ────────────────────────────────────────────────────

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

export function getCurrentUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem("user");
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function logout(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem("token");
  localStorage.removeItem("user");
  window.location.href = "/login";
}

// ─── Core Request Wrapper ────────────────────────────────────────────────────

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers = new Headers(options.headers || {});

  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  let response: Response;
  try {
    response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
    });
  } catch {
    const errorMsg = "Backend not reachable at localhost:8000";
    toast.error(errorMsg);
    throw new Error(errorMsg);
  }

  if (!response.ok) {
    if (response.status === 401) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        toast.error("Session expired or unauthorized. Redirecting to login...");
        window.location.href = "/login";
      }
      throw new Error("Unauthorized");
    }

    let detail = `Request failed (${response.status})`;
    try {
      const errJson = await response.json();
      detail = errJson.detail || detail;
    } catch {
      // not JSON
    }

    toast.error(detail);
    throw new Error(detail);
  }

  // If response is a PDF or other blob
  const contentType = response.headers.get("content-type");
  if (contentType && contentType.includes("application/pdf")) {
    return (await response.blob()) as unknown as T;
  }

  return response.json() as Promise<T>;
}

// ─── API Endpoints ───────────────────────────────────────────────────────────

export async function login(
  email: string,
  password: string
): Promise<AuthResponse> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
  } catch {
    const msg = "Backend not reachable at localhost:8000";
    toast.error(msg);
    throw new Error(msg);
  }

  if (!res.ok) {
    let detail = "Login failed";
    try {
      const data = await res.json();
      detail = data.detail || detail;
    } catch {
      // ignore
    }
    toast.error(detail);
    throw new Error(detail);
  }

  const data: AuthResponse = await res.json();
  if (typeof window !== "undefined") {
    localStorage.setItem("token", data.token);
    localStorage.setItem("user", JSON.stringify(data.user));
  }
  return data;
}

export async function signup(
  name: string,
  email: string,
  password: string,
  role: "clinician" | "auditor"
): Promise<AuthResponse> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password, role }),
    });
  } catch {
    const msg = "Backend not reachable at localhost:8000";
    toast.error(msg);
    throw new Error(msg);
  }

  if (!res.ok) {
    let detail = "Signup failed";
    try {
      const data = await res.json();
      detail = data.detail || detail;
    } catch {
      // ignore
    }
    toast.error(detail);
    throw new Error(detail);
  }

  const data: AuthResponse = await res.json();
  if (typeof window !== "undefined") {
    localStorage.setItem("token", data.token);
    localStorage.setItem("user", JSON.stringify(data.user));
  }
  return data;
}

export async function getStates(): Promise<StateAQI[]> {
  return request<StateAQI[]>("/api/states", { method: "GET" });
}

export async function analyze(
  patient: PatientInputData
): Promise<AnalyzeResponse> {
  return request<AnalyzeResponse>("/api/analyze", {
    method: "POST",
    body: JSON.stringify(patient),
  });
}

export async function generateReport(
  patient: PatientInputData
): Promise<Blob> {
  return request<Blob>("/api/report", {
    method: "POST",
    body: JSON.stringify(patient),
  });
}
