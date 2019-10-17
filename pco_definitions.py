""" This file defines the PCOEdge class that contains functions to communicate with
the camera. These python functions are using the C functions from the SC2_Cam.dll
library """

__author__ = 'dplatzer'
import ctypes
import os
import sys
import numpy as np
import traceback
import matplotlib.pyplot as plt
import time, queue

import sc2_SDKStructures as struct

class PCOCAM_Exception(Exception):
    """Camera exceptions."""
    def __init__(self, message):
        Exception.__init__(self, message)

# I use the same framework as in
# https://github.com/patapisp/PCO_PixelFly/blob/master/core/pco_definitions.py
class PCOEdge(object):
    """
       PCOEdge class loads the SC2_Cam.dll in order to interface
       the basic functions of the pco.edge cmos detector.
       """
    def __init__(self):
        # Opening the dll
        libname = os.path.abspath(os.path.join(os.path.dirname(__file__), "SC2_Cam.dll"))
        self.libc = ctypes.CDLL(libname)

        self.iRet = ctypes.c_int()
        self.cam = struct.HANDLE()
        self.RecordingState = struct.WORD()

        self.CameraWarning = struct.DWORD()
        self.CameraError = struct.DWORD()
        self.CameraStatus = struct.DWORD()

        self.bin = 1
        self.v_max = 2048
        self.h_max = 2048
        self.time_modes = {1: "us", 2: "ms"}
        self.set_params = {'ROI': [1, 1, self.h_max, self.v_max],
                           'binning': [1, 1],
                           'Exposure time': [0, '0'],
                           'Camera ROI dimensions': [0, 0]}
        self.armed = False
        self.buffer_numbers = []
        self.buffer_pointers, self.buffer_events = (
            [], [])
        self.out = 0
        # Queues that hold the data collected in the camera.
        self.q = queue.Queue(maxsize=2)
        self.q_m = queue.Queue(maxsize=2)

        """########################################################################"""
        """ Initialization of the C functions in the dll"""
        self.Open_Camera = self.libc.PCO_OpenCamera
        self.Open_Camera.argtypes = [ctypes.POINTER(struct.HANDLE), ctypes.c_int]
        self.Open_Camera.restype = ctypes.c_int

        self.PCO_CancelImages = self.libc.PCO_CancelImages
        self.PCO_CancelImages.argtypes = [struct.HANDLE]
        self.PCO_CancelImages.restype = ctypes.c_int

        self.PCO_GetRecordingState = self.libc.PCO_GetRecordingState
        self.PCO_GetRecordingState.argtypes = [struct.HANDLE, ctypes.POINTER(struct.WORD)]
        self.PCO_GetRecordingState.restype = ctypes.c_int

        self.PCO_ResetSettingsToDefault = self.libc.PCO_ResetSettingsToDefault
        self.PCO_ResetSettingsToDefault.argtypes = [struct.HANDLE]
        self.PCO_ResetSettingsToDefault.restype = ctypes.c_int

        self.PCO_CloseCamera = self.libc.PCO_CloseCamera
        self.PCO_CloseCamera.argtypes = [struct.HANDLE]
        self.PCO_CloseCamera.restype = ctypes.c_int

        self.PCO_ArmCamera = self.libc.PCO_ArmCamera
        self.PCO_ArmCamera.argtypes = [struct.HANDLE]
        self.PCO_ArmCamera.restype = ctypes.c_int

        self.PCO_SetRecordingState = self.libc.PCO_SetRecordingState
        self.PCO_SetRecordingState.argtypes = [struct.HANDLE, struct.WORD]
        self.PCO_SetRecordingState.restype = ctypes.c_int

        self.PCO_GetDelayExposureTime = self.libc.PCO_GetDelayExposureTime
        self.PCO_GetDelayExposureTime.argtypes = [struct.HANDLE, ctypes.POINTER(struct.DWORD), ctypes.POINTER(struct.DWORD),
                                                  ctypes.POINTER(struct.WORD), ctypes.POINTER(struct.WORD)]
        self.PCO_GetDelayExposureTime.restype = ctypes.c_int

        self.PCO_SetDelay_ExposureTime = self.libc.PCO_SetDelayExposureTime
        self.PCO_SetDelay_ExposureTime.argtypes = [struct.HANDLE, ctypes.c_uint32, ctypes.c_uint32,
                                                   ctypes.c_uint16, ctypes.c_uint16]
        self.PCO_SetDelay_ExposureTime.restype = ctypes.c_int

        self.PCO_GetSizes = self.libc.PCO_GetSizes
        self.PCO_GetSizes.argtypes = [struct.HANDLE, ctypes.POINTER(struct.WORD), ctypes.POINTER(struct.WORD),
                                      ctypes.POINTER(struct.WORD), ctypes.POINTER(struct.WORD)]
        self.PCO_GetSizes.restype = ctypes.c_int

        self.PCO_WaitforBuffer = self.libc.PCO_WaitforBuffer
        self.PCO_WaitforBuffer.argtypes = [struct.HANDLE, ctypes.c_int, ctypes.POINTER(struct.PCO_Buflist),
                                           ctypes.c_int]
        self.PCO_WaitforBuffer.restype = ctypes.c_int

        self.PCO_RemoveBuffer = self.libc.PCO_RemoveBuffer
        self.PCO_FreeBuffer = self.libc.PCO_FreeBuffer
        self.PCO_AllocateBuffer = self.libc.PCO_AllocateBuffer
        self.PCO_AddBufferEx = self.libc.PCO_AddBufferEx
        self.PCO_GetBufferStatus = self.libc.PCO_GetBufferStatus
        self.PCO_GetImageEx = self.libc.PCO_GetImageEx
        self.PCO_SetImageParameters = self.libc.PCO_SetImageParameters

    def open_camera(self):
        self.iRet = self.Open_Camera(ctypes.byref(self.cam), 0)
        if (self.iRet != struct.PCO_NOERROR):
            print("No camera found")
            error = 1
        else:
            print('Camera connected!')
            error = 0
        self.iRet = self.PCO_GetRecordingState(self.cam, ctypes.byref(self.RecordingState))
        if self.RecordingState.value == 1:
            self.iRet = self.PCO_SetRecordingState(self.cam, 0)
        # Set camera to default state
        self.iRet = self.PCO_ResetSettingsToDefault(self.cam)
        return error

    def close_camera(self):
        self.iRet = self.PCO_CloseCamera(self.cam)
        if (self.iRet != struct.PCO_NOERROR):
            print("Impossible to close camera")
            raise PCOCAM_Exception
        else:
            print('Camera closed!')

    def get_exposure_time(self):
        dwDelay = ctypes.c_uint32(0)
        dwExposure = ctypes.c_uint32(0)
        wTimeBaseDelay = ctypes.c_uint16(2) # 0 for ns, 1 for us and 2 for ms
        wTimeBaseExposure = ctypes.c_uint16(2) # 0 for ns, 1 for us and 2 for ms
        self.iRet = self.PCO_GetDelayExposureTime(self.cam, ctypes.byref(dwDelay), ctypes.byref(dwExposure),
                                             ctypes.byref(wTimeBaseDelay), ctypes.byref(wTimeBaseExposure))

        print("Exposure time", dwExposure.value, "ms")
        return dwExposure.value

    def set_exposure_time(self, exp_time):
        dwDelay = ctypes.c_uint32(0)
        dwExposure = ctypes.c_uint32(exp_time)
        wTimeBaseDelay = ctypes.c_uint16(2)  # 0 for ns, 1 for us and 2 for ms
        wTimeBaseExposure = ctypes.c_uint16(2)  # 0 for ns, 1 for us and 2 for ms
        self.iRet = self.PCO_SetDelay_ExposureTime(self.cam, dwDelay, dwExposure, wTimeBaseDelay,
                                                   wTimeBaseExposure)
        return None

    def arm_camera(self):
        if self.armed:
            print('Camera already armed')
        else:
            self.iRet = self.PCO_ArmCamera(self.cam)

            self.wXResAct, self.wYResAct, wXResMax, wYResMax = (
                ctypes.c_uint16(), ctypes.c_uint16(), ctypes.c_uint16(),
                ctypes.c_uint16())
            self.iRet = self.PCO_GetSizes(self.cam, ctypes.byref(self.wXResAct),
                                    ctypes.byref(self.wYResAct), ctypes.byref(wXResMax),
                                    ctypes.byref(wYResMax))

            self.set_params['Camera ROI dimensions'] = [self.wXResAct.value,
                                                        self.wYResAct.value]
            self.armed = True

    def disarm_camera(self):
        self.iRet = self.PCO_CancelImages(self.cam)
        # set recording state to 0
        self.iRet = self.PCO_SetRecordingState(self.cam, 0)

        # free all allocated buffers
        #self.PCO_RemoveBuffer(self.cam)

        """for buf in self.buffer_numbers:
            self.PCO_FreeBuffer(self.cam, buf)""" # sometimes makes the program crash with mousemoved
        # after stopping grabbing

        self.buffer_numbers, self.buffer_pointers, self.buffer_events = (
            [], [], [])
        self.armed = False

    def allocate_buffer(self, num_buffers=4):
        """
                Allocate buffers for image grabbing
                :param num_buffers:
                :return:
                """
        dwSize = ctypes.c_uint32(self.wXResAct.value * self.wYResAct.value * 2)  # 2 bytes per pixel
        # set buffer variable to []
        self.buffer_numbers, self.buffer_pointers, self.buffer_events = ([], [], [])
        # now set buffer variables to correct value and pass them to the API

        for i in range(num_buffers):
            self.buffer_numbers.append(ctypes.c_int16(-1))
            self.buffer_pointers.append(ctypes.c_void_p(0))
            self.buffer_events.append(ctypes.c_void_p(0))

            self.PCO_AllocateBuffer(self.cam, ctypes.byref(self.buffer_numbers[i]),
                                              dwSize, ctypes.byref(self.buffer_pointers[i]),
                                              ctypes.byref(self.buffer_events[i]))

    def start_recording(self):
        self.iRet = self.PCO_SetRecordingState(self.cam, 1)

    def _prepare_to_record_to_memory(self,grab_bool):

        dw1stImage, dwLastImage = ctypes.c_uint32(0), ctypes.c_uint32(0)
        wBitsPerPixel = ctypes.c_uint16(16)
        dwStatusDll, dwStatusDrv = ctypes.c_uint32(), ctypes.c_uint32()
        bytes_per_pixel = ctypes.c_uint32(2)
        pixels_per_image = ctypes.c_uint32(self.wXResAct.value * self.wYResAct.value)
        added_buffers = []

        for which_buf in range(len(self.buffer_numbers)):
            if grab_bool:
                err = self.PCO_AddBufferEx(
                    self.cam, dw1stImage, dwLastImage,
                    self.buffer_numbers[which_buf], self.wXResAct,
                    self.wYResAct, wBitsPerPixel)
                #print(f'{which_buf} - {err}')

            added_buffers.append(which_buf)

        # prepare Python data types for receiving data
        # http://stackoverflow.com/questions/7543675/how-to-convert-pointer-to-c-array-to-python-array
        ArrayType = ctypes.c_uint16 * pixels_per_image.value
        self._prepared_to_record = (dw1stImage, dwLastImage,
                                    wBitsPerPixel,
                                    dwStatusDll, dwStatusDrv,
                                    bytes_per_pixel, pixels_per_image,
                                    added_buffers, ArrayType)

    def record_live(self):
        if not self.armed:
            raise UserWarning('Cannot record to memory with disarmed camera')

        if not hasattr(self, '_prepared_to_record'):
            self._prepare_to_record_to_memory(grab_bool=True)

        (dw1stImage, dwLastImage, wBitsPerPixel, dwStatusDll,
         dwStatusDrv, bytes_per_pixel, pixels_per_image, added_buffers, ArrayType) = self._prepared_to_record
        poll_timeout = 5e5
        message = 0
        verbose = False
        self.live = True
        #out_preview = self.record_to_memory(1)[0]

        t0 = time.clock()
        while True:
            if not self.live:
                break

            num_polls = 0
            polling = True

            which_buf = added_buffers.pop(0)
            try:
                while polling:
                    num_polls += 1
                    message = self.PCO_GetBufferStatus(
                        self.cam, self.buffer_numbers[which_buf],
                        ctypes.byref(dwStatusDll), ctypes.byref(dwStatusDrv))
                    if dwStatusDll.value == 0xc0008000:
                        # Buffer exits the queue
                        if verbose:
                            print("After", num_polls, "polls, buffer")
                            print(self.buffer_numbers[which_buf].value)
                            print("is ready.")
                        polling = False
                        t0 = time.clock()
                        break
                    else:
                        time.sleep(0.05)  # Wait 5 milliseconds
                    if num_polls > poll_timeout:
                        print("After %i polls, no buffer." % (poll_timeout))
                        raise TimeoutError
            except TimeoutError:
                print('Timeout error')
                pass

            try:
                if dwStatusDrv.value == 0x00000000 and dwStatusDll.value == 0xc0008000:
                    pass
                elif dwStatusDrv.value == 0x80332028:
                    raise DMAError('DMA error during record_to_memory')
                else:
                    print("dwStatusDrv:", dwStatusDrv.value)
                    raise UserWarning("Buffer status error")

                if verbose:
                    print("Record to memory result:")
                    print(hex(dwStatusDll.value), hex(dwStatusDrv.value))
                    print(message)
                    print('Retrieving image from buffer ', which_buf)
                self.ts = time.clock()
                if self.q.full():
                    self.q.queue.clear()
                if self.q_m.full():
                    self.q_m.queue.clear()

                buffer_ptr = ctypes.cast(self.buffer_pointers[which_buf], ctypes.POINTER(ArrayType))
                out = np.frombuffer(buffer_ptr.contents, dtype=np.uint16).reshape(
                    (self.wYResAct.value, self.wXResAct.value))

                self.q_m.put(np.ndarray.max(out))
                self.q.put(out)

            except UserWarning:
                pass
            finally:
                self.PCO_AddBufferEx(  # Put the buffer back in the queue
                    self.cam, dw1stImage, dwLastImage,
                    self.buffer_numbers[which_buf], self.wXResAct, self.wYResAct,
                    wBitsPerPixel)
                added_buffers.append(which_buf)

    def record_single(self):
        out = []
        if not self.armed:
            raise UserWarning('Cannot record to memory with disarmed camera')

        dw1stImage, dwLastImage = ctypes.c_uint32(0), ctypes.c_uint32(0)
        wBitsPerPixel = ctypes.c_uint16(16)
        wsegment = ctypes.c_uint16(1)
        pixels_per_image = ctypes.c_uint32(self.wXResAct.value * self.wYResAct.value)
        ArrayType = ctypes.c_uint16 * pixels_per_image.value

        iRet = self.PCO_SetImageParameters(self.cam, self.wXResAct, self.wYResAct,
                                              struct.IMAGEPARAMETERS_READ_WHILE_RECORDING,
                                              ctypes.c_void_p(0),ctypes.c_int(0))
        iRet = self.start_recording()
        iRet = self.PCO_GetImageEx(self.cam, wsegment, dw1stImage, dwLastImage,
                                      self.buffer_numbers[0], self.wXResAct, self.wYResAct,
                                      wBitsPerPixel)

        buffer_ptr = ctypes.cast(self.buffer_pointers[0], ctypes.POINTER(ArrayType))
        out = np.frombuffer(buffer_ptr.contents, dtype=np.uint16).reshape(
                (self.wYResAct.value, self.wXResAct.value))

        #iRet = self.PCO_SetRecordingState(self.cam, 0)
        #iRet = self.PCO_FreeBuffer(self.cam, self.buffer_numbers[0]) # crashes if called
        #self.buffer_numbers, self.buffer_pointers, self.buffer_events = (
            #[], [], [])
        #self.armed = False

        return out

    def reset_settings(self):
        self.iRet = self.PCO_ResetSettingsToDefault(self.cam)



class DMAError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)