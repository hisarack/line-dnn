import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.httpclient as httpclient

import simplejson as json

import pprint

import logging


class MainHandler(tornado.web.RequestHandler):

    smile_counters = {}

    channel_id = ''
    channel_secret = ''
    channel_access_token = ''

    reply_url = 'https://api.line.me/v2/bot/message/reply'
    push_url = 'https://api.line.me/v2/bot/message/push'

    def _send_text_msg(self, who, reply_token, msg):

        def handle_request(response):
            print(response)

        headers = {
            'Content-Type': 'application/json; charser=UTF-8',
            'Authorization': 'Bearer {}'.format(MainHandler.channel_access_token)
        }

        data = {
            'replyToken': reply_token,
            'messages': [
                {'type': 'text', 'text': msg}
            ]
        }

        http_client = httpclient.AsyncHTTPClient()
        http_request = httpclient.HTTPRequest(
            MainHandler.reply_url,
            'POST',
            headers,
            body=json.dumps(data)
        )
        http_client.fetch(http_request, handle_request)

    def _send_smile_img(self, who):

        def handle_request(response):
            print(response.body)

        headers = {
            'Content-Type': 'application/json; charser=UTF-8',
            'Authorization': 'Bearer {}'.format(MainHandler.channel_access_token)
        }

        logging.error(MainHandler.smile_counters)
        if who not in MainHandler.smile_counters:
            MainHandler.smile_counters[who] = 0
        else:
            MainHandler.smile_counters[who] = MainHandler.smile_counters[who] + 1
            if MainHandler.smile_counters[who] >= 3:
                MainHandler.smile_counters[who] = 0

        imgUrls = [
            'https://i.ytimg.com/vi/BtuQtKIRbQw/maxresdefault.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/d/d2/Siberian_Husky_with_Blue_Eyes.jpg'
        ]

        user_id = ''
        data = {
            'to': user_id,
            'messages': [
                {
                    'type': 'image',
                    'originalContentUrl': imgUrls[MainHandler.smile_counters[who]],
                    'previewImageUrl': imgUrls[MainHandler.smile_counters[who]]
                }
            ]
        }

        http_client = httpclient.AsyncHTTPClient()
        http_request = httpclient.HTTPRequest(
            MainHandler.push_url,
            'POST',
            headers,
            body=json.dumps(data)
        )
        http_client.fetch(http_request, handle_request)

    def _send_sticker(self, who, reply_token, package_id, sticker_id):

        def handle_request(response):
            print(response.body)

        headers = {
            'Content-Type': 'application/json; charser=UTF-8',
            'Authorization': 'Bearer {}'.format(MainHandler.channel_access_token)
        }

        user_id = ''
        data = {
            'to': user_id,
            'messages': [
                {
                    'type': 'sticker',
                    'packageId': package_id,
                    'stickerId': sticker_id
                }
            ]
        }

        http_client = httpclient.AsyncHTTPClient()
        http_request = httpclient.HTTPRequest(
            MainHandler.push_url,
            'POST',
            headers,
            body=json.dumps(data)
        )
        http_client.fetch(http_request, handle_request)

    def post(self):
        obj = json.loads(self.request.body)
        pprint.pprint(obj)

        content_type = obj['events'][0]['message']['type']
        who = obj['events'][0]['source']['userId']
        reply_token = obj['events'][0]['replyToken']

        if content_type == 'text':
            msg = obj['events'][0]['message']['text']
            logging.error(msg)
            if msg == "smile":
                self._send_smile_img(who)
            else:
                bot_msg = msg
                self._send_text_msg(who, reply_token, bot_msg)
        elif content_type == 'sticker':
            package_id = obj['events'][0]['message']['packageId']
            sticker_id = obj['events'][0]['message']['stickerId']
            self._send_sticker(who, reply_token, package_id, sticker_id)

application = tornado.web.Application([
    (r"/", MainHandler),
])

if __name__ == "__main__":
    http_server = tornado.httpserver.HTTPServer(application, ssl_options={
        "certfile": "",
        "keyfile": ""
    })
    http_server.listen(8443)
    tornado.ioloop.IOLoop.instance().start()

