""" This is an adapted version of the sc2_SDKStructures.h file
I use the camera in USB 3.0 so I removed all the Camera Link related elements

In this file I reproduce the .h file sc2_SDKStructures.h located at
C:\Program Files (x86)\Digital_Camera_Toolbox\pco.sdk\include
but I'm not even sure this is useful at all
"""

# The wZZAlignDummies are only used in order to reflect the compiler output.
# Default setting of the MS-VC-compiler is 8 byte alignment!!
# Despite the default setting of 8 byte the MS compiler falls back to the biggest member, e.g.
# in case the biggest member in a struct is a DWORD, all members will be aligned to 4 bytes and
# not to default of 8.

import ctypes

# PCO Constants
PCO_NOERROR = int("0x00000000",0)
#PCO_ERROR_CODE_MASK = int("0x00000FFF",0)
IMAGEPARAMETERS_READ_FROM_SEGMENTS = int("0x02",0)
IMAGEPARAMETERS_READ_WHILE_RECORDING = int("0x01",0)

PCO_STRUCTREV = 102         # set this value to wStructRev

PCO_BUFCNT = 16                   # see PCO_API struct
PCO_MAXDELEXPTABLE = 16          # see PCO_Timing struct
PCO_RAMSEGCNT = 4                # see PCO_Storage struct
PCO_MAXVERSIONHW = 10
PCO_MAXVERSIONFW = 10

PCO_ARM_COMMAND_TIMEOUT = 10000
PCO_HPX_COMMAND_TIMEOUT = 10000
PCO_COMMAND_TIMEOUT = 400

# SDK-Dll internal defines (different to interface type in sc2_defs.h!!!
# In case you're going to enumerate interface types, please refer to sc2_defs.h.
PCO_INTERFACE_FW = 1         # Firewire interface
PCO_INTERFACE_GIGE = 5         # Gigabit Ethernet
PCO_INTERFACE_USB = 6         # USB 2.0
PCO_INTERFACE_USB3 = 8         # USB 3.0 and USB 3.1 Gen1
PCO_INTERFACE_WLAN = 9         # WLan (Only control path, not data path)

PCO_INTERFACE_GENERIC = 20

PCO_OPENFLAG_HIDE_PROGRESS = int("0x0002",0) # Hides the progress dialog when automatic scanning runs

"""
class HANDLE(ctypes.c_bool):
    pass
class WORD(ctypes.c_uint16):
    pass
class SHORT(ctypes.c_int16):
    pass
class DWORD(ctypes.c_uint32):
    pass"""

#HANDLE = ctypes.c_voidp
#WORD = ctypes.c_uint16
#SHORT = ctypes.c_int16
#DWORD = ctypes.c_uint32
HANDLE = ctypes.wintypes.HANDLE
WORD = ctypes.wintypes.WORD
DWORD = ctypes.wintypes.DWORD
SHORT = WORD


class PCO_Buflist(ctypes.Structure):
    _fields_ = [
        ("sBufNr", SHORT),
        ("ZZwAlignDummy", WORD),
        ("dwStatusDll", DWORD),
        ("dwStatusDrv", DWORD)] #12

class PCO_OpenStruct(ctypes.Structure):
    _fields_ = [
        ("wSize", WORD), # Sizeof this struct
            ("wInterfaceType", WORD),      # 1: Firewire, 2: CamLink with Matrox, 3: CamLink with Silicon SW Me3
                                           # 4: CamLink with NI, 5: GigE, 6: USB2.0, 7: CamLink with Silicon SW Me4,
                                           # 8: USB3.0, 8: WLan
            ("wCameraNumber", WORD),       # Start with 0 and increment till error 'No driver' is returned
                                           # Due to port occupation it might be necessary to increment this
                                           # value a second time to get the next camera.
        ("wCameraNumAtInterface", WORD),   # Current number of camera at the interface
        ("wOpenFlags", WORD * 10),         # [0]: moved to dwnext to position 0xFF00
                                           # [1]: moved to dwnext to position 0xFFFF0000
                                           # [2]: Bit0: PCO_OPENFLAG_GENERIC_IS_CAMLINK
                                           #            Set this bit in case of a generic Cameralink interface
                                           #            This enables the import of the additional three camera-
                                           #            link interface functions.
                                           #      Bit1: PCO_OPENFLAG_HIDE_PROGRESS
                                           #            Set this bit to disable scanner dialog
        ("dwOpenFlags", DWORD * 5),        # [0]-[4]: moved to strCLOpen.dummy[0]-[4]
        ("wOpenPtr", ctypes.c_void_p * 6),
        ("zzwDummy", WORD * 8)]             # 88 - 64bit: 112

class PCO_SC2_Hardware_DESC(ctypes.Structure):
    _fields_ = [
        ("szName", ctypes.c_char * 16),     # string with board name
        ("wBatchNo", WORD),                 # production batch no
        ("wRevision", WORD),                # use range 0 to 99
        ("wVariant", WORD),                 # variant    # 22
        ("ZZwDummy", WORD * 20)]            #            # 62

class PCO_SC2_Firmware_DESC(ctypes.Structure):
    _fields_ = [
        ("szName", ctypes.c_char * 16),     # string with device name
        ("bMinorRev", ctypes.c_byte),       # use range 0 to 99
        ("bMajorRev", ctypes.c_byte),       # use range 0 to 255
        ("wVariant", WORD),                 # variant    # 20
        ("ZZwDummy", WORD * 22)]            #            # 64

