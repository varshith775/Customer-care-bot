
from uuid import uuid4

from flask import Flask, jsonify, render_template, request, session


app = Flask(__name__)
app.secret_key = "customer-care-local-ui"

ORDERS = {"777": "varshith", "555": "shyam", "666": "srineeth"}


def new_conversation():
    return {"stage": "intent", "intent": None}


def respond(message, conversation):
    text = message.strip()
    lower = text.lower()
    stage = conversation.get("stage", "intent")
    intent = conversation.get("intent")

    if not text:
        return "Tell me what you need help with: order status, a return, a refund, or an exchange.", conversation
    if stage == "order_id":
        if text in ORDERS:
            conversation.update(stage="intent", intent=None)
            return f"Hi {ORDERS[text]}, your order is on the way and arriving soon.", conversation
        return "That order ID is not in our system. Try 777, 555, or 666.", conversation
    if stage == "details":
        if intent == "return":
            conversation.update(stage="intent", intent=None)
            if any(word in lower for word in ("size", "broken", "damage", "overpaid", "other")):
                return "I’m sorry for the inconvenience. Your order will be returned. Anything else I can help with?", conversation
            return "I can help with a size issue, a broken product, an overpayment, or another return reason.", conversation
        if intent == "exchange":
            if "color" in lower:
                conversation["stage"] = "color"
                return "What color would you like instead?", conversation
            conversation["stage"] = "size"
            return "What matching size should I arrange?", conversation
        if intent == "refund":
            conversation["stage"] = "upi"
            return "I can process that refund. Enter your UPI ID to continue.", conversation
    if stage == "upi":
        conversation.update(stage="intent", intent=None)
        return "Refund initiated and completed successfully. Anything else I can help with?", conversation
    if stage == "size":
        conversation.update(stage="intent", intent=None)
        return f"Your product will be exchanged soon for size {text}. Anything else I can help with?", conversation
    if stage == "color":
        conversation.update(stage="intent", intent=None)
        return f"Your product will be exchanged soon for a {text} item. Anything else I can help with?", conversation
    if "status" in lower or "track" in lower:
        conversation["stage"] = "order_id"
        return "I can check that. What is your order ID?", conversation
    for possible_intent in ("return", "refund", "exchange"):
        if possible_intent in lower:
            conversation.update(stage="details", intent=possible_intent)
            if possible_intent == "return":
                return "I can arrange that. What happened: sizing, damage, overpayment, or something else?", conversation
            if possible_intent == "refund":
                return "I can help with a refund. Briefly describe the issue first.", conversation
            return "I can arrange an exchange. Is it for a different size, fit, or color?", conversation
    return "I can help with order status, returns, refunds, and exchanges. Which one should we handle?", conversation


@app.get("/")
def home():
    return render_template("index.html")


@app.post("/api/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    conversation = session.get("conversation", new_conversation())
    reply, conversation = respond(payload.get("message", ""), conversation)
    session["conversation"] = conversation
    return jsonify({"reply": reply, "conversation_id": session.get("conversation_id")})


@app.post("/api/reset")
def reset():
    session["conversation"] = new_conversation()
    session["conversation_id"] = str(uuid4())[:8]
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True)
       
