import asyncio
import aiohttp
import pendulum
from collections import defaultdict
from config import STORE_URL, TOKEN, CHANNEL


# We can't use backslash in f-strings
newline = '\n'
# Translate order gateways
gateway = defaultdict(lambda: "Other", {"sell-on-amazon": "Amazon", "web": "Shopify", "shopify_draft_order": "manual order"})


async def slack_api_call(method, data=None, token=TOKEN):
    with aiohttp.ClientSession() as session:
        form = aiohttp.FormData(data or {})
        form.add_field('token', token)
        async with session.post(f'https://slack.com/api/{method}', data=form) as response:
            assert response.status == 200, (f'{method} with {data} failed.')
            return await response.json()


async def get_orders(client, params=None):
    endpoint = f'{STORE_URL}/orders.json'
    async with client.get(endpoint, params=params) as resp:
        return await resp.json()


async def main(loop):
    timestamp = pendulum.now().to_atom_string()
    params = {'status': 'any', 'since_id': '1'}
    async with aiohttp.ClientSession(loop=loop) as client:
        # Avoid reprocessing orders when starting service.
        last_order = await get_orders(client, params={'limit': '1', 'status': 'any', 'fields': 'id'})
        params['since_id'] = last_order['orders'][0]['id']
        while True:
            orders = await get_orders(client, params=params)
            try:
                if len(orders['orders']) > 0:
                    params['since_id'] = orders['orders'][0]['id']
                for order in orders['orders']:
                    # TODO: Shorter lines
                    message = '\n>'.join([f'New order placed at {order["created_at"]} via {gateway[order["source_name"]]}',
                                         f'Name: {order["customer"]["default_address"]["first_name"]} {order["customer"]["default_address"]["last_name"]}',
                                         f'Location: {order["customer"]["default_address"]["city"]}, {order["customer"]["default_address"]["province"]} - {order["customer"]["default_address"]["country"]}',
                                         f'Amount: {order["total_price_usd"]}',
                                         f'Items: {f", {newline}>".join(" ".join(("`", str(item["quantity"]), item["name"], "`")) for item in order["line_items"])}',
                                         ])
                    await slack_api_call('chat.postMessage',
                                         {'channel': CHANNEL, 'text': message})
                await asyncio.sleep(60)
            except:
                print("Error ocurred in processing order notification.")


loop = asyncio.get_event_loop()
loop.run_until_complete(main(loop))
