import { describe, expect, it } from "vitest";
import { lowStockText, remainingStock } from "./stock";

describe("remainingStock", () => {
  it("subtracts what is already in the cart", () => {
    expect(remainingStock(5, 0)).toBe(5);
    expect(remainingStock(5, 1)).toBe(4);
    expect(remainingStock(5, 2)).toBe(3);
    expect(remainingStock(5, 5)).toBe(0);
  });

  it("never goes negative", () => {
    expect(remainingStock(3, 9)).toBe(0);
    expect(remainingStock(0, 0)).toBe(0);
  });
});

describe("lowStockText", () => {
  it("warns at 5 or fewer remaining, counting down as the cart grows", () => {
    expect(lowStockText(remainingStock(5, 0))).toMatch(/Only 5 items left/);
    expect(lowStockText(remainingStock(5, 1))).toMatch(/Only 4 items left/);
    expect(lowStockText(remainingStock(5, 2))).toMatch(/Only 3 items left/);
    expect(lowStockText(1)).toMatch(/Only 1 item left/);
  });

  it("stays quiet above the threshold", () => {
    expect(lowStockText(6)).toBeNull();
    expect(lowStockText(40)).toBeNull();
  });

  it("explains when the cart already holds all the stock", () => {
    expect(lowStockText(0)).toMatch(/in your cart/i);
  });
});