class PCO_HW_Vers(ctypes.Structure):
    _fields_ = [
        ("BoardNum", WORD),                 # number of devices
        ("Board", PCO_SC2_Hardware_DESC * PCO_MAXVERSIONHW)] # 622

class PCO_FW_Vers(ctypes.Structure):
    _fields_ = [
        ("DeviceNum", WORD),                # number of devices
        ("Device", PCO_SC2_Firmware_DESC * PCO_MAXVERSIONFW)] # 642

class PCO_CameraType(ctypes.Structure):
    _fields_ = [
        ("wSize", WORD),                        # Sizeof this struct
        ("wCamType", WORD),                     # Camera type
        ("wCamSubType", WORD),                  # Camera sub type
        ("ZZwAlignDummy1", WORD),
        ("dwSerialNumber", DWORD),              # Serial number of camera # 12
        ("dwHWVersion", DWORD),                 # Hardware version number
        ("dwFWVersion", DWORD),                 # Firmware version number
        ("wInterfaceType", WORD),               # Interface type          # 22
        ("strHardwareVersion", PCO_HW_Vers),    # Hardware versions of all boards # 644
        ("strFirmwareVersion", PCO_FW_Vers),    # Firmware versions of all devices # 1286
        ("ZZwDummy", WORD * 39)]                #                         # 1364

class PCO_General(ctypes.Structure):
    _fields_ = [
        ("wSize", WORD),                        # Sizeof this struct
        ("ZZwAlignDummy1", WORD),
        ("strCamType", PCO_CameraType),         # previous described structure # 1368
        ("dwCamHealthWarnings", DWORD),         # Warnings in camera system
        ("dwCamHealthErrors", DWORD),           # Errors in camera system
        ("dwCamHealthStatus", DWORD),           # Status of camera system      # 1380
        ("sCCDTemperature", SHORT),             # CCD temperature
        ("sCamTemperature", SHORT),             # Camera temperature           # 1384
        ("sPowerSupplyTemperature", SHORT),     # Power device temperature
        ("ZZwDummy", WORD * 37)]                                               # 1460

