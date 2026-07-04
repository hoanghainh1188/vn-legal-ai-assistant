const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

/** Proxy danh sách lĩnh vực (động) từ backend cho bộ lọc UI. */
export async function GET() {
  try {
    const res = await fetch(`${BACKEND_URL}/api/domains`, {
      cache: "no-store",
    });
    if (!res.ok) {
      return Response.json({ domains: [] }, { status: 200 });
    }
    return Response.json(await res.json());
  } catch {
    return Response.json({ domains: [] }, { status: 200 });
  }
}
