import { NextRequest, NextResponse } from "next/server";
import Stripe from "stripe";

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: "2024-06-20"
});

export async function POST(req: NextRequest) {
  const body = await req.json();
  const { email, mode } = body as { email: string; mode: "base" | "per_truck" };

  const price =
    mode === "base"
      ? process.env.NEXT_PUBLIC_STRIPE_PRICE_ID_BASE
      : process.env.NEXT_PUBLIC_STRIPE_PRICE_ID_PER_TRUCK;

  if (!price) {
    return NextResponse.json({ error: "Price not configured" }, { status: 400 });
  }

  const session = await stripe.checkout.sessions.create({
    mode: "subscription",
    customer_email: email,
    line_items: [{ price, quantity: 1 }],
    success_url: `${process.env.NEXT_PUBLIC_SITE_URL}/dashboard?session_id={CHECKOUT_SESSION_ID}`,
    cancel_url: `${process.env.NEXT_PUBLIC_SITE_URL}/?canceled=true`,
    subscription_data: {
      trial_period_days: 14
    }
  });

  return NextResponse.json({ url: session.url });
}
