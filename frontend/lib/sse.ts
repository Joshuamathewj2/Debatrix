/**
 * Incrementally split a Server-Sent Events byte stream into JSON payloads.
 * Frames may arrive split across network chunks; only complete frames are emitted.
 */
export class SseDecoder<T = unknown> {
  private pending = "";

  push(chunk: string): T[] {
    this.pending += chunk.replace(/\r\n/g, "\n");
    const frames = this.pending.split("\n\n");
    this.pending = frames.pop() ?? "";
    const events: T[] = [];
    for (const frame of frames) {
      const data = frame
        .split("\n")
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.slice(5).trimStart())
        .join("\n");
      if (data) events.push(JSON.parse(data) as T);
    }
    return events;
  }
}

export async function* readSse<T>(body: ReadableStream<Uint8Array>): AsyncGenerator<T> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  const sse = new SseDecoder<T>();
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    yield* sse.push(decoder.decode(value, { stream: true }));
  }
}
