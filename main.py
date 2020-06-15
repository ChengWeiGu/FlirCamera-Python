# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 10:22:53 2020

@author: William_Wu
"""

import sys
import os
import numpy as np
import cv2
from flir_camera import FLIRCamera, BayerPattern
from flir_camera_config import FLIRCameraConfig, flir_camera_config_parser
import utils

if __name__ == '__main__':

    # Camera Setting
    camera_config = FLIRCameraConfig()
    if len(sys.argv) == 2:
        # read camera setting from config file
        print ('[config file]', sys.argv[1])
        if not flir_camera_config_parser(sys.argv[1], camera_config):
            sys.exit()
    else:
        # modify camera setting in code
        camera_config._camera_index = 0
        camera_config._width = int(2736*2)
        camera_config._height = int(1824*2)
        camera_config._ae_gain = 12
        camera_config._ae_expTime = 8000.0
        camera_config._bayer_pattern = BayerPattern.BGR

    # Initial Camera
    camera = FLIRCamera(camera_config)
    
    # Open Camera
    if camera.open() is False:
        sys.exit()

    window_name = "preview"
    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, utils.click_and_crop, window_name)
    i = 0
    while True:
        frame = camera.acquire_images()
                
        if utils.cropping:
            cv2.rectangle(frame, pt1=(utils.refPt[0][0], utils.refPt[0][1]), pt2=(utils.refPt[1][0], utils.refPt[1][1]), color=(0, 255, 0), thickness=2)
        
        frame_small = cv2.resize(frame, (1064,800))
        cv2.imshow(window_name, frame_small)
        
        key = cv2.waitKey(1)
        if key == ord('s'):
            cv2.imwrite('./test_'+str(i)+'.jpg',frame)
            i += 1
            
        if key & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            break
              
    # Close Camera
    camera.close()