class PCO_Description(ctypes.Structure):
    _fields_ = [
        ("wSize", WORD),                        # Sizeof this struct
        ("wSensorTypeDESC", WORD),              # Sensor Type
        ("wSensorSubTypeDESC", WORD),           # Sensor subtype
        ("wMaxHorzResStdDESC", WORD),           # Maxmimum horz. resolution in std.mode
        ("wMaxVertResStdDESC", WORD),           # Maxmimum vert. resolution in std.mode # 10
        ("wMaxHorzResExtDESC", WORD),           # Maxmimum horz. resolution in ext.mode
        ("wMaxVertResExtDESC", WORD),           # Maxmimum vert. resolution in ext.mode
        ("wDynResDESC", WORD),                  # Dynamic resolution of ADC in bit
        ("wMaxBinHorzDESC", WORD),              # Maxmimum horz. binning
        ("wBinHorzSteppingDESC", WORD),         # Horz. bin. stepping (0:bin, 1:lin)    # 20
        ("wMaxBinVertDESC", WORD),              # Maxmimum vert. binning
        ("wBinVertSteppingDESC", WORD),         # Vert. bin. stepping (0:bin, 1:lin)
        ("wRoiHorStepsDESC", WORD),             # Minimum granularity of ROI in pixels
        ("wRoiVertStepsDESC", WORD),            # Minimum granularity of ROI in pixels
        ("wNumADCsDESC", WORD),                 # Number of ADCs in system              # 30
        ("wMinSizeHorzDESC", WORD),             # Minimum x-size in pixels in horz. direction
        ("dwPixelRateDESC", DWORD * 4),         # Possible pixelrate in Hz              # 48
        ("ZZdwDummypr", DWORD * 20),            #                                       # 128
        ("wConvFactDESC", WORD * 4),            # Possible conversion factor in e/cnt   # 136
        ("sCoolingSetpoints", SHORT * 10),      # Cooling setpoints in case there is no cooling range # 156
        ("ZZwDummycv", WORD * 8),               #                                       # 172
        ("wSoftRoiHorStepsDESC", WORD),         # Minimum granularity of SoftROI in pixels
        ("wSoftRoiVertStepsDESC", WORD),        # Minimum granularity of SoftROI in pixels
        ("wIRDESC", WORD),                      # IR enhancment possibility
        ("wMinSizeVertDESC", WORD),             # Minimum y-size in pixels in vert. direction
        ("dwMinDelayDESC", DWORD),              # Minimum delay time in ns
        ("dwMaxDelayDESC", DWORD),              # Maximum delay time in ms
        ("dwMinDelayStepDESC", DWORD),          # Minimum stepping of delay time in ns  # 192
        ("dwMinExposureDESC", DWORD),           # Minimum exposure time in ns
        ("dwMaxExposureDESC", DWORD),           # Maximum exposure time in ms           # 200
        ("dwMinExposureStepDESC", DWORD),       # Minimum stepping of exposure time in ns
        ("dwMinDelayIRDESC", DWORD),            # Minimum delay time in ns
        ("dwMaxDelayIRDESC", DWORD),            # Maximum delay time in ms              # 212
        ("dwMinExposureIRDESC", DWORD),         # Minimum exposure time in ns
        ("dwMaxExposureIRDESC", DWORD),         # Maximum exposure time in ms           # 220
        ("wTimeTableDESC", WORD),               # Timetable for exp/del possibility
        ("wDoubleImageDESC", WORD),             # Double image mode possibility
        ("sMinCoolSetDESC", SHORT),             # Minimum value for cooling
        ("sMaxCoolSetDESC", SHORT),             # Maximum value for cooling
        ("sDefaultCoolSetDESC", SHORT),         # Default value for cooling             # 230
        ("wPowerDownModeDESC", WORD),           # Power down mode possibility
        ("wOffsetRegulationDESC", WORD),        # Offset regulation possibility
        ("wColorPatternDESC", WORD),            # Color pattern of color chip
                                                # four nibbles (0,1,2,3) in word
                                                #  -----------------
                                                #  | 3 | 2 | 1 | 0 |
                                                #  -----------------
                                                #
                                                # describe row,column  2,2 2,1 1,2 1,1
                                                #
                                                #   column1 column2
                                                #  -----------------
                                                #  |       |       |
                                                #  |   0   |   1   |   row1
                                                #  |       |       |
                                                #  -----------------
                                                #  |       |       |
                                                #  |   2   |   3   |   row2
                                                #  |       |       |
                                                #  -----------------
                                                #
        ("wPatternTypeDESC", WORD),             # Pattern type of color chip
                                                # 1: Bayer pattern RGB
        ("wDummy1", WORD),                      # former DSNU correction mode             # 240
        ("wDummy2", WORD),
        ("wNumCoolingSetpoints", WORD),
        ("dwGeneralCapsDESC1", DWORD),          # General capabilities:
                                                # Bit 0: Noisefilter available
											    # Bit 1: Hotpixelfilter available
											    # Bit 2: Hotpixel works only with noisefilter
											    # Bit 3: Timestamp ASCII only available (Timestamp mode 3 enabled)

											    # Bit 4: Dataformat 2x12
											    # Bit 5: Record Stop Event available
											    # Bit 6: Hot Pixel correction
											    # Bit 7: Ext.Exp.Ctrl. not available

											    # Bit 8: Timestamp not available
											    # Bit 9: Acquire mode not available
											    # Bit10: Dataformat 4x16
											    # Bit11: Dataformat 5x16

											    # Bit12: Camera has no internal recorder memory
											    # Bit13: Camera can be set to fast timing mode (PIV)
											    # Bit14: Camera can produce metadata
											    # Bit15: Camera allows Set/GetFrameRate cmd

											    # Bit16: Camera has Correlated Double Image Mode
											    # Bit17: Camera has CCM
											    # Bit18: Camera can be synched externally
											    # Bit19: Global shutter setting not available

											    # Bit20: Camera supports global reset rolling readout
											    # Bit21: Camera supports extended acquire command
											    # Bit22: Camera supports fan control command
											    # Bit23: Camera vert.ROI must be symmetrical to horizontal axis

											    # Bit24: Camera horz.ROI must be symmetrical to vertical axis
											    # Bit25: Camera has cooling setpoints instead of cooling range

											    # Bit26:
											    # Bit27: reserved for future use

											    # Bit28: reserved for future desc.# Bit29:  reserved for future desc.

											    # Bit 30: HW_IO_SIGNAL_DESCRIPTOR available
											    # Bit 31: Enhanced descriptor available
        ("dwGeneralCapsDESC2", DWORD),          # General capabilities 2                  # 252
                                                # Bit 0 ... 29: reserved for future use
                                                # Bit 30: used internally (sc2_defs_intern.h)
                                                # Bit 31: used internally (sc2_defs_intern.h)
        ("dwExtSyncFrequency", DWORD * 4),      # lists four frequencies for external sync feature
        ("dwGeneralCapsDESC3", DWORD),          # general capabilites descr. 3
        ("dwGeneralCapsDESC4", DWORD),          # general capabilites descr. 4            # 276
        ("ZZdwDummy", DWORD * 40)]              #                                         # 436

class PCO_Description2(ctypes.Structure):
    _fields_ = [
        ("wSize", WORD),                                    # Sizeof this struct
        ("ZZwAlignDummy1", WORD),
        ("dwMinPeriodicalTimeDESC2", DWORD),                # Minimum periodical time tp in (nsec)
        ("dwMaxPeriodicalTimeDESC2", DWORD),                # Maximum periodical time tp in (msec)        (12)
        ("dwMinPeriodicalConditionDESC2", DWORD),           # System imanent condition in (nsec)
                                                            # tp - (td + te) must be equal or longer than
                                                            # dwMinPeriodicalCondition
        ("dwMaxNumberOfExposuresDESC2", DWORD),             # Maximum number of exporures possible        (20)
        ("lMinMonitorSignalOffsetDESC2", ctypes.c_long),    # Minimum monitor signal offset tm in (nsec)
                                                            # if(td + tstd) > dwMinMon.)
                                                            #   tm must not be longer than dwMinMon
                                                            # else
                                                            #   tm must not be longer than td + tstd
        ("dwMaxMonitorSignalOffsetDESC2", DWORD),           # Maximum -''- in (nsec)
        ("dwMinPeriodicalStepDESC2", DWORD),                # Minimum step for periodical time in (nsec)  (32)
        ("dwStartTimeDelayDESC2", DWORD),                   # Minimum monitor signal offset tstd in (nsec)
        ("dwMinMonitorStepDESC2", DWORD),                   # see condition at dwMinMonitorSignalOffset
        ("dwMinDelayModDESC2", DWORD),                      # Minimum step for monitor time in (nsec)     (40)
        ("dwMaxDelayModDESC2", DWORD),                      # Minimum delay time for modulate mode in (nsec)
        ("dwMinDelayStepModDESC2", DWORD),                  # Maximum delay time for modulate mode in (msec)
        ("dwMinExposureModDESC2", DWORD),                   # Minimum delay time step for modulate mode in (nsec)(52)
        ("dwMaxExposureModDESC2", DWORD),                   # Minimum exposure time for modulate mode in (nsec)
        ("dwMinExposureStepModDESC2", DWORD),               # Maximum exposure time for modulate mode in (msec)(60)
        ("dwModulateCapsDESC2", DWORD),                     # Minimum exposure time step for modulate mode in (nsec)
        ("dwReserved", DWORD * 16),                         #                                            #(132)
        ("ZZdwDummy", DWORD * 41)]                          #                                            # 296

