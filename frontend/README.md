# Rental Portal (React + TypeScript, served by Frappe at /portal)

Backend = existing `equip_rental` app. Portal reads via Frappe REST/permissions; create/submit/cancel and
Dispatch/JCR/Return mapping call existing doctype logic. Only new Python: `equip_rental/portal_api.py` (read-only).

## Install (from the app repo root, e.g. ~/frappe-bench-v16/apps/equip_rental)
    cp portal_api.py equip_rental/portal_api.py
    mkdir -p equip_rental/www/portal && cp www_portal/* equip_rental/www/portal/
    cd frontend && npm install && npm run build      # outputs to equip_rental/public/portal
    cd ~/frappe-bench-v16 && bench --site equip-rental.localhost clear-cache && bench build --app equip_rental
Open http://equip-rental.localhost:8002/portal
Rebuild with `npm run build` after any frontend change. (`npm run dev` proxies /api but POSTs may fail CSRF; test on the built page.)

## Pages
#/dashboard · #/sales-orders · #/dispatch · #/returns (outstanding qty) · #/return-notes · #/jcr · #/doc/<DocType>/<name> (detail, related docs, timeline, actions) · #/profile
