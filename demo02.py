import os

import tensorflow as tf

from seq2seq.configs.config import FLAGS
from seq2seq.lib import data_utils
from seq2seq.lib.seq2seq_model_utils import create_model, get_predicted_sentence

import jieba

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.httpclient as httpclient

import simplejson as json

import logging

brain = None


class Brain:

    def __init__(self):
        jieba.set_dictionary("/usr/share/hisarack-wikipedia/dict.txt.big")
        # Create model and load parameters.
        self.sess = tf.Session()
        self.model = create_model(self.sess, forward_only=True)
        self.model.batch_size = 1  # We decode one sentence at a time.

        # Load vocabularies.
        vocab_path = os.path.join(FLAGS.data_dir, "vocab%d.in" % FLAGS.vocab_size)
        self.vocab, self.rev_vocab = data_utils.initialize_vocabulary(vocab_path)

    def _tokenize_then_join(self, sentence):
        tokens = jieba.cut(sentence, cut_all=False)
        tokens = filter(None, [token.strip() for token in tokens])
        sentence = ' '.join(tokens).encode('utf8')
        return sentence

    def think(self, msg):
        # Decode from standard input.
        sentence = self._tokenize_then_join(msg)
        predicted_sentence = get_predicted_sentence(
            sentence,
            self.vocab,
            self.rev_vocab,
            self.model,
            self.sess
        )
        return predicted_sentence


class MainHandler(tornado.web.RequestHandler):

    def _send_msg(self, who, msg):

        def handle_request(response):
            print response

        headers = {
            'Content-Type': 'application/json; charser=UTF-8',
            'X-Line-ChannelID': '',
            'X-Line-ChannelSecret': '',
            'X-Line-Trusted-User-With-ACL': ''
        }

        data = {
            'to': [who],
            'toChannel': 1383378250,
            'eventType': '138311608800106203',
            'content': {
                'contentType': 1,
                'toType': 1,
                'text': msg
            }
        }

        http_client = httpclient.AsyncHTTPClient()
        http_request = httpclient.HTTPRequest(
            'https://trialbot-api.line.me/v1/events',
            'POST',
            headers,
            body=json.dumps(data)
        )
        http_client.fetch(http_request, handle_request)

    def get(self):
        self.write("Hello world")

    def post(self):
        obj = json.loads(self.request.body)
        msg = obj['result'][0]['content']['text']
        who = obj['result'][0]['content']['from']
        logging.error(msg)
        global brain
        bot_msg = brain.think(msg)
        logging.error(bot_msg)
        self._send_msg(who, bot_msg)
        self.write("Hello bot callback")


application = tornado.web.Application([
    (r"/", MainHandler),
])


def run():
    http_server = tornado.httpserver.HTTPServer(application, ssl_options={
        "certfile": "",
        "keyfile": ""
    })
    http_server.listen(8443)
    tornado.ioloop.IOLoop.instance().start()


def main(_):
    global brain
    brain = Brain()
    run()

if __name__ == "__main__":
    tf.app.run()
