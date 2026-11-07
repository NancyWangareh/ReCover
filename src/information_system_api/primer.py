from pathlib import Path
from .config import DOCS_DIR

EDUCATIONAL_PRIMER_CONTENT = """=== PAGE 1 ===
RECOVER MICROINSURANCE FOUNDATIONAL EDUCATIONAL PRIMER
Module 1: What is Microinsurance and Risk Pooling?
Microinsurance provides accessible, low-cost insurance protection tailored specifically for low-income individuals and informal business operators, such as market vendors and mitumba traders.
Core Concept: Risk Pooling
Insurance functions as a collective risk-sharing mechanism. Thousands of policyholders contribute small, affordable sums (called premiums) into a shared fund. When an unexpected insured disaster—such as a market fire or burglary—strikes one member, the pooled funds are used to compensate that specific individual.
What a Premium Pays For:
A premium is NOT a savings deposit or a bank balance. It is a non-refundable risk transfer fee that purchases continuous financial protection over a defined period (e.g., one month or one year).

=== PAGE 2 ===
Module 2: Coverage Scope, Grace Periods, and Claims Procedures
Grace Period:
If an informal trader experiences irregular daily cash flow and misses a scheduled premium payment, standard Kenyan microinsurance regulations provide a grace period (typically 15 to 30 days). During this grace period, full coverage remains active. If payment is not settled before the period ends, the policy lapses.
Claims Procedure:
When an insured disaster occurs, follow these required steps:
1. Immediate Notice: Notify the insurer or broker within the specified window (often 24 to 48 hours).
2. Official Incident Report: Obtain an official Kenya Police Abstract form (incident report) confirming the loss event.
3. Proof of Loss: Provide photographs of the damage and commercial inventory records, stock receipts, or sales logs.
4. Formal Claim Form: Complete and submit the insurer's official claim document.

=== PAGE 3 ===
Module 3: Excess (Deductibles), Policy Exclusions, and Regulatory Rights
What is an Excess (Deductible)?
An excess (or deductible) is the first agreed portion of any claim that the policyholder must pay out of pocket before the insurance company pays the remainder.
Standard Exclusions:
Property insurance policies cover specific "named perils" (such as fire, lightning, or forcible burglary). Policies do NOT cover:
- Goods left completely unattended in open-air public alleys overnight.
- Losses caused by deliberate gross negligence or intentional fraud.
- Pre-existing damage occurring prior to policy activation.
Regulatory Protection:
Under the Insurance Regulatory Authority (IRA) of Kenya guidelines, policyholders have statutory rights to fair claims adjudication and transparent dispute resolution procedures.
"""

def ensure_educational_primer() -> Path:
    target_path = DOCS_DIR / "recover_microinsurance_educational_primer.txt"
    if not target_path.exists():
        target_path.write_text(EDUCATIONAL_PRIMER_CONTENT, encoding="utf-8")
    return target_path