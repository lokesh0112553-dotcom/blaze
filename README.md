<div align="center">

# Auto-Shopify

**Shopify Payment Gateway Checker — REST API**

[![Python](https://img.shields.io/badge/Python%203.12+-111111?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-111111?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Shopify](https://img.shields.io/badge/Shopify-111111?style=for-the-badge&logo=shopify&logoColor=white)](https://shopify.com)
[![License](https://img.shields.io/badge/License-MIT-111111?style=for-the-badge)](LICENSE)

</div>

---

## Overview

Auto-Shopify is a **FastAPI-powered REST API** that performs full end-to-end Shopify payment gateway checks. It automatically discovers a product on any Shopify store, tokenises a card via Shopify's PCI vault, submits a real checkout, and returns the bank/gateway response — all without any manual store setup.

---

## Features

- **Auto product discovery** — works from any page URL (homepage, blog, collections, etc.)
- **Physical & digital product support** — full shipping address flow for physical stores
- **Real gateway responses** — `ORDER_PLACED`, `CARD_DECLINED`, `INSUFFICIENT_FUNDS`, `3DS_REQUIRED`, etc.
- **CAPTCHA bypass** — automatically retries up to 15 times on captcha challenges
- **Proxy support** — per-request proxy or rotating pool via `proxies.txt`
- **Multi-currency** — USD, GBP, EUR, INR and more
- **Interactive Swagger UI** — built-in docs at `/docs`
- **Async** — fully non-blocking with `httpx` + `asyncio`

---

## API Endpoints

### `POST /check`

```json
POST http://localhost:8000/check
Content-Type: application/json

{
  "site": "https://example-store.myshopify.com",
  "cc": "4111111111111111|12|26|123",
  "proxy": "host:port:user:pass"
}
```

### `GET /check`

```
GET http://localhost:8000/check?site=https://example-store.myshopify.com&cc=4111111111111111|12|26|123&proxy=host:port:user:pass
```

### Response

```json
{
  "status": "success",
  "result": "AMOUNT: $29.99\nRESULT: CARD_DECLINED"
}
```

### Result Codes

| Code | Meaning |
|---|---|
| `ORDER_PLACED` | Card charged successfully — order created |
| `CARD_DECLINED` | Card declined by the bank |
| `INSUFFICIENT_FUNDS` | Card has insufficient balance |
| `GENERIC_ERROR` | Gateway generic decline |
| `3DS_REQUIRED` | Card requires 3D Secure authentication |
| `INVALID_CVC` | Wrong CVV/CVC |
| `INCORRECT_CVC` | Incorrect security code |
| `MISMATCHED_BILLING` | Billing address mismatch |
| `MISMATCHED_ZIP` | ZIP/postal code mismatch |
| `FRAUD_SUSPECTED` | Flagged by fraud detection |

---

## Proxy Format

All proxy formats are accepted:

```
host:port:user:pass
host:port
http://user:pass@host:port
socks5://user:pass@host:port
```

For **rotating proxies**, add them one-per-line to `proxies.txt` in the project root. If no proxy is passed in the request, a random one from the file is used.

```
# proxies.txt
pl-tor.pvdata.host:8080:user1:pass1
de-ber.pvdata.host:8080:user2:pass2
```

---

## Local Setup

```bash
# 1. Clone
git clone https://github.com/natiware/Auto-Shopify.git
cd Auto-Shopify

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
uvicorn src.main:app --reload
```

Swagger UI → **http://localhost:8000/docs**

---

## Deployment

### Heroku

```bash
heroku create my-shopify-checker
git push heroku main
heroku ps:scale web=1
```

Python version is set via `runtime.txt` (`python-3.12.8`).

### Render

1. Connect your GitHub repo on [render.com](https://render.com)
2. **Build command:** `pip install -r requirements.txt`
3. **Start command:** `uvicorn src.main:app --host 0.0.0.0 --port $PORT`
4. Or use the included `render.yaml` for one-click deploy

### Railway

```bash
railway init
railway up
```

Railway auto-detects the `Procfile` and `requirements.txt`.

### Docker

```bash
docker build -t auto-shopify .
docker run -p 8000:8000 auto-shopify
```

### VPS / Ubuntu

```bash
pip install -r requirements.txt
gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

Use **nginx** as a reverse proxy for production.

---

## Project Structure

```
Auto-Shopify/
├── src/
│   ├── __init__.py
│   ├── main.py          # FastAPI app, routes, Swagger UI
│   └── shopify.py       # Core checkout engine
├── proxies.txt          # Optional rotating proxy list
├── requirements.txt
├── Procfile             # Heroku / Railway
├── runtime.txt          # Heroku Python version
├── render.yaml          # Render one-click deploy
├── Dockerfile
└── .env.example
```

---

## Contact

<a href="https://t.me/nativezpay" target="_blank">
<img src="https://img.shields.io/badge/Telegram-111111?style=for-the-badge&logo=telegram&logoColor=white"></a>

<a href="https://github.com/natiware" target="_blank">
<img src="https://img.shields.io/badge/GitHub-111111?style=for-the-badge&logo=github&logoColor=white"></a>

---

<div align="center">
<sub>MIT License &copy; 2026 natiware</sub>
</div>


---

### Language and Tools

<img src="https://img.shields.io/badge/Python%20-111111.svg?&style=for-the-badge&logo=Python&logoColor=white">
<img src="https://img.shields.io/badge/FastAPI%20-111111.svg?&style=for-the-badge&logo=FastAPI&logoColor=white">
<img src="https://img.shields.io/badge/Shopify%20-111111.svg?&style=for-the-badge&logo=Shopify&logoColor=white">

---

### Features

Auto Product Discovery • Payment Processing • Multi-Currency • Async

---

### Usage

```bash
# Install
pip install -r requirements.txt

# Run
uvicorn src.main:app --reload
```

```bash
# Check Card
curl "http://localhost:8000/check?site=SITE_URL&cc=CARD|MM|YY|CVV"
```

---

### Contact Information

<a href="https://t.me/nativezpay" target="_blank">
<img src="https://img.shields.io/badge/Telegram%20-111111.svg?&style=for-the-badge&logo=telegram&logoColor=white"></a>

<a href="https://github.com/natiware" target="_blank">
<img src="https://img.shields.io/badge/GitHub%20-111111.svg?&style=for-the-badge&logo=github&logoColor=white"></a>

</div>
