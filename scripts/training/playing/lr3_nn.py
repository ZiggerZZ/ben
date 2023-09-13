import sys
import numpy as np
import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()
import os
import logging

# Set logging level to suppress warnings
logging.getLogger().setLevel(logging.ERROR)
# Just disables the warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'


from batcher import Batcher

model_path = './lr3_simple_model/lr3_simple'

seed = 1337

batch_size = 64
n_iterations = 1000000
display_step = 10000

X_train = np.load('./lr3_bin/X.npy')
y_train = np.load('./lr3_bin/y.npy')

n_examples = X_train.shape[0]
n_ftrs = X_train.shape[1]
n_tricks = y_train.shape[1]


n_hidden_units = 512


keep_prob = tf.placeholder(tf.float32, name='keep_prob')

X = tf.placeholder(tf.float32, [None, n_ftrs], 'X')
y = tf.placeholder(tf.float32, [None, n_tricks], 'y')

w1 = tf.get_variable('w1', shape=[n_ftrs, n_hidden_units], dtype=tf.float32, initializer=tf.compat.v1.initializers.glorot_uniform(seed=seed))
z1 = tf.matmul(X, w1)
a1 = tf.nn.dropout(tf.nn.relu(z1), keep_prob=keep_prob)

w2 = tf.get_variable('w2', shape=[n_hidden_units, n_hidden_units], dtype=tf.float32, initializer=tf.compat.v1.initializers.glorot_uniform(seed=seed))
z2 = tf.matmul(a1, w2)
a2 = tf.nn.dropout(tf.nn.relu(z2), keep_prob=keep_prob)

w3 = tf.get_variable('w3', shape=[n_hidden_units, n_hidden_units], dtype=tf.float32, initializer=tf.compat.v1.initializers.glorot_uniform(seed=seed))
z3 = tf.matmul(a2, w3)
a3 = tf.nn.dropout(tf.nn.relu(z3), keep_prob=keep_prob)

w4 = tf.get_variable('w4', shape=[n_hidden_units, n_hidden_units], dtype=tf.float32, initializer=tf.compat.v1.initializers.glorot_uniform(seed=seed))
z4 = tf.matmul(a3, w4)
a4 = tf.nn.dropout(tf.nn.relu(z4), keep_prob=keep_prob)

w_out = tf.get_variable('w_out', shape=[n_hidden_units, 14], dtype=tf.float32, initializer=tf.compat.v1.initializers.glorot_uniform(seed=seed))
tricks_logit = tf.matmul(a4, w_out, name='tricks_logit')
tricks_softmax = tf.nn.softmax(tricks_logit, name='tricks_softmax')

#import pdb; pdb.set_trace()

cost = tf.losses.softmax_cross_entropy(y, tricks_logit)


learning_rate = tf.placeholder(tf.float32, name='learning_rate')

train_step = tf.train.AdamOptimizer(learning_rate).minimize(cost)


batch = Batcher(n_examples, batch_size)
cost_batch = Batcher(n_examples, 10000)

with tf.Session() as sess:
    sess.run(tf.global_variables_initializer())

    saver = tf.train.Saver(max_to_keep=50)

    for i in range(n_iterations):
        x_batch, y_batch = batch.next_batch([X_train, y_train])
        if i % display_step == 0:
            x_cost, y_cost = cost_batch.next_batch([X_train, y_train])
            c_train = sess.run(cost, feed_dict={X: x_cost, y: y_cost, keep_prob: 1.0})
            t_train = sess.run(tricks_softmax, feed_dict={X: x_cost, y: y_cost, keep_prob: 1.0})
            #import pdb; pdb.set_trace()
            print('{}. c_train={}'.format(i, c_train))
            print(np.mean(np.argmax(t_train, axis=1) == np.argmax(y_cost, axis=1)))
            print(np.mean(np.abs(np.argmax(t_train, axis=1) - np.argmax(y_cost, axis=1)) > 1))
            print(np.mean(np.abs(np.argmax(t_train, axis=1) - np.argmax(y_cost, axis=1))))
            
            sys.stdout.flush()

            saver.save(sess, model_path, global_step=i)
        
        sess.run(train_step, feed_dict={X: x_batch, y: y_batch, keep_prob: 0.6, learning_rate: 0.001 / (2**(i/5e5))})

    saver.save(sess, model_path, global_step=n_iterations)