from fastapi import APIRouter, Request
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse

router = APIRouter()


@router.post("/whatsapp")
async def whatsapp_webhook(request: Request):

    try:
        form = await request.form()

        incoming_message = form.get("Body", "").strip()
        sender = form.get("From", "")

        if not incoming_message:
            return Response(
                content="Empty message",
                status_code=400
            )

        # WhatsApp number identifies the conversation
        session_id = sender

        # Connect to the existing chatbot orchestration
        answer = process_chat_message(
            message=incoming_message,
            session_id=session_id
        )

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
