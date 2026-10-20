export const API_URL = 'http://booklocal-backend-alb-1738618234.eu-west-1.elb.amazonaws.com';

export type ApiResult = { ok: boolean; status: number; data: any };

export async function api(
  path: string,
  token: string | null,
  options: RequestInit = {}
): Promise<ApiResult> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers.Authorization = `Bearer ${token}`;
  try {
    const res = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: { ...headers, ...((options.headers as Record<string, string>) || {}) },
    });
    let data: any = null;
    try {
      data = await res.json();
    } catch {
      data = null;
    }
    return { ok: res.ok, status: res.status, data };
  } catch {
    return { ok: false, status: 0, data: { detail: 'Could not reach the server' } };
  }
}

export function errText(data: any): string {
  if (data && typeof data.detail === 'string') return data.detail;
  return 'Please check your details and try again';
}
