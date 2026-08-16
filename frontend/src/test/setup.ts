import "@testing-library/jest-dom/vitest";

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

vi.stubGlobal("ResizeObserver", ResizeObserverMock);

vi.mock("@/api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/api/client")>();
  return {
    ...actual,
    refreshAccessToken: vi.fn().mockResolvedValue(null),
  };
});

HTMLElement.prototype.getBoundingClientRect = function getBoundingClientRect() {
  return {
    width: 800,
    height: 256,
    top: 0,
    left: 0,
    bottom: 256,
    right: 800,
    x: 0,
    y: 0,
    toJSON() {
      return {};
    },
  };
};
