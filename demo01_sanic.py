from sanic import Sanic
from sanic.response import json
import simplejson

import uvloop
import asyncio
import aiohttp
import async_timeout

channel_access_token = ''
reply_url = 'https://api.line.me/v2/bot/message/reply'
push_url = 'https://api.line.me/v2/bot/message/push'
headers = {
    'Content-Type': 'application/json; charser=UTF-8',
    'Authorization': 'Bearer {}'.format(channel_access_token)
}

loop = uvloop.new_event_loop()
app = Sanic(__name__)

async def fetch(session, url, data):
    print(reply_url)
    print(headers)
    print(data)
    async with session.post(
        reply_url,
        data=simplejson.dumps(data),
        headers=headers
    ) as response:
        return await response

@app.route("/", methods=['POST'])
async def line(request):
    obj = request.json

    content_type = obj['events'][0]['message']['type']
    who = obj['events'][0]['source']['userId']
    reply_token = obj['events'][0]['replyToken']
    msg = obj['events'][0]['message']['text']
    data = {
        'replyToken': reply_token,
        'messages': [
            {'type': 'text', 'text': msg}
        ]
    }
    async with aiohttp.ClientSession(loop=loop) as session:
        response = await fetch(session, url, data)
        print(response.text())
        return json({'status': 200})

app.run(host='127.0.0.1', port=5566, loop=loop)