class PCO_Description_Intensified(ctypes.Structure):
    _fields_ = [
        ("wSize", WORD),                                    # Sizeof this struct
        ("wChannelNumberIntensifiedDESC", WORD),            # 0: Master channel; 1…x: Slave channels
        ("wNumberOfChannelsIntensifiedDESC", WORD),         # Number of active channels in this camera
        ("wMinVoltageIntensifiedDESC", WORD),               # Min voltage for MCP, usually ~700V (GaAs, ~600V)
        ("wMaxVoltageIntensifiedDESC", WORD),               # Max voltage for MCP, usually ~1100V (GaAs, ~900V)
        ("wVoltageStepIntensifiedDESC", WORD),              # Voltage step for MCP, usually 10V
        ("wExtendedMinVoltageIntensifiedDESC", WORD),       # Extended min voltage for MCP, 600V (GaAs, ~500V)
        ("wMaxLoopCountIntensifiedDESC", WORD),             # Maximum loop count for multi exposure (16)
        ("dwMinPhosphorDecayIntensified_ns_DESC", DWORD),   # Minimum decay time in (nsec)
        ("dwMaxPhosphorDecayIntensified_ms_DESC", DWORD),   # Maximum decay time in (msec)        (24)
        ("dwFlagsIntensifiedDESC", DWORD),                  # Flags which gating modes are supported        (28)
                                                            # 0x0001: Gating mode 1 (switch off MCP after and till next exposure)
                                                            # 0x0002: Gating mode 2 (switch off MCP and on when a trigger signal is detected)
        ("szIntensifierTypeDESC", ctypes.c_char * 24),
        # dwMCP_Rectangle??_DESC describes the position of the rectangle including the MCP circle area
        #   referenced to the sensor format which is greater. Note that the data in 1/100 pixel reso-
        #   lution, thus you have to divide the values by 100 to get the pixel coordinate
        # If data is not valid, all values are 0x80000000!
        ("dwMCP_RectangleXL_DESC", DWORD),                  # rectangle of the MCP circle area, x left
        ("dwMCP_RectangleXR_DESC", DWORD),                  # rectangle of the MCP circle area, x right
        ("dwMCP_RectangleYT_DESC", DWORD),                  # rectangle of the MCP circle area, y top
        ("dwMCP_RectangleYB_DESC", DWORD),                  # rectangle of the MCP circle area, y bottom (68)
        ("ZZdwDummy", DWORD * 23)]                          #                                       #(160)

class PCO_DescriptionEx(ctypes.Structure):
    _fields_ = [
        ("wSize", WORD)]  # Sizeof this struct

# Hardware IO Signals definition
# see sc2_defs.h for signal options, type, polarity and filter definitions
NUM_MAX_SIGNALS = 20         # Maximum number of signals available
NUM_SIGNALS = 4
NUM_SIGNAL_NAMES = 4

class PCO_Single_Signal_Desc(ctypes.Structure):
    _fields_ = [
        ("wSize", WORD),                                        # Sizeof this struct
        ("ZZwAlignDummy1", WORD),
        ("strSignalName",(ctypes.c_char*NUM_SIGNAL_NAMES)*25),  # Name of signal 104
                                                                # Specifies NUM_SIGNAL_NAMES functionalities (1-4)
        # https://stackoverflow.com/questions/50003760/python-ctypes-calling-a-function-with-custom-types-in-c
        ("wSignalDefinitions", WORD),   # Flags showing signal options
                                        # 0x01: Signal can be enabled/disabled
                                        # 0x02: Signal is a status (output)
                                        # 0x10: Func. 1 has got timing settings
                                        # 0x20: Func. 2 has got timing settings
                                        # 0x40: Func. 3 has got timing settings
                                        # 0x80: Func. 4 has got timing settings
                                        # Rest: future use, set to zero!
        ("wSignalTypes", WORD),         # Flags showing the selectability of signal types
                                        # 0x01: TTL
                                        # 0x02: High Level TTL
                                        # 0x04: Contact Mode
                                        # 0x08: RS485 diff.
                                        # Rest: future use, set to zero!
        ("wSignalPolarity", WORD),      # Flags showing the selectability
                                        # of signal levels/transitions
                                        # 0x01: High Level active
                                        # 0x02: Low Level active
                                        # 0x04: Rising edge active
                                        # 0x08: Falling edge active
                                        # Rest: future use, set to zero!
        ("wSignalFilter", WORD),        # Flags showing the selectability of filter
                                        # settings
                                        # 0x01: Filter can be switched off (t > ~65ns)
                                        # 0x02: Filter can be switched to medium (t > ~1us)
                                        # 0x04: Filter can be switched to high (t > ~100ms) 112
        ("dwDummy", DWORD * 22)]        # reserved for future use. (only in SDK) 200

