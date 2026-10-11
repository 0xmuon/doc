import { describe, expect, it } from "vitest";
import { validateEmail, validateName, validateQuantity } from "./validate";

describe("validateQuantity", () => {
  it("accepts a positive whole number within stock", () => {
    expect(validateQuantity("2", 5)).toBe("");
  });

  it("rejects an empty value, zero, a fraction, a number above stock, and a number above the cap", () => {
    expect(validateQuantity("", 5)).toMatch(/required/i);
    expect(validateQuantity("0", 5)).toMatch(/positive/i);
    expect(validateQuantity("1.5", 5)).toMatch(/positive/i);
    expect(validateQuantity("6", 5)).toMatch(/stock/i);
    expect(validateQuantity("11", 20)).toMatch(/at most 10/i);
  });
});

describe("validateName", () => {
  it("requires six letters and single spaces", () => {
    expect(validateName("Al")).toMatch(/6/);
    expect(validateName("Het Patel")).toBe("");
    expect(validateName("Het  Patel")).toMatch(/letters/i);
    expect(validateName("Het1 Patel")).toMatch(/letters/i);
  });
});

describe("validateEmail", () => {
  it("requires an email shape", () => {
    expect(validateEmail("not-an-email")).toMatch(/valid email/i);
    expect(validateEmail("het@example.com")).toBe("");
  });
});
