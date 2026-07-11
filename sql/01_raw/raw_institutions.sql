-- Layer: RAW
-- Source: FFIEC HMDA "filers" API -- the lender/institution reference list
-- for a given state+year (LEI -> institution name). This is the second
-- table in the multi-table join story: loan record x lender reference.
--   https://ffiec.cfpb.gov/documentation/api/data-browser/#hmda-filers
select
    lei,
    name as lender_name,
    count as loan_count_reported,
    period as activity_year
from read_csv_auto('__SOURCE_CSV__', all_varchar=true)
