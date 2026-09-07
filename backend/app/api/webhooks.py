import hashlib
import hmac
import json
import logging
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, Depends, Header, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.config import settings
from app.models.progress import ProgressEvent
from app.models.ingestion_source import IngestionSource
from app.services.progress_service import extract_and_store_progress
from app.matching.service import run_matching_for_event
from app.services.confidence_service import evaluate_confidence

router = APIRouter(prefix="/webhooks/whatsapp", tags=["WhatsApp Webhook"])
logger = logging.getLogger(__name__)


def verify_whatsapp_signature(payload: bytes, signature: str, app_secret: str) -> bool:
    """Verify the X-Hub-Signature-256 header from Meta."""
    if not signature or not signature.startswith("sha256="):
        return False
    expected_signature = hmac.new(
        app_secret.encode("utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()
    provided_signature = signature[7:]  # Remove "sha256=" prefix
    return hmac.compare_digest(expected_signature, provided_signature)


def get_whatsapp_source(db: Session) -> IngestionSource:
    """Get or create the WhatsApp ingestion source."""
    source = db.query(IngestionSource).filter(IngestionSource.code == "WHATSAPP").first()
    if not source:
        source = IngestionSource(
            code="WHATSAPP",
            name="WhatsApp",
            description="WhatsApp Business Cloud API messages",
        )
        db.add(source)
        db.commit()
        db.refresh(source)
    return source


async def send_whatsapp_reply(phone_number_id: str, access_token: str, to: str, message: str) -> dict:
    """Send a reply message via WhatsApp Cloud API."""
    import httpx
    
    url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message},
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=data)
        return response.json()


@router.get("/inbound", summary="WhatsApp webhook verification")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    """Verify the webhook subscription with Meta."""
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("WhatsApp webhook verified successfully")
        return int(hub_challenge)
    
    logger.warning("WhatsApp webhook verification failed")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/inbound", summary="Receive WhatsApp inbound messages")
async def receive_whatsapp_message(
    request: Request,
    x_hub_signature_256: str = Header(None, alias="X-Hub-Signature-256"),
    db: Session = Depends(get_db),
):
    """Receive and process inbound WhatsApp messages."""
    payload = await request.body()
    
    # Verify signature
    if settings.WHATSAPP_APP_SECRET:
        if not verify_whatsapp_signature(payload, x_hub_signature_256, settings.WHATSAPP_APP_SECRET):
            logger.warning("Invalid WhatsApp signature")
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    try:
        data = json.loads(payload.decode("utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    logger.info(f"Received WhatsApp webhook: {json.dumps(data)[:500]}")
    
    # Process the webhook data
    try:
        await process_whatsapp_webhook(db, data)
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {e}")
        # Don't raise - acknowledge receipt to Meta
    
    return {"status": "ok"}


async def process_whatsapp_webhook(db: Session, data: dict):
    """Process the WhatsApp webhook payload and feed into the extraction pipeline."""
    
    # Get WhatsApp ingestion source
    whatsapp_source = get_whatsapp_source(db)
    
    # Extract entries from webhook
    entries = data.get("entry", [])
    for entry in entries:
        changes = entry.get("changes", [])
        for change in changes:
            value = change.get("value", {})
            messages = value.get("messages", [])
            contacts = value.get("contacts", [])
            
            # Get sender info
            sender_name = "Unknown"
            if contacts:
                sender_name = contacts[0].get("profile", {}).get("name", "Unknown")
            
            for message in messages:
                # Only process text messages for now
                if message.get("type") != "text":
                    logger.info(f"Skipping non-text message type: {message.get('type')}")
                    continue
                
                # Extract message content
                text_body = message.get("text", {}).get("body", "")
                if not text_body.strip():
                    continue
                
                sender_phone = message.get("from", "")
                message_id = message.get("id", "")
                timestamp = message.get("timestamp", "")
                
                logger.info(f"Processing WhatsApp message from {sender_phone}: {text_body[:100]}")
                
                # Create progress event with WhatsApp source
                progress_event = ProgressEvent(
                    organization_id=1,  # TODO: Map phone to org/project
                    project_id=1,       # TODO: Map phone to org/project
                    raw_text=text_body,
                    event_type="PROGRESS",
                    event_date=date.today(),
                    discipline=None,
                    location=None,
                    equipment_tag=None,
                    source_type="WHATSAPP",
                    source_file=f"whatsapp:{message_id}",
                    session_id=None,
                    ingestion_source_id=whatsapp_source.id,
                )
                db.add(progress_event)
                db.commit()
                db.refresh(progress_event)
                
                # Run the full pipeline: extraction -> matching -> confidence
                try:
                    # The extraction is already done in the webhook handler
                    # We now run matching and confidence evaluation
                    matching_result = run_matching_for_event(db, progress_event.id)
                    confidence_result = evaluate_confidence(db, progress_event.id)
                    
                    logger.info(f"WhatsApp message {message_id} processed: match={matching_result.top_matches[0].activity_code if matching_result.top_matches else 'none'}, confidence={confidence_result.get('confidence_score', 'N/A')}")
                    
                    # Send confirmation reply if configured
                    if settings.WHATSAPP_ACCESS_TOKEN and settings.WHATSAPP_PHONE_NUMBER_ID:
                        reply_text = f"✅ Received: \"{text_body[:50]}\"\n"
                        if matching_result.top_matches:
                            match = matching_result.top_matches[0]
                            reply_text += f"Matched: {match.activity_code} - {match.activity_name}\n"
                            reply_text += f"Confidence: {confidence_result.get('confidence_score', 0):.0%}"
                        else:
                            reply_text += "No match found - will be reviewed by planner"
                        
                        await send_whatsapp_reply(
                            settings.WHATSAPP_PHONE_NUMBER_ID,
                            settings.WHATSAPP_ACCESS_TOKEN,
                            sender_phone,
                            reply_text
                        )
                        
                except Exception as e:
                    logger.error(f"Error in pipeline for WhatsApp message {message_id}: {e}")
                    # Still send a basic acknowledgment
                    if settings.WHATSAPP_ACCESS_TOKEN and settings.WHATSAPP_PHONE_NUMBER_ID:
                        await send_whatsapp_reply(
                            settings.WHATSAPP_PHONE_NUMBER_ID,
                            settings.WHATSAPP_ACCESS_TOKEN,
                            sender_phone,
                            f"✅ Received your message. It will be processed shortly."
                        )