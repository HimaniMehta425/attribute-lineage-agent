-- Layer: STAGING
-- Source: raw_hmda_loans
--
-- Casts every numeric field, treating the sentinel strings "Exempt" and "NA"
-- as NULL, and assigns a synthetic surrogate key (the public HMDA extract has
-- no loan-level id) so downstream attribute models can join back cleanly.
select
    row_number() over () as loan_id,
    cast(activity_year as integer) as activity_year,
    lei,
    state_code,
    county_code,
    census_tract,
    derived_loan_product_type as loan_product_type,
    derived_dwelling_category as dwelling_category,
    derived_ethnicity as ethnicity,
    derived_race as race,
    derived_sex as sex,
    cast(action_taken as integer) as action_taken,
    cast(loan_type as integer) as loan_type,
    cast(loan_purpose as integer) as loan_purpose,
    cast(lien_status as integer) as lien_status,
    try_cast(loan_amount as double) as loan_amount,
    try_cast(nullif(nullif(loan_to_value_ratio, 'Exempt'), 'NA') as double) as loan_to_value_ratio,
    try_cast(nullif(nullif(interest_rate, 'Exempt'), 'NA') as double) as interest_rate,
    try_cast(nullif(nullif(rate_spread, 'Exempt'), 'NA') as double) as rate_spread,
    try_cast(hoepa_status as integer) as hoepa_status,
    try_cast(nullif(loan_term, 'Exempt') as integer) as loan_term,
    try_cast(nullif(property_value, 'Exempt') as double) as property_value,
    try_cast(occupancy_type as integer) as occupancy_type,
    total_units,
    try_cast(nullif(income, 'NA') as double) as income_thousands,
    debt_to_income_ratio as debt_to_income_ratio_raw,
    applicant_age,
    applicant_credit_score_type,
    try_cast(tract_population as double) as tract_population,
    try_cast(tract_minority_population_percent as double) as tract_minority_population_percent,
    try_cast(ffiec_msa_md_median_family_income as double) as msa_median_family_income,
    try_cast(tract_to_msa_income_percentage as double) as tract_to_msa_income_percentage,
    try_cast(tract_owner_occupied_units as double) as tract_owner_occupied_units
from raw_hmda_loans
