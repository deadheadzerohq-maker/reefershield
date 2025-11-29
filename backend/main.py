import os
import io
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List

from fastapi import FastAPI, Request, Depends, HTTPException, BackgroundTasks
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import requests
from supabase import create_client, Client
from web3 import Web3, HTTPProvider
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import qrcode
from PIL import Image

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reefershield")

SUPABASE_URL = os.getenv("BACKEND_SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("BACKEND_SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Supabase env vars missing for backend")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

WEB3_STORAGE_TOKEN = os.getenv("WEB3_STORAGE_TOKEN")
POLYGON_RPC_URL_PRIMARY = os.getenv("POLYGON_RPC_URL_PRIMARY")
POLYGON_RPC_URL_FALLBACK = os.getenv("POLYGON_RPC_URL_FALLBACK")
POLYGON_PRIVATE_KEY = os.getenv("POLYGON_PRIVATE_KEY")
POLYGON_CHAIN_ID = int(os.getenv("POLYGON_CHAIN_ID", "137"))
POLYGON_CERT_CONTRACT_ADDRESS = os.getenv("POLYGON_CERT_CONTRACT_ADDRESS")

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@reefershield.app")

SAMSARA_CLIENT_ID = os.getenv("SAMSARA_CLIENT_ID")
SAMSARA_CLIENT_SECRET = os.getenv("SAMSARA_CLIENT_SECRET")
SAMSARA_OAUTH_REDIRECT_URI = os.getenv("SAMSARA_OAUTH_REDIRECT_URI")

MOTIVE_CLIENT_ID = os.getenv("MOTIVE_CLIENT_ID")
MOTIVE_CLIENT_SECRET = os.getenv("MOTIVE_CLIENT_SECRET")
MOTIVE_OAUTH_REDIRECT_URI = os.getenv("MOTIVE_OAUTH_REDIRECT_URI")

GEOTAB_CLIENT_ID = os.getenv("GEOTAB_CLIENT_ID")
GEOTAB_CLIENT_SECRET = os.getenv("GEOTAB_CLIENT_SECRET")
GEOTAB_OAUTH_REDIRECT_URI = os.getenv("GEOTAB_OAUTH_REDIRECT_URI")

BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")

# Polygon web3 setup
def get_web3() -> Optional[Web3]:
    rpc = POLYGON_RPC_URL_PRIMARY or POLYGON_RPC_URL_FALLBACK
    if not rpc:
        return None
    return Web3(HTTPProvider(rpc))

w3 = get_web3()

app = FastAPI(title="ReeferShield Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Utility ----------

def upload_pdf_to_web3_storage(pdf_bytes: bytes) -> Optional[str]:
    if not WEB3_STORAGE_TOKEN:
        logger.warning("WEB3_STORAGE_TOKEN not set; skipping IPFS upload")
        return None
    headers = {
        "Authorization": f"Bearer {WEB3_STORAGE_TOKEN}",
        "Content-Type": "application/pdf",
    }
    resp = requests.post("https://api.web3.storage/upload", headers=headers, data=pdf_bytes)
    if resp.status_code not in (200, 202):
        logger.error("web3.storage upload error: %s %s", resp.status_code, resp.text)
        return None
    data = resp.json()
    cid = data.get("cid") or data.get("value", {}).get("cid")
    return cid

def record_on_polygon(cid: str, timestamp: int) -> Optional[str]:
    if not (w3 and POLYGON_PRIVATE_KEY and POLYGON_CERT_CONTRACT_ADDRESS):
        logger.warning("Polygon not fully configured; skipping on-chain record")
        return None

    acct = w3.eth.account.from_key(POLYGON_PRIVATE_KEY)
    cid_hash = w3.keccak(text=cid)
    nonce = w3.eth.get_transaction_count(acct.address)

    tx = {
        "chainId": POLYGON_CHAIN_ID,
        "nonce": nonce,
        "to": Web3.to_checksum_address(POLYGON_CERT_CONTRACT_ADDRESS),
        "value": 0,
        "gas": 200000,
        "gasPrice": w3.eth.gas_price,
        "data": cid_hash,  # simple marker; ABI-encoded call can be wired later
    }
    signed = w3.eth.account.sign_transaction(tx, private_key=POLYGON_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    return w3.to_hex(tx_hash)

def send_certificate_email(to_emails: List[str], subject: str, html: str, pdf_bytes: bytes):
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY missing; skipping email send")
        return
    files = [
        {
            "content": pdf_bytes.decode("latin1"),
            "filename": "reefer-certificate.pdf",
        }
    ]
    payload = {
        "from": FROM_EMAIL,
        "to": to_emails,
        "subject": subject,
        "html": html,
    }
    # Resend attachments require multipart; here we keep it simple and just send link-less email
    resp = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
        data=json.dumps(payload),
    )
    if resp.status_code >= 400:
        logger.error("Error sending email via Resend: %s %s", resp.status_code, resp.text)

def generate_certificate_pdf(trip, events, ipfs_cid: Optional[str], polygon_tx: Optional[str]) -> bytes:
    buff = io.BytesIO()
    c = canvas.Canvas(buff, pagesize=A4)
    width, height = A4

    c.setFillColorRGB(0, 0.5, 1)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height - 50, "ReeferShield Certificate of Temperature Integrity")

    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica", 10)
    y = height - 90
    lines = [
        f"Trip ID: {trip['id']}",
        f"Truck ID: {trip['truck_id']}",
        f"Cargo Type: {trip.get('cargo_type') or 'N/A'}",
        f"Origin: {trip.get('origin') or 'N/A'}",
        f"Destination: {trip.get('destination') or 'N/A'}",
        f"Started: {trip.get('started_at')}",
        f"Completed: {trip.get('ended_at')}",
    ]
    for line in lines:
        c.drawString(50, y, line)
        y -= 14

    # Draw a simple temperature graph
    temps = [e.get("temperature") for e in events if e.get("temperature") is not None]
    times = [datetime.fromisoformat(e["occurred_at"].replace("Z", "+00:00")) for e in events]
    if temps and times:
        min_temp = min(temps)
        max_temp = max(temps)
        min_t = min(times)
        max_t = max(times)
        graph_left = 50
        graph_bottom = 250
        graph_width = width - 100
        graph_height = 200

        c.setStrokeColorRGB(0.3, 0.3, 0.3)
        c.rect(graph_left, graph_bottom, graph_width, graph_height)

        def norm_x(t):
            if max_t == min_t:
                return graph_left
            return graph_left + ( (t - min_t).total_seconds() / (max_t - min_t).total_seconds() ) * graph_width

        def norm_y(temp):
            if max_temp == min_temp:
                return graph_bottom
            return graph_bottom + ((temp - min_temp) / (max_temp - min_temp)) * graph_height

        c.setStrokeColorRGB(0, 0.7, 1)
        c.setLineWidth(1.5)
        last_x, last_y = None, None
        for t, temp in zip(times, temps):
            x = norm_x(t)
            y = norm_y(temp)
            if last_x is not None:
                c.line(last_x, last_y, x, y)
            last_x, last_y = x, y

        c.setFont("Helvetica", 8)
        c.drawString(graph_left, graph_bottom - 12, f"Min temp: {min_temp}  Max temp: {max_temp}")

    # IPFS / Polygon details
    y = 200
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Tamper‑proof anchors")
    c.setFont("Helvetica", 9)
    y -= 14
    if ipfs_cid:
        c.drawString(50, y, f"IPFS CID: {ipfs_cid}")
        y -= 12
        c.drawString(50, y, f"IPFS Gateway: https://{ipfs_cid}.ipfs.w3s.link")
        y -= 14
    if polygon_tx:
        c.drawString(50, y, f"Polygon Tx: {polygon_tx}")
        y -= 12
        c.drawString(50, y, f"Polygonscan: https://polygonscan.com/tx/{polygon_tx}")
        y -= 14

    # QR code linking to Polygonscan if present, otherwise IPFS
    qr_target = None
    if polygon_tx:
        qr_target = f"https://polygonscan.com/tx/{polygon_tx}"
    elif ipfs_cid:
        qr_target = f"https://{ipfs_cid}.ipfs.w3s.link"

    if qr_target:
        qr = qrcode.QRCode(box_size=2, border=2)
        qr.add_data(qr_target)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img_buff = io.BytesIO()
        img.save(img_buff, format="PNG")
        img_buff.seek(0)
        qr_x = width - 150
        qr_y = 50
        c.drawInlineImage(Image.open(img_buff), qr_x, qr_y, width=100, height=100)
        c.setFont("Helvetica", 7)
        c.drawString(qr_x, qr_y + 105, "Scan to verify immutability")

    c.showPage()
    c.save()
    pdf_bytes = buff.getvalue()
    buff.close()
    return pdf_bytes

def complete_trip_and_issue_certificate(trip_id: str):
    # Load trip
    trip = supabase.table("reefer_trips").select("*").eq("id", trip_id).single().execute().data
    if not trip:
        logger.error("Trip not found for certificate generation")
        return
    user_id = trip["user_id"]
    truck_id = trip["truck_id"]

    # Fetch events for this trip
    events_resp = supabase.table("reefer_events").select("*").eq("user_id", user_id).eq("truck_id", truck_id)        .gte("occurred_at", trip["started_at"]).lte("occurred_at", trip["ended_at"]).order("occurred_at").execute()
    events = events_resp.data or []

    ipfs_cid = None
    polygon_tx = None

    pdf_bytes = generate_certificate_pdf(trip, events, ipfs_cid=None, polygon_tx=None)

    # Upload to IPFS
    cid = upload_pdf_to_web3_storage(pdf_bytes)
    if cid:
        ipfs_cid = cid

    # Record on Polygon
    ts = int(datetime.now(timezone.utc).timestamp())
    try:
        polygon_tx = record_on_polygon(ipfs_cid or trip_id, ts)
    except Exception as e:
        logger.error("Polygon record failed: %s", e)

    # Regenerate PDF with final CID / tx
    pdf_bytes = generate_certificate_pdf(trip, events, ipfs_cid=ipfs_cid, polygon_tx=polygon_tx or None)

    # Store certificate row
    cert_ins = supabase.table("reefer_certificates").insert({
        "user_id": user_id,
        "truck_id": truck_id,
        "trip_id": trip_id,
        "pdf_url": "",  # can be filled with storage URL if you upload to Supabase Storage later
        "ipfs_cid": ipfs_cid,
        "polygon_tx_hash": polygon_tx,
    }).execute().data[0]

    # Email recipients if configured
    rec = supabase.table("recipient_emails").select("*").eq("user_id", user_id).eq("truck_id", truck_id).maybe_single().execute().data
    emails = []
    if rec:
        for key in ["driver_email", "shipper_email", "broker_email", "insurance_email"]:
            if rec.get(key):
                emails.append(rec[key])
    if emails:
        subject = "ReeferShield Certificate – Trip Completed"
        link_text = "Your reefer certificate is attached or available via your ReeferShield dashboard."
        html = f"<p>{link_text}</p>"
        try:
            send_certificate_email(emails, subject, html, pdf_bytes)
        except Exception as e:
            logger.error("Error sending certificate email: %s", e)

# ---------- Routes ----------

@app.get("/health")
def health():
    return {"status": "ok"}

# OAuth start endpoints

@app.get("/auth/{provider}/start")
def oauth_start(provider: str, user_id: str):
    if provider == "samsara":
        if not (SAMSARA_CLIENT_ID and SAMSARA_OAUTH_REDIRECT_URI):
            raise HTTPException(500, "Samsara not configured")
        url = (
            "https://api.samsara.com/oauth2/authorize"
            f"?response_type=code&client_id={SAMSARA_CLIENT_ID}"
            f"&redirect_uri={SAMSARA_OAUTH_REDIRECT_URI}"
            f"&state={user_id}"
            "&scope=vehicles.read%20assets.read%20read_refrigerated_trailer"
        )
        return RedirectResponse(url)
    if provider == "motive":
        if not (MOTIVE_CLIENT_ID and MOTIVE_OAUTH_REDIRECT_URI):
            raise HTTPException(500, "Motive not configured")
        url = (
            "https://api.gomotive.com/oauth/authorize"
            f"?response_type=code&client_id={MOTIVE_CLIENT_ID}"
            f"&redirect_uri={MOTIVE_OAUTH_REDIRECT_URI}"
            f"&state={user_id}"
            "&scope=offline_access+read_vehicles"
        )
        return RedirectResponse(url)
    if provider == "geotab":
        # Geotab OAuth varies by environment; this is a placeholder
        if not (GEOTAB_CLIENT_ID and GEOTAB_OAUTH_REDIRECT_URI):
            raise HTTPException(500, "Geotab not configured")
        url = (
            "https://my.geotab.com/apiv1/oauth/authorize"
            f"?response_type=code&client_id={GEOTAB_CLIENT_ID}"
            f"&redirect_uri={GEOTAB_OAUTH_REDIRECT_URI}"
            f"&state={user_id}"
        )
        return RedirectResponse(url)
    raise HTTPException(404, "Unknown provider")

@app.get("/auth/{provider}/callback")
def oauth_callback(provider: str, code: str, state: str):
    user_id = state
    token_url = None
    client_id = None
    client_secret = None
    redirect_uri = None
    if provider == "samsara":
        token_url = "https://api.samsara.com/oauth2/token"
        client_id = SAMSARA_CLIENT_ID
        client_secret = SAMSARA_CLIENT_SECRET
        redirect_uri = SAMSARA_OAUTH_REDIRECT_URI
    elif provider == "motive":
        token_url = "https://api.gomotive.com/oauth/token"
        client_id = MOTIVE_CLIENT_ID
        client_secret = MOTIVE_CLIENT_SECRET
        redirect_uri = MOTIVE_OAUTH_REDIRECT_URI
    elif provider == "geotab":
        token_url = "https://my.geotab.com/apiv1/oauth/token"
        client_id = GEOTAB_CLIENT_ID
        client_secret = GEOTAB_CLIENT_SECRET
        redirect_uri = GEOTAB_OAUTH_REDIRECT_URI
    else:
        raise HTTPException(404, "Unknown provider")

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret,
    }
    resp = requests.post(token_url, data=data)
    if resp.status_code >= 400:
        logger.error("OAuth token exchange error: %s %s", resp.status_code, resp.text)
        raise HTTPException(400, "Token exchange failed")
    tokens = resp.json()
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    expires_in = tokens.get("expires_in")
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in or 3600)

    supabase.table("telematics_connections").upsert({
        "user_id": user_id,
        "provider": provider,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": expires_at.isoformat(),
        "scope": tokens.get("scope"),
    }, on_conflict="user_id,provider").execute()

    return JSONResponse({"status": "connected", "provider": provider})

