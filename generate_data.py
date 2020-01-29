#!/usr/bin/env python3
import random
import numpy as np
from common import *
import cv2
import tensorflow as tf

def resize_image(image, height, width, channels):

    o_height, o_width, _ = image.shape

    resized = np.zeros((height, width, channels))

    scale_factor = o_height / width

    resized_width = int(o_width/scale_factor)
    resized_height = int(o_height/scale_factor)

    res = cv2.resize(image, dsize=(resized_width,resized_height), interpolation=cv2.INTER_CUBIC)

    resized = res[0:height, 0:width, :]

    return resized/255.0


def convert_data_to_image(x_data, y_data):
    # Input.
    image = np.reshape(x_data, [HEIGHT, WIDTH, CHANNEL])

    # Labels
    labels = []

    n_row, n_col, _ = y_data.shape
    for row in range(n_row):
        for col in range(n_col):
            d = y_data[row, col]
            # If cash note in the grid cell
            if d[0] < 0.8:
                continue

            # Convert data.
            bx, by, bw, bh = d[1:5]
            w = int(bw * WIDTH)
            h = int(bh * HEIGHT)
            x = int(col * GRID_WIDTH + (bx * GRID_WIDTH - w/2))
            y = int(row * GRID_HEIGHT + (by * GRID_HEIGHT - h/2))

            s = CLASSES[np.argmax(d[5:])]

            print([d[0],x,y,w,h,s])
            # labels
            labels.append([d[0],x,y,w,h,s])

    return image, labels

def load_image_names(mode):

    if mode == "train":
        filename = "data/train/train.txt"
    elif mode == "test":
        filename = "data/test/test.txt"
    elif mode == "valid":
        filename = "data/validation/validation.txt"

    with open(filename) as f:
        image_paths = f.readlines()
    image_paths = [x.strip() for x in image_paths]

    if mode == "train":
        image_paths = [x.replace("data/train/images/","") for x in image_paths]
    elif mode == "test":
        image_paths = [x.replace("data/test/images/","") for x in image_paths]
    elif mode == "valid":
        image_paths = [x.replace("data/validation/images/","") for x in image_paths]

    image_paths = [x.replace(".jpg","") for x in image_paths]


    return image_paths

def read_data(mode):

    if mode == "train":
        image_path = "data/train/images/"
    elif mode == "test":
        image_path = "data/test/images/"
    elif mode == "valid":
        image_path = "data/validation/images/"

    IMAGE_NAMES = load_image_names(mode=mode)
    print('total.images: ', len(IMAGE_NAMES))

    image_data = []
    annotation_data = []


    for image_name in IMAGE_NAMES:

        image_type = ".jpg"

        # print(image_path + image_name + image_type)
        image = cv2.imread(image_path + image_name + image_type).astype(np.float32)/255.0

        image_data.append(image)
        
        if mode == "train":
            label_path = "data/train/labels/"
        elif mode == "test":
            label_path = "data/test/labels/"
        elif mode == "valid":
            label_path = "data/validation/labels/"

        with open(label_path + image_name + ".txt") as f:
            annotations = f.readlines()


        annotations = [x.strip() for x in annotations]
        annotations = [x.split() for x in annotations]
        annotations = np.asarray(annotations)

        y_data = np.zeros((GRID_Y, GRID_X, 5+len(CLASSES)))

        for row in range(GRID_X):
            for col in range(GRID_Y):
                y_data[row, col, 0] = float(annotations[row * GRID_X + col][0])
                y_data[row, col, 1:5] = [
                    float(annotations[row * GRID_X + col][2]),
                    float(annotations[row * GRID_X + col][3]),
                    float(annotations[row * GRID_X + col][4]),
                    float(annotations[row * GRID_X + col][5])
                ]
                y_data[row, col, int(5+float(annotations[row * GRID_X + col][1]))] = float(1)

        annotation_data.append(y_data)

    image_data = np.asarray(image_data)
    annotation_data = np.asarray(annotation_data)

    return image_data, annotation_data

def load_image(images, labels):
    num = random.randrange(0, len(images))
    return images[num], labels[num]

def render_with_labels(image, labels, display):
    colors = {
        "RM50" : (0,128,0),
        "RM1" : (255,0,0),
        "RM10" : (0,0,255),
        "RM20" : (0,128,255),
        "RM100" : (255,255,255),
    }

    for label in labels:

        cv2.rectangle(image, (label[1],label[2]), (label[1]+label[3],label[2]+label[4]), colors[label[5]], 2)
        # cv2.putText(image, label[5], (label[2],label[1]), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 1, cv2.LINE_AA)
        cv2.putText(image, label[5], (label[1], label[2]-1), cv2.FONT_HERSHEY_SIMPLEX, 0.3, colors[label[5]], 1)

    if display:
        cv2.imshow('image',image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return 255.0 * image

def main():
    read_data()

if __name__ == '__main__':
    main()
