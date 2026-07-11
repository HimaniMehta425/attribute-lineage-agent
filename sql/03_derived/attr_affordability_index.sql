-- Layer: DERIVED ATTRIBUTE
-- Source: stg_loans
-- New attributes: loan_to_income_ratio, income_to_area_median_ratio --
-- composite affordability signals not present in the raw extract, combining
-- the applicant's reported income with loan amount and the area (tract/MSA)
-- median family income.
select
    loan_id,
    income_thousands,
    loan_amount,
    msa_median_family_income,
    case when income_thousands > 0 then loan_amount / (income_thousands * 1000) end as loan_to_income_ratio,
    case when msa_median_family_income > 0 then (income_thousands * 1000) / msa_median_family_income end as income_to_area_median_ratio
from stg_loans