class PCO_Signal_Description(ctypes.Structure):
    _fields_ = [
        ("wSize", WORD),            # Sizeof ‘this’ (for future enhancements)
        ("wNumOfSignals", WORD),    # Parameter to fetch the num. of descr. from the camera
        ("strSingeSignalDesc", PCO_Single_Signal_Desc * NUM_MAX_SIGNALS), # Array of singel signal descriptors  # 4004
        ("dwDummy", DWORD * 524)]   # reserved for future use.     # 6100

PCO_SENSORDUMMY = 7
class PCO_Sensor(ctypes.Structure):
    _fields_ = [
        ("wSize", WORD),                                # Sizeof this struct
        ("ZZwAlignDummy1", WORD),
        ("strDescription", PCO_Description),            # previous described structure // 440
        ("strDescription2", PCO_Description2),          # second descriptor            // 736
        ("strDescriptionIntensified", PCO_Description_Intensified), #Intensified camera descriptor        // 896
        ("ZZdwDummy2", DWORD * 216),                    #                              // 1760
        ("wSensorformat", WORD),                        # Sensor format std/ext
        ("wRoiX0", WORD),                               # Roi upper left x
        ("wRoiY0", WORD),                               # Roi upper left y
        ("wRoiX1", WORD),                               # Roi lower right x
        ("wRoiY1", WORD),                               # Roi lower right y            // 1770
        ("wBinHorz", WORD),                             # Horizontal binning
        ("wBinVert", WORD),                             # Vertical binning
        ("wIntensifiedFlags", WORD),                    # Additional Intensified flags for setup: 0x01 - Enable Extended Min Voltage for MCP
        ("dwPixelRate", DWORD),                         # 32bit unsigend, Pixelrate in Hz: // 1780
                                                        # depends on descriptor values
        ("wConvFact", WORD),
        ("wDoubleImage", WORD),
        ("wADCOperation", WORD),
        ("wIR", WORD),
        ("sCoolSet", SHORT),
        ("wOffsetRegulation", WORD),
        ("wNoiseFilterMode", WORD),
        ("wFastReadoutMode", WORD),
        ("wDSNUAdjustMode", WORD),
        ("wCDIMode", WORD),
        ("wIntensifiedVoltage", WORD),
        ("wIntensifiedGatingMode", WORD),
        ("dwIntensifiedPhosphorDecay_us", DWORD),
        ("ZZwDummy", WORD * 32),
        ("strSignalDesc", PCO_Signal_Description),
        ("ZZdwDummy", DWORD * PCO_SENSORDUMMY)]

class PCO_Signal(ctypes.Structure):
    _fields_ = [
        ("wSize", WORD),                    # Sizeof this struct
        ("wSignalNum", WORD),               # Index for strSignal (0,1,2,3,)
        ("wEnabled", WORD),                 # Flag shows enable state of the signal (0: off, 1: on)
        ("wType", WORD),                    # Selected signal type (1: TTL, 2: HL TTL, 4: contact, 8: RS485, 80: TTL-A/GND-B)
        ("wPolarity", WORD),                # Selected signal polarity (1: H, 2: L, 4: rising, 8: falling)
        ("wFilterSetting", WORD),           # Selected signal filter (1: off, 2: med, 4: high) // 12
        ("wSelected", WORD),                # Select signal (0: standard signal, >1 other signal)
        ("ZZwReserved", WORD),
        ("dwParameter", DWORD * 4),         # Timing parameter for signal[wSelected]
        ("dwSignalFunctionality", DWORD * 4),   # Type of functionality behind the signal[wSelected] to select the
                                                # correct parameter set (e.g. 7->Parameter for 'Rolling Shutter exp.signal'
        ("ZZdwReserved", DWORD * 3)]        # 60

class PCO_ImageTiming(ctypes.Structure):
    _fields_ = [
        ("wSize", WORD),
        ("wDummy", WORD),
        ("FrameTime_ns", DWORD),            # Frametime replaces COC_Runtime
        ("FrameTime_s", DWORD),
        ("ExposureTime_ns", DWORD),
        ("ExposureTime_s", DWORD),          # 5
        ("TriggerSystemDelay_ns", DWORD),   # System internal min. trigger delay
        ("TriggerSystemJitter_ns", DWORD),  # Max. possible trigger jitter -0/+ ... ns
        ("TriggerDelay_ns", DWORD),         # Resulting trigger delay = system delay
        ("TriggerDelay_s", DWORD),          # + delay of SetDelayExposureTime ... // 9
        ("ZZdwDummy", DWORD * 11)]          # 80

