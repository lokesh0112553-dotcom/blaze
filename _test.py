import asyncio
import sys
sys.path.insert(0, '.')
from src.shopify import check_card

async def test():
    result = await check_card(
        'https://keithdotson.com/pages/privacy-policy',
        '4403934654807846', '06', '28', '683',
        '175.29.133.8:5433:799JRELTBPAE:F7BQ7D3EQSQA'
    )
    print('RESULT:', result)

asyncio.run(test())

asyncio.run(test())

