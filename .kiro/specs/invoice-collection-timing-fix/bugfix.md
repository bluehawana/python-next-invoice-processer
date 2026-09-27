# Bugfix Requirements Document

## Introduction

The invoice collection system currently filters emails based on invoice period dates found in email subject lines (e.g., "May 4-10" or "April 23-30"). This approach misses invoices where:
- Work was performed in late May but the payout arrived in early June
- Partners have varying payout schedules (weekly, bi-weekly, monthly) that span month boundaries
- The invoice period is in one month but the payout date is in another

This causes incomplete accounting records for monthly reconciliation. For Swedish restaurant accounting (Ichiban Sushi), income must be recorded when money is actually received in the bank account (payout date), not when the work was performed (invoice period).

**Example Missing Invoices for May 2026:**
- Stripe: 630.90 SEK (work in May, paid early June)
- Uber: 228.80, 667.55, 677.55 SEK (weekly payouts spanning May-June)
- Foodora: 9667.82 SEK (last week of May, paid in June)

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN searching for May invoices THEN the system uses date criteria like "SINCE 4/15 BEFORE 6/15" combined with subject line date filtering

1.2 WHEN an Uber weekly summary has subject "4/27/26–5/10/26" THEN the system filters it by the period start date (4/27) and may exclude it from May results

1.3 WHEN a Foodora invoice covers "April 23-30" but was paid May 1 THEN the system excludes it from May collection because the period is in April

1.4 WHEN a Stripe payout covers work from late May but arrived in early June THEN the system may miss it when collecting May invoices

1.5 WHEN a Wolt payout_report covers "May 16–June 1" THEN the system filters based on whether the period dates match the target month, potentially excluding cross-month payouts

1.6 WHEN partner payout schedules vary (weekly vs bi-weekly vs monthly) THEN the system inconsistently captures invoices because it relies on invoice period rather than payout arrival date

### Expected Behavior (Correct)

2.1 WHEN searching for May invoices THEN the system SHALL collect all invoices where the payout arrived in May (email received date between May 1-31), regardless of the work period in the subject line

2.2 WHEN an Uber weekly summary has subject "4/27/26–5/10/26" THEN the system SHALL include it in May results if the email was received in May

2.3 WHEN a Foodora invoice covers "April 23-30" but was paid May 1 THEN the system SHALL include it in May collection because the payout arrived in May

2.4 WHEN a Stripe payout covers work from late May but arrived in early June THEN the system SHALL include it in June collection based on when the payout arrived

2.5 WHEN a Wolt payout_report covers "May 16–June 1" THEN the system SHALL include it based on the email received date, not the period dates

2.6 WHEN collecting invoices for a specific month THEN the system SHALL use email received date as the primary criterion, matching when money actually arrived in the bank account

### Unchanged Behavior (Regression Prevention)

3.1 WHEN emails contain PDF attachments THEN the system SHALL CONTINUE TO download and save those PDFs

3.2 WHEN processing Wolt emails THEN the system SHALL CONTINUE TO skip sales_report and main fee invoice PDFs, only downloading payout_report PDFs

3.3 WHEN processing Uber emails without PDF attachments THEN the system SHALL CONTINUE TO generate PDFs from the HTML email body

3.4 WHEN filtering emails from specific senders THEN the system SHALL CONTINUE TO use sender-based filters (e.g., "restaurants.sweden@uber.com" for Uber, "Foodora" in subject)

3.5 WHEN downloading invoices THEN the system SHALL CONTINUE TO prepend partner tags to filenames for reconciliation purposes

3.6 WHEN the search window extends beyond month boundaries (2 weeks before/after) THEN the system SHALL CONTINUE TO use an extended search window, but filter results by email received date

3.7 WHEN deduplicating emails THEN the system SHALL CONTINUE TO track processed email IDs to avoid downloading the same invoice multiple times
