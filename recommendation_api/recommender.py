
import joblib
import pandas as pd
import numpy as np
from pathlib import Path

# Locate the project directory
BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = BASE_DIR / "models" / "recover_model_bundle.pkl"

# Load saved model bundle
bundle = joblib.load(MODEL_PATH)

preprocessor = bundle["preprocessor"]
kmeans = bundle["kmeans"]

feature_columns = bundle["feature_columns"]

cluster_product_preferences = bundle["cluster_product_preferences"]

products = bundle["products"]


def convert_to_bool(value):
    if isinstance(value, (bool, np.bool_)):
        return bool(value)

    if isinstance(value, str):
        return value.strip().lower() in ["true", "yes", "1", "y"]

    return bool(value)




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

    if preferred_frequency == "pay_at_restock":
        reason = "The trader prefers paying when restocking inventory."

    elif preferred_frequency == "daily":
        reason = "Daily payments match the trader's stated preference."

    elif preferred_frequency == "weekly":
        reason = "Weekly payments match the trader's stated preference."

    elif preferred_frequency == "monthly":
        reason = "Monthly payments match the trader's stated preference."

    else:
        reason = "The payment preference needs further review."

    return {
        "recommended_frequency": preferred_frequency,
        "reason": reason,
        "income_receipt_pattern": income_pattern,
        "income_variability": variability,
        "restock_cycle_days": restock_days,
        "basis": "trader_stated_preference",
        "insurer_confirmation_required": True
    }


def recommend_products(trader_data, top_n=3):

    # Prepare trader information
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

    # Apply saved preprocessing pipeline
    transformed_data = preprocessor.transform(trader_df)

    # Assign trader to a cluster
    cluster = int(kmeans.predict(transformed_data)[0])

    # Retrieve preferred products for the cluster
    preferred_products = cluster_product_preferences[cluster]

    stock_value = float(trader_data["stock_value_kes"])
    monthly_wtp = float(trader_data["wtp_monthly_kes"])
    payment_recommendation = recommend_payment_frequency(trader_data)

    recommendations = []

    risk_columns = {
        "fire": "fire_limit_kes",
        "burglary": "burglary_limit_kes"
    }

    risk_interest = {
        "fire": "wants_cover_fire",
        "burglary": "wants_cover_theft"
    }

    for risk, limit_column in risk_columns.items():

        if not convert_to_bool(trader_data[risk_interest[risk]]):
            continue

        # First consider cluster-preferred products
        options = products[
            products["plan_name"].isin(preferred_products)
        ].copy()

        options[limit_column] = pd.to_numeric(
            options[limit_column], errors="coerce"
        )

        options["premium_kes_pa"] = pd.to_numeric(
            options["premium_kes_pa"], errors="coerce"
        )

        options = options[
            options[limit_column] >= stock_value
        ].copy()

        selection_method = "cluster_preferred"

        # Fallback to all available products if necessary
        if options.empty:

            options = products.copy()

            options[limit_column] = pd.to_numeric(
                options[limit_column], errors="coerce"
            )

            options["premium_kes_pa"] = pd.to_numeric(
                options["premium_kes_pa"], errors="coerce"
            )

            options = options[
                options[limit_column] >= stock_value
            ].copy()

            selection_method = "fallback"

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

        # Rank qualifying products
        options["coverage_gap"] = (
            options[limit_column] - stock_value
        )

        options = options.sort_values(
            ["coverage_gap", "premium_kes_pa"]
        ).head(top_n)

        for _, product in options.iterrows():

            monthly_equivalent = (
                product["premium_kes_pa"] / 12
            )

            recommendations.append({

                "risk_type": risk,

                "product_id": product["product_id"],

                "product_name": product["plan_name"],

                "annual_premium_kes": float(
                    product["premium_kes_pa"]
                ),

                "monthly_premium_equivalent_kes": round(
                    monthly_equivalent, 2
                ),

                "coverage_limit_kes": float(
                    product[limit_column]
                ),

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

    return {
    "cluster": cluster,
    "cluster_preferred_products": preferred_products,
    "payment_recommendation": payment_recommendation,
    "recommendations": recommendations
}
