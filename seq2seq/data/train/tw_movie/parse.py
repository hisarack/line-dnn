import jieba

from tensorflow.python.platform import gfile

if __name__ == '__main__':
    jieba.set_dictionary('/usr/share/hisarack-wikipedia/dict.txt.big')
    new_f = gfile.GFile("/usr/share/hisarack-kerkerbot/tf_seq2seq_chatbot/tf_seq2seq_chatbot/data/train/tw_movie/train_tw.txt", "w+")
    with gfile.GFile("/usr/share/hisarack-kerkerbot/tf_seq2seq_chatbot/tf_seq2seq_chatbot/data/train/tw_movie/raw.txt", "r") as f:
        for line in f:
            seq_list = jieba.cut(line, cut_all=False)
            seq_list = filter(None, [seq.strip() for seq in seq_list])
            if len(seq_list) == 0:
                continue
            line = ' '.join(seq_list).encode('utf8')
            new_f.write('{}\n{}\n'.format(line, line))
    new_f.close()
