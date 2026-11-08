
def generate_recommendation_response(result):
    """
    Convert structured recommendation results into
    a readable conversational response.

    Product details are taken directly from the
    recommendation engine. No product information
    is invented.
    """

    if not result or not result.get("success"):
        return (
            "I couldn't generate your recommendations "
            "at the moment. Please try again."
        )

    profile = result.get("trader_profile", {})
    products = result.get("recommendations", [])
    payment = result.get("payment_guidance", {})

    stock_value = profile.get("stock_value_kes", 0)
    budget = profile.get("wtp_monthly_kes")
    main_risk = profile.get("primary_risk_concern", "business risks")

    if not products:
        return (
            "I couldn't find suitable products in the "
            "available catalogue for your profile. "
            "You may need further assessment."
        )

    lines = []

    lines.append(
        f"Based on your business profile, I've identified "
        f"{len(products)} insurance options worth considering."
    )

    lines.append(
        f"\nYour stock is valued at KES {stock_value:,.0f}, "
        f"and your main concern is {main_risk}."
    )

    if budget is not None:
        lines.append(
            f"Your stated monthly insurance budget is "
            f"KES {float(budget):,.0f}."
        )

    lines.append("\nHere are your recommendations:")

    for index, product in enumerate(products, start=1):

        name = product.get("product_name", "Unnamed product")

        annual = product.get("annual_premium_kes")
        monthly = product.get("monthly_premium_equivalent_kes")

        affordability = product.get(
            "affordability_status",
            "Not specified"
        )

        lines.append(f"\n{index}. {name}")

        if annual is not None:
            lines.append(
                f"   Annual premium: KES {float(annual):,.2f}"
            )

        if monthly is not None:
            lines.append(
                f"   Monthly equivalent: KES {float(monthly):,.2f}"
            )

        lines.append(
            f"   Affordability: {affordability}"
        )

        coverage_list = product.get("coverage_by_risk", [])

        if coverage_list:
            lines.append("   Coverage:")

            for coverage in coverage_list:

                risk = coverage.get("risk_type", "Unspecified")
                limit = coverage.get("coverage_limit_kes", 0)
                shortfall = coverage.get("coverage_shortfall_kes", 0)

                lines.append(
                    f"   - {risk.title()}: "
                    f"KES {float(limit):,.0f}"
                )

                if shortfall > 0:
                    lines.append(
                        f"     Coverage shortfall against your stock: "
                        f"KES {float(shortfall):,.0f}"
                    )

        else:
            lines.append(
                "   Detailed coverage information is unavailable."
            )

    frequency = payment.get("recommended_frequency")

    if frequency:
        lines.append(
            f"\nPayment guidance: {frequency.replace('_', ' ').title()}."
        )

    if payment.get("requires_further_assessment"):
        lines.append(
            "Your payment arrangement requires further assessment."
        )

    if payment.get("insurer_confirmation_required", True):
        lines.append(
            "Please confirm the actual premium, payment arrangements, "
            "coverage conditions and exclusions with the insurer."
        )

    lines.append(
        "\nThese are model-generated recommendations to help you "
        "compare available options. They are not confirmation of "
        "policy eligibility or guaranteed coverage."
    )

    lines.append(
        "\nWould you like me to explain the difference between "
        "these products?"
    )

    return "\n".join(lines)
