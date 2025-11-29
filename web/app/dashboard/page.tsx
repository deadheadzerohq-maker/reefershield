"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ShieldCheck, Thermometer, Truck, Link2 } from "lucide-react";
import { BACKEND_BASE_URL } from "@/lib/config";

const demoTrucks = [
  {
    id: "demo-1",
    name: "RS-204 · 53' Carrier",
    provider: "samsara",
    status: "Monitoring",
    cargo: "Fresh produce",
    temp: "36°F",
    setpoint: "35°F"
  },
  {
    id: "demo-2",
    name: "RS-305 · 48' Thermo King",
    provider: "motive",
    status: "Trip in progress",
    cargo: "Frozen",
    temp: "-5°F",
    setpoint: "-10°F"
  }
];

export default function DashboardPage() {
  const [trucks] = useState(demoTrucks);

  const onConnect = (provider: "samsara" | "motive" | "geotab") => {
    // In production you pass the Supabase user id here
    const userId = "SUPABASE_USER_ID_PLACEHOLDER";
    window.location.href = `${BACKEND_BASE_URL}/auth/${provider}/start?user_id=${userId}`;
  };

  return (
    <main className="mx-auto flex min-h-screen max-w-6xl flex-col gap-8 px-4 py-8">
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-2xl bg-cyan-400/10 ring-1 ring-cyan-400/40">
            <ShieldCheck className="h-4 w-4 text-cyan-300" />
          </div>
          <div className="space-y-0.5">
            <p className="text-sm font-semibold">ReeferShield</p>
            <p className="text-xs text-slate-400">Autonomous reefer integrity OS</p>
          </div>
        </div>
        <Button variant="outline" className="text-xs px-3">
          Billing & plan
        </Button>
      </header>

      <section className="grid gap-4 md:grid-cols-[2fr,1.5fr]">
        <Card>
          <CardHeader className="flex items-center justify-between">
            <CardTitle>Fleet overview</CardTitle>
            <Badge>Live demo data</Badge>
          </CardHeader>
          <CardContent className="space-y-4 text-xs">
            <div className="grid grid-cols-3 gap-3">
              <div className="rounded-xl border border-slate-800 bg-slate-950/80 p-3">
                <p className="text-[11px] text-slate-400">Reefers monitored</p>
                <p className="mt-1 text-lg font-semibold">14</p>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-950/80 p-3">
                <p className="text-[11px] text-slate-400">Trips today</p>
                <p className="mt-1 text-lg font-semibold">9</p>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-950/80 p-3">
                <p className="text-[11px] text-slate-400">Certificates 7d</p>
                <p className="mt-1 text-lg font-semibold">63</p>
              </div>
            </div>

            <div className="mt-2 space-y-2">
              {trucks.map((t) => (
                <div
                  key={t.id}
                  className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/80 px-3 py-2"
                >
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <Truck className="h-3.5 w-3.5 text-cyan-300" />
                      <span className="text-xs font-medium">{t.name}</span>
                    </div>
                    <p className="text-[11px] text-slate-400">
                      {t.cargo} · {t.status}
                    </p>
                  </div>
                  <div className="text-right text-[11px]">
                    <p className="text-slate-300">
                      <Thermometer className="mr-1 inline h-3 w-3 text-cyan-300" />
                      {t.temp} <span className="text-slate-500">/ {t.setpoint}</span>
                    </p>
                    <p className="mt-0.5 text-slate-500">{t.provider.toUpperCase()}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Connect telematics</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-xs">
            <p className="text-slate-300">
              Hook ReeferShield into your telematics in one click. We store OAuth refresh tokens securely in
              Supabase and only use them to stream reefer sensor data and remote set‑point commands.
            </p>

            <div className="space-y-2">
              <Button
                variant="outline"
                className="flex w-full items-center justify-between rounded-xl border border-cyan-500/30 bg-slate-950/80 px-3 py-2"
                onClick={() => onConnect("samsara")}
              >
                <span className="flex items-center gap-2 text-xs">
                  <Link2 className="h-3.5 w-3.5 text-cyan-300" />
                  Connect <span className="font-semibold">Samsara</span>
                </span>
                <span className="text-[11px] text-slate-400">OAuth · full reefer telemetry</span>
              </Button>

              <Button
                variant="outline"
                className="flex w-full items-center justify-between rounded-xl border border-emerald-500/20 bg-slate-950/80 px-3 py-2"
                onClick={() => onConnect("motive")}
              >
                <span className="flex items-center gap-2 text-xs">
                  <Link2 className="h-3.5 w-3.5 text-emerald-300" />
                  Connect <span className="font-semibold">Motive</span>
                </span>
                <span className="text-[11px] text-slate-400">OAuth · remote set‑point</span>
              </Button>

              <Button
                variant="outline"
                className="flex w-full items-center justify-between rounded-xl border border-indigo-500/20 bg-slate-950/80 px-3 py-2"
                onClick={() => onConnect("geotab")}
              >
                <span className="flex items-center gap-2 text-xs">
                  <Link2 className="h-3.5 w-3.5 text-indigo-300" />
                  Connect <span className="font-semibold">Geotab</span>
                </span>
                <span className="text-[11px] text-slate-400">OAuth · events + GPS</span>
              </Button>
            </div>

            <div className="mt-3 rounded-xl border border-slate-800 bg-slate-950/80 p-3 text-[11px] text-slate-400">
              <p className="font-medium text-slate-300">What happens after you connect?</p>
              <ul className="mt-2 list-disc space-y-1 pl-4">
                <li>We start listening for reefer temperature, doors, defrost cycles, and ignition events.</li>
                <li>Trips are auto-detected and closed when ignition shuts off at the receiver.</li>
                <li>Every completed trip gets a tamper‑proof PDF certificate anchored to IPFS + Polygon.</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      </section>
    </main>
  );
}
