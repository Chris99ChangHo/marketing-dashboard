# Google Ads Integration — Plan and Direction

## Status

-   Not implemented. The UI shows placeholders, and Ads metrics are manually provided.
    
-   This document captures the future direction; no backend code is enabled at this time.
    

## Why MCC (Manager Account)?

-   Operate under a single Google Ads manager (MCC) account controlled by us.
    
-   Link each client’s Ads account under the MCC, and store only the client’s customer_id.
    
-   Benefits: centralized access control, simpler credential management, consistent reporting queries.
    

## Intended Operating Model

-   Account model: 1 MCC → many client accounts (each with customer_id).
    
-   Data scope: campaign-level KPIs for a selected date range.
    
-   Output shape (normalized):
    
    -   campaigns: [{ name, impression, clicks, cost, interactions, avg_cost }]
        
    -   totals: total_impressions, total_clicks, total_cost, total_interactions, overall_avg_cost
        
    -   meta: location, language, devices, daily_budget (optional, if later expanded)
        

## Planned API (disabled)

-   Method: GET
    
-   Path: /api/google_ads_data
    
-   Auth: JWT required
    
-   Params: customer_id, start_date (YYYY-MM-DD), end_date (YYYY-MM-DD)
    
-   Note: This endpoint is intentionally disabled until MCC setup and credentials are finalized.
    

## Security and Operations

-   Credentials in google-ads.yaml are environment-managed and must never be committed to VCS.
    
-   Enforce a feature flag (ADS_ENABLED=false by default) to prevent accidental activation.
    
-   Before enabling in production, define rate-limit handling and consider caching per client/date-range.
    

## Rollout Roadmap

-   Phase 1: MCC ready, feature flag on per environment, endpoint skeleton returns safe dummy payloads.
    
-   Phase 2: Enable GAQL reads via official client, manage per-client customer_id, add tests/mocks.
    
-   Phase 3: Add caching and optional dimensions (devices/location/language); wire into the PDF pipeline.
    

## What to do now

-   Instruct clients to provide access under our MCC.
    
-   For reporting today, continue manual inputs in the UI; switch to API-driven data after Phase 2.
    

----------

## Concept note (comment-only, non-executable)

```text
/* Concept only (non-executable)
Goal: Use one MCC account; each client provides their customer_id.
Later, the backend will:
  1) Check ADS_ENABLED == true
  2) Read google-ads.yaml (env-managed, not in VCS)
  3) Run a GAQL query for campaign metrics within [start_date, end_date]
  4) Return normalized JSON:
     {
       campaigns: [{ name, impression, clicks, cost, interactions, avg_cost }],
       totals: { total_impressions, total_clicks, total_cost, total_interactions, overall_avg_cost },
       meta: { location, language, devices, daily_budget }
     }
For now: UI values remain manual; no server calls are made.
*/
```