PCO_TIMINGDUMMY = 24
class PCO_Timing(ctypes.Structure):
    _fields_ = [
        ("wSize", WORD),                                # Sizeof this struct
        ("wTimeBaseDelay", WORD),                       # Timebase delay 0:ns, 1:µs, 2:ms
        ("wTimeBaseExposure", WORD),                    # Timebase expos 0:ns, 1:µs, 2:ms
        ("wCMOSParameter", WORD),                       # Line Time mode: 0: off 1: on    // 8
        ("dwCMOSDelayLines", DWORD),                    # See next line
        ("dwCMOSExposureLines", DWORD),                 # Delay and Exposure lines for lightsheet // 16
        ("dwDelayTable", DWORD * PCO_MAXDELEXPTABLE),   # Delay table             // 80
        ("ZZdwDummy1", DWORD * 110),                    #                           // 520
        ("dwCMOSLineTimeMin", DWORD),                   # Minimum line time in ns
        ("dwCMOSLineTimeMax", DWORD),                   # Maximum line time in ms         // 528
        ("dwCMOSLineTime", DWORD),                      # Current line time value         // 532
        ("wCMOSTimeBase", WORD),                        # Current time base for line time
        ("wIntensifiedLoopCount", WORD),                # Number of loops to use for mutli exposure
        ("dwExposureTable", DWORD * PCO_MAXDELEXPTABLE),# Exposure table       // 600
        ("ZZdwDummy2", DWORD * 110),                    #                       // 1040
        ("dwCMOSFlags", DWORD),                         # Flags indicating the option, whether it is possible to LS-Mode with slow/fast scan, etc.
        ("ZZdwDummy3", DWORD),
        ("wTriggerMode", WORD),                         # Trigger mode                    // 1050
                                                        # 0: auto, 1: software trg, 2:extern 3: extern exp. ctrl
        ("wForceTrigger", WORD),                        # Force trigger (Auto reset flag!)
        ("wCameraBusyStatus", WORD),                    # Camera busy status 0: idle, 1: busy
        ("wPowerDownMode", WORD),                       # Power down mode 0: auto, 1: user // 1056
        ("dwPowerDownTime", DWORD),                     # Power down time 0ms...49,7d     // 1060
        ("wExpTrgSignal", WORD),                        # Exposure trigger signal status
        ("wFPSExposureMode", WORD),                     # Cmos-Sensor FPS exposure mode
        ("dwFPSExposureTime", DWORD),                   # Resulting exposure time in FPS mode // 1068
        ("wModulationMode", WORD),                      # Mode for modulation (0 = modulation off, 1 = modulation on) // 1070
        ("wCameraSynchMode", WORD),                     # Camera synchronization mode (0 = off, 1 = master, 2 = slave)
        ("dwPeriodicalTime", DWORD),                    # Periodical time (unit depending on timebase) for modulation // 1076
        ("wTimeBasePeriodical", WORD),                  # timebase for periodical time for modulation  0 -> ns, 1 -> µs, 2 -> ms
        ("ZZwDummy3", WORD),
        ("dwNumberOfExposures", DWORD),                 # Number of exposures during modulation // 1084
        ("lMonitorOffset", ctypes.c_long),              # Monitor offset value in ns      // 1088
        ("strSignal", PCO_Signal * NUM_MAX_SIGNALS),    # Signal settings               // 2288
        ("wStatusFrameRate", WORD),                     # Framerate status
        ("wFrameRateMode", WORD),                       # Dimax: Mode for frame rate
        ("dwFrameRate", DWORD),                         # Dimax: Framerate in mHz
        ("dwFrameRateExposure", DWORD),                 # Dimax: Exposure time in ns      // 2300
        ("wTimingControlMode", WORD),                   # Dimax: Timing Control Mode: 0->Exp./Del. 1->FPS
        ("wFastTimingMode", WORD),                      # Dimax: Fast Timing Mode: 0->off 1->on
        ("ZZwDummy", WORD * PCO_TIMINGDUMMY)]           # 2352

PCO_STORAGEDUMMY = 39
class PCO_Storage(ctypes.Structure):
    _fields_ = [
        ("wSize", WORD),                        # Sizeof this struct
        ("ZZwAlignDummy1", WORD),
        ("dwRamSize", DWORD),                   # Size of camera ram in pages
        ("wPageSize", WORD),                    # Size of one page in pixel       // 10
        ("ZZwAlignDummy4", WORD),
        ("dwRamSegSize", DWORD * PCO_RAMSEGCNT),# Size of ram segment 1-4 in pages // 28
        ("ZZdwDummyrs", DWORD * 20),            # 108
        ("wActSeg", WORD),                      # no. (0 .. 3) of active segment  // 110
        ("ZZwDummy", WORD * PCO_STORAGEDUMMY)]  # 188

PCO_RECORDINGDUMMY = 22
class PCO_Recording(ctypes.Structure):
    _fields_ = [
        ("wSize", WORD),                        # Sizeof this struct
        ("wStorageMode", WORD),                 # 0 = recorder, 1 = fifo
        ("wRecSubmode", WORD),                  # 0 = sequence, 1 = ringbuffer
        ("wRecState", WORD),                    # 0 = off, 1 = on
        ("wAcquMode", WORD),                    # 0 = internal auto, 1 = external // 10
        ("wAcquEnableStatus", WORD),            # 0 = Acq disabled, 1 = enabled
        ("ucDay", ctypes.c_byte),               # MSB...LSB: day, month, year; 21.March 2003: 0x150307D3
        ("ucMonth", ctypes.c_byte),
        ("wYear", WORD),
        ("wHour", WORD),
        ("ucMin", ctypes.c_byte),
        ("ucSec", ctypes.c_byte),               # MSB...LSB: h, min, s; 17:05:32 : 0x00110520 // 20
        ("wTimeStampMode", WORD),               # 0: no stamp, 1: stamp in first 14 pixel, 2: stamp+ASCII
        ("wRecordStopEventMode", WORD),         # 0: no stop event recording, 1: recording stops with event
        ("dwRecordStopDelayImages", DWORD),     # Number of images which should pass by till stop event rises. // 28
        ("wMetaDataMode", WORD),                # Metadata mode 0: off, 1: meta data will be added to image data
        ("wMetaDataSize", WORD),                # Size of metadata in byte (number of pixel)
        ("wMetaDataVersion", WORD),             # Version info for metadata
        ("ZZwDummy1", WORD),
        ("dwAcquModeExNumberImages", DWORD),    # Number of images for extended acquire mode
        ("dwAcquModeExReserved", DWORD * 4),    # Reserved for future use
        ("ZZwDummy", WORD * PCO_RECORDINGDUMMY)]

