
from fastapi import FastAPI, Request, Query
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import Optional
import asyncio
from src.shopify import get_variant_and_token, check_card

# ── Pydantic models for Swagger docs ──────────────────────────────────────────

class CheckRequest(BaseModel):
    site: str = Field(
        ...,
        example="https://example-shopify-store.myshopify.com",
        description="Full URL of the Shopify store you want to check against."
    )
    cc: str = Field(
        ...,
        example="4111111111111111|12|26|123",
        description="Card details in the format: **CARD_NUMBER|MM|YY|CVV**"
    )
    proxy: Optional[str] = Field(
        None,
        example="http://user:pass@1.2.3.4:8080",
        description=(
            "*(Optional)* Proxy to route this request through. "
            "Format: `http://user:pass@ip:port` or `http://ip:port`. "
            "If omitted, a random proxy from `proxies.txt` is used (if available)."
        )
    )

class CheckResponse(BaseModel):
    status: str = Field(example="success")
    result: Optional[str] = Field(
        None,
        example="AMOUNT: $9.99\nRESULT: CARD_DECLINED"
    )
    message: Optional[str] = Field(None, example="Missing required parameters")


# ── App definition ─────────────────────────────────────────────────────────────

description = """
## Auto-Shopify Gateway Checker API

This API automates the **full Shopify checkout flow** to verify a credit card against any live Shopify store.

---

### How It Works

1. **Product Discovery** — Scrapes the target store and finds the first available product automatically.
2. **Cart & Session** — Adds the product to the cart and initiates a real checkout session.
3. **Card Tokenisation** — Sends the card details to Shopify's PCI-compliant vault (`checkout.pci.shopifyinc.com`) to generate a secure session token.
4. **GraphQL Checkout** — Uses Shopify's internal `SubmitForCompletion` mutation to attempt the payment.
5. **Result Polling** — Polls the receipt and returns the bank/gateway response.

---

### Card Format

All card data must be passed as a single string in this format:

```
CARD_NUMBER|MM|YY|CVV
```

Example: `4111111111111111|12|26|123`

---

### Proxy Support

You can pass a proxy per-request via the `proxy` parameter:

```
http://user:pass@ip:port
```

If omitted, a random proxy from `proxies.txt` is used (if available).

---

### Possible Results

| Result | Meaning |
|---|---|
| `ORDER_PLACED` | Card is **live** — transaction succeeded |
| `CARD_DECLINED` | Card was declined by the bank |
| `INSUFFICIENT_FUNDS` | Card has no available balance |
| `3DS_REQUIRED` | Card requires 3D Secure authentication |
| `INVALID_CVC` | Wrong CVV provided |
| `INCORRECT_NUMBER` | Card number is invalid |
| `FRAUD_SUSPECTED` | Gateway flagged the transaction as fraud |
| `MISMATCHED_BILLING` | Billing address mismatch |
| `GENERIC_ERROR` | Unknown gateway error |

---
"""

app = FastAPI(
    title="Auto-Shopify Gateway",
    description=description,
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url="/openapi.json",
    contact={
        "name": "Schweis Projects",
        "url": "https://t.me/nativezpay",
    },
)


