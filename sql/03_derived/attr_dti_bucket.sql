-- Layer: DERIVED ATTRIBUTE
-- Source: stg_loans
-- New attribute: dti_bucket -- HMDA reports debt-to-income as EITHER an exact
-- percentage ("49") OR a pre-bucketed range string ("30%-<36%") depending on
-- the filer, with no documented rule for which one a given row will use.
-- This model normalizes both formats into one consistent set of categories.
select
    loan_id,
    debt_to_income_ratio_raw,
    case
        when debt_to_income_ratio_raw is null or debt_to_income_ratio_raw = 'NA' then null
        when debt_to_income_ratio_raw like '%<%' or debt_to_income_ratio_raw like '%-%' then debt_to_income_ratio_raw
        when try_cast(debt_to_income_ratio_raw as double) < 20 then '<20%'
        when try_cast(debt_to_income_ratio_raw as double) < 30 then '20%-<30%'
        when try_cast(debt_to_income_ratio_raw as double) < 36 then '30%-<36%'
        when try_cast(debt_to_income_ratio_raw as double) < 43 then '36%-<43%'
        when try_cast(debt_to_income_ratio_raw as double) < 50 then '43%-<50%'
        else '50%+'
    end as dti_bucket
from stg_loans
