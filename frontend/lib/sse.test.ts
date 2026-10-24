import { test } from "node:test";
import assert from "node:assert/strict";
import { SseDecoder } from "./sse.ts";

const stream =
  'data: {"type":"section","section":"position","text":"No."}\n\n' +
  'data: {"type":"done","sections":{"position":"No."},"provider":"mock"}\n\n';

test("decodes complete frames in one chunk", () => {
  const events = new SseDecoder<{ type: string }>().push(stream);
  assert.deepEqual(
    events.map((e) => e.type),
    ["section", "done"],
  );
});

test("frames split at every possible byte boundary decode identically", () => {
  for (let cut = 1; cut < stream.length; cut++) {
    const sse = new SseDecoder<{ type: string }>();
    const events = [...sse.push(stream.slice(0, cut)), ...sse.push(stream.slice(cut))];
    assert.deepEqual(
      events.map((e) => e.type),
      ["section", "done"],
      `split at ${cut}`,
    );
  }
});

test("holds back an incomplete frame until it is finished", () => {
  const sse = new SseDecoder<{ type: string }>();
  assert.deepEqual(sse.push('data: {"type":"sec'), []);
  assert.equal(sse.push('tion"}\n\n')[0].type, "section");
});

test("tolerates CRLF line endings and multi-line data fields", () => {
  const sse = new SseDecoder<{ a: number }>();
  assert.deepEqual(sse.push('data: {"a":\r\ndata: 1}\r\n\r\n'), [{ a: 1 }]);
});
