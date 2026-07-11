-- Layer: RAW
-- Source: FFIEC/CFPB HMDA Data Browser API (public, unauthenticated)
--   https://ffiec.cfpb.gov/documentation/api/data-browser/
-- Loaded from: data/sample/hmda_il_sample.csv (or data/raw/hmda_*.csv for a full pull)
--
-- Raw layer does no cleaning -- everything is loaded as VARCHAR on purpose.
-- HMDA data mixes true nulls, the literal string "NA", and the literal string
-- "Exempt" (a filer legally declined to report the field) inside otherwise
-- numeric columns. Casting happens explicitly in staging so that decision is
-- visible and traceable rather than silently baked into the CSV load.
select
    activity_year,
    lei,
    state_code,
    county_code,
    census_tract,
    derived_loan_product_type,
    derived_dwelling_category,
    derived_ethnicity,
    derived_race,
    derived_sex,
    action_taken,
    loan_type,
    loan_purpose,
    lien_status,
    loan_amount,
    loan_to_value_ratio,
    interest_rate,
    rate_spread,
    hoepa_status,
    loan_term,
    property_value,
    occupancy_type,
    total_units,
    income,
    debt_to_income_ratio,
    applicant_age,
    applicant_credit_score_type,
    tract_population,
    tract_minority_population_percent,
    ffiec_msa_md_median_family_income,
    tract_to_msa_income_percentage,
    tract_owner_occupied_units
from read_csv_auto('__SOURCE_CSV__', all_varchar=true)
