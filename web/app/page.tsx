"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { ShieldCheck, Thermometer, Truck, Zap } from "lucide-react";

const steps = [
  "Create your account with Supabase Auth email link or magic link.",
  "Add your first truck and cargo defaults.",
  "Connect Samsara, Motive, or Geotab in one click.",
  "Let ReeferShield monitor every trip and auto-issue certificates.",
];

export default function LandingPage() {
  const [currentStep, setCurrentStep] = useState(0);
  const [digest, setDigest] = useState(true);

  return (
    <main className="mx-auto flex min-h-screen max-w-6xl flex-col gap-10 px-4 py-10">
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-2xl bg-cyan-400/10 ring-1 ring-cyan-400/40">
            <ShieldCheck className="h-5 w-5 text-cyan-300" />
          </div>
          <span className="text-lg font-semibold tracking-tight">ReeferShield</span>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="ghost" className="text-xs px-3">Log in</Button>
          <Button className="text-xs px-3">Launch dashboard</Button>
        </div>
      </header>

      <section className="grid gap-6 md:grid-cols-[2fr,1.4fr]">
        <div className="space-y-6">
          <Badge>Autonomous reefer monitoring · No brokering, no rate talk</Badge>
          <h1 className="text-3xl md:text-4xl font-semibold tracking-tight">
            Stop spoiled-load disputes with <span className="text-cyan-300">tamper‑proof reefer certificates.</span>
          </h1>
          <p className="max-w-xl text-sm text-slate-300">
            ReeferShield watches every second of your cold‑chain via Samsara, Motive, and Geotab.
            When a trip ends at the receiver, we auto‑generate a temperature integrity certificate, anchor it to IPFS + Polygon, and email everyone who matters.
          </p>

          <div className="flex flex-wrap gap-3 text-xs text-slate-300">
            <div className="flex items-center gap-2 rounded-full border border-slate-800 bg-slate-950/60 px-3 py-1">
              <Thermometer className="h-3.5 w-3.5 text-cyan-300" />
              <span>Live temperature, doors, and defrost</span>
            </div>
            <div className="flex items-center gap-2 rounded-full border border-slate-800 bg-slate-950/60 px-3 py-1">
              <Truck className="h-3.5 w-3.5 text-cyan-300" />
              <span>Unlimited trucks*</span>
            </div>
            <div className="flex items-center gap-2 rounded-full border border-slate-800 bg-slate-950/60 px-3 py-1">
              <Zap className="h-3.5 w-3.5 text-cyan-300" />
              <span>Automatic recovery commands</span>
            </div>
          </div>

          <Card className="mt-4 border-cyan-500/15 bg-slate-950/80">
            <CardHeader>
              <CardTitle>Get onboarded in under 3 minutes</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-col gap-2 text-xs sm:flex-row sm:items-center">
                <Input placeholder="you@carrier.com" className="sm:max-w-xs" />
                <Button className="sm:w-auto w-full text-xs">Start 14‑day free trial</Button>
              </div>
              <p className="text-[11px] text-slate-400">
                $49/mo base + $29/mo per truck after trial. Cancel anytime. No brokering, no rate negotiation, no load‑matching.
              </p>
              <div className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-2">
                <div className="space-y-0.5">
                  <p className="text-xs font-medium">Daily digest</p>
                  <p className="text-[11px] text-slate-400">
                    Nightly email with certificates created in the last 24 hours.
                  </p>
                </div>
                <Switch checked={digest} onCheckedChange={setDigest} />
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="border-cyan-500/15 bg-slate-950/80">
          <CardHeader>
            <CardTitle>Onboarding tour</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-xs">
            <p className="text-slate-300">
              Step {currentStep + 1} of {steps.length}
            </p>
            <p className="rounded-xl border border-slate-800 bg-slate-950/80 p-3 text-slate-200">
              {steps[currentStep]}
            </p>
            <div className="flex items-center justify-between text-[11px] text-slate-400">
              <span>Click next to preview your setup flow.</span>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  className="h-7 px-2 text-[11px]"
                  onClick={() => setCurrentStep((s) => (s - 1 + steps.length) % steps.length)}
                >
                  Back
                </Button>
                <Button
                  className="h-7 px-3 text-[11px]"
                  onClick={() => setCurrentStep((s) => (s + 1) % steps.length)}
                >
                  Next
                </Button>
              </div>
            </div>
            <div className="mt-4 space-y-2">
              <p className="text-[11px] uppercase tracking-[0.14em] text-slate-500">
                Example fleet snapshot
              </p>
              <div className="space-y-2 rounded-xl border border-slate-800 bg-slate-950/70 p-3">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-300">Reefers online</span>
                  <span className="font-semibold text-cyan-300">12 / 14</span>
                </div>
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-300">Trips in progress</span>
                  <span className="font-semibold">5</span>
                </div>
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-300">Certificates last 7 days</span>
                  <span className="font-semibold">63</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </section>

      <footer className="mt-auto flex items-center justify-between border-t border-slate-900 pt-6 text-[11px] text-slate-500">
        <span>© {new Date().getFullYear()} ReeferShield – monitoring only. No freight brokering or rate negotiation.</span>
        <span>Polygon + IPFS backed integrity</span>
      </footer>
    </main>
  );
}
