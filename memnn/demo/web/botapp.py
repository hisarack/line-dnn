import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.httpclient as httpclient

import simplejson as json

import logging

import glob
import numpy as np

from demo.qa import MemN2N
from util import parse_babi_task

brain = None


class Brain:

    def __init__(self, data_dir, model_file):
        self.memn2n = MemN2N(data_dir, model_file)
        self.memn2n.load_model()
        self.test_story = None
        self.test_questions = None
        self.test_qstory = None

        print("Reading test data from %s ..." % self.memn2n.data_dir)
        test_data_path = glob.glob('%s/qa[12]_*_test.txt' % self.memn2n.data_dir)
        self.test_story, self.test_questions, self.test_qstory = \
            parse_babi_task(
                test_data_path,
                self.memn2n.general_config.dictionary,
                False
            )

        self.user_story_txt = []
        self.user_story_maxlen = 0

    def think(self, msg):
        """
            story (3-D array)
                [position of word in sentence, sentence index, story index] = index of word in dictionary
            questions (2-D array)
                [0-9, question index], in which the first component is encoded as follows:
                    0 - story index
                    1 - index of the last sentence before the question
                    2 - index of the answer word in dictionary
                    3 to 13 - indices of supporting sentence
                    14 - line index
            qstory (2-D array) question's indices within a story
                [index of word in question, question index] = index of word in dictionary
        """
        dictionary = self.memn2n.general_config.dictionary

        # check user input is question or not
        if '?' not in msg:
            msg = msg.rstrip().lower()
            words = msg.split()
            for word in words:
                if word not in dictionary.keys():
                    logging.error("{} not in dictionary".format(word))
                    return "{}? I don't understand...".format(word)
            self.user_story_txt.append(words)
            if self.user_story_maxlen < len(words):
                self.user_story_maxlen = len(words)
            return "I Got It"

        # transfer words list to mem2n input matrix
        user_story = []
        dictionary = self.memn2n.general_config.dictionary
        for story_txt in self.user_story_txt:
            user_story.append([dictionary[word] for word in story_txt])
        user_story = np.transpose(user_story)
        logging.error(user_story)

        question_idx      = 0
        story_idx         = self.test_questions[0, question_idx]
        last_sentence_idx = self.test_questions[1, question_idx]
        story_txt, question_txt, correct_answer = self.memn2n.get_story_texts(
            self.test_story,
            self.test_questions,
            self.test_qstory,
            question_idx,
            story_idx,
            last_sentence_idx
        )

        logging.error("story context :{}".format(self.user_story_txt))

        pred_answer_idx, pred_prob, memory_probs = self.memn2n.predict_answer_for_bot(
            self.test_story,
            self.test_questions,
            self.test_qstory,
            question_idx,
            story_idx,
            last_sentence_idx,
            user_story,
            msg
        )
        pred_answer = self.memn2n.reversed_dict[pred_answer_idx]
        logging.error("memory_probs : {}".format(memory_probs))
        logging.error("pred_prob : {}".format(pred_prob))
        return pred_answer


def init(data_dir, model_file):
    global brain
    brain = Brain(data_dir, model_file)


class MainHandler(tornado.web.RequestHandler):

    def _send_msg(self, who, msg):

        def handle_request(response):
            print response

        headers = {
            'Content-Type': 'application/json; charser=UTF-8',
            'X-Line-ChannelID': '1469025676',
            'X-Line-ChannelSecret': '4035aef55b1dd5cb0f8bba1cdf0fa9c3',
            'X-Line-Trusted-User-With-ACL': 'u5aec2325897ac0e09fb0ebc3c82b5185'
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
        "certfile": "/etc/letsencrypt/live/hisarack.mooo.com/fullchain.pem",
        "keyfile": "/etc/letsencrypt/live/hisarack.mooo.com/privkey.pem"
    })
    http_server.listen(8443)
    tornado.ioloop.IOLoop.instance().start()

