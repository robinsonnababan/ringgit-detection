#!/usr/bin/env python3
from common import *
import tensorflow as tf
import cv2
import os
import numpy as np
import random
import math
import imutils
from uuid import uuid4
import json
import sys
import copy
import glob
from itertools import combinations

from common import *

def image_resize(image, width = None, height = None, inter = cv2.INTER_AREA):
    # initialize the dimensions of the image to be resized and
    # grab the image size
    dim = None
    (h, w) = image.shape[:2]

    # if both the width and height are None, then return the
    # original image
    if width is None and height is None:
        return image

    # check to see if the width is None
    if width is None:
        # calculate the ratio of the height and construct the
        # dimensions
        r = height / float(h)
        dim = (int(w * r), height)

    # otherwise, the height is None
    else:
        # calculate the ratio of the width and construct the
        # dimensions
        r = width / float(w)
        dim = (width, int(h * r))

    if width is not None and height is not None:
        dim = (width,height)

    # resize the image
    resized = cv2.resize(image, dim, interpolation = inter)

    # return the resized image
    return resized

def generate_geometrical_noise(image):
    height, width, depth = image.shape
    

    # # Draw line.
    for _ in range(10):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        thickness = random.randint(1, 5)

        image = cv2.line(image, (x1,y1), (x2,y2), (r,g,b), thickness) 

    # Draw rect.
    for _ in range(20):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        thickness = random.randint(1, 3)

        image = cv2.rectangle(image, (x1,y1), (x2,y2), (r,g,b), thickness)

    # Draw circle.
    for _ in range(20):
        x1 = random.randint(-width//2, width+width//2)
        y1 = random.randint(-height//2, height+height//2)
        radius = random.randint(0, width)
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        thickness = random.randint(1, 3)

        image = cv2.circle(image, (x1,y1), radius, (r,g,b), thickness) 

    return image

def change_brightness(image, mode = "uniform"):

    if mode == "uniform":
        image = image * random.uniform(0.5, 1.5)
        return np.clip(final_image,a_min = 0, a_max = 255.0)

    if mode == "transparent_triangle":

        pt1 = (random.randint(0,WIDTH), random.randint(0,HEIGHT))
        pt2 = (random.randint(0,WIDTH), random.randint(0,HEIGHT))
        pt3 = (random.randint(0,WIDTH), random.randint(0,HEIGHT))

        triangle_cnt = np.array( [pt1, pt2, pt3] )
        shape = cv2.drawContours(np.full((HEIGHT,WIDTH,CHANNEL), 255.), [triangle_cnt], 0, (0,0,0), -1)

        return cv2.addWeighted(shape,0.3,image,0.7,0)
        


def generate_background(mode = "noise"):
    
    if mode == "white" :

        return np.full((HEIGHT,WIDTH,CHANNEL), 255.)

    elif mode== "black" :

        return np.full((HEIGHT,WIDTH,CHANNEL), 0.)

    elif mode == "noise" :
        return np.random.randint(256, size=(HEIGHT, WIDTH,CHANNEL))

    elif mode == 'geometric':
        
        return generate_geometrical_noise(np.full((HEIGHT,WIDTH,CHANNEL), 0.))




def progress(count, total, suffix=''):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', suffix))
    sys.stdout.flush()


def read_subimages(path_to_folder):
    images = []
    files = glob.glob(path_to_folder + "*.png")

    for filename in files:
        img = cv2.imread(filename, cv2.IMREAD_UNCHANGED)
        if img is not None:
            images.append(img)

    return images, files


def overlay_image(layer0_img, layer1_img, x, y):

    height, width, channel = layer1_img.shape

    layer0_img[y: y + height, x: x + width ] = layer1_img

    return layer0_img

def doOverlap(first, second): 
    x_axis_not_overlap = False
    y_axis_not_overlap = False

    if(int(first["x1"]) > int(second["x2"]) or int(first["x2"]) < int(second["x1"])):
        x_axis_not_overlap = True
  
    if(int(first["y1"]) > int(second["y2"]) or int(first["y2"]) < int(second["y1"])):
        y_axis_not_overlap = True
  
    if x_axis_not_overlap and y_axis_not_overlap:
        return False
    else:
        return True

def overlay_transparent(background, overlay, x, y):

    background_width = background.shape[1]
    background_height = background.shape[0]

    if x >= background_width or y >= background_height:
        return background

    h, w = overlay.shape[0], overlay.shape[1]

    if x + w > background_width:
        w = background_width - x
        overlay = overlay[:, :w]

    if y + h > background_height:
        h = background_height - y
        overlay = overlay[:h]

    if overlay.shape[2] < 4:
        overlay = np.concatenate(
            [
                overlay,
                np.ones((overlay.shape[0], overlay.shape[1], 1), dtype = overlay.dtype) * 255
            ],
            axis = 2,
        )

    overlay_image = overlay[..., :3]
    mask = overlay[..., 3:] / 255.0

    background[y:y+h, x:x+w] = (1.0 - mask) * background[y:y+h, x:x+w] + mask * overlay_image

    return background

def rotate_image(mat, angle):
    """
    Rotates an image (angle in degrees) and expands image to avoid cropping
    """

    height, width = mat.shape[:2] # image shape has 3 dimensions
    image_center = (width/2, height/2) # getRotationMatrix2D needs coordinates in reverse order (width, height) compared to shape

    rotation_mat = cv2.getRotationMatrix2D(image_center, angle, 1.)

    # rotation calculates the cos and sin, taking absolutes of those.
    abs_cos = abs(rotation_mat[0,0]) 
    abs_sin = abs(rotation_mat[0,1])

    # find the new width and height bounds
    bound_w = int(height * abs_sin + width * abs_cos)
    bound_h = int(height * abs_cos + width * abs_sin)

    # subtract old image center (bringing image back to origo) and adding the new image center coordinates
    rotation_mat[0, 2] += bound_w/2 - image_center[0]
    rotation_mat[1, 2] += bound_h/2 - image_center[1]

    # rotate image with the new bounds and translated rotation matrix
    rotated_mat = cv2.warpAffine(mat, rotation_mat, (bound_w, bound_h))
    return rotated_mat

def non_maximum_supression(labels):

    remove_index = [0] * len(labels)

    labels = sorted(labels, key=lambda label: label[2]) 
    # print(labels)
    for i in range(0,len(labels) - 1):

        for j in range(i+1, len(labels) - 1):

            # print(i,j)

            box1 = labels[i]
            box2 = labels[j]

            value = iou(box1[1],box1[2],box1[3],box1[4],box2[1],box2[2],box2[3],box2[4])
            
            if value >= 0.1 and box1[0] > box2[0]:
                remove_index[j] = 1
            elif value >= 0.1 and box1[0] <= box2[0]:
                remove_index[i] = 1
            else:
                pass

    new_labels = []
    for i in range(len(remove_index)):
        if remove_index[i] == 0:
            new_labels.append(labels[i])

    # print(new_labels)
    return new_labels

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
            if d[0] < DETECTION_PARAMETER:
                continue
            # print(d[1:5])
            # Convert data.
            bx, by, bw, bh = d[1:5]

            w = int(bw * WIDTH)
            h = int(bh * HEIGHT)
            x = abs(int(col * GRID_WIDTH + (bx * GRID_WIDTH - w/2)))
            y = abs(int(row * GRID_HEIGHT + (by * GRID_HEIGHT - h/2)))

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
        "RM50" : (0,255,0),
        "RM1" : (255,0,0),
        "RM10" : (0,0,255),
        "RM20" : (0,128,255),
        "RM100" : (255,255,255),
    }

    for label in labels:
        # cv2.rectangle(image,(0,0),(5,5),(0,255,0),2)
        cv2.rectangle(image, (int(label[1]),int(label[2])), (int(label[1]+label[3]),int(label[2]+label[4])), colors[label[5]], 2)
        cv2.putText(image, label[5], (label[1], label[2]-1), cv2.FONT_HERSHEY_SIMPLEX, 0.3, colors[label[5]], 1)

    if display:
        cv2.imshow('image',image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return image

def calculate_iou(fact,pred):
    fact = tf.reshape(fact, [-1, GRID_Y*GRID_X, 5+len(CLASSES)])
    pred = tf.reshape(pred, [-1, GRID_Y*GRID_X, 5+len(CLASSES)])
    # Truth
    fact_conf = fact[:,:,0]
    fw = fact[:,:,3] * WIDTH
    fh = fact[:,:,4] * HEIGHT
    fx = fact[:,:,0] * GRID_WIDTH - fw/2
    fy = fact[:,:,1] * GRID_HEIGHT - fh/2
    # Prediction
    pw = pred[:,:,3] * WIDTH
    ph = pred[:,:,4] * HEIGHT
    px = pred[:,:,0] * GRID_WIDTH - pw/2
    py = pred[:,:,1] * GRID_HEIGHT - ph/2
    # IOU
    intersect = (tf.minimum(fx+fw, px+pw) - tf.maximum(fx, px)) * (tf.minimum(fy+fh, py+ph) - tf.maximum(fy, py))
    union = (fw * fh) + (pw * ph) - intersect
    nonzero_count = tf.math.count_nonzero(fact_conf, dtype=tf.float32)
    return (intersect/union)
    # return switch(
    #     tf.equal(nonzero_count, 0),
    #     1.0,
    #     sum((intersect / union) * fact_conf) / nonzero_count
    # )

def iou(fx,fy,fw,fh,px,py,pw,ph):
    # IOU
    intersect = (np.minimum(fx+fw, px+pw) - np.maximum(fx, px)) * (np.minimum(fy+fh, py+ph) - np.maximum(fy, py))
    union = (fw * fh) + (pw * ph) - intersect
    return (intersect/union)