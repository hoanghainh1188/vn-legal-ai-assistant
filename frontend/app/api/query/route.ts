const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function POST(request: Request) {
  const body = await request.json();

  const backendResponse = await fetch(`${BACKEND_URL}/api/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!backendResponse.ok) {
    return new Response(
      JSON.stringify({ error: "Backend request failed" }),
      {
        status: backendResponse.status,
        headers: { "Content-Type": "application/json" },
      },
    );
  }

  const reader = backendResponse.body?.getReader();
  if (!reader) {
    return new Response(JSON.stringify({ error: "No response body" }), {
      status: 502,
      headers: { "Content-Type": "application/json" },
    });
  }

  const stream = new ReadableStream({
    async pull(controller) {
      const { done, value } = await reader.read();
      if (done) {
        controller.close();
        return;
      }
      controller.enqueue(value);
    },
    cancel() {
      reader.cancel();
    },
  });

  return new Response(stream, {
    status: 200,
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}
