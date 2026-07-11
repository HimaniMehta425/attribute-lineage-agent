-- Layer: FACT
-- Sources: stg_loans, stg_institutions, attr_ltv_bucket, attr_dti_bucket,
--          attr_rate_spread_tier, attr_hoepa_flag, attr_high_minority_tract_flag,
--          attr_affordability_index
--
-- The enriched loan fact table: joins the cleaned loan-level staging table
-- against the lender reference table and every derived attribute model.
-- This is the multi-table-join pattern that surfaces 25+ analysis-ready loan
-- attributes for downstream reporting -- exactly the kind of model an
-- attribute-lineage tool needs to be able to explain end-to-end.
select
    l.loan_id,
    l.activity_year,
    l.lei,
    i.lender_name,
    l.state_code,
    l.county_code,
    l.census_tract,
    l.loan_product_type,
    l.dwelling_category,
    l.ethnicity,
    l.race,
    l.sex,
    l.action_taken,
    l.loan_amount,
    l.loan_to_value_ratio,
    ltv.ltv_bucket,
    l.interest_rate,
    l.rate_spread,
    rst.rate_spread_tier,
    hoepa.is_hoepa_high_cost,
    l.loan_term,
    l.property_value,
    l.occupancy_type,
    l.total_units,
    l.income_thousands,
    dti.dti_bucket,
    aff.loan_to_income_ratio,
    aff.income_to_area_median_ratio,
    l.applicant_age,
    l.tract_population,
    l.tract_minority_population_percent,
    minority.is_majority_minority_tract,
    l.msa_median_family_income,
    l.tract_to_msa_income_percentage,
    l.tract_owner_occupied_units
from stg_loans l
left join stg_institutions i on l.lei = i.lei
left join attr_ltv_bucket ltv on l.loan_id = ltv.loan_id
left join attr_rate_spread_tier rst on l.loan_id = rst.loan_id
left join attr_hoepa_flag hoepa on l.loan_id = hoepa.loan_id
left join attr_dti_bucket dti on l.loan_id = dti.loan_id
left join attr_affordability_index aff on l.loan_id = aff.loan_id
left join attr_high_minority_tract_flag minority on l.loan_id = minority.loan_id
