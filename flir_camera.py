# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 10:22:53 2020

@author: William_Wu
"""


from enum import Enum
import numpy as np
import PySpin
import cv2


class BayerPattern(Enum):
    GRAY = 0
    RGB = 1
    BGR = 2
    NUM = 3


class AutoAlgoSelector(Enum):
    AUTO_AE = 0
    AUTO_AWB = 1
    NUM = 2


class AeTargetGreyValue(Enum):
    LT_OFF = 0
    LT_AUTO = 1
    NUM = 2


class FLIRCamera:

    def __init__(self, config):
        self._camIdx = config._camera_index
        self._width = config._width
        self._height = config._height
        self._num_camera = 0
        self._ae_gain = config._ae_gain
        self._ae_expTime = config._ae_expTime
        self._pixel_format = config._pixel_format
        self._ae_blacklevel = config._ae_blacklevel
        self._awb_ratio = config._awb_ratio
        self._AasRoiEnable = config._AasRoiEnable
        self._AutoAlgorithmSelector = config._AutoAlgorithmSelector
        self._AasRoiOffsetX = config._AasRoiOffsetX
        self._AasRoiOffsetY = config._AasRoiOffsetY
        self._AasRoiWidth = config._AasRoiWidth
        self._AasRoiHeight = config._AasRoiHeight
        self._AutoExposureTargetGreyValueAuto = config._AutoExposureTargetGreyValueAuto
        self._AutoExposureTargetGreyValue = config._AutoExposureTargetGreyValue
        self._AutoExposureGainLowerLimit = config._AutoExposureGainLowerLimit
        self._AutoExposureGainUpperLimit = config._AutoExposureGainUpperLimit
        self._AutoExposureExposureTimeLowerLimit = config._AutoExposureExposureTimeLowerLimit
        self._AutoExposureExposureTimeUpperLimit = config._AutoExposureExposureTimeUpperLimit
        self._AutoExposureGreyValueLowerLimit = config._AutoExposureGreyValueLowerLimit
        self._AutoExposureGreyValueUpperLimit = config._AutoExposureGreyValueUpperLimit

        self.system = None
        self.cam = None
        self.cam_list = None

    def open(self):
        self.system = PySpin.System.GetInstance()
        self.cam_list = self.system.GetCameras()
        num_cameras = self.cam_list.GetSize()
        print("Number of cameras detected: %d" % num_cameras)

        bState = True
        if num_cameras == 0:
            self.close()
            raise Exception("[ERROR] Not enough cameras!")

        try:
            self.cam = self.cam_list.GetByIndex(self._camIdx)
            self.cam.Init()

            self.show_camera_setting()
            bState &= self.set_gain(self._ae_gain)
            bState &= self.set_expTime(self._ae_expTime)
            bState &= self.set_pixel_format()
            bState &= self.set_width()
            bState &= self.set_height()
            bState &= self.set_blacklevel(self._ae_blacklevel)
            bState &= self.set_awb_ratio()
            bState &= self.set_auto_algo()

            self.cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)
            self.cam.BeginAcquisition()

            node_map = self.cam.GetTLStreamNodeMap()
            handling_mode = PySpin.CEnumerationPtr(node_map.GetNode('StreamBufferHandlingMode'))
            handling_mode_entry = handling_mode.GetEntryByName('NewestOnly')
            handling_mode.SetIntValue(handling_mode_entry.GetValue())

        except PySpin.SpinnakerException as ex:
            raise Exception('[ERROR] %s' % ex)

        return bState

    def close(self):
        if self.cam is not None:
            self.cam.EndAcquisition()
            self.cam.DeInit()
            del self.cam
        if self.cam_list is not None:
            self.cam_list.Clear()
            del self.cam_list
        if self.system is not None:
            self.system.ReleaseInstance()

    def set_gain(self, gain):      
        status = True
        try:
            if self.cam.GainAuto.GetAccessMode() != PySpin.RW:
                print("[ERROR] Unable to disable automatic gain. Aborting...")
                status = False
                return status

            if gain >= 0:
                # Manual AE
                self.cam.GainAuto.SetValue(PySpin.GainAuto_Off)
                print("Automatic gain disabled...")
                
                if self.cam.Gain.GetAccessMode() == PySpin.RW:
                    gain_to_set = min(self.get_gain_max(), gain)
                    print("gain_to_set:", gain_to_set)
                    self.cam.Gain.SetValue(gain_to_set)
                    self._ae_gain = gain_to_set
                else:
                    print("[ERROR] Unable to set gain. Aborting...")
                    status = False
            else:
                # Auto AE
                self.cam.GainAuto.SetValue(PySpin.GainAuto_Continuous)
                print ("Automatic gain enabled...")
        except PySpin.SpinnakerException as ex:
            print('[ERROR] %s' % ex)
            status = False

        return status

    def set_expTime(self, expTime):
        status = True
        try:
            if self.cam.ExposureAuto.GetAccessMode() != PySpin.RW:
                print("[ERROR] Unable to disable automatic exposure. Aborting...")
                status = False
                return status

            if expTime > 0:
                # Manual AE
                self.cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)
                print("Automatic exposure disabled...")
                
                if self.cam.ExposureTime.GetAccessMode() == PySpin.RW:
                    exposure_time_to_set = min(self.cam.ExposureTime.GetMax(), expTime)
                    print("exposure_time_to_set: ", exposure_time_to_set)
                    self.cam.ExposureTime.SetValue(exposure_time_to_set)
                    self._ae_expTime = exposure_time_to_set
                else:
                    print("[ERROR] Unable to set exposure time. Aborting...")
                    status =False           
            else:
                # Auto AE
                self.cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Continuous)
                print("Automatic exposure enabled...")
        except PySpin.SpinnakerException as ex:
            print('[ERROR] %s' % ex)
            status = False

        return True

    def set_pixel_format(self):
        try:
            nodemap = self.cam.GetNodeMap()
            node_pixel_format = PySpin.CEnumerationPtr(nodemap.GetNode('PixelFormat'))
            if PySpin.IsAvailable(node_pixel_format) and PySpin.IsWritable(node_pixel_format):
                if self._pixel_format is BayerPattern.GRAY:
                    node_pixel_format_type = PySpin.CEnumEntryPtr(node_pixel_format.GetEntryByName('Mono8'))
                elif self._pixel_format is BayerPattern.RGB:
                    node_pixel_format_type = PySpin.CEnumEntryPtr(node_pixel_format.GetEntryByName('RGB8'))
                elif self._pixel_format is BayerPattern.BGR:
                    node_pixel_format_type = PySpin.CEnumEntryPtr(node_pixel_format.GetEntryByName('BGR8'))
                else:
                    node_pixel_format_type = PySpin.CEnumEntryPtr(node_pixel_format.GetEntryByName('Mono8'))
                if PySpin.IsAvailable(node_pixel_format_type) and PySpin.IsReadable(node_pixel_format_type):
                    pixel_format_type = node_pixel_format_type.GetValue()
                    node_pixel_format.SetIntValue(pixel_format_type)
                    print ('Pixel format set to: %s' % node_pixel_format.GetCurrentEntry().GetSymbolic())
                else:
                    raise Exception("[ERROR] Can't set BayerPattern.", self.cam.PixelFormat.GetAccessMode())
            else:
                print (PySpin.IsAvailable(node_pixel_format))
                raise Exception("[ERROR] Can't set BayerPattern.", self.cam.PixelFormat.GetAccessMode())

        except PySpin.SpinnakerException as ex:
            raise Exception('[ERROR] %s' % ex)

        return True

    def set_width(self):
        self.cam.OffsetX.SetValue(0)
        width_max = self.cam.WidthMax.GetValue()
        if self._width <= 0:
            self._width = width_max

        try:
            if self.cam.Width is not None and self.cam.Width.GetAccessMode() == PySpin.RW:
                self.cam.Width.SetValue(self._width)
                nodemap = self.cam.GetNodeMap()
                node_offsetX = PySpin.CIntegerPtr(nodemap.GetNode('OffsetX'))
                if PySpin.IsAvailable(node_offsetX) and PySpin.IsWritable(node_offsetX):
                    node_offsetX.SetValue(int((width_max - self.cam.Width.GetValue()) / 2))
                else:
                    raise Exception("[ERROR] Offset X not available...")
            else:
                raise Exception("[ERROR] Can't set Width.", self.cam.Width.GetAccessMode())

        except PySpin.SpinnakerException as ex:
            raise Exception('[ERROR] %s' % ex)

        return True

    def set_height(self):
        self.cam.OffsetY.SetValue(0)
        height_max = self.cam.HeightMax.GetValue()
        if self._height <= 0:
            self._height = height_max

        try:
            if self.cam.Height is not None and self.cam.Height.GetAccessMode() == PySpin.RW:
                self.cam.Height.SetValue(self._height)
                nodemap = self.cam.GetNodeMap()
                node_offsetY = PySpin.CIntegerPtr(nodemap.GetNode('OffsetY'))
                if PySpin.IsAvailable(node_offsetY) and PySpin.IsWritable(node_offsetY):
                    node_offsetY.SetValue(int((height_max - self.cam.Height.GetValue()) / 2))
                else:
                    raise Exception("[ERROR] Offset Y not available...")
            else:
                raise Exception("[ERROR] Can't set Height.", self.cam.Height.GetAccessMode())

        except PySpin.SpinnakerException as ex:
            raise Exception('[ERROR] %s' % ex)

        return True

    def set_blacklevel(self, blacklevel):
        bState = True
        self._ae_blacklevel = blacklevel
        
        if self._ae_blacklevel < 0:
            self._ae_blacklevel = 6

        try:
            if self.cam.BlackLevel is None or self.cam.BlackLevel.GetAccessMode() != PySpin.RW:
                raise Exception("[ERROR] Can't set BlackLevel.", self.cam.BlackLevel.GetAccessMode())
            self.cam.BlackLevel.SetValue(self._ae_blacklevel)
            print ("blacklevel set to:", self._ae_blacklevel)

        except PySpin.SpinnakerException as ex:
            raise Exception('[ERROR] %s' % ex)

        return bState

    def set_awb_ratio(self):
        if self._pixel_format is BayerPattern.GRAY:
            return True

        try:
            if self.cam.BalanceWhiteAuto is None or self.cam.BalanceWhiteAuto.GetAccessMode() != PySpin.RW:
                raise Exception("[ERROR] Can't set BalanceWhiteAuto.", self.cam.BalanceWhiteAuto.GetAccessMode())

            if self._awb_ratio >= 0:
                # Manual AWB
                self.cam.BalanceWhiteAuto.SetValue(PySpin.BalanceWhiteAuto_Off)
                print ("Automatic white balance disabled...")
            else:
                # Auto AWB
                self.cam.BalanceWhiteAuto.SetValue(PySpin.BalanceWhiteAuto_Continuous)
                print ("Automatic white balance enabled...")
                return True

            if self.cam.BalanceRatio is None or self.cam.BalanceRatio.GetAccessMode() != PySpin.RW:
                raise Exception("[ERROR] Can't set BalanceRatio.", self.cam.BalanceRatio.GetAccessMode())

            self.cam.BalanceRatio.SetValue(self._awb_ratio)

        except PySpin.SpinnakerException as ex:
            raise Exception("[ERROR] %s" % ex)

        return True

    def set_auto_algo(self):
        try:
            if not self._AasRoiEnable:
                return True

            if self.cam.AasRoiEnable.GetAccessMode() == PySpin.NI:
                raise Exception("[ERROR] AasRoi is not implementd")

            if self.cam.AasRoiEnable is not None and self.cam.AasRoiEnable.GetAccessMode() == PySpin.RW:
                self.cam.AasRoiEnable.SetValue(self._AasRoiEnable)
            else:
                raise Exception("[ERROR] Can't set AasRoiEnable.", self.cam.AasRoiEnable.GetAccessMode())

            if self.cam.AutoAlgorithmSelector is not None and self.cam.AutoAlgorithmSelector.GetAccessMode() == PySpin.RW:
                if self._AutoAlgorithmSelector is AutoAlgoSelector.AUTO_AE:
                    self.cam.AutoAlgorithmSelector.SetValue(PySpin.AutoAlgorithmSelector_Ae)
                elif self._AutoAlgorithmSelector is AutoAlgoSelector.AUTO_AWB:
                    self.cam.AutoAlgorithmSelector.SetValue(PySpin.AutoAlgorithmSelector_Awb)
                else:
                    self.cam.AutoAlgorithmSelector.SetValue(PySpin.AutoAlgorithmSelector_Ae)
            else:
                raise Exception("[ERROR] Can't set AutoAlgorithmSelector.", self.cam.AutoAlgorithmSelector.GetAccessMode())

            if self.cam.AasRoiOffsetX is not None and self.cam.AasRoiOffsetX.GetAccessMode() == PySpin.RW:
                self.cam.AasRoiOffsetX.SetValue(self._AasRoiOffsetX)
            else:
                raise Exception("[ERROR] Can't set AasRoiOffsetX.", self.cam.AasRoiOffsetX.GetAccessMode())

            if self.cam.AasRoiOffsetY is not None and self.cam.AasRoiOffsetY.GetAccessMode() == PySpin.RW:
                self.cam.AasRoiOffsetY.SetValue(self._AasRoiOffsetY)
            else:
                raise Exception("[ERROR] Can't set AasRoiOffsetY.", self.cam.AasRoiOffsetY.GetAccessMode())

            if self.cam.AasRoiWidth is not None and self.cam.AasRoiWidth.GetAccessMode() == PySpin.RW:
                self.cam.AasRoiWidth.SetValue(self._AasRoiWidth)
            else:
                raise Exception("[ERROR] Can't set AasRoiWidth.", self.cam.AasRoiWidth.GetAccessMode())

            if self.cam.AasRoiHeight is not None and self.cam.AasRoiHeight.GetAccessMode() == PySpin.RW:
                self.cam.AasRoiHeight.SetValue(self._AasRoiHeight)
            else:
                raise Exception("[ERROR] Can't set AasRoiHeight.", self.cam.AasRoiHeight.GetAccessMode())

            if self.cam.AutoExposureTargetGreyValueAuto is not None and self.cam.AutoExposureTargetGreyValueAuto.GetAccessMode() == PySpin.RW:
                if self._AutoExposureTargetGreyValueAuto is AeTargetGreyValue.LT_OFF:
                    self.cam.AutoExposureTargetGreyValueAuto.SetValue(PySpin.AutoExposureTargetGreyValueAuto_Off)
                elif self._AutoExposureTargetGreyValueAuto is AeTargetGreyValue.LT_AUTO:
                    self.cam.AutoExposureTargetGreyValueAuto.SetValue(PySpin.AutoExposureTargetGreyValueAuto_Continuous)
                else:
                    self.cam.AutoExposureTargetGreyValueAuto.SetValue(PySpin.AutoExposureTargetGreyValueAuto_Off)
            else:
                raise Exception("[ERROR] Can't set AutoExposureTargetGreyValueAuto.", self.cam.AutoExposureTargetGreyValueAuto.GetAccessMode())

            if self.cam.AutoExposureTargetGreyValue is not None and self.cam.AutoExposureTargetGreyValue.GetAccessMode() == PySpin.RW:
                if self.cam.AutoExposureTargetGreyValue > 0:
                    self.cam.AutoExposureTargetGreyValue.SetValue(self._AutoExposureTargetGreyValue)
            else:
                raise Exception("[ERROR] Can't set AutoExposureTargetGreyValue.", self.cam.AutoExposureTargetGreyValue.GetAccessMode())

            if self.cam.AutoExposureGainLowerLimit is not None and self.cam.AutoExposureGainLowerLimit.GetAccessMode() == PySpin.RW:
                if self.cam.AutoExposureGainLowerLimit > 0:
                    self.cam.AutoExposureGainLowerLimit.SetValue(self._AutoExposureGainLowerLimit)
            else:
                raise Exception("[ERROR] Can't set AutoExposureGainLowerLimit.", self.cam.AutoExposureGainLowerLimit.GetAccessMode())

            if self.cam.AutoExposureGainUpperLimit is not None and self.cam.AutoExposureGainUpperLimit.GetAccessMode() == PySpin.RW:
                if self.cam.AutoExposureGainUpperLimit > 0:
                    self.cam.AutoExposureGainUpperLimit.SetValue(self._AutoExposureGainUpperLimit)
            else:
                raise Exception("[ERROR] Can't set AutoExposureGainUpperLimit.", self.cam.AutoExposureGainUpperLimit.GetAccessMode())

            if self.cam.AutoExposureExposureTimeLowerLimit is not None and self.cam.AutoExposureExposureTimeLowerLimit.GetAccessMode() == PySpin.RW:
                if self.cam.AutoExposureExposureTimeLowerLimit > 0:
                    self.cam.AutoExposureExposureTimeLowerLimit.SetValue(self._AutoExposureExposureTimeLowerLimit)
            else:
                raise Exception("[ERROR] Can't set AutoExposureExposureTimeLowerLimit.", self.cam.AutoExposureExposureTimeLowerLimit.GetAccessMode())

            if self.cam.AutoExposureExposureTimeUpperLimit is not None and self.cam.AutoExposureExposureTimeUpperLimit.GetAccessMode() == PySpin.RW:
                if self.cam.AutoExposureExposureTimeUpperLimit > 0:
                    self.cam.AutoExposureExposureTimeUpperLimit.SetValue(self._AutoExposureExposureTimeUpperLimit)
            else:
                raise Exception("[ERROR] Can't set AutoExposureExposureTimeUpperLimit.", self.cam.AutoExposureExposureTimeUpperLimit.GetAccessMode())

            if self.cam.AutoExposureGreyValueLowerLimit is not None and self.cam.AutoExposureGreyValueLowerLimit.GetAccessMode() == PySpin.RW:
                if self.cam.AutoExposureGreyValueLowerLimit > 0:
                    self.cam.AutoExposureGreyValueLowerLimit.SetValue(self._AutoExposureGreyValueLowerLimit)
            else:
                raise Exception("[ERROR] Can't set AutoExposureGreyValueLowerLimit.", self.cam.AutoExposureGreyValueLowerLimit.GetAccessMode())

            if self.cam.AutoExposureGreyValueUpperLimit is not None and self.cam.AutoExposureGreyValueUpperLimit.GetAccessMode() == PySpin.RW:
                if self.cam.AutoExposureGreyValueUpperLimit > 0:
                    self.cam.AutoExposureGreyValueUpperLimit.SetValue(self._AutoExposureGreyValueUpperLimit)
            else:
                raise Exception("[ERROR] Can't set AutoExposureGreyValueUpperLimit.", self.cam.AutoExposureGreyValueUpperLimit.GetAccessMode())

        except PySpin.SpinnakerException as ex:
            raise Exception("[ERROR] %s" % ex)

        return True

    def get_gain(self):
        return self._ae_gain
    
    def get_gain_max(self):
        gain_max = 0.0    
        try:
            gain_max = self.cam.Gain.GetMax()
        except PySpin.SpinnakerException as ex:
            raise Exception('[ERROR] %s' % ex)

        return gain_max        

    def get_expTime(self):
        return self._ae_expTime

    def get_width(self):
        return self._width

    def get_height(self):
        return self._height
        
    def get_blacklevel(self):
        return self._ae_blacklevel

    def get_pixel_format(self):
        return self._pixel_format
        
    def get_awb(self):
        return self.cam.BalanceRatio.GetValue()

    def acquire_images(self):
        try:
            image_result = self.cam.GetNextImage()
            if image_result.IsIncomplete():
                print("Image incomplete with image status {}...".format(image_result.GetImageStatus()))
            else:
                width = image_result.GetWidth()
                height = image_result.GetHeight()
                # print("Grabbed image width = {width}, height = {height}".format(width=width, height=height))

            if self._pixel_format is BayerPattern.GRAY:
                image_converted = image_result.Convert(PySpin.PixelFormat_Mono8, 0).GetNDArray()
                channels = (image_converted, image_converted, image_converted)
                result = cv2.merge(channels).astype(np.uint8)
            elif self._pixel_format is BayerPattern.RGB:
                image_converted = image_result.Convert(PySpin.PixelFormat_RGB8, 0).GetNDArray()
                channels = cv2.split(image_converted)
                # RGB to BGR
                R_channel = channels[0]
                G_channel = channels[1]
                B_channel = channels[2]

                result = cv2.merge((B_channel, G_channel, R_channel)).astype(np.uint8)
            elif self._pixel_format is BayerPattern.BGR:
                image_converted = image_result.Convert(PySpin.PixelFormat_BGR8, 0).GetNDArray()
                result = image_converted.astype(np.uint8)
            else:
                image_converted = image_result.Convert(PySpin.PixelFormat_Mono8, 0).GetNDArray()
                channels = (image_converted, image_converted, image_converted)
                result = cv2.merge(channels).astype(np.uint8)

            image_result.Release()

        except PySpin.SpinnakerException as ex:
            raise Exception('[ERROR] %s' % ex)

        return result

    def show_camera_setting(self):
        try:
            print (' ================================================== ')
            print ('[Main]')
            print ('- camIdx:', self._camIdx)
            print ('- width:', self._width)
            print ('- height:', self._height)
            print ('- num_camera:', self._num_camera)
            print ('- pixel_format:', self._pixel_format)
            print ('- ae_expTime:', self._ae_expTime)
            print ('- ae_gain:', self._ae_gain)
            print ('- ae_blacklevel:', self._ae_blacklevel)
            print ('- awb_ratio:', self._awb_ratio)
            print (' ================================================== ')
            print ('[Auto Algo]')
            print ('- AasRoiEnable:', self._AasRoiEnable)
            print ('- AutoAlgorithmSelector:', self._AutoAlgorithmSelector)
            print ('- AasRoiOffsetX:', self._AasRoiOffsetX)
            print ('- AasRoiOffsetY:', self._AasRoiOffsetY)
            print ('- AasRoiWidth:', self._AasRoiWidth)
            print ('- AasRoiHeight:', self._AasRoiHeight)
            print ('- AutoExposureTargetGreyValueAuto:', self._AutoExposureTargetGreyValueAuto)
            print ('- AutoExposureTargetGreyValue:', self._AutoExposureTargetGreyValue)
            print ('- AutoExposureGainLowerLimit:', self._AutoExposureGainLowerLimit)
            print ('- AutoExposureGainUpperLimit:', self._AutoExposureGainUpperLimit)
            print ('- AutoExposureExposureTimeLowerLimit:', self._AutoExposureExposureTimeLowerLimit)
            print ('- AutoExposureExposureTimeUpperLimit:', self._AutoExposureExposureTimeUpperLimit)
            print ('- AutoExposureGreyValueLowerLimit:', self._AutoExposureGreyValueLowerLimit)
            print ('- AutoExposureGreyValueUpperLimit:', self._AutoExposureGreyValueUpperLimit)
            print (' ================================================== ')

        except Exception as e:
            raise Exception('[ERROR] %s' % e)