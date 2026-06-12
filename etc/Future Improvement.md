# Future Improvements

## 1) GA4 and SERanking Data Alignment

Current issue

-   GA4 queries always use the GNA Korea GA4 property for development, due to privacy concerns and the lack of client-specific credentials configured in production.
    
-   SERanking already supports per-client selection, but GA4 does not, so the two data sources can be misaligned.
    

Goal

-   Allow selecting a client and consistently fetching both GA4 and SERanking data for that client.
    

Proposed approach

-   Configuration design:
    
    -   Add a client registry (JSON/DB) that maps each client to:
        
        -   GA4 property_id (or data stream ID as needed)
            
        -   SERanking site_id
            
    -   Keep client-level secrets/tokens out of the repository (instance/ or external secret store).
        
-   Backend changes:
    
    -   Extend GA4 endpoints to accept client_id and resolve to the client’s GA4 property_id.
        
    -   Validate access based on the authenticated user and allowed clients (optional, future).
        
-   Frontend changes:
    
    -   Client dropdown becomes the single source of truth for both GA4 and SERanking requests.
        
    -   When the client changes, both data sources are refreshed using the mapped identifiers.
        

Implementation notes

-   Store the development GA4 property in .env for fallback only (DEV_GA4_PROPERTY_ID).
    
-   For production, prefer per-client mapping (clients.json/DB), e.g.:  
    {  
    "acme": {"ga4_property_id": "properties/123", "seranking_site_id": 456},  
    "globex": {"ga4_property_id": "properties/789", "seranking_site_id": 1011}  
    }
    
-   Consider a feature flag (GA4_MULTI_TENANT=true) to switch from single GA4 to per-client GA4.
    

Risks and mitigations

-   Privacy: do not log raw GA4 identifiers; ensure access controls if multi-tenant.
    
-   Operational: clearly document how to add a new client and rotate credentials.
    

----------

## 2) PDF Output and Layout Modernization

Current issue

-   To maximize compatibility on cPanel, HTML→PDF uses table-based layout and older engines; modern CSS (flex/grid) is not fully honored.
    
-   Text overlay on images is constrained; current workaround generates cover/back-cover images with Pillow and then injects them into HTML.
    

Goals

-   Improve typographic and layout fidelity.
    
-   Keep deployment constraints in mind (shared hosting; limited OS packages).
    

Short-term improvements (within current stack)

-   Continue generating text-on-image covers via Pillow, but:
    
    -   Control size and DPI explicitly (see section 4 for scaling).
        
    -   Pre-generate high-resolution images that match the target PDF page size.
        
-   Fine-tune xhtml2pdf HTML/CSS:
    
    -   Use simple, print-friendly CSS (floats/block layout) and avoid unsupported features.
        
    -   Embed fonts (Noto Sans EN/KR/SC) and ensure correct font-face declarations for multilingual text.
        

Mid-term options

-   Switch to WeasyPrint only if cPanel packages (cairo, pango, gdk-pixbuf) can be installed and maintained.
    
-   Consider a serverless or job-queue based rendering microservice (e.g., headless Chromium/Puppeteer) if hosting constraints allow, to unlock modern CSS.
    
-   Introduce a “print theme” HTML template that prioritizes flow/pagination over interactivity.
    

Operational notes

-   Keep font licensing and embedding compliant.
    
-   Measure performance and memory usage on cPanel (image generation and PDF conversion can be resource-intensive).
    

----------

## 3) Security Posture and Hardening

Current approach

-   Authentication: stateless JWT, issued after WordPress login (WP is the identity provider).
    
-   CSRF: mitigated by sending the token via Authorization header instead of cookies.
    
-   Transport: HTTPS via cPanel; file isolation and basic firewalling handled by hosting.
    
-   XSS: Jinja2 auto-escaping on the backend; client-side risk if innerHTML is used.
    

Gaps and improvements

