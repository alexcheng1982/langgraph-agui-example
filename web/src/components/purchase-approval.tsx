"use client";

import { useHumanInTheLoop } from "@copilotkit/react-core/v2";
import { z } from "zod";

type PurchaseReview = {
  type: "purchase_approval";
  title: string;
  items: Array<{ item: string; unit_price: number; currency: string }>;
  total: number;
  currency: string;
  message: string;
};

export function PurchaseApproval() {
  useHumanInTheLoop({
    agentId: "default",
    name: "purchase_online",
    description: "Prepare a shopping list and ask the user to approve it before placing the order.",
    parameters: z.object({
      items: z.array(z.object({ item: z.string(), unit_price: z.number(), currency: z.string() })),
      total: z.number(),
      currency: z.string(),
    }),
    render: ({ args, status, respond }) => {
      const review = (args ?? {}) as Partial<PurchaseReview>;
      const items = Array.isArray(review.items)
        ? review.items
            .map((item) => {
              if (typeof item === "string") {
                return { item, unit_price: 0, currency: review.currency || "USD" };
              }
              if (!item || typeof item !== "object") return null;
              const value = item as Partial<PurchaseReview["items"][number]>;
              return {
                item: value.item || "Unknown item",
                unit_price: typeof value.unit_price === "number" ? value.unit_price : 0,
                currency: value.currency || review.currency || "USD",
              };
            })
            .filter((item): item is { item: string; unit_price: number; currency: string } => item !== null)
        : [];
      const total = typeof review.total === "number" ? review.total : 0;
      const currency = review.currency || "USD";
      return (
        <div className="my-3 rounded-2xl border border-amber-300 bg-amber-50 p-4 text-stone-900 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-amber-700">Human approval required</p>
          <h3 className="mt-1 text-base font-bold">{review.title || "Confirm online purchase"}</h3>
          <p className="mt-1 text-sm text-stone-600">{review.message || "Please review the shopping list before placing the order."}</p>
          <ul className="mt-3 space-y-1 text-sm">
            {items.length > 0 ? items.map((item, index) => <li key={`${item.item}-${index}`}>• {item.item} — {item.currency} {item.unit_price.toFixed(2)}</li>) : <li className="text-stone-500">Preparing shopping list…</li>}
          </ul>
          <p className="mt-3 font-semibold">Total: {currency} {total.toFixed(2)}</p>
          <div className="mt-4 flex gap-2">
            <button disabled={status !== "executing"} className="rounded-lg bg-stone-900 px-3 py-2 text-sm font-semibold text-white disabled:opacity-50" onClick={() => respond?.({ approved: true })}>Confirm purchase</button>
            <button disabled={status !== "executing"} className="rounded-lg border border-stone-300 bg-white px-3 py-2 text-sm disabled:opacity-50" onClick={() => respond?.({ approved: false })}>Cancel</button>
          </div>
        </div>
      );
    },
  });
  return null;
}