class PCO_Segment(ctypes.Structure):
    _fields_ = [
        ("wSize", WORD),                # Sizeof this struct
        ("wXRes", WORD),                # Res. h. = resulting horz.res.(sensor resolution, ROI, binning)
        ("wYRes", WORD),                # Res. v. = resulting vert.res.(sensor resolution, ROI, binning)
        ("wBinHorz", WORD),             # Horizontal binning
        ("wBinVert", WORD),             # Vertical binning                // 10
        ("wRoiX0", WORD),               # Roi upper left x
        ("wRoiY0", WORD),               # Roi upper left y
        ("wRoiX1", WORD),               # Roi lower right x
        ("wRoiY1", WORD),               # Roi lower right y
        ("ZZwAlignDummy1", WORD),       #                                 // 20
        ("dwValidImageCnt", DWORD),     # no. of valid images in segment
        ("dwMaxImageCnt", DWORD),       # maximum no. of images in segment // 28
        ("wRoiSoftX0", WORD),           # SoftRoi upper left x
        ("wRoiSoftY0", WORD),           # SoftRoi upper left y
        ("wRoiSoftX1", WORD),           # SoftRoi lower right x
        ("wRoiSoftY1", WORD),           # SoftRoi lower right y
        ("wRoiSoftXRes", WORD),         # Res. h. = resulting horz.res.(softroi resolution, ROI, binning)
        ("wRoiSoftYRes", WORD),         # Res. v. = resulting vert.res.(softroi resolution, ROI, binning)
        ("wRoiSoftDouble", WORD),       # Soft ROI with double image
        ("ZZwDummy", WORD * 33)]        # 108

class PCO_Image_ColorSet(ctypes.Structure):
    _fields_ = [
        ("wSize", WORD),            # Sizeof this struct
        ("sSaturation", SHORT),     # Saturation from -100 to 100, 0 is default // 4
        ("sVibrance", SHORT),       # Vibrance   from -100 to 100, 0 is default
        ("wColorTemp", WORD),       # Color Temperature from 2000 t0 20000 K
        ("sTint", SHORT),           # Tint       from -100 to 100, 0 is default
        ("wMulNormR", WORD),        # for  setting color ratio (when not using Color
        ("wMulNormG", WORD),        # Temp. and Tint! 1000 corresponds to 1.0 // 14
        ("wMulNormB", WORD),        # normalized: wMulNorm(R + G + B) / 3 = 1000!
        ("sContrast", SHORT),       # Contrast   from -100 to 100, 0 is default
        ("wGamma", WORD),           # Gamma * 0.01 from 40 to 250 => 0.40 to 2.5
        ("wSharpFixed", WORD),      # 0 = off, 100 = max.
        ("wSharpAdaptive", WORD),   # 0 = off, 100 = max. // 24
        ("wScaleMin", WORD),        # 0 to 4095
        ("wScaleMax", WORD),        # 0 to 4095
        ("wProcOptions", WORD),     # Processing Options as bit mask // 30
        ("ZZwDummy", WORD * 93)]    #                                // 216

class PCO_Image(ctypes.Structure):
    _fields_ = [
        ("wSize", WORD),                            # Sizeof this struct
        ("ZZwAlignDummy1", WORD),                   # 4
        ("strSegment", PCO_Segment * PCO_RAMSEGCNT),# Segment info                   // 436
        #PCO_Segment ZZstrDummySeg[6];          // Segment info dummy             // 1084
        # PCO_Segment strSegmentSoftROI[PCO_RAMSEGCNT];// Segment info SoftROI     // 1516
        ("ZZstrDummySeg", PCO_Segment * 14),        # Segment info dummy             // 1948
        ("strColorSet", PCO_Image_ColorSet),        # Image conversion info          // 2164
        ("wBitAlignment", WORD),                    # Bitalignment during readout. 0: MSB, 1: LSB aligned
        ("wHotPixelCorrectionMode", WORD),          # Correction mode for hotpixel
        ("ZZwDummy", WORD * 38)]                    # 2244

PCO_BUFFER_STATICS = int("0xFFFF0000",0)    # Mask for all static flags
# Static flags:
PCO_BUFFER_ALLOCATED = int("0x80000000",0)  # A buffer is allocated
PCO_BUFFER_EVENTDLL = int("0x40000000",0)   # An event is allocated
PCO_BUFFER_ISEXTERN = int("0x20000000",0)   # The buffer was allocated externally
PCO_BUFFER_EVAUTORES = int("0x10000000",0)  # Set this flag to do an 'auto reset' of the
                                            # event, in case you call WaitForBuffer

# Dynamic flags:
PCO_BUFFER_EVENTSET = int("0x00008000",0)  # The event of the buffer is set
# Informations about buffer status flags:
# 00000000 00000000 00000000 00000000
# |||||||| |||||||| |||||||| ||||||||
# ||||              |
# ||||              -------------------- Buffer event is set to signaled
# ||||
# |||----------------------------------- Signaled Buffer event will be reset in WaitForBuffer
# ||------------------------------------ Buffer allocated externally
# |------------------------------------- Buffer event handle created inside DLL
# -------------------------------------- Buffer allocated


