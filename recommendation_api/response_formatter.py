
def format_recommendation_response(api_response):

    if not api_response.get("success"):
        return (
            "Sorry, we couldn't generate your recommendations "
            "at the moment. Please try again."
        )

    result = api_response.get("result", {})

    recommendations = result.get("recommendations", [])
    payment = result.get("payment_recommendation", {})

    if not recommendations:
        return (
            "We couldn't identify a suitable product at the moment. "
            "Please contact our team for assistance."
        )

    message = [
        "Hello! 👋 Welcome to ReCover.",
        "",
        "Based on the information you shared about your business, "
        "we've identified some insurance options worth exploring.",
        "",
        "🛡️ YOUR PRODUCT RECOMMENDATIONS"
    ]

    # PRODUCT RECOMMENDATIONS

    for index, product in enumerate(recommendations, start=1):

        name = product.get("product_name", "Insurance option")
        risk = product.get("risk_type", "business")
        premium = product.get("annual_premium_kes", 0)
        monthly = product.get("monthly_premium_equivalent_kes", 0)
        coverage = product.get("coverage_limit_kes", 0)
        wtp = product.get("monthly_wtp_kes", 0)
        affordability = product.get("affordability_status", "")

        message.extend([
            "",
            f"{index}. {name}",
            f"Risk covered: {risk.capitalize()}",
            f"Coverage limit: KES {coverage:,.0f}",
            f"Annual premium: KES {premium:,.2f}",
            f"Monthly premium equivalent: KES {monthly:,.2f}"
        ])

        if affordability == "Above stated WTP":

            difference = monthly - wtp

            message.append(
                f"⚠️ This exceeds your stated monthly budget "
                f"by KES {difference:,.2f}."
            )

        elif affordability == "Within stated WTP":

            message.append(
                "✅ Within your stated monthly budget."
            )

    # PAYMENT FREQUENCY RECOMMENDATION

    recommended_frequency = payment.get(
        "recommended_frequency", "review_required"
    )

    preferred_frequency = payment.get(
        "preferred_frequency", "not specified"
    )

    reason = payment.get(
        "reason", "Further assessment is required."
    )

    message.append("\\n📅 PAYMENT FREQUENCY RECOMMENDATION")

    if recommended_frequency != "review_required":

        message.append(
            f"ReCover recommends {recommended_frequency} payments."
        )

        message.append(f"Reason: {reason}")

        if recommended_frequency != preferred_frequency:

            message.append(
                f"Your stated preference was "
                f"{preferred_frequency.replace('_', ' ')} payments."
            )

    else:

        message.append(
            "We need more information to recommend a suitable "
            "payment frequency."
        )

    if payment.get("insurer_confirmation_required", True):

        message.append(
            "Please confirm with the insurer whether this "
            "payment arrangement is available."
        )

        message.append(
            "The monthly premium equivalent is for comparison "
            "only, not a confirmed instalment schedule."
        )

    # CLOSING MESSAGE

    message.extend([
        "",
        "💡 WHAT SHOULD YOU CONSIDER?",
        "Compare the premiums, coverage limits and your ability "
        "to afford each option before making a decision.",
        "",
        "These are recommendations, not confirmation of insurance "
        "coverage. Actual policy terms and conditions apply.",
        "",
        "Would you like to know more about the coverage, "
        "exclusions or eligibility requirements?"
    ])

    return "\\n".join(message)
