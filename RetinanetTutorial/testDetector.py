# Code adapted from https://github.com/fizyr/keras-retinanet
# jasperebrown@gmail.com
# 2020

# This script loads a single image, runs inferencing on it
# and saves that image back out with detections overalaid.

# You need to set the model_path and image_path below

# import keras
import csv
import keras

# import keras_retinanet
from keras_retinanet import models
from keras_retinanet.utils.image import preprocess_image, resize_image

# import miscellaneous modules
import cv2
import os
import numpy as np
import time
from PIL import Image
import pandas as pd

# set tf backend to allow memory to grow, instead of claiming everything
import tensorflow as tf

model_path = '../Models/logos_inference.h5'
image_paths = ['../Input/' + name for name in os.listdir('../Input')]
image_output_paths = ['../Output/' + name for name in os.listdir('../Input')]
csv_path = "../Output/output.csv"
with open(csv_path, 'w') as csv_file:
    pass
confidence_cutoff = 0.4 #Detections below this confidence will be ignored

def get_session():
    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True
    return tf.Session(config=config)

# use this environment flag to change which GPU to use
#os.environ["CUDA_VISIBLE_DEVICES"] = "1"

# set the modified tf session as backend in keras
#keras.backend.tensorflow_backend.set_session(get_session())

# adjust this to point to your downloaded/trained model
# models can be downloaded here: https://github.com/fizyr/keras-retinanet/releases
#model_path = os.path.join('..', 'snapshots', 'resnet50_coco_best_v2.1.0.h5')
model = models.load_model(model_path, backbone_name='resnet50')

for imageIndex in range(len(image_paths)):
    print("Loading image from {}".format(image_paths[imageIndex]))
    image = np.asarray(Image.open(image_paths[imageIndex]).convert('RGB'))
    image = image[:, :, ::-1].copy()

    # load retinanet model
    print("Loading Model: {}".format(model_path))

    #Check that it's been converted to an inference model

    # load label to names mapping for visualization purposes
    labels_to_names = {
            0: 'nike', 
            1: 'under_armour',
            2: 'adidas'
    }

    # copy to draw on
    draw = image.copy()
    draw = cv2.cvtColor(draw, cv2.COLOR_BGR2RGB)

    # Image formatting specific to Retinanet
    image = preprocess_image(image)
    image, scale = resize_image(image)

    # Run the inference
    start = time.time()

    boxes, scores, labels = model.predict_on_batch(np.expand_dims(image, axis=0))
    print("processing time: ", time.time() - start)

    # correct for image scale
    boxes /= scale

    # visualize detections
    for box, score, label in zip(boxes[0], scores[0], labels[0]):
        # scores are sorted so we can break
        if score < confidence_cutoff:
            break

        #Add boxes and captions
        color = (0, 128, 0)
        thickness = 2
        b = np.array(box).astype(int)
        cv2.rectangle(draw, (b[0], b[1]), (b[2], b[3]), color, thickness, cv2.LINE_AA)

        if(label > len(labels_to_names)):
            print("WARNING: Got unknown label, using 'detection' instead")
            caption = "Detection {:.3f}".format(score)
        else:
            caption = "{} {:.3f}".format(labels_to_names[label], score)

        cv2.putText(draw, caption, (b[0], b[1] - 10), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 2)
        cv2.putText(draw, caption, (b[0], b[1] - 10), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
        fields = [b[0], b[1], b[2], b[3], score, labels_to_names[label],
                os.path.basename(image_paths[imageIndex][7:])]
        with open(csv_path, 'a') as csv_file:
           writer = csv.writer(csv_file) 
           writer.writerow(fields);

    #Write out image
    draw = Image.fromarray(draw)
    draw.save(image_output_paths[imageIndex])