class PCO_APIBuffer(ctypes.Structure):
    _fields_ = [
        ("wSize", WORD),                        # Sizeof this struct
        ("ZZwAlignDummy1", WORD),
        ("dwBufferStatus", DWORD),              # Buffer status
        ("hBufferEvent", HANDLE),               # Handle to buffer event  // 12 (16 @64bit)
                                                # HANDLE will be 8byte on 64bit OS and 4byte on 32bit OS.
        ("ZZdwBufferAddress", DWORD),           # Buffer address, obsolete
        ("dwBufferSize", DWORD),                # Buffer size             // 20 (24 @64bit)
        ("dwDrvBufferStatus", DWORD),           # Buffer status in driver
        ("dwImageSize", DWORD),                 # Image size              // 28 (32 @64bit)
        ("pBufferAdress", ctypes.c_void_p),]    # buffer address          // 32 (40 @64bit)
    # the equivalent I try for "#if defined"
    if "_WIN64" not in globals():               # additional dword        // 36 (40 @64bit)
        _fields_.append(("ZZdwDummyFill", DWORD))

    _fields_.append(("ZZwDummy", WORD * 32))     # 100 (104 @64bit)

TAKENFLAG_TAKEN = int("0x0001",0)                       # Device is taken by an application
TAKENFLAG_DEADHANDLE = int("0x0002",0)                  # The handle of this device is invalid because of a camera power down
                                                        # or another device removal
TAKENFLAG_HANDLEVALID = int("0x0004",0)                 # The handle of this device is valid. Changed accoring to DEADHANDLE flag.

APIMANAGEMENTFLAG_SOFTROI_MASK = int("0xFEFE",0)
APIMANAGEMENTFLAG_SOFTROI = int("0x0001",0)             # Soft ROI is active
APIMANAGEMENTFLAG_SOFTROI_RESET = int("0x0100",0)       # Reset Soft ROI to default camera ROI
APIMANAGEMENTFLAG_LINE_TIMING = int("0x0002",0)         # Line timing is available

APIMANAGEMENTFLAG_POWERCYCLE_LENSCTRL = int("0x0001",0) # In case a power on is detected this flag is set in Open (reserved for lens control)

class PCO_APIManagement(ctypes.Structure):
    _fields_ = [
        ("wSize", WORD),                                    # Sizeof this struct
        ("wCameraNum", WORD),                               # Current number of camera
        ("hCamera", HANDLE),                                # Handle of the device
        ("wTakenFlag", WORD),                               # Flags to show whether the device is taken or not. // 10
        ("wAPIManagementFlags", WORD),                      # Flags for internal use                            // 12
        ("pSC2IFFunc", ctypes.c_void_p * 20),               #                                                   // 92 (172 @64bit)
        ("strPCOBuf", PCO_APIBuffer * PCO_BUFCNT),          # Bufferlist                                        // 1692 (1836 @64bit)
        ("ZZstrDummyBuf", PCO_APIBuffer * (28 - PCO_BUFCNT)),   # Bufferlist
        ("sBufferCnt", SHORT),              # Index for buffer allocation
        ("wCameraNumAtInterface", WORD),    # Current number of camera at the interface
        ("wInterface", WORD),               # Interface type (used before connecting to camera)
                                            # different from PCO_CameraType (!)
        ("wXRes", WORD),                    # X Resolution in Grabber (CamLink only)            // 2900 (3092 @64bit)
        ("wYRes", WORD),                    # Y Resolution in Buffer (CamLink only)             // 2902 (3094 @64bit)
        ("wPowerCycleFlag", WORD),          # This will be set to 0xFFFF in order to forward an eventuall power on state
        ("dwIF_param", DWORD * 5),          # Interface specific parameter                      // 2924 (3116 @64bit)
                                            # 0 (FW:bandwidth or CL:baudrate )
                                            # 1 (FW:speed     or CL:clkfreq  )
                                            # 2 (FW:channel   or CL:ccline   )
                                            # 3 (FW:buffer    or CL:data     )
                                            # 4 (FW:iso_bytes or CL:transmit )
        ("wImageTransferMode", WORD),
        ("wRoiSoftX0", WORD),               # Soft ROI settings
        ("wRoiSoftY0", WORD),
        ("wRoiSoftX1", WORD),
        ("wRoiSoftY1", WORD),
        ("wImageTransferParam", WORD * 2),
        ("wImageTransferTxWidth", WORD),
        ("wImageTransferTxHeight", WORD),
        ("ZZwDummy", WORD * 17)]            #                                                    // 2976 (3168 @64bit)

class PCO_Camera(ctypes.Structure):
    _fields_ = [
        ("wSize", WORD),                        # Sizeof this struct
        ("wStructRev", WORD),                   # internal parameter, must be set to PCO_STRUCTDEF
        ("strGeneral", PCO_General),
        ("strSensor", PCO_Sensor),
        ("strTiming", PCO_Timing),
        ("strStorage", PCO_Storage),
        ("strRecording", PCO_Recording),
        ("strImage", PCO_Image),
        ("strAPIManager", PCO_APIManagement),
        ("ZZwDummy", WORD * 40)]                # 17404 (17600 @64Bit)

#/////////////////////////////////////////////////////////////////////
#/////// End: PCO_Camera structure definitions ///////////////////////
#/////////////////////////////////////////////////////////////////////

#/////////////////////////////////////////////////////////////////////
#/////// User Interface and Lens Control defines and structures //////
#/////////////////////////////////////////////////////////////////////

# https://stackoverflow.com/questions/49202120/python-get-contents-of-pointer-to-pointer-to-structure-coming-from-c-dll-to-pyt
"""class HANDLE(ctypes.Structure):
    _fields_ = [
        ("cTitle", ctypes.c_bool)]"""











