
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from recommender import recommend_products

app = FastAPI(
    title="ReCover Recommendation API",
    description=(
        "A cluster-based microinsurance recommendation "
        "system for Kenyan mitumba traders."
    ),
    version="1.0.0"
)


# Trader information required by the recommendation model
class TraderInput(BaseModel):

    stock_value_kes: float = Field(gt=0)
    total_loss_24m_kes: float = Field(ge=0)
    monthly_income_kes: float = Field(ge=0)
    wtp_monthly_kes: float = Field(ge=0)
    restock_cycle_days: int = Field(gt=0)

    primary_risk_concern: str

    wants_cover_fire: bool
    wants_cover_theft: bool

    income_variability: str
    preferred_premium_frequency: str
    income_receipt_pattern: str


# Home endpoint
@app.get("/")
def home():

    return {
        "project": "ReCover",
        "message": "Microinsurance Recommendation API",
        "status": "running"
    }


# Health-check endpoint
@app.get("/health")
def health():

    return {
        "status": "healthy",
        "service": "ReCover Recommendation API"
    }


# Recommendation endpoint
@app.post("/recommend")
def get_recommendations(trader: TraderInput):

    try:

        trader_data = trader.model_dump()

        result = recommend_products(trader_data)

        return {
            "success": True,
            "message": "Recommendations generated successfully",
            "result": result
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
