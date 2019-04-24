# import random
# import numpy as np
# from PIL import Image


# def initTable(_jpg):
# 	""" 二值化 """
# 	im=Image.open(_jpg)
# 	x,y = im.size
# 	for i in range(x):
# 		for j in range(y):
# 			r,g,b=im.getpixel((i,j))
# 			if b-g>3 and b-r>3:
# 				r,g,b = 0,0,0
# 		    	im.putpixel((i,j),(r,g,b,0))
# 	return im.convert('L')

# def get_name_and_image():
# 	path = r'D:\tools\Tools\August_2018\2018-8-31\CaptchaGenerator-master\mycaptchas'
# 	all_image = os.listdir(path)
# 	random_file = random.randint(0,30000)
# 	name = all_image[random_file][:6]
# 	image = Image.open(path+'\\'+all_image[random_file])
# 	image = np.array(image)
# 	return name,image

# def name2vec(name):
# 	zer = len(name)*6
# 	vector = np.zeros(zer)
# 	for i,c in enumerate(name):
# 		idx = i*26+ord(c) - 97
# 		vector[idx] = 1
# 	return vector

# def vec2name(vecs):
# 	name = []
# 	for i in vecs:
# 		a = chr(i+97)
# 		name.append(a)
# 	return "".join(name)


# 文章链接：https://www.jianshu.com/p/26ff7b9075a1

"""
使用生成的验证码训练模型
模型按准确率保存在文件夹saved_model、7、8、9、95、highest
"""

from PIL import Image
import numpy as np
import tensorflow as tf
import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import random
import string
import datetime

STR = string.printable[:62]

IMAGE_HEIGHT = 25
IMAGE_WIDTH = 96
MAX_CAPTCHA = 6
CHAR_SET_LEN = 62  # 有多少种可能的字符

_path = r'D:\tools\Tools\EveryDay\demo\2018-9\生成cfmmc验证码\mycaptchas\\'
all_image = os.listdir(_path)
random.shuffle(all_image)
all_image = [i for i in all_image if '.jpg' in i]


def get_name_and_image():
    random_file = random.randint(0, 40000)
    base = os.path.basename(_path + all_image[random_file])
    name = os.path.splitext(base)[0]
    image = Image.open(_path + all_image[random_file])
    image = np.array(image.convert('L'))
    return name, image


def name2vec(name):
    vector = np.zeros(MAX_CAPTCHA * CHAR_SET_LEN)
    for i, c in enumerate(name):
        idx = i * 62 + STR.index(c)
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
    batch_x = np.zeros([batch_size, IMAGE_HEIGHT * IMAGE_WIDTH])
    batch_y = np.zeros([batch_size, MAX_CAPTCHA * CHAR_SET_LEN])

    for i in range(batch_size):
        name, image = get_name_and_image()
        batch_x[i, :] = 1 * (image.flatten())
        batch_y[i, :] = name2vec(name)
    return batch_x, batch_y


####################################################

X = tf.placeholder(tf.float32, [None, IMAGE_HEIGHT * IMAGE_WIDTH])
Y = tf.placeholder(tf.float32, [None, MAX_CAPTCHA * CHAR_SET_LEN])
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


mymodels = None


# 训练
def train_crack_captcha_cnn():
    global mymodels
    output = crack_captcha_cnn()
    loss = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=output, labels=Y))
    optimizer = tf.train.AdamOptimizer(learning_rate=0.001).minimize(loss)

    predict = tf.reshape(output, [-1, MAX_CAPTCHA, CHAR_SET_LEN])
    max_idx_p = tf.argmax(predict, 2)
    max_idx_l = tf.argmax(tf.reshape(Y, [-1, MAX_CAPTCHA, CHAR_SET_LEN]), 2)
    correct_pred = tf.equal(max_idx_p, max_idx_l)
    accuracy = tf.reduce_mean(tf.cast(correct_pred, tf.float32))

    saver = tf.train.Saver()
    _accs = 0
    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())

        step = 0
        _keep_prob = 0.7
        while True:
            batch_x, batch_y = get_next_batch(64)
            _, loss_ = sess.run([optimizer, loss], feed_dict={X: batch_x, Y: batch_y, keep_prob: _keep_prob})
            # print(step, loss_)

            # 每100 step计算一次准确率
            if step % 100 == 0:
                batch_x_test, batch_y_test = get_next_batch(100)
                acc = sess.run(accuracy, feed_dict={X: batch_x_test, Y: batch_y_test, keep_prob: 1.})
                print(step, loss_, acc, datetime.datetime.now())
                # 如果准确率大于50%,保存模型,完成训练
                if acc > 0.9 and acc > _accs:
                    _accs = acc
                    try:
                        for rmv in os.listdir('saved_model_highest'):
                            os.remove('saved_model_highest\\' + rmv)
                        saver.save(sess, "saved_model_highest\\crack_capcha.ckpt", global_step=step)
                    except Exception as exc:
                        print(exc)

                if acc > 0.99:
                    saver.save(sess, "saved_model\\crack_capcha.ckpt", global_step=step)
                    break
                elif acc > 0.95:
                    mymodels = sess
                    if not os.listdir('saved_model95'):
                        try:
                            saver.save(sess, "saved_model95\\crack_capcha95.ckpt", global_step=step)
                        except Exception as exc:
                            print(exc)
                elif acc > 0.91:
                    mymodels = sess
                    if not os.listdir('saved_model9'):
                        try:
                            saver.save(sess, "saved_model9\\crack_capcha91.ckpt", global_step=step)
                        except Exception as exc:
                            print(exc)
                elif acc > 0.81:
                    mymodels = sess
                    if not os.listdir('saved_model8'):
                        try:
                            saver.save(sess, "saved_model8\\crack_capcha81.ckpt", global_step=step)
                        except Exception as exc:
                            print(exc)
                elif acc > 0.71:
                    mymodels = sess
                    if not os.listdir('saved_model7'):
                        try:
                            saver.save(sess, "saved_model7\\crack_capcha71.ckpt", global_step=step)
                        except Exception as exc:
                            print(exc)

            step += 1
            _keep_prob = _keep_prob * 0.9 if not step % 10000 and step < 38000 else _keep_prob




# 训练完成后#掉train_crack_captcha_cnn()，取消下面的注释，开始预测，注意更改预测集目录

# def crack_captcha():
#     output = crack_captcha_cnn()
#
#     saver = tf.train.Saver()
#     with tf.Session() as sess:
#         saver.restore(sess, tf.train.latest_checkpoint('.'))
#         n = 1
#         while n <= 10:
#             text, image = get_name_and_image()
#             image = 1 * (image.flatten())
#             predict = tf.argmax(tf.reshape(output, [-1, MAX_CAPTCHA, CHAR_SET_LEN]), 2)
#             text_list = sess.run(predict, feed_dict={X: [image], keep_prob: 1})
#             vec = text_list[0].tolist()
#             predict_text = vec2name(vec)
#             print("正确: {}  预测: {}".format(text, predict_text))
#             n += 1
#
# crack_captcha()


if __name__ == '__main__':
	train_crack_captcha_cnn()