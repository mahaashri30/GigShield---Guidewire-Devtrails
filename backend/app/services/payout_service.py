"""
Payout Service - Razorpay X Test Mode Integration
"""
import uuid
import asyncio
import razorpay
from datetime import datetime
from app.config import settings


def _get_client() -> razorpay.Client:
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def _is_mock() -> bool:
    return settings.RAZORPAY_KEY_ID == "rzp_test_mock"


async def initiate_upi_payout(
    worker_id: str,
    upi_id: str,
    amount: float,
    claim_id: str,
) -> dict:
    if _is_mock():
        return await _mock_payout(upi_id, amount, claim_id)

    try:
        client = _get_client()
        amount_paise = int(amount * 100)
        loop = asyncio.get_event_loop()
        payout = await loop.run_in_executor(
            None,
            lambda: client.payout.create({
                "account_number": settings.RAZORPAY_ACCOUNT_NUMBER,
                "fund_account": {
                    "account_type": "vpa",
                    "vpa": {"address": upi_id},
                    "contact": {
                        "name": "GigShield Worker",
                        "type": "customer",
                        "reference_id": worker_id,
                    },
                },
                "amount": amount_paise,
                "currency": "INR",
                "mode": "UPI",
                "purpose": "payout",
                "queue_if_low_balance": True,
                "reference_id": f"GS_{claim_id[:8].upper()}",
                "narration": "GigShield Claim Payout",
            })
        )
        return {
            "success": payout.get("status") in ("processing", "processed", "queued"),
            "payout_id": payout.get("id"),
            "transaction_ref": payout.get("reference_id"),
            "upi_id": upi_id,
            "amount": amount,
            "status": payout.get("status"),
            "message": f"₹{amount:.0f} payout initiated to {upi_id}",
        }
    except Exception as e:
        return {
            "success": False,
            "payout_id": None,
            "transaction_ref": None,
            "status": "failed",
            "message": f"Razorpay error: {str(e)}",
        }


async def _mock_payout(upi_id: str, amount: float, claim_id: str) -> dict:
    """Mock payout — always succeeds in dev/demo mode."""
    await asyncio.sleep(0.3)
    return {
        "success": True,
        "payout_id": f"pout_mock_{uuid.uuid4().hex[:12]}",
        "transaction_ref": f"GS{claim_id[:8].upper()}",
        "upi_id": upi_id,
        "amount": amount,
        "status": "completed",
        "completed_at": datetime.utcnow().isoformat(),
        "message": f"₹{amount:.0f} credited to {upi_id}",
    }
