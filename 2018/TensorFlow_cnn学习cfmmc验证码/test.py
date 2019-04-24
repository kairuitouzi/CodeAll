
"""
测试模型的准确性
"""
#################################### 测试一，本测试文件需与保存的模型放在同一个文件夹 ##########################################
from PIL import Image
import numpy as np
import tensorflow as tf
import os
import sys
os.environ['TF_CPP_MIN_LOG_LEVEL']='2'
import random
import string
STR = string.printable[:62]

IMAGE_HEIGHT = 25
IMAGE_WIDTH = 96
MAX_CAPTCHA = 6
CHAR_SET_LEN = 62  # 有多少种可能的字符
try:
    _path = sys.argv[1] + '\\' # r'D:\tools\Tools\August_2018\2018-8-31\CaptchaGenerator-master\new_capt\\'
except:
    _path = r'D:\tools\Tools\EveryDay\demo\2018-9\生成cfmmc验证码\mycaptchas\\'
all_image = os.listdir(_path)
random.shuffle(all_image)
all_image = [i for i in all_image[:2100] if '.jpg' in i]

def get_name_and_image(n=0):

    base = os.path.basename(_path + all_image[n])
    name = os.path.splitext(base)[0]
    image = Image.open(_path + all_image[n])
    image = image.convert('L') # 灰度化
    image = np.array(image)
    return name, image


def name2vec(name):
    vector = np.zeros(MAX_CAPTCHA*CHAR_SET_LEN)
    for i, c in enumerate(name):
        idx = i*62+STR.index(c)
        vector[idx] = 1
    return vector


def vec2name(vec):
    name = []
    for i in vec:
        a = STR[i]
        name.append(a)
    return "".join(name)


# 生成一个训练batch
def get_next_batch(batch_size=64):
    batch_x = np.zeros([batch_size, IMAGE_HEIGHT*IMAGE_WIDTH])
    batch_y = np.zeros([batch_size, MAX_CAPTCHA*CHAR_SET_LEN])

    for i in range(batch_size):
        name, image = get_name_and_image()
        batch_x[i, :] = 1*(image.flatten())
        batch_y[i, :] = name2vec(name)
    return batch_x, batch_y

#########################

X = tf.placeholder(tf.float32, [None, IMAGE_HEIGHT*IMAGE_WIDTH])
Y = tf.placeholder(tf.float32, [None, MAX_CAPTCHA*CHAR_SET_LEN])
keep_prob = tf.placeholder(tf.float32)



# 定义CNN
def crack_captcha_cnn(w_alpha=0.01, b_alpha=0.1):
    x = tf.reshape(X, shape=[-1, IMAGE_HEIGHT, IMAGE_WIDTH, 1])
    # 3 conv layer
    w_c1 = tf.Variable(w_alpha * tf.random_normal([5, 5, 1, 32]))
    b_c1 = tf.Variable(b_alpha * tf.random_normal([32]))
    conv1 = tf.nn.relu(tf.nn.bias_add(tf.nn.conv2d(x, w_c1, strides=[1, 1, 1, 1], padding='SAME'), b_c1))
    conv1 = tf.nn.max_pool(conv1, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')
    conv1 = tf.nn.dropout(conv1, keep_prob)

    w_c2 = tf.Variable(w_alpha * tf.random_normal([5, 5, 32, 64]))
    b_c2 = tf.Variable(b_alpha * tf.random_normal([64]))
    conv2 = tf.nn.relu(tf.nn.bias_add(tf.nn.conv2d(conv1, w_c2, strides=[1, 1, 1, 1], padding='SAME'), b_c2))
    conv2 = tf.nn.max_pool(conv2, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')
    conv2 = tf.nn.dropout(conv2, keep_prob)

    w_c3 = tf.Variable(w_alpha * tf.random_normal([5, 5, 64, 64]))
    b_c3 = tf.Variable(b_alpha * tf.random_normal([64]))
    conv3 = tf.nn.relu(tf.nn.bias_add(tf.nn.conv2d(conv2, w_c3, strides=[1, 1, 1, 1], padding='SAME'), b_c3))
    conv3 = tf.nn.max_pool(conv3, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')
    conv3 = tf.nn.dropout(conv3, keep_prob)

    # Fully connected layer
    w_d = tf.Variable(w_alpha * tf.random_normal([4 * 12 * 64, 1024]))
    b_d = tf.Variable(b_alpha * tf.random_normal([1024]))
    dense = tf.reshape(conv3, [-1, w_d.get_shape().as_list()[0]])
    dense = tf.nn.relu(tf.add(tf.matmul(dense, w_d), b_d))
    dense = tf.nn.dropout(dense, keep_prob)

    w_out = tf.Variable(w_alpha * tf.random_normal([1024, MAX_CAPTCHA * CHAR_SET_LEN]))
    b_out = tf.Variable(b_alpha * tf.random_normal([MAX_CAPTCHA * CHAR_SET_LEN]))
    out = tf.add(tf.matmul(dense, w_out), b_out)
    return out




def crack_captcha():
    output = crack_captcha_cnn()

    saver = tf.train.Saver()
    counts = 0
    with tf.Session() as sess:
        saver.restore(sess, tf.train.latest_checkpoint('.'))
        n = 1
        while n <= 50:
            text, image = get_name_and_image(n)
            image = 1 * (image.flatten())
            predict = tf.argmax(tf.reshape(output, [-1, MAX_CAPTCHA, CHAR_SET_LEN]), 2)
            text_list = sess.run(predict, feed_dict={X: [image], keep_prob: 1})
            vec = text_list[0].tolist()
            predict_text = vec2name(vec)
            counts += 1 if text[:6].upper()==predict_text.upper() else 0
            print("正确: {}  预测: {}".format(text, predict_text),counts)
            n += 1

# 测试指定文件夹，里面的50张验证码，需提前把验证码的文件名改为结果字符
crack_captcha()





##################################### 测试二 ############################################
   
from PIL import Image
import numpy as np
import tensorflow as tf
import os
import sys
# os.environ['TF_CPP_MIN_LOG_LEVEL']='2'
import random
import string
import requests
import io




class Captcha:
    def __init__(self):
        self.IMAGE_HEIGHT = 25
        self.IMAGE_WIDTH = 96
        self.MAX_CAPTCHA = 6
        self.CHAR_SET_LEN = 62  # 有多少种可能的字符
        self.keep_prob = tf.placeholder(tf.float32)
        self.X = tf.placeholder(tf.float32, [None, self.IMAGE_HEIGHT * self.IMAGE_WIDTH])
        self.Y = tf.placeholder(tf.float32, [None, self.MAX_CAPTCHA * self.CHAR_SET_LEN])
    def get_name_and_image(self, img_path):
        image = Image.open(img_path)
        image = image.convert('L')  # 灰度化
        image = np.array(image)
        return image

    def vec2name(self, vec):
        name = []
        STR = string.printable[:62]
        for i in vec:
            a = STR[i]
            name.append(a)
        return "".join(name)


    # 定义CNN
    def crack_captcha_cnn(self,w_alpha=0.01, b_alpha=0.1):
        IMAGE_HEIGHT = self.IMAGE_HEIGHT
        IMAGE_WIDTH = self.IMAGE_WIDTH
        MAX_CAPTCHA = self.MAX_CAPTCHA
        CHAR_SET_LEN = self.CHAR_SET_LEN
        keep_prob = self.keep_prob
        X = self.X
        Y = self.Y
        x = tf.reshape(X, shape=[-1, IMAGE_HEIGHT, IMAGE_WIDTH, 1])
        # 3 conv layer
        w_c1 = tf.Variable(w_alpha * tf.random_normal([5, 5, 1, 32]))
        b_c1 = tf.Variable(b_alpha * tf.random_normal([32]))
        conv1 = tf.nn.relu(tf.nn.bias_add(tf.nn.conv2d(x, w_c1, strides=[1, 1, 1, 1], padding='SAME'), b_c1))
        conv1 = tf.nn.max_pool(conv1, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')
        conv1 = tf.nn.dropout(conv1, keep_prob)

        w_c2 = tf.Variable(w_alpha * tf.random_normal([5, 5, 32, 64]))
        b_c2 = tf.Variable(b_alpha * tf.random_normal([64]))
        conv2 = tf.nn.relu(tf.nn.bias_add(tf.nn.conv2d(conv1, w_c2, strides=[1, 1, 1, 1], padding='SAME'), b_c2))
        conv2 = tf.nn.max_pool(conv2, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')
        conv2 = tf.nn.dropout(conv2, keep_prob)

        w_c3 = tf.Variable(w_alpha * tf.random_normal([5, 5, 64, 64]))
        b_c3 = tf.Variable(b_alpha * tf.random_normal([64]))
        conv3 = tf.nn.relu(tf.nn.bias_add(tf.nn.conv2d(conv2, w_c3, strides=[1, 1, 1, 1], padding='SAME'), b_c3))
        conv3 = tf.nn.max_pool(conv3, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')
        conv3 = tf.nn.dropout(conv3, keep_prob)

        # Fully connected layer
        w_d = tf.Variable(w_alpha * tf.random_normal([4 * 12 * 64, 1024]))
        b_d = tf.Variable(b_alpha * tf.random_normal([1024]))
        dense = tf.reshape(conv3, [-1, w_d.get_shape().as_list()[0]])
        dense = tf.nn.relu(tf.add(tf.matmul(dense, w_d), b_d))
        dense = tf.nn.dropout(dense, keep_prob)

        w_out = tf.Variable(w_alpha * tf.random_normal([1024, MAX_CAPTCHA * CHAR_SET_LEN]))
        b_out = tf.Variable(b_alpha * tf.random_normal([MAX_CAPTCHA * CHAR_SET_LEN]))
        out = tf.add(tf.matmul(dense, w_out), b_out)
        return out

    def crack_captcha(self,model_path):

        keep_prob = self.keep_prob
        output = self.crack_captcha_cnn()
        X = self.X
        saver = tf.train.Saver()
        img_path = ''
        predict_text = ''
        with tf.Session() as sess:
            saver.restore(sess, tf.train.latest_checkpoint(model_path))
            while 1:
                img_path = yield predict_text
                image = self.get_name_and_image(img_path)
                image = 1 * (image.flatten())
                predict = tf.argmax(tf.reshape(output, [-1, self.MAX_CAPTCHA, self.CHAR_SET_LEN]), 2)
                text_list = sess.run(predict, feed_dict={X: [image], keep_prob: 1})
                vec = text_list[0].tolist()
                predict_text = self.vec2name(vec)
            # print("预测({}): {}".format(vec, predict_text))
        return predict_text

    

def test():
    d=requests.get('https://investorservice.cfmmc.com/veriCode.do?t=1536022886480').content
    d=io.BytesIO(d)
    print(ca.send(d))
    img=Image.open(d)
    img.show()


#      可以动态测试验证码 使用方法：
#      capt = Captcha()
#      ca = capt.crack_captcha(model_fold)  # 测试为保存模型的文件夹
#      ca.send(None)
#      test()
##############################################################################