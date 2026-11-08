from recommendation_api.recommender import recommend_products


def process_recommendations(trader):
    """
    Call the ReCover recommendation engine directly,
    without making an HTTP request to Render.
    """

    # Generate recommendations directly
    result = recommend_products(trader)

    cluster = result.get("cluster")
    payment = result.get("payment_recommendation", {})
    products = result.get("recommendations", [])

    stock_value = float(trader.get("stock_value_kes", 0))

    # Consolidate duplicate products
    consolidated_products = {}

    for product in products:

        product_id = product.get("product_id")

        if not product_id:
            continue

        if product_id not in consolidated_products:

            consolidated_products[product_id] = {
                "product_id": product_id,
                "product_name": product.get("product_name"),
                "annual_premium_kes": product.get(
                    "annual_premium_kes"
                ),
                "monthly_premium_equivalent_kes": product.get(
                    "monthly_premium_equivalent_kes"
                ),
                "affordability_status": product.get(
                    "affordability_status"
                ),
                "selection_method": product.get(
                    "selection_method"
                ),
                "coverage_by_risk": []
            }

        coverage_limit = float(
            product.get("coverage_limit_kes", 0)
        )

        coverage_details = {
            "risk_type": product.get("risk_type"),
            "coverage_limit_kes": coverage_limit,
            "coverage_surplus_kes": max(
                coverage_limit - stock_value, 0
            ),
            "coverage_shortfall_kes": max(
                stock_value - coverage_limit, 0
            )
        }

        existing_risks = consolidated_products[
            product_id
        ]["coverage_by_risk"]

        if coverage_details not in existing_risks:
            existing_risks.append(coverage_details)

    # Payment guidance
    recommended_frequency = payment.get(
        "recommended_frequency",
        "review_required"
    )

    payment_guidance = {
        "preferred_frequency": payment.get(
            "preferred_frequency"
        ),
        "recommended_frequency": recommended_frequency,
        "preference_match": payment.get(
            "preference_match"
        ),
        "reason": payment.get("reason"),
        "insurer_confirmation_required": payment.get(
            "insurer_confirmation_required",
            True
        ),
        "requires_further_assessment": (
            recommended_frequency == "review_required"
        )
    }

    return {
        "success": True,
        "trader_profile": {
            "stock_value_kes": stock_value,
            "monthly_income_kes": trader.get(
                "monthly_income_kes"
            ),
            "wtp_monthly_kes": trader.get(
                "wtp_monthly_kes"
            ),
            "primary_risk_concern": trader.get(
                "primary_risk_concern"
            )
        },
        "cluster": cluster,
        "payment_guidance": payment_guidance,
        "recommendations": list(
            consolidated_products.values()
        )
    }
