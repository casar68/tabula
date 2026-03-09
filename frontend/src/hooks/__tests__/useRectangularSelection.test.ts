import { describe, it, expect, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useRectangularSelection } from "../useRectangularSelection";

// Minimal mock for crypto.randomUUID (not available in jsdom)
vi.stubGlobal("crypto", {
  ...globalThis.crypto,
  randomUUID: () => "test-uuid-1234",
});

function createOptions(overrides = {}) {
  return {
    pageNumber: 1,
    pageWidthPts: 612,
    pageHeightPts: 792,
    scale: 1,
    existingSelections: [],
    onSelectionComplete: vi.fn(),
    ...overrides,
  };
}

function makeMouseEvent(
  x: number,
  y: number,
  rectOverrides: Partial<DOMRect> = {}
): React.MouseEvent<HTMLDivElement> {
  const rect = {
    left: 0,
    top: 0,
    width: 612,
    height: 792,
    right: 612,
    bottom: 792,
    x: 0,
    y: 0,
    toJSON: () => {},
    ...rectOverrides,
  };

  return {
    button: 0,
    clientX: x,
    clientY: y,
    target: document.createElement("div"),
    currentTarget: {
      getBoundingClientRect: () => rect,
    },
    preventDefault: vi.fn(),
  } as unknown as React.MouseEvent<HTMLDivElement>;
}

describe("useRectangularSelection", () => {
  it("starts not drawing", () => {
    const { result } = renderHook(() =>
      useRectangularSelection(createOptions())
    );
    expect(result.current.isDrawing).toBe(false);
    expect(result.current.drawRect).toBeNull();
  });

  it("starts drawing on mousedown", () => {
    const { result } = renderHook(() =>
      useRectangularSelection(createOptions())
    );

    act(() => {
      result.current.handleMouseDown(makeMouseEvent(100, 100));
    });

    expect(result.current.isDrawing).toBe(true);
    expect(result.current.drawRect).toEqual({ x: 100, y: 100, w: 0, h: 0 });
  });

  it("updates draw rect on mousemove", () => {
    const { result } = renderHook(() =>
      useRectangularSelection(createOptions())
    );

    act(() => {
      result.current.handleMouseDown(makeMouseEvent(100, 100));
    });

    act(() => {
      result.current.handleMouseMove(makeMouseEvent(300, 250));
    });

    expect(result.current.drawRect).toEqual({ x: 100, y: 100, w: 200, h: 150 });
  });

  it("calls onSelectionComplete on mouseup with valid rectangle", () => {
    const onComplete = vi.fn();
    const { result } = renderHook(() =>
      useRectangularSelection(createOptions({ onSelectionComplete: onComplete }))
    );

    act(() => {
      result.current.handleMouseDown(makeMouseEvent(100, 100));
    });
    act(() => {
      result.current.handleMouseMove(makeMouseEvent(300, 250));
    });
    act(() => {
      result.current.handleMouseUp();
    });

    expect(onComplete).toHaveBeenCalledTimes(1);
    const sel = onComplete.mock.calls[0][0];
    expect(sel.page).toBe(1);
    expect(sel.x1).toBe(100);
    expect(sel.y1).toBe(100);
    expect(sel.width).toBe(200);
    expect(sel.height).toBe(150);
    expect(sel.extraction_method).toBe("guess");
    expect(result.current.isDrawing).toBe(false);
    expect(result.current.drawRect).toBeNull();
  });

  it("ignores tiny selections (below 1% of page)", () => {
    const onComplete = vi.fn();
    const { result } = renderHook(() =>
      useRectangularSelection(createOptions({ onSelectionComplete: onComplete }))
    );

    act(() => {
      result.current.handleMouseDown(makeMouseEvent(100, 100));
    });
    act(() => {
      // Very small rectangle: 2x2 pixels
      result.current.handleMouseMove(makeMouseEvent(102, 102));
    });
    act(() => {
      result.current.handleMouseUp();
    });

    expect(onComplete).not.toHaveBeenCalled();
    expect(result.current.isDrawing).toBe(false);
  });

  it("applies scale when converting to PDF points", () => {
    const onComplete = vi.fn();
    const { result } = renderHook(() =>
      useRectangularSelection(
        createOptions({ scale: 2, onSelectionComplete: onComplete })
      )
    );

    act(() => {
      result.current.handleMouseDown(makeMouseEvent(200, 200));
    });
    act(() => {
      result.current.handleMouseMove(makeMouseEvent(400, 400));
    });
    act(() => {
      result.current.handleMouseUp();
    });

    const sel = onComplete.mock.calls[0][0];
    // Pixel coords divided by scale = PDF points
    expect(sel.x1).toBe(100);
    expect(sel.y1).toBe(100);
    expect(sel.width).toBe(100);
    expect(sel.height).toBe(100);
  });
});