-   XSS hardening:
    
    -   Minimize innerHTML usage; prefer textContent and DOM APIs.
        
    -   Sanitize any necessary HTML input with a library (e.g., DOMPurify).
        
    -   Consider a Content Security Policy (CSP) with strict defaults (nonce for inline scripts, disallow unsafe-inline).
        
-   Dependency and secret management:
    
    -   Pin dependency versions (requirements.txt) and schedule updates.
        
    -   Keep .env, client_secret.json, credentials.json under instance/ or a private path with restricted permissions.
        
-   2FA strategy:
    
    -   This project delegates 2FA to WordPress; clearly document that effective 2FA depends on the WP site’s policy.
        
    -   If needed later, add a “step-up auth required” flag for sensitive operations and verify 2FA status via WP API (if available).
        
-   Logging and monitoring:
    
    -   Centralize logs; avoid writing secrets/PII to logs.
        
    -   Add rate-limiting on sensitive endpoints (login callback, token refresh) to reduce brute-force or abuse risk.
        

Optional future

-   Introduce a per-client access control list to prevent cross-tenant data access.
    
-   Add signed URLs or short-lived tokens for downloading generated PDFs.
    

----------

## 4) Date Range Defaults (Calendar Logic)

Current issue

-   Default date range is “last 30 days,” which does not align exactly with calendar months (28/30/31 days).
    

Goal

-   Default to “last full month” or “same day last month” semantics (e.g., Aug 1–Sep 1 yields precisely one month).
    

Proposed behavior

-   If the user opens the dashboard without a selection:
    
    -   Default start_date = first day of the previous month.
        
    -   Default end_date = first day of the current month.
        
-   If “one month from selected start” is desired:
    
    -   Compute end_date by adding 1 calendar month and clamping to month boundaries (handle Feb/31-day months).
        

Implementation notes

-   Implement a small date utility:
    
    -   add_months(date, n): handle month overflow; if the target month has fewer days, clamp to the last day.
        
    -   Helpers for first_day_of_month and first_day_of_next_month.
        
-   Apply the same logic consistently to both GA4 and SERanking queries to keep comparisons coherent.
    

----------

## 5) Cover and Back Cover Image Scaling

Current issue

-   Source images are smaller than the PDF page (A3 landscape), resulting in undersized visuals when rendered.
    

Goal

-   Render cover/back-cover images at the correct size, with crisp text overlays.
    

Recommendations

-   Use target pixel dimensions that match the PDF page at chosen DPI:
    
    -   A3 landscape: 420mm×297mm → at 300 DPI ≈ 4961×3508px (or 2480×1754px at 150 DPI).
        
-   Pillow generation:
    
    -   Create the base image with the target pixel dimensions and explicitly set DPI metadata.
        
    -   Render text with font sizes calculated for the chosen DPI; center and margin guides should be derived from the target resolution.
        
-   In HTML→PDF:
    
    -   Avoid further scaling; set the image size to 100% of the page container.
        
    -   Ensure CSS/engine does not downsample; prefer using the exact image size and print CSS units (mm/in) where supported.
        

Operational tip

-   Keep a single constants module for PAGE_WIDTH_PX, PAGE_HEIGHT_PX, and DPI to avoid mismatches.
    
-   Batch-generate cover/back-cover assets and cache them if the same design is reused.
    

----------

## Appendix: Quick Tasks Checklist

-   Data alignment
    
    -   Implement client mapping (GA4 property_id + SERanking site_id).
        
    -   Update endpoints and UI to pass client_id and resolve identifiers server-side.
        
-   PDF/layout
    
    -   Standardize high-DPI Pillow images for covers; refine xhtml2pdf template for print.
        
-   Security
    
    -   Remove/replace innerHTML where possible; integrate DOMPurify if needed.
        
    -   Add CSP and dependency pinning; document 2FA delegation to WP.
        
-   Calendar defaults
    
    -   Replace “last 30 days” with calendar-aware month logic.
        
-   Image scaling
    
    -   Adopt A3 landscape target sizes; generate images at the correct DPI with Pillow.