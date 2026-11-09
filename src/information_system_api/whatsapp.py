from fastapi import APIRouter, Request
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse

from orchestration.agent import handle_message

router = APIRouter()


@router.post("/whatsapp")
async def whatsapp_webhook(request: Request):

    try:
        form = await request.form()

        incoming_message = form.get("Body", "").strip()
        sender = form.get("From", "")

        if not incoming_message or not sender:
            return Response(
                content="Invalid message",
                status_code=400
            )

        # Identify the conversation using the sender's WhatsApp number
        session_id = sender

        # Send the message to ReCover orchestration
        answer = handle_message(
            message=incoming_message,
            session_id=session_id
        )

        # Extract the response from orchestration
        if isinstance(answer, dict):
            answer = (
                answer.get("answer")
                or answer.get("reply")
                or answer.get("response")
                or answer.get("text")
                or str(answer)
            )

        # Return response in Twilio-compatible TwiML format
        response = MessagingResponse()
        response.message(str(answer))

        return Response(
            content=str(response),
            media_type="application/xml"
        )

    except Exception as e:
        print(f"WhatsApp webhook error: {e}")

        response = MessagingResponse()
        response.message(
            "Sorry, something went wrong. Please try again shortly."
        )

        return Response(
            content=str(response),
            media_type="application/xml"
        )
