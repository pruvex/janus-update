import test from "node:test";
import assert from "node:assert/strict";

import {
  configureMarkdownRenderer,
  renderChatMarkdown,
} from "../js/markdown-renderer.js";

test("renderChatMarkdown escapes HTML when marked is unavailable", () => {
  const previousWindow = globalThis.window;
  const previousMarked = globalThis.marked;
  delete globalThis.window;
  delete globalThis.marked;

  try {
    assert.equal(
      renderChatMarkdown("<img src=x onerror=alert(1)>\nsecond line"),
      "&lt;img src=x onerror=alert(1)&gt;<br>second line",
    );
  } finally {
    if (previousWindow === undefined) {
      delete globalThis.window;
    } else {
      globalThis.window = previousWindow;
    }
    if (previousMarked === undefined) {
      delete globalThis.marked;
    } else {
      globalThis.marked = previousMarked;
    }
  }
});

test("renderChatMarkdown renders fallback links with hidden href when marked is unavailable", () => {
  const previousWindow = globalThis.window;
  const previousMarked = globalThis.marked;
  delete globalThis.window;
  delete globalThis.marked;

  try {
    assert.equal(
      renderChatMarkdown(
        "Quelle: GamesRadar. [Link](https://vertexaisearch.cloud.google.com/grounding-api-redirect/example)\n**Titel**",
      ),
      'Quelle: GamesRadar. <a href="https://vertexaisearch.cloud.google.com/grounding-api-redirect/example" target="_blank" rel="noopener noreferrer">Link</a><br><strong>Titel</strong>',
    );
  } finally {
    if (previousWindow === undefined) {
      delete globalThis.window;
    } else {
      globalThis.window = previousWindow;
    }
    if (previousMarked === undefined) {
      delete globalThis.marked;
    } else {
      globalThis.marked = previousMarked;
    }
  }
});

test("renderChatMarkdown keeps unsafe fallback links as escaped text", () => {
  const previousWindow = globalThis.window;
  const previousMarked = globalThis.marked;
  delete globalThis.window;
  delete globalThis.marked;

  try {
    assert.equal(
      renderChatMarkdown("[Link](javascript:alert(1))"),
      "[Link](javascript:alert(1))",
    );
  } finally {
    if (previousWindow === undefined) {
      delete globalThis.window;
    } else {
      globalThis.window = previousWindow;
    }
    if (previousMarked === undefined) {
      delete globalThis.marked;
    } else {
      globalThis.marked = previousMarked;
    }
  }
});

test("renderChatMarkdown delegates to marked when it is available", () => {
  const previousMarked = globalThis.marked;
  let configured = null;
  globalThis.marked = {
    setOptions(options) {
      configured = options;
    },
    parse(value) {
      return `<p>${value}</p>`;
    },
  };

  try {
    configureMarkdownRenderer();
    assert.deepEqual(configured, { breaks: true, gfm: true });
    assert.equal(renderChatMarkdown("**ok**"), "<p>**ok**</p>");
  } finally {
    if (previousMarked === undefined) {
      delete globalThis.marked;
    } else {
      globalThis.marked = previousMarked;
    }
  }
});