# ── Custom black & white Swagger UI ───────────────────────────────────────────

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
  <title>Auto-Shopify Gateway — Docs</title>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
  <style>
    *, *::before, *::after { box-sizing: border-box; }

    html, body {
      background: #000 !important;
      color: #fff !important;
      font-family: 'Segoe UI', system-ui, sans-serif;
      margin: 0; padding: 0;
    }

    /* ── Topbar ── */
    .swagger-ui .topbar { display: none !important; }

    /* ── All backgrounds ── */
    .swagger-ui,
    .swagger-ui .wrapper,
    .swagger-ui .info,
    .swagger-ui .scheme-container,
    .swagger-ui .opblock-tag-section,
    .swagger-ui .no-margin { background: #000 !important; }

    /* ── Kill every link colour (cyan/teal) ── */
    .swagger-ui a,
    .swagger-ui a:link,
    .swagger-ui a:visited,
    .swagger-ui a:hover,
    .swagger-ui a:active,
    .swagger-ui .info a,
    .swagger-ui .info__contact a,
    .swagger-ui .info__license a { color: #fff !important; text-decoration: none !important; border-bottom: 1px solid #444 !important; }

    /* ── Kill the OAS / version badges ── */
    .swagger-ui .info .title small,
    .swagger-ui .info .title small.version-stamp,
    .swagger-ui .info .title small pre,
    .swagger-ui span.version,
    .swagger-ui .version-stamp,
    .swagger-ui .version-pragma { background: #222 !important; color: #aaa !important; border: 1px solid #444 !important; border-radius: 4px !important; }
    /* OAS 3.1 green badge */
    .swagger-ui .info .title small.version-stamp { background: #111 !important; color: #888 !important; }

    /* ── All text white/grey ── */
    .swagger-ui .info h1,
    .swagger-ui .info h2,
    .swagger-ui .info h3,
    .swagger-ui .info h4,
    .swagger-ui .info h5,
    .swagger-ui .info p,
    .swagger-ui .info li,
    .swagger-ui .info td,
    .swagger-ui .info th,
    .swagger-ui .info .title,
    .swagger-ui .info .base-url,
    .swagger-ui .renderedMarkdown p,
    .swagger-ui .renderedMarkdown li,
    .swagger-ui .renderedMarkdown h1,
    .swagger-ui .renderedMarkdown h2,
    .swagger-ui .renderedMarkdown h3,
    .swagger-ui label,
    .swagger-ui .parameter__name,
    .swagger-ui .parameter__type,
    .swagger-ui .parameter__deprecated,
    .swagger-ui .parameter__in,
    .swagger-ui .parameter__default,
    .swagger-ui table thead tr th,
    .swagger-ui table tbody tr td,
    .swagger-ui .col_header,
    .swagger-ui .response-col_status,
    .swagger-ui .response-col_description,
    .swagger-ui .response-col_links,
    .swagger-ui .responses-inner h4,
    .swagger-ui .responses-inner h5,
    .swagger-ui .opblock-description-wrapper p,
    .swagger-ui .opblock-external-docs-wrapper,
    .swagger-ui .opblock-title_normal,
    .swagger-ui section.models h4,
    .swagger-ui section.models h5,
    .swagger-ui .model-title,
    .swagger-ui .model,
    .swagger-ui .model span,
    .swagger-ui .model .property,
    .swagger-ui .prop-type,
    .swagger-ui .prop-format,
    .swagger-ui .prop-name,
    .swagger-ui .markdown p,
    .swagger-ui .markdown li { color: #ddd !important; }

    /* ── Info title big ── */
    .swagger-ui .info .title {
      font-size: 1.8rem !important;
      font-weight: 700 !important;
      color: #fff !important;
      letter-spacing: -0.5px;
    }

    /* ── Base URL pill ── */
    .swagger-ui .info .base-url { color: #777 !important; }

    /* ── Markdown description ── */
    .swagger-ui .info .renderedMarkdown { color: #bbb !important; }
    .swagger-ui .renderedMarkdown h3 { color: #fff !important; font-size: 1rem !important; font-weight: 600 !important; margin: 16px 0 8px !important; border-bottom: 1px solid #222 !important; padding-bottom: 4px !important; }
    .swagger-ui .renderedMarkdown hr { border-color: #1e1e1e !important; }
    .swagger-ui .renderedMarkdown code {
      background: #161616 !important;
      color: #fff !important;
      padding: 2px 7px;
      border-radius: 4px;
      border: 1px solid #2a2a2a;
      font-size: 0.85em;
    }
    .swagger-ui .renderedMarkdown pre {
      background: #111 !important;
      padding: 14px 16px;
      border-radius: 6px;
      border: 1px solid #2a2a2a;
      color: #eee !important;
      overflow-x: auto;
    }
    .swagger-ui .renderedMarkdown pre code { background: transparent !important; border: none !important; padding: 0 !important; }
    .swagger-ui .renderedMarkdown table { border-collapse: collapse; width: 100%; margin: 10px 0; }
    .swagger-ui .renderedMarkdown table td,
    .swagger-ui .renderedMarkdown table th { border: 1px solid #2a2a2a !important; padding: 8px 12px; color: #ccc !important; }
    .swagger-ui .renderedMarkdown table th { background: #0f0f0f !important; color: #fff !important; font-weight: 600 !important; }
    .swagger-ui .renderedMarkdown table tr:nth-child(even) td { background: #0a0a0a !important; }

    /* ── Scheme container ── */
    .swagger-ui .scheme-container { padding: 10px 0 !important; box-shadow: none !important; border-bottom: 1px solid #1e1e1e !important; }

    /* ── Operation blocks ── */
    .swagger-ui .opblock {
      background: #0a0a0a !important;
      border: 1px solid #2a2a2a !important;
      border-radius: 8px !important;
      margin-bottom: 10px !important;
      box-shadow: none !important;
    }
    .swagger-ui .opblock.is-open { border-color: #444 !important; }
    .swagger-ui .opblock-summary {
      background: #0f0f0f !important;
      border-radius: 7px !important;
      padding: 8px 12px !important;
    }
    .swagger-ui .opblock-summary:hover { background: #151515 !important; }
    .swagger-ui .opblock-summary-path,
    .swagger-ui .opblock-summary-path__deprecated { color: #fff !important; font-weight: 600 !important; font-size: 0.95rem !important; }
    .swagger-ui .opblock-summary-description { color: #888 !important; font-size: 0.85rem !important; }
    .swagger-ui .opblock-summary-path-description-wrapper { gap: 8px; }
    .swagger-ui .opblock-body { background: #060606 !important; border-radius: 0 0 7px 7px !important; }
    .swagger-ui .opblock-section-header { background: #0a0a0a !important; border-bottom: 1px solid #1e1e1e !important; }
    .swagger-ui .opblock-section-header h4 { color: #fff !important; }
    .swagger-ui .opblock-section-header label { color: #aaa !important; }

    /* ── Method badges ── */
    .swagger-ui .opblock-summary-method {
      border-radius: 4px !important;
      font-weight: 700 !important;
      font-size: 0.75rem !important;
      min-width: 62px !important;
      text-align: center !important;
      letter-spacing: 0.5px !important;
    }
    .swagger-ui .opblock.opblock-get .opblock-summary-method { background: #fff !important; color: #000 !important; }
    .swagger-ui .opblock.opblock-post .opblock-summary-method { background: #333 !important; color: #fff !important; border: 1px solid #555 !important; }
    .swagger-ui .opblock.opblock-put .opblock-summary-method { background: #222 !important; color: #fff !important; }
    .swagger-ui .opblock.opblock-delete .opblock-summary-method { background: #1a0000 !important; color: #ff6b6b !important; border: 1px solid #400 !important; }
    .swagger-ui .opblock.opblock-get { border-left: 3px solid #fff !important; }
    .swagger-ui .opblock.opblock-post { border-left: 3px solid #555 !important; }

    /* ── Tags ── */
    .swagger-ui .opblock-tag {
      color: #fff !important;
      font-size: 1.05rem !important;
      font-weight: 600 !important;
      border-bottom: 1px solid #1e1e1e !important;
      padding: 10px 0 !important;
    }
    .swagger-ui .opblock-tag:hover { background: transparent !important; }
    .swagger-ui .opblock-tag svg { fill: #fff !important; }

    /* ── Buttons ── */
    .swagger-ui .btn {
      background: #fff !important;
      color: #000 !important;
      border: 1px solid #fff !important;
      border-radius: 5px !important;
      font-weight: 600 !important;
      font-size: 0.82rem !important;
      box-shadow: none !important;
      transition: background 0.15s;
    }
    .swagger-ui .btn:hover { background: #ddd !important; color: #000 !important; }
    .swagger-ui .btn.execute {
      background: #000 !important;
      color: #fff !important;
      border: 1px solid #fff !important;
    }
    .swagger-ui .btn.execute:hover { background: #1a1a1a !important; }
    .swagger-ui .btn.cancel {
      background: #0a0a0a !important;
      color: #ccc !important;
      border: 1px solid #444 !important;
    }
    .swagger-ui .btn.cancel:hover { background: #1a1a1a !important; }
    .swagger-ui .btn.try-out__btn { background: #0a0a0a !important; color: #fff !important; border: 1px solid #555 !important; }
    .swagger-ui .btn.try-out__btn:hover { background: #1a1a1a !important; }
    .swagger-ui .btn.authorize { background: #000 !important; color: #fff !important; border: 1px solid #fff !important; }

    /* ── Inputs / Textareas ── */
    .swagger-ui input[type=text],
    .swagger-ui input[type=password],
    .swagger-ui input[type=search],
    .swagger-ui input[type=email],
    .swagger-ui textarea,
    .swagger-ui select {
      background: #111 !important;
      color: #fff !important;
      border: 1px solid #333 !important;
      border-radius: 5px !important;
      outline: none !important;
    }
    .swagger-ui input::placeholder, .swagger-ui textarea::placeholder { color: #555 !important; }
    .swagger-ui input:focus, .swagger-ui textarea:focus { border-color: #666 !important; }
    .swagger-ui select option { background: #111 !important; color: #fff !important; }

    /* ── Parameter rows ── */
    .swagger-ui .parameter-item { border-bottom: 1px solid #1a1a1a !important; }
    .swagger-ui .parameter__name.required span { color: #ff6b6b !important; }
    .swagger-ui .parameter__name.required::after { color: #ff6b6b !important; }

    /* ── Response area ── */
    .swagger-ui .responses-wrapper { background: #060606 !important; }
    .swagger-ui .responses-table { background: #060606 !important; }
    .swagger-ui .responses-table tbody tr { background: #0a0a0a !important; border-bottom: 1px solid #1a1a1a !important; }
    .swagger-ui .highlight-code,
    .swagger-ui .highlight-code > pre,
    .swagger-ui .microlight {
      background: #0d0d0d !important;
      color: #e0e0e0 !important;
    }
    .swagger-ui .curl-command { background: #0a0a0a !important; border: 1px solid #222 !important; border-radius: 5px !important; }
    .swagger-ui .curl-command .copy-to-clipboard { background: #222 !important; border: 1px solid #444 !important; }
    .swagger-ui .response-col_status { color: #fff !important; font-weight: 600 !important; }
    .swagger-ui .live-responses-table .response { background: #0a0a0a !important; }
    .swagger-ui .request-url { background: #0a0a0a !important; border: 1px solid #222 !important; border-radius: 5px !important; }
    .swagger-ui .request-url pre { color: #ddd !important; }

    /* ── Models section ── */
    .swagger-ui section.models {
      background: #0a0a0a !important;
      border: 1px solid #2a2a2a !important;
      border-radius: 8px !important;
      margin-top: 16px !important;
    }
    .swagger-ui section.models h4 { color: #fff !important; font-size: 1rem !important; font-weight: 600 !important; }
    .swagger-ui section.models h4 svg { fill: #fff !important; }
    .swagger-ui .model-container { background: #111 !important; border-radius: 5px !important; border: 1px solid #222 !important; margin: 6px !important; }
    .swagger-ui .model-box { background: #111 !important; }
    .swagger-ui .model { color: #ccc !important; }
    .swagger-ui .model-toggle::after { background: #fff !important; }
    .swagger-ui .prop-type { color: #aaa !important; }

    /* ── Arrows / SVG icons ── */
    .swagger-ui svg { fill: #fff !important; }
    .swagger-ui .expand-operation svg,
    .swagger-ui .arrow { filter: invert(1) !important; }

    /* ── Authorization lock ── */
    .swagger-ui .authorization__btn { background: transparent !important; border: none !important; }
    .swagger-ui .authorization__btn svg { fill: #fff !important; }

    /* ── Info contact/license ── */
    .swagger-ui .info__contact, .swagger-ui .info__license { margin-top: 8px !important; }

    /* ── Example value box ── */
    .swagger-ui .example { background: #0d0d0d !important; border: 1px solid #222 !important; border-radius: 5px !important; color: #ddd !important; }
    .swagger-ui .model-example { background: #0d0d0d !important; }
    .swagger-ui .tab li { color: #aaa !important; }
    .swagger-ui .tab li.active { color: #fff !important; border-bottom: 2px solid #fff !important; }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: #000; }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #555; }
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    window.onload = function () {
      SwaggerUIBundle({
        url: "/openapi.json",
        dom_id: '#swagger-ui',
        presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
        layout: "BaseLayout",
        deepLinking: true,
        defaultModelsExpandDepth: 1,
        defaultModelExpandDepth: 1,
        displayRequestDuration: true,
        tryItOutEnabled: true,
        syntaxHighlight: { activated: true, theme: "monokai" },
      });
    };
  </script>
</body>
</html>
""")


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Status"], summary="Health Check")
async def root():
    """Returns the current status of the API."""
    return {"status": "OK", "message": "Shopify Gate API working."}


@app.post(
    "/check",
    tags=["Checker"],
    summary="Check Card (POST)",
    response_model=CheckResponse,
)
async def check_card_post(data: CheckRequest):
    """
    Runs the **full Shopify checkout flow** to verify a credit card.

    - Discovers a product on the target store automatically.
    - Tokenises the card with Shopify's PCI vault.
    - Submits a real payment via Shopify's GraphQL checkout API.
    - Returns the bank/gateway response (e.g. `ORDER_PLACED`, `CARD_DECLINED`).
    """
    try:
        result = await check_card(
            data.site, data.cc.split("|")[0], data.cc.split("|")[1],
            data.cc.split("|")[2], data.cc.split("|")[3], data.proxy
        )
        return {"status": "success", "result": result}
    except (ValueError, IndexError):
        return {"status": "error", "message": "Invalid CC format. Use card|mm|yy|cvv"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get(
    "/check",
    tags=["Checker"],
    summary="Check Card (GET)",
    response_model=CheckResponse,
)
async def check_card_get(
    site: str = Query(..., examples=["https://example-shopify-store.myshopify.com"], description="Full URL of the Shopify store."),
    cc: str = Query(..., examples=["4111111111111111|12|26|123"], description="Card in format: `CARD|MM|YY|CVV`"),
    proxy: Optional[str] = Query(None, examples=["http://user:pass@1.2.3.4:8080"], description="*(Optional)* Proxy URL to route through.")
):
    """
    Runs the **full Shopify checkout flow** to verify a credit card via GET request.

    Pass all parameters in the URL query string.  
    Handy for quick testing directly from the browser or a simple HTTP client.
    """
    try:
        cc_number, cc_month, cc_year, cc_cvv = cc.split("|")
    except ValueError:
        return {"status": "error", "message": "Invalid CC format. Use card|mm|yy|cvv"}

    try:
        result = await check_card(site, cc_number, cc_month, cc_year, cc_cvv, proxy)
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}
