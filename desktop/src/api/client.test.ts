import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { fetchHealth, executeApproved, scoreProduct } from "./client";

function mockFetch(value: unknown, ok = true, status = 200) {
  const fn = vi.fn().mockResolvedValue({
    ok,
    status,
    statusText: "Err",
    json: async () => value,
    text: async () => JSON.stringify(value),
  });
  vi.stubGlobal("fetch", fn);
  return fn;
}

describe("api client", () => {
  beforeEach(() => {
    localStorage.clear();
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("issues a GET to the right URL", async () => {
    const fn = mockFetch({ status: "ok", version: "0.2.0" });
    const r = await fetchHealth();
    expect(r.status).toBe("ok");
    expect(fn).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/health",
      expect.objectContaining({ method: "GET" }),
    );
  });

  it("sends a JSON body on POST", async () => {
    const fn = mockFetch({ verdict: "pass" });
    await scoreProduct({
      product_name: "Kit", est_sale_price: 59, est_product_cost: 12, est_shipping_cost: 5,
      competition: 0.5, return_risk: 0.3, compliance_risk: 0, content_potential: 0.5,
      repeat_purchase_potential: 0.3, personal_fit: 0.5, supplier_reliability: 0.5,
      evidence_quality: 0.3, niche: "",
    });
    const [, opts] = fn.mock.calls[0];
    expect(opts.method).toBe("POST");
    expect(JSON.parse(opts.body).product_name).toBe("Kit");
  });

  it("adds Authorization header when a token is stored", async () => {
    localStorage.setItem("marketmind_api_token", "tok123");
    const fn = mockFetch({});
    await executeApproved("apr_1", true);
    const [, opts] = fn.mock.calls[0];
    expect(opts.headers["Authorization"]).toBe("Bearer tok123");
  });

  it("omits Authorization header when no token is stored", async () => {
    const fn = mockFetch({ status: "ok", version: "x" });
    await fetchHealth();
    const [, opts] = fn.mock.calls[0];
    expect(opts.headers["Authorization"]).toBeUndefined();
  });

  it("throws with status + detail on an error response", async () => {
    mockFetch({ detail: "nope" }, false, 409);
    await expect(fetchHealth()).rejects.toThrow("409: nope");
  });
});
