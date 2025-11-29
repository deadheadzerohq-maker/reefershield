import { NextRequest, NextResponse } from "next/server";
import Stripe from "stripe";
import { createClient } from "@supabase/supabase-js";

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: "2024-06-20"
});

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

export async function POST(req: NextRequest) {
  const sig = req.headers.get("stripe-signature");
  if (!sig) {
    return new NextResponse("Missing signature", { status: 400 });
  }

  const text = await req.text();

  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(
      text,
      sig,
      process.env.STRIPE_WEBHOOK_SECRET!
    );
  } catch (err: any) {
    console.error("Stripe webhook error", err.message);
    return new NextResponse(`Webhook Error: ${err.message}`, { status: 400 });
  }

  if (
    event.type === "customer.subscription.created" ||
    event.type === "customer.subscription.updated" ||
    event.type === "customer.subscription.deleted"
  ) {
    const sub = event.data.object as Stripe.Subscription;
    const stripeCustomerId = sub.customer as string;

    const priceId = sub.items.data[0]?.price?.id;
    let plan = "free";
    let maxTrucks = 0;
    if (priceId === process.env.NEXT_PUBLIC_STRIPE_PRICE_ID_BASE) {
      plan = "base";
      maxTrucks = 5;
    } else if (priceId === process.env.NEXT_PUBLIC_STRIPE_PRICE_ID_PER_TRUCK) {
      plan = "per_truck";
      maxTrucks = 100;
    }

    await supabase
      .from("profiles")
      .update({
        plan,
        max_trucks: maxTrucks,
        stripe_customer_id: stripeCustomerId
      })
      .eq("stripe_customer_id", stripeCustomerId);
  }

  if (event.type === "checkout.session.completed") {
    const session = event.data.object as Stripe.Checkout.Session;
    const email = session.customer_details?.email;
    const customerId = session.customer as string;

    if (email) {
      const { data, error } = await supabase
        .from("profiles")
        .update({ stripe_customer_id: customerId })
        .eq("email", email);
      if (error) console.error("Error linking Stripe to profile", error);
    }
  }

  return NextResponse.json({ received: true });
}
