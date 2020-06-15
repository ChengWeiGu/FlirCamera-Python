# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 10:22:53 2020

@author: William_Wu
"""


import os
import cv2


refPt = []
cropping = False


def click_and_crop(event, x, y, flags, window_name):
    global refPt, cropping

    window_x, window_y, window_w, window_h = cv2.getWindowImageRect(window_name)
    # print(event, x, y)
    # print(window_x, window_y, window_w, window_h)
    
    if x < 0:
        x = 0
    elif x >= window_w:
        x = window_w - 1
    
    if y < 0:
        y = 0
    elif y >= window_h:
        y = window_h - 1    

    if event == cv2.EVENT_LBUTTONDOWN:
        refPt.append((x, y))

    elif event == cv2.EVENT_LBUTTONUP:
        if len(refPt) < 1:
            return

        refPt.append((x, y))
        min_x = min(refPt[-2][0], refPt[-1][0])
        max_x = max(refPt[-2][0], refPt[-1][0])
        min_y = min(refPt[-2][1], refPt[-1][1])
        max_y = max(refPt[-2][1], refPt[-1][1])

        refPt.clear()
        if (max_x - min_x) > 20 and (max_y - min_y) > 20:
            refPt.append((min_x, min_y))
            refPt.append((max_x, max_y))
            cropping = True
        else:
            cropping = False             


def empty_folder(folder_path):
    for root, dirs, files in os.walk(folder_path, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