# Webhook handlers for telematics providers.
# These normalize incoming data into reefer_events and may trigger trip completion.

def handle_telematics_event(provider: str, payload: dict):
    logger.info("Telematics webhook from %s: %s", provider, payload)
    # This assumes payload contains user_id and truck_id fields that you map via provider config.
    user_id = payload.get("user_id")
    truck_id = payload.get("truck_id")
    if not user_id or not truck_id:
        logger.warning("Missing user_id/truck_id in webhook payload")
        return

    event_type = payload.get("event_type")
    cargo_type = payload.get("cargo_type")
    temperature = payload.get("temperature")
    setpoint = payload.get("setpoint")
    latitude = payload.get("latitude")
    longitude = payload.get("longitude")
    occurred_at = payload.get("occurred_at") or datetime.now(timezone.utc).isoformat()

    supabase.table("reefer_events").insert({
        "user_id": user_id,
        "truck_id": truck_id,
        "provider": provider,
        "event_type": event_type,
        "cargo_type": cargo_type,
        "temperature": temperature,
        "setpoint": setpoint,
        "latitude": latitude,
        "longitude": longitude,
        "raw_payload": payload,
        "occurred_at": occurred_at,
    }).execute()

    # Simple temp range logic
    if temperature is not None and cargo_type:
        # Example ranges
        ranges = {
            "frozen": (-20, 10),
            "fresh": (30, 40),
            "produce": (34, 42),
        }
        rng = ranges.get(cargo_type.lower())
        if rng:
            low, high = rng
            if temperature < low or temperature > high:
                # Attempt auto-recovery via OEM API
                try:
                    execute_recovery_command(provider, user_id, truck_id, setpoint= (low + high) / 2)
                except Exception as e:
                    logger.error("Recovery command failed: %s", e)

    # Trip completion detection: ignition_off near receiver
    if event_type == "ignition_off":
        # Find open trip for this truck
        trips = supabase.table("reefer_trips").select("*").eq("truck_id", truck_id).eq("status", "open").execute().data
        if trips:
            trip = trips[0]
            receiver_lat = trip.get("receiver_lat")
            receiver_lng = trip.get("receiver_lng")
            if receiver_lat is not None and receiver_lng is not None and latitude and longitude:
                # naive distance check
                dist = abs(float(receiver_lat) - float(latitude)) + abs(float(receiver_lng) - float(longitude))
                if dist < 0.5:  # rough threshold
                    # close trip and generate cert
                    supabase.table("reefer_trips").update({
                        "status": "completed",
                        "ended_at": occurred_at,
                    }).eq("id", trip["id"]).execute()
                    complete_trip_and_issue_certificate(trip["id"])

def execute_recovery_command(provider: str, user_id: str, truck_id: str, setpoint: float):
    conn = supabase.table("telematics_connections").select("*").eq("user_id", user_id).eq("provider", provider).maybe_single().execute().data
    if not conn:
        logger.warning("No telematics connection found for recovery")
        return
    token = conn["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    if provider == "samsara":
        # Placeholder: adjust to Samsara's reefer API
        url = f"https://api.samsara.com/fleet/assets/{truck_id}/reefer/setpoint"
        resp = requests.post(url, headers=headers, json={"setPoint": setpoint})
        logger.info("Samsara recovery response: %s %s", resp.status_code, resp.text[:200])
    elif provider == "motive":
        url = f"https://api.gomotive.com/v1/reefers/{truck_id}/set_temperature"
        resp = requests.post(url, headers=headers, json={"set_temperature": setpoint})
        logger.info("Motive recovery response: %s %s", resp.status_code, resp.text[:200])
    elif provider == "geotab":
        # Geotab may not support remote setpoint; placeholder no-op
        logger.info("Geotab recovery not implemented; provider may not support remote setpoint")
    else:
        logger.warning("Unknown provider for recovery command: %s", provider)

@app.post("/webhooks/{provider}")
async def telematics_webhook(provider: str, request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()
    # In a real app, validate HMAC / signatures per provider.
    background_tasks.add_task(handle_telematics_event, provider, payload)
    return {"status": "ok"}

@app.get("/cron/daily-digest")
def daily_digest():
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    # For each profile with daily_digest enabled, aggregate certificates
    profiles = supabase.table("profiles").select("*").eq("daily_digest", True).execute().data or []
    for prof in profiles:
        user_id = prof["id"]
        email = prof["email"]
        certs = supabase.table("reefer_certificates").select("*").eq("user_id", user_id)            .gte("created_at", yesterday.isoformat()).execute().data or []
        if not certs:
            continue
        html = "<h2>Your ReeferShield daily digest</h2><ul>"
        for c_row in certs:
            html += f"<li>Truck {c_row['truck_id']} – Trip {c_row.get('trip_id')} – Created {c_row['created_at']}</li>"
        html += "</ul>"
        try:
            send_certificate_email([email], "ReeferShield daily digest", html, pdf_bytes=b"")
        except Exception as e:
            logger.error("Error sending daily digest: %s", e)
    return {"status": "ok"}
