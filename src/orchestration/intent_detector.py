
import re

def detect_intent(message):
    # Normalize punctuation and spacing
    text = re.sub(r"[^\w\s']", " ", message.lower())
    text = " ".join(text.split())

    recommendation_keywords = [
        "recommend", "recommendation",
        "what insurance would you recommend",
        "what insurance should i choose",
        "which insurance should i choose",
        "which insurance is suitable",
        "what insurance is suitable",
        "suggest insurance", "suggest a product",
        "which product should i choose",
        "what cover can i get", "what cover can i afford",
        "i need insurance", "i need cover",
        "i want insurance", "i want cover",
        "protect my stock", "insurance for my stock",
        "insurance for my business", "cover for my business",
        "insurance for my shop", "get recommendations",

        # Kiswahili and Sheng
        "nataka bima", "nahitaji bima",
        "bima ya biashara", "bima ya duka",
        "bima ya stock", "bima ya bidhaa",
        "bima ya moto", "bima ya wizi",
        "nisaidie kupata bima", "ni bima gani",
        "bima gani inafaa", "naweza pata bima gani"
    ]

    greeting_keywords = [
        "hello", "hi", "hey",
        "good morning", "good afternoon",
        "good evening", "how are you",
        "habari", "hujambo", "sasa",
        "niaje", "mambo", "uko aje",
        "asante", "thank you", "thanks", "sawa"
    ]

    if any(keyword in text for keyword in recommendation_keywords):
        return "recommendation"

    if any(
        text == greeting or text.startswith(greeting + " ")
        for greeting in greeting_keywords
    ):
        return "general_conversation"

    return "information"
