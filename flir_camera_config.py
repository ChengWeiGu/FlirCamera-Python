from Camera_Panel.flir_camera import BayerPattern, AutoAlgoSelector, AeTargetGreyValue


class FLIRCameraConfig:

    def __init__(self):
        # Main
        self._camera_index = 0
        self._width = -1
        self._height = -1
        self._pixel_format = BayerPattern.GRAY

        # AE/AWB
        self._ae_gain = -1
        self._ae_expTime = 0
        self._ae_blacklevel = -1
        self._awb_ratio = -1

        # ROI Setting of Auto AE/AWB
        self._AasRoiEnable = False
        self._AutoAlgorithmSelector = AutoAlgoSelector.AUTO_AE
        self._AasRoiOffsetX = -1
        self._AasRoiOffsetY = -1
        self._AasRoiWidth = -1
        self._AasRoiHeight = -1

        self._AutoExposureTargetGreyValueAuto = AeTargetGreyValue.LT_OFF
        self._AutoExposureTargetGreyValue = -1
        self._AutoExposureGainLowerLimit = -1
        self._AutoExposureGainUpperLimit = -1
        self._AutoExposureExposureTimeLowerLimit = -1
        self._AutoExposureExposureTimeUpperLimit = -1
        self._AutoExposureGreyValueLowerLimit = -1
        self._AutoExposureGreyValueUpperLimit = -1

        #Images
        self.image_saved_path = ''
        

def flir_camera_config_parser(cfg_path, config):
    try:
        with open(cfg_path, 'r') as cfg_file:
            for line in cfg_file.readlines():
                segment = line.split('=')
                if len(segment) > 1:
                    key = segment[0].strip()
                    value = segment[1].strip()
                    if key == 'camera_index':
                        config._camera_index = int(value)
                    elif key == 'width':
                        config._width = int(value)
                    elif key == 'height':
                        config._height = int(value)
                    elif key == 'pixel_format':
                        nValue = int(value)
                        if nValue is BayerPattern.GRAY.value:
                            config._pixel_format = BayerPattern.GRAY
                        elif nValue is BayerPattern.BGR.value:
                            config._pixel_format = BayerPattern.BGR
                        elif nValue is BayerPattern.RGB.value:
                            config._pixel_format = BayerPattern.RGB
                        else:
                            config._pixel_format = BayerPattern.GRAY
                    elif key == 'ae_gain':
                        config._ae_gain = float(value)
                    elif key == 'ae_expTime':
                        config._ae_expTime = int(value)
                    elif key == 'ae_blacklevel':
                        config._ae_blacklevel = int(value)
                    elif key == 'awb_ratio':
                        config._awb_ratio = float(value)
                    elif key == 'AasRoiEnable':
                        if int(value) == 1:
                            config._AasRoiEnable = True
                        else:
                            config._AasRoiEnable = False
                    elif key == 'AutoAlgorithmSelector':
                        nValue = int(value)
                        if nValue is AutoAlgoSelector.AUTO_AE.value:
                            config._AutoAlgorithmSelector = AutoAlgoSelector.AUTO_AE
                        elif nValue is AutoAlgoSelector.AUTO_AWB.value:
                            config._AutoAlgorithmSelector = AutoAlgoSelector.AUTO_AWB
                        else:
                            config._AutoAlgorithmSelector = AutoAlgoSelector.AUTO_AE
                    elif key == 'AasRoiOffsetX':
                        config._AasRoiOffsetX = int(value)
                    elif key == 'AasRoiOffsetY':
                        config._AasRoiOffsetY = int(value)
                    elif key == 'AasRoiWidth':
                        config._AasRoiWidth = int(value)
                    elif key == 'AasRoiHeight':
                        config._AasRoiHeight = int(value)
                    elif key == 'AutoExposureTargetGreyValueAuto':
                        nValue = int(value)
                        if nValue is AeTargetGreyValue.LT_OFF.value:
                            config._AutoExposureTargetGreyValueAuto = AeTargetGreyValue.LT_OFF
                        elif nValue is AeTargetGreyValue.LT_AUTO.value:
                            config._AutoExposureTargetGreyValueAuto = AeTargetGreyValue.LT_AUTO
                        else:
                            config._AutoExposureTargetGreyValueAuto = AeTargetGreyValue.LT_OFF
                    elif key == 'AutoExposureTargetGreyValue':
                        config._AutoExposureTargetGreyValue = float(value)
                    elif key == 'AutoExposureGainLowerLimit':
                        config._AutoExposureGainLowerLimit = float(value)
                    elif key == 'AutoExposureGainUpperLimit':
                        config._AutoExposureGainUpperLimit = float(value)
                    elif key == 'AutoExposureExposureTimeLowerLimit':
                        config._AutoExposureExposureTimeLowerLimit = float(value)
                    elif key == 'AutoExposureExposureTimeUpperLimit':
                        config._AutoExposureExposureTimeUpperLimit = float(value)
                    elif key == 'AutoExposureGreyValueLowerLimit':
                        config._AutoExposureGreyValueLowerLimit = float(value)
                    elif key == 'AutoExposureGreyValueUpperLimit':
                        config._AutoExposureGreyValueUpperLimit = float(value)
                    elif key == 'ImageSavedPath':
                        config.image_saved_path = value
                    else:
                        print ('[WARNING] Find Undefined Identifier:', key)
                        return False
    except Exception as e:
        raise Exception('[ERROR] %s' % e)

    return True
