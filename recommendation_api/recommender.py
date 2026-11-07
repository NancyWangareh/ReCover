
import joblib
import pandas as pd
import numpy as np
from pathlib import Path


# =========================================================
# 1. LOAD SAVED MODEL BUNDLE
# =========================================================

import os
import joblib
import pandas as pd
import numpy as np


# ============================================================
# 1. LOAD TRAINED MODEL BUNDLE
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.abspath(
    os.path.join(
        BASE_DIR,
        "..",
        "models",
        "recover_model_bundle.pkl"
    )
)

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(
        f"Model bundle not found: {MODEL_PATH}"
    )

bundle = joblib.load(MODEL_PATH)

preprocessor = bundle["preprocessor"]
kmeans = bundle["kmeans"]
feature_columns = bundle["feature_columns"]

cluster_rankings_df = bundle["cluster_rankings_df"]
products = bundle["products"]

print("ReCover model bundle loaded successfully.")

# =========================================================
# 2. HELPER FUNCTION: BOOLEAN CONVERSION
# =========================================================

def convert_to_bool(value):

    if isinstance(value, (bool, np.bool_)):
        return bool(value)

    if isinstance(value, str):
        return value.strip().lower() in ["true", "yes", "1", "y"]

    return bool(value)


# =========================================================
# 3. PAYMENT FREQUENCY RECOMMENDATION
# =========================================================

def recommend_payment_frequency(trader):

    preferred_frequency = str(
        trader["preferred_premium_frequency"]
    ).strip().lower()

    income_pattern = str(
        trader["income_receipt_pattern"]
    ).strip().lower()

    variability = str(
        trader["income_variability"]
    ).strip().lower()

    restock_days = int(trader["restock_cycle_days"])

    # -----------------------------------------------------
    # Determine suitable payment frequency
    # -----------------------------------------------------

    if income_pattern == "daily":

        if variability == "high":

            recommended_frequency = "weekly"

            reason = (
                "Weekly payments may provide greater flexibility "
                "for a trader with highly variable daily income."
            )

        elif variability == "low":

            recommended_frequency = "monthly"

            reason = (
                "Monthly payments may be manageable because "
                "the trader receives income daily with low variability."
            )

        else:

            recommended_frequency = "review_required"

            reason = (
                "Income variability is unclear. Further assessment "
                "is needed before suggesting a payment frequency."
            )

    elif income_pattern == "weekly":

        if variability == "high":

            recommended_frequency = "weekly"

            reason = (
                "Weekly payments may better align with irregular "
                "weekly income."
            )

        elif variability == "low":

            recommended_frequency = "monthly"

            reason = (
                "Monthly payments may be manageable given the "
                "trader's relatively predictable weekly income."
            )

        else:

            recommended_frequency = "review_required"

            reason = (
                "Income variability is unclear. Further assessment "
                "is needed."
            )

    elif income_pattern == "monthly":

        if variability == "high":

            recommended_frequency = "review_required"

            reason = (
                "Monthly income is highly variable. Affordability "
                "should be assessed before recommending a schedule."
            )

        elif variability == "low":

            recommended_frequency = "monthly"

            reason = (
                "Monthly payments align with the trader's "
                "relatively predictable monthly income."
            )

        else:

            recommended_frequency = "review_required"

            reason = (
                "Income variability is unclear. Further assessment "
                "is needed."
            )

    else:

        recommended_frequency = "review_required"

        reason = (
            "The income receipt pattern is unclear. "
            "Further assessment is required."
        )

    # -----------------------------------------------------
    # Compare system recommendation with trader preference
    # -----------------------------------------------------

    preference_match = (
        recommended_frequency == preferred_frequency
    )

    return {

        "recommended_frequency": recommended_frequency,

        "preferred_frequency": preferred_frequency,

        "preference_match": preference_match,

        "reason": reason,

        "income_receipt_pattern": income_pattern,

        "income_variability": variability,

        "restock_cycle_days": restock_days,

        "basis": "cash_flow_suitability_rules",

        "insurer_confirmation_required": True

    }


# =========================================================
# 4. PRODUCT RECOMMENDATION ENGINE
# =========================================================

def recommend_products(trader_data, top_n=3):

    # -----------------------------------------------------
    # Prepare trader information
    # -----------------------------------------------------

    trader_df = pd.DataFrame([trader_data])

    # Preserve training feature order
    trader_df = trader_df[feature_columns]

    # Preserve Boolean data types
    trader_df["wants_cover_fire"] = (
        trader_df["wants_cover_fire"].apply(convert_to_bool)
    )

    trader_df["wants_cover_theft"] = (
        trader_df["wants_cover_theft"].apply(convert_to_bool)
    )

    # -----------------------------------------------------
    # Apply saved preprocessing pipeline
    # -----------------------------------------------------

    transformed_data = preprocessor.transform(trader_df)

    # Assign trader to a cluster
    cluster = int(kmeans.predict(transformed_data)[0])

    # Retrieve cluster-preferred products
    trader_rankings = cluster_rankings_df[
    cluster_rankings_df["cluster"] == cluster
].copy()

    # -----------------------------------------------------
    # Retrieve trader financial information
    # -----------------------------------------------------

    stock_value = float(trader_data["stock_value_kes"])

    monthly_wtp = float(trader_data["wtp_monthly_kes"])

    # -----------------------------------------------------
    # Generate payment recommendation
    # -----------------------------------------------------

    payment_recommendation = recommend_payment_frequency(
        trader_data
    )

    recommendations = []

    # Define supported business risks
    risk_columns = {

        "fire": "fire_limit_kes",

        "burglary": "burglary_limit_kes"

    }

    risk_interest = {

        "fire": "wants_cover_fire",

        "burglary": "wants_cover_theft"

    }

    # -----------------------------------------------------
    # Evaluate products for each selected business risk
    # -----------------------------------------------------

    for risk, limit_column in risk_columns.items():

        if not convert_to_bool(
            trader_data[risk_interest[risk]]
        ):
            continue

        # -------------------------------------------------
        # First consider cluster-preferred products
        # -------------------------------------------------

        options = products.merge(
            trader_rankings,
            on="product_id",
            how="inner"
        )

        if options.empty:
            raise ValueError(
                f"No products found for cluster {cluster}."
            )

        options["cluster_rank"] = pd.to_numeric(
            options["cluster_rank"],
            errors="coerce"
        )

        options["premium_kes_pa"] = pd.to_numeric(
            options["premium_kes_pa"],
            errors="coerce"
        )

        # Retain products whose coverage limit meets
        # or exceeds the trader's declared stock value

        options = options[
            options[limit_column] >= stock_value
        ].copy()

        selection_method = "cluster_preferred"

        # -------------------------------------------------
        # Fallback to all available products if necessary
        # -------------------------------------------------

        if options.empty:

            options = products.copy()

            options[limit_column] = pd.to_numeric(
                options[limit_column],
                errors="coerce"
            )

            options["premium_kes_pa"] = pd.to_numeric(
                options["premium_kes_pa"],
                errors="coerce"
            )

            options = options[
                options[limit_column] >= stock_value
            ].copy()

            selection_method = "fallback"

        # -------------------------------------------------
        # Handle cases where no product qualifies
        # -------------------------------------------------

        if options.empty:

            recommendations.append({

                "risk_type": risk,

                "status": "No suitable product found",

                "message": (
                    "Available coverage limits are below "
                    "the declared stock value."
                )

            })

            continue

        # -------------------------------------------------
        # Rank qualifying products
        # -------------------------------------------------

        options["coverage_gap"] = (
            options[limit_column] - stock_value
        )

        options = options.sort_values(
            ["coverage_gap", "premium_kes_pa"]
        ).head(top_n)

        # -------------------------------------------------
        # Generate individual product recommendations
        # -------------------------------------------------

        for _, product in options.iterrows():

            annual_premium = float(
                product["premium_kes_pa"]
            )

            monthly_equivalent = annual_premium / 12

            coverage_limit = float(
                product[limit_column]
            )

            recommendations.append({

                "risk_type": risk,

                "product_id": product["product_id"],

                "product_name": product["plan_name"],

                "annual_premium_kes": annual_premium,

                "monthly_premium_equivalent_kes": round(
                    monthly_equivalent,
                    2
                ),

                "coverage_limit_kes": coverage_limit,

                "stock_value_kes": stock_value,

                "coverage_gap_kes": float(
                    product["coverage_gap"]
                ),

                "affordability_status": (

                    "Within stated WTP"

                    if monthly_equivalent <= monthly_wtp

                    else "Above stated WTP"

                ),

                "monthly_wtp_kes": monthly_wtp,

                "selection_method": selection_method

            })

    # =====================================================
    # 5. RETURN COMPLETE RECOMMENDATION RESULTS
    # =====================================================

    return {
    "cluster": cluster,

    "payment_recommendation": payment_recommendation,

    "recommendations": recommendations
}
