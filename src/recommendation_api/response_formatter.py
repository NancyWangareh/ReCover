
import pandas as pd


def format_currency(value):
    """Format a numeric value as Kenyan shillings."""
    try:
        return f"KES {float(value):,.2f}"
    except (TypeError, ValueError):
        return "Not available"


def format_recommendation_response(trader, recommendations):
    """
    Format ReCover recommendations into a WhatsApp-friendly message.

    Expected arguments:
        trader: Dictionary or Pydantic trader input.
        recommendations: Output dictionary from recommend_products().
    """

    # Convert trader input into a dictionary
    if hasattr(trader, "model_dump"):
        trader = trader.model_dump()
    elif hasattr(trader, "dict"):
        trader = trader.dict()
    elif hasattr(trader, "to_dict"):
        trader = trader.to_dict()

    if not isinstance(trader, dict):
        raise TypeError("Trader information must be a dictionary or compatible object.")

    cluster = recommendations.get("cluster", {})

    payment = recommendations.get("payment_recommendation", {})

    products = recommendations.get("recommendations", [])

    # Trader profile
    stock_value = trader.get("stock_value_kes", 0)
    monthly_income = trader.get("monthly_income_kes", 0)
    monthly_wtp = trader.get("wtp_monthly_kes", 0)
    risk = trader.get("primary_risk_concern", "Not specified")

    wants_fire = trader.get("wants_cover_fire", False)
    wants_theft = trader.get("wants_cover_theft", False)

    if not products:
        return (
            "RECover Microinsurance Recommendations\n\n"
            "We could not identify a suitable product from the "
            "available catalogue that meets the requested coverage "
            "requirements. Please contact a representative for further "
            "information."
        )

    message = []

    # Header
    message.append("🛡️ *ReCover Microinsurance Recommendations*")
    message.append("")
    message.append("👤 *YOUR BUSINESS PROFILE*")
    message.append(f"• Stock value: {format_currency(stock_value)}")
    message.append(f"• Monthly income: {format_currency(monthly_income)}")
    message.append(f"• Monthly willingness to pay: {format_currency(monthly_wtp)}")
    message.append(f"• Main risk concern: {str(risk).replace('_', ' ').title()}")
    message.append(f"• Predicted trader cluster: {cluster}")

    # Requested coverage
    requested_cover = []

    if wants_fire:
        requested_cover.append("Fire")

    if wants_theft:
        requested_cover.append("Burglary/Theft")

    message.append(
        "• Requested cover: "
        + (", ".join(requested_cover) if requested_cover else "Not specified")
    )

    # Product recommendations
    message.append("")
    message.append("📋 *RECOMMENDED INSURANCE PRODUCTS*")
    for index, product in enumerate(products, start=1):

       risk_type = product.get("risk_type", "").lower()
       coverage_limit = product.get("coverage_limit_kes", 0)

    affordability = product.get(
        "affordability_status",
        "Not assessed"
    )

    message.append(f"\n*{index}. {product.get('product_name', 'Unknown Product')}*")
    message.append(f"• Product ID: {product.get('product_id', 'N/A')}")
    message.append(f"• Annual premium: {format_currency(product.get('annual_premium_kes', 0))}")
    message.append(f"• Monthly premium equivalent: {format_currency(product.get('monthly_premium_equivalent_kes', 0))}")

    if risk_type == "fire":
        message.append(
            f"• Fire coverage limit: {format_currency(coverage_limit)}"
    )

    elif risk_type == "burglary":
        message.append(
            f"• Burglary coverage limit: {format_currency(coverage_limit)}"
    )

    message.append(f"• Affordability: {affordability}")

   
    # Payment guidance
    message.append("")
    message.append("💳 *PAYMENT FREQUENCY GUIDANCE*")

    message.append(
        "• Stated preference: "
        + str(payment.get("preferred_frequency", "Not provided")).title()
    )

    message.append(
        "• Suggested frequency: "
        + str(payment.get("recommended_frequency", "Review required")).replace(
            "_", " "
        ).title()
    )

    message.append(
        "• Reason: "
        + str(payment.get("reason", "Further assessment required."))
    )

    # Important clarification
    message.append("")
    message.append("ℹ️ *IMPORTANT INFORMATION*")
    message.append(
        "Monthly premium equivalents are provided for affordability "
        "comparison only. They do not confirm that the insurer accepts "
        "monthly instalments."
    )

    message.append(
        "Please confirm product eligibility, exclusions, claims conditions, "
        "and available payment arrangements with the insurer before purchase."
    )

    message.append("")
    message.append(
        "ReCover helps you access information about microinsurance "
        "products to support informed business decisions."
    )

    return "\n".join(message)