from PyQt5.QtWidgets import QWidget, QLineEdit, QMainWindow, QApplication,\
    QGridLayout, QPushButton, QLabel, QFileDialog, QGroupBox, QComboBox, QCheckBox, \
    QProgressBar
from PyQt5.QtCore import QTimer, Qt
from pco_definitions import PCOEdge
from threading import Thread
import os, time, sys, traceback
import pyqtgraph as pg
import pyqtgraph.dockarea as dock
import numpy as np
from queue import Empty
from threading import Thread
import threading
import warnings
from copy import deepcopy

import abel_davis_class as abel

""" GUI to display images from the PCO Edge Camera """
"""written by dplatzer"""


class CameraWidget(QWidget):
    """ In the naming of the variables, I tried to use a kind of standard
    concerning the object types:
    btn = QPushButton, le = QLineEdit, fn = function, cb = Checkbox,..."""
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.default_path = 'Q:/LIDYL/Atto/ATTOLAB/SE1/'
        self.cam = PCOEdge()
        self.available = True  # for the mouse_moved function
        self.image_available = False  # any data in self.im (loaded or recorded)?
        self.connected = False
        self.live_view_bool = False
        self.alive = False
        self.cor = np.uint16([50, 100])  # used for thresholding
        self.thresh_bool = False  # Do we do thresholding?
        self.substract_bool = False  # Do we substract background?
        self.data = []
        self.exposure_time = 0
        self.im = []
        self.bkg = []

        self.image_view_thread = []
        self.record_live_thread = []

        # for abel inversion
        self.center_x = 1024
        self.center_y = 1024
        self.dalpha = 1  # in degrees
        self.dr = 1
        self.N_photons = 1
        self.abel_precalc_bool = False  # are the basis functions precalculated?
        self.with_abel_bool = False
        self.color_beta = [(255, 0, 0), (0, 255, 0), (0, 0, 255),
                           (255, 255, 0), (0, 255, 255)]
        self.abel_obj = []
        self.levels_min = 0
        self.levels_max = 20000

        """##############################################################"""
        """GUI main objects Initialization"""
        # central widget of the Main Window
        self.central_widget = dock.DockArea()

        self.dock_control = dock.Dock("", size=(150, 600))
        self.dock_control.hideTitleBar()

        self.dock_direct_image = dock.Dock("Direct Image", size=(600, 600))

        self.dock_beta_even = dock.Dock("even betas", size=(300, 250))
        self.dock_beta_odd = dock.Dock("odd betas", size=(300, 250))


        self.dock_abel = dock.Dock("abel", size=(300, 50))
        #self.dock_abel.hideTitleBar()

        self.central_widget.addDock(self.dock_control, 'left')
        self.central_widget.addDock(self.dock_direct_image, 'right', self.dock_control)
        self.central_widget.addDock(self.dock_beta_odd, 'right')
        self.central_widget.addDock(self.dock_beta_even, 'above', self.dock_beta_odd)
        self.central_widget.addDock(self.dock_abel, 'top', self.dock_beta_even)

        """##############################################################"""
        """ Graphic (1D and 2D) objects initialization"""
        self.gw_even = pg.GraphicsLayoutWidget()
        # make margins around image items zero
        self.gw_even.ci.layout.setContentsMargins(0, 0, 0, 0)
        self.gw_odd = pg.GraphicsLayoutWidget()
        # make margins around image items zero
        self.gw_odd.ci.layout.setContentsMargins(0, 0, 0, 0)

        self.beta_plot = []
        self.beta_curve = []
        for i in range(3):
            if i % 2 == 0:  # even i
                gw = self.gw_even
            else:  # odd i
                gw = self.gw_odd
            gw.nextRow()
            self.beta_plot.append(gw.addPlot(title="P_" + str(i)))
            self.beta_curve.append(self.beta_plot[i].plot(np.random.normal(size=100),
                                   pen=self.color_beta[i],
                                   name="P_" + str(i)))

        self.dock_beta_even.addWidget(self.gw_even)
        self.dock_beta_odd.addWidget(self.gw_odd)

        self.image = pg.ImageItem()
        self.image_view = pg.ImageView(imageItem=self.image)
        self.image_view.view.invertY(False)
        # self.image.setOpts(axisOrder='row-major')

        # doing a custom colormap (trying to make it close to the Labview one)
        pos = np.array([0.0, 0.01, 0.2, 0.4, 0.5, 0.8, 1.0])
        color = np.array([[0, 0, 0, 255], [128, 0, 255, 255], [0, 0, 255, 255],
                          [0, 255, 255, 255], [0, 255, 0, 255],
                          [255, 255, 0, 255], [255, 0, 0, 255]], dtype=np.ubyte)
        map = pg.ColorMap(pos, color)
        #lut = map.getLookupTable(0.0, 1.0, 256)
        self.image_view.setColorMap(map)

        self.image_view.scene.sigMouseMoved.connect(self.mouse_moved)
        self.dock_direct_image.addWidget(self.image_view)

        # just for tests
        self.im = np.load("5000_3945_25cm_r0p1_l3_x45_y0_z0_0deg_1eV_iso_180k_merged.npy")
        self.im[1000,50] += 20
        self.image.setImage(self.im)  # set image to display, used only for tests

        """##############################################################"""
        """ abel settings"""
        self.abel_layout = pg.LayoutWidget()

        self.center_x_le = QLineEdit("")
        self.center_y_le = QLineEdit("")
        self.dalpha_le = QLineEdit("")  # in degrees
        self.dr_le = QLineEdit("")

        self.N_photons_combo = QComboBox()
        self.N_phot_list = ['1', '2']
        self.N_photons_combo.addItems(self.N_phot_list)
        self.N_photons_combo.currentIndexChanged.connect(self.set_n_photons_fn)

        self.with_abel_cb = QCheckBox("with abel")
        self.precalculate_abel_btn = QPushButton("Precalculate")

        self.progress_precalc = QProgressBar()

        self.center_x_le.setText(str(self.center_x))
        self.center_y_le.setText(str(self.center_y))
        self.dalpha_le.setText(str(self.dalpha))
        self.dr_le.setText(str(self.dr))

        self.center_x_le.returnPressed.connect(self.update_center_x)
        self.center_y_le.returnPressed.connect(self.update_center_y)
        self.dalpha_le.returnPressed.connect(self.update_dalpha)
        self.dr_le.returnPressed.connect(self.update_dr)
        self.precalculate_abel_btn.clicked.connect(self.precalculate_abel_fn)
        self.with_abel_cb.stateChanged.connect(self.with_abel_fn)


        self.abel_layout.addWidget(QLabel("center x"), 0, 0)
        self.abel_layout.addWidget(self.center_x_le, 0, 1)
        self.abel_layout.addWidget(QLabel("center y"), 1, 0)
        self.abel_layout.addWidget(self.center_y_le, 1, 1)
        self.abel_layout.addWidget(QLabel("dalpha (deg)"), 0, 2)
        self.abel_layout.addWidget(self.dalpha_le, 0, 3)
        self.abel_layout.addWidget(QLabel("dr"), 1, 2)
        self.abel_layout.addWidget(self.dr_le, 1, 3)
        self.abel_layout.addWidget(QLabel("N photons"), 2, 0)
        self.abel_layout.addWidget(self.N_photons_combo, 2, 1)
        self.abel_layout.addWidget(self.with_abel_cb, 3, 0, 1, 2)
        self.abel_layout.addWidget(self.precalculate_abel_btn, 4, 0)
        self.abel_layout.addWidget(self.progress_precalc, 4, 1, 1, 3)

        self.dock_abel.addWidget(self.abel_layout)

        self.with_abel_cb.setEnabled(False)

        """##############################################################"""
        """ Buttons, controls,... objects initialization"""
        self.controls_layout = pg.LayoutWidget()
        self.controls_layout.layout.setSpacing(10)
        self.open_camera_btn = QPushButton('Open camera')
        self.grab_btn = QPushButton("Grab")
        self.single_btn = QPushButton("Single")
        self.load_btn = QPushButton("Load")
        self.save_current_btn = QPushButton("Save current")
        self.exposure_le = QLineEdit()  # to set exposure time


        self.noise_gb = QGroupBox(self)
        self.noise_gb.setTitle("Background treatment")

        self.noise_combo = QComboBox()
        noise_list = ['None', 'Thresholding', 'Substract']
        self.noise_combo.addItems(noise_list)
        self.noise_combo.currentIndexChanged.connect(self.set_noise_fn)

        self.noise_layout = QGridLayout()
        self.noise_layout.addWidget(self.noise_combo)
        self.noise_gb.setLayout(self.noise_layout)

        self.levels_gb = QGroupBox()
        self.levels_gb.setTitle("Color Levels")

        self.levels_auto_cb = QCheckBox("Color auto")
        self.levels_auto_cb.setCheckState(Qt.Checked)
        self.levels_auto_cb.stateChanged.connect(self.levels_auto_cb_lr)

        self.levels_min_le = QLineEdit(str(self.levels_min))  # to set the min value of the range
        self.levels_min_le.setEnabled(False)
        self.levels_max_le = QLineEdit(str(self.levels_max))  # to set the max value of the range
        self.levels_max_le.setEnabled(False)

        self.levels_min_le.returnPressed.connect(self.update_level_min)
        self.levels_max_le.returnPressed.connect(self.update_level_max)

        self.levels_layout = QGridLayout()
        self.levels_layout.addWidget(self.levels_auto_cb, 0, 0, 1, 4)
        self.levels_layout.addWidget(QLabel("min"), 1, 0, 1, 1)
        self.levels_layout.addWidget(self.levels_min_le, 1, 1, 1, 1)
        self.levels_layout.addWidget(QLabel("max"), 1, 2, 1, 1)
        self.levels_layout.addWidget(self.levels_max_le, 1, 3, 1, 1)

        self.levels_gb.setLayout(self.levels_layout)

        self.coords_lb = QLabel("")  # gives x, y and value where the mouse is
        self.stat_lb = QLabel("")  # gives max and average of the image

        self.grab_btn.setCheckable(True)

        self.open_camera_btn.setFixedSize(80, 30)
        self.grab_btn.setFixedSize(80, 40)
        self.single_btn.setFixedSize(80, 40)
        self.load_btn.setFixedSize(80, 30)
        self.save_current_btn.setFixedSize(80, 30)
        self.exposure_le.setFixedSize(55, 20)
        self.coords_lb.setFixedSize(70, 50)
        self.stat_lb.setFixedSize(70, 30)

        self.open_camera_btn.clicked.connect(self.open_camera_btn_lr)
        self.grab_btn.clicked[bool].connect(self.grab2_fn)
        self.single_btn.clicked.connect(self.single_fn)
        self.load_btn.clicked.connect(self.load_fn)
        self.save_current_btn.clicked.connect(self.save_current_fn)
        self.exposure_le.returnPressed.connect(self.update_exposure)

        self.controls_layout.addWidget(self.open_camera_btn, 0, 0)
        self.controls_layout.addWidget(self.grab_btn, 1, 0)
        self.controls_layout.addWidget(self.single_btn, 1, 1)
        self.controls_layout.addWidget(self.load_btn, 2, 0)
        self.controls_layout.addWidget(self.save_current_btn, 2, 1)
        self.controls_layout.addWidget(QLabel("Exposure time (ms)"), 3, 0)
        self.controls_layout.addWidget(self.exposure_le, 3, 1)

        self.controls_layout.addWidget(self.noise_gb, 4, 0, 1, 2)
        self.controls_layout.addWidget(self.levels_gb, 5, 0, 1, 2)

        empty = QWidget()
        empty.setSizePolicy(1, 1)
        self.controls_layout.addWidget(empty, 6, 0)

        self.controls_layout.addWidget(self.coords_lb, 7, 0)
        self.controls_layout.addWidget(self.stat_lb, 7, 1)

        self.dock_control.addWidget(self.controls_layout)

        self.grab_btn.setEnabled(False)
        self.single_btn.setEnabled(False)
        self.save_current_btn.setEnabled(False)
        self.exposure_le.setEnabled(False)

        self.set_noise_fn(0)

    def with_abel_fn(self, state):
        """ updates the "with abel" QCheckBox (abel Dock)"""
        if state == Qt.Checked:
            self.with_abel_bool = True
        else:
            self.with_abel_bool = False

    def set_noise_fn(self, i):
        """ updates the noise treatment choice QComboBox.
        A change implies to remove all the widgets in the "Background Treatment"
        QGroupBox and to add new ones corresponding to the choice made"""
        if self.thresh_bool:
            self.thresh_bool = False
        if self.substract_bool:
            self.substract_bool = False

        for widget in self.noise_gb.children():
            if isinstance(widget, QGridLayout):
                pass
            else:
                # self.noise_layout.removeWidget(widget)
                widget.setParent(None)

        if i == 0:
            self.noise_gb.setFixedHeight(70)
            self.noise_layout.addWidget(self.noise_combo, 0, 0)

        elif i == 1: # Thresholding
            self.noise_gb.setFixedHeight(160)
            self.cor0_le = QLineEdit(str(self.cor[0]))
            self.cor0_le.returnPressed.connect(self.update_cor0)
            self.cor1_le = QLineEdit(str(self.cor[1]))
            self.cor1_le.returnPressed.connect(self.update_cor1)
            self.thresh_cb = QCheckBox()
            self.thresh_cb.stateChanged.connect(self.update_thresh_bool)
            self.noise_layout.addWidget(self.noise_combo, 0, 0, 1, 2)
            self.noise_layout.addWidget(QLabel("cor0"), 1, 0)
            self.noise_layout.addWidget(self.cor0_le, 1, 1)
            self.noise_layout.addWidget(QLabel("cor1"), 2, 0)
            self.noise_layout.addWidget(self.cor1_le, 2, 1)
            self.noise_layout.addWidget(QLabel("On/Off"), 3, 0)
            self.noise_layout.addWidget(self.thresh_cb, 3, 1)
            lab = QLabel("if signal <= cor1, signal = 0\nif signal > cor1, signal -= cor0")
            self.noise_layout.addWidget(lab, 4, 0, 1, 2)

        elif i == 2: # substraction
            self.noise_gb.setFixedHeight(120)

            self.set_current_bkg_btn = QPushButton("Set current as bkg")
            if not self.image_available:
                self.set_current_bkg_btn.setEnabled(False)
            self.set_current_bkg_btn.clicked.connect(self.set_current_bkg_fn)
            self.substract_cb = QCheckBox()
            self.substract_cb.stateChanged.connect(self.update_substract_bool)

            self.noise_layout.addWidget(self.noise_combo, 0, 0, 1, 2)
            self.noise_layout.addWidget(self.set_current_bkg_btn, 1, 0, 1, 2)
            self.noise_layout.addWidget(QLabel("On/Off"), 2, 0)
            self.noise_layout.addWidget(self.substract_cb, 2, 1)

    def set_n_photons_fn(self, i):
        """ updates the "N photons" QComboBox. A change implies to add or remove figures
         for the plotting of P_i parameters (0<=i<=2N+1)"""
        self.N_photons = int(self.N_phot_list[i])
        if self.abel_precalc_bool:
            self.abel_precalc_bool = False
            self.precalculate_abel_btn.setEnabled(True)
            if self.with_abel_cb.isChecked():
                self.with_abel_cb.toggle()
            self.with_abel_cb.setEnabled(False)
        if self.N_photons == 2:
            self.gw_odd.nextRow()
            self.beta_plot.append(self.gw_odd.addPlot(title="P_3"))
            self.beta_curve.append(self.beta_plot[3].plot(np.random.normal(size=100),
                                   pen=self.color_beta[3],
                                   name="P_3"))
            self.gw_even.nextRow()
            self.beta_plot.append(self.gw_even.addPlot(title="P_4"))
            self.beta_curve.append(self.beta_plot[4].plot(np.random.normal(size=100),
                                    pen=self.color_beta[4],
                                    name="P_4"))
        else:
            self.gw_odd.removeItem(self.beta_plot[3])
            self.gw_even.removeItem(self.beta_plot[4])
            del self.beta_plot[4]
            del self.beta_plot[3]
            del self.beta_curve[4]
            del self.beta_curve[3]
        self.dock_beta_even.repaint()

    def update_thresh_bool(self, state):
        """ updates the "On/Off" QcheckBox (Background treatment, Thresholding)"""
        if state == Qt.Checked:
            self.thresh_bool = True
        else:
            self.thresh_bool = False

    def update_substract_bool(self, state):
        """ updates the "On/Off" QcheckBox (Background treatment, Substraction)"""
        if state == Qt.Checked:
            self.substract_bool = True
        else:
            self.substract_bool = False

    def update_cor0(self):
        """ updates the "cor0" LineEdit (Backgroung treatment, thresholding)"""
        try:
            self.cor[0] = np.uint16(self.cor0_le.text())
        except ValueError:
            print("Incorrect value for cor0, put back to previous value")
            self.cor0_le.setText(str(self.cor[0]))

    def update_cor1(self):
        """ updates the "cor1" LineEdit (Backgroung treatment, thresholding)"""
        try:
            self.cor[1] = np.uint16(self.cor1_le.text())
        except ValueError:
            print("Incorrect value for cor1, put back to previous value")
            self.cor1_le.setText(str(self.cor[1]))

    def levels_auto_cb_lr(self):
        if self.levels_auto_cb.isChecked():
            self.levels_min_le.setEnabled(False)
            self.levels_max_le.setEnabled(False)
        else:
            self.levels_min_le.setEnabled(True)
            self.levels_max_le.setEnabled(True)

    def update_level_min(self):
        """ updates the "levels_min_le" LineEdit ("Color levels" groupbox)"""
        try:
            self.levels_min = np.uint16(self.levels_min_le.text())
        except ValueError:
            print("Incorrect value for cor1, put back to previous value")

    def update_level_max(self):
        """ updates the "levels_max_le" LineEdit ("Color levels" groupbox)"""
        try:
            self.levels_max = np.uint16(self.levels_max_le.text())
        except ValueError:
            print("Incorrect value for cor1, put back to previous value")

    def update_center_x(self):
        """ updates the "center x" LineEdit (abel dock)"""
        try:
            self.center_x = int(self.center_x_le.text())
            if self.abel_precalc_bool:
                self.abel_precalc_bool = False
                self.precalculate_abel_btn.setEnabled(True)
                if self.with_abel_cb.isChecked():
                    self.with_abel_cb.toggle()
                self.with_abel_cb.setEnabled(False)
        except ValueError:
            print("Incorrect value for center x, put back to previous value")
            self.center_x_le.setText(str(self.center_x))

    def update_center_y(self):
        """ updates the "center y" LineEdit (abel dock)"""
        try:
            self.center_y = int(self.center_y_le.text())
            if self.abel_precalc_bool:
                self.abel_precalc_bool = False
                self.precalculate_abel_btn.setEnabled(True)
                if self.with_abel_cb.isChecked():
                    self.with_abel_cb.toggle()
                self.with_abel_cb.setEnabled(False)
        except ValueError:
            print("Incorrect value for center y, put back to previous value")
            self.center_y_le.setText(str(self.center_y))

    def update_dalpha(self):
        """ updates the "dalpha (deg)" LineEdit (abel dock)"""
        try:
            self.dalpha = float(self.dalpha_le.text())
            if self.abel_precalc_bool:
                self.abel_precalc_bool = False
                self.precalculate_abel_btn.setEnabled(True)
                if self.with_abel_cb.isChecked():
                    self.with_abel_cb.toggle()
                self.with_abel_cb.setEnabled(False)
        except ValueError:
            print("Incorrect value for dalpha, put back to previous value")
            self.dalpha_le.setText(str(self.dalpha))

    def update_dr(self):
        """ updates the "dr" LineEdit (abel dock)"""
        try:
            self.dr = float(self.dr_le.text())
            if self.abel_precalc_bool:
                self.abel_precalc_bool = False
                self.precalculate_abel_btn.setEnabled(True)
                if self.with_abel_cb.isChecked():
                    self.with_abel_cb.toggle()
                self.with_abel_cb.setEnabled(False)
        except ValueError:
            print("Incorrect value for dr, put back to previous value")
            self.dr_le.setText(str(self.dr))

    def precalculate_abel_fn(self):
        self.precalculate_abel_btn.setEnabled(False)
        self.grab_btn.setEnabled(False)
        self.precalculate_abel_btn.repaint()
        self.abel_obj = abel.abel_object(data=self.im, center_x=self.center_x,
                                         center_y=self.center_y, d_alpha_deg=self.dalpha,
                                         dr=self.dr, N=self.N_photons, parent=self)
        self.precalc_th = Precalculate_abel(parent=self)
        self.precalc_th.start()

    def abel_invert(self):
        self.abel_obj.set_data(self.im)
        self.abel_obj.invert()

        for i in range(0, 2*self.N_photons+1):
            self.beta_curve[i].setData(self.abel_obj.F[i])

    def image_available_fn(self):
        if not self.image_available:
            self.image_available = True
        if not self.save_current_btn.isEnabled():
            self.save_current_btn.setEnabled(True)
        if self.noise_combo.currentIndex() == 2:
            if not self.set_current_bkg_btn.isEnabled():
                self.set_current_bkg_btn.setEnabled(True)

    def set_current_bkg_fn(self):
        self.bkg = deepcopy(self.im)

    def open_camera_btn_lr(self):
        error = self.cam.open_camera()
        if error == 0:
            self.connected = True
            self.open_camera_btn.setEnabled(False)
            self.grab_btn.setEnabled(True)
            self.single_btn.setEnabled(True)
            self.exposure_le.setEnabled(True)

            self.exposure_time = self.cam.get_exposure_time()
            self.exposure_le.setText(str(self.exposure_time))

    def update_exposure(self):
        if self.alive:
            self.grab2_fn()  # stops grabbing
        try:
            self.exposure_time = int(self.exposure_le.text())
            self.cam.set_exposure_time(self.exposure_time)  # changing exposure time (in ms)
            self.exposure_le.setText(str(self.cam.get_exposure_time()))
        except ValueError:
            print('Incorrect exposure time value')

    def mouse_moved(self, view_pos):
        if self.available and not self.live_view_bool:
            self.available = False
            try:
                data = self.im
                n_rows, n_cols = data.shape
                scene_pos = self.image_view.getImageItem().mapFromScene(view_pos)

                row, col = int(scene_pos.x()), int(scene_pos.y())  # I inverted x and y

                if (0 <= row < n_rows) and (0 <= col < n_cols):
                    value = data[row, col]
                    self.coords_lb.setText('x = {:d}\ny = {:d}\nvalue = {:}'.format(row, col, value))
                    self.coords_lb.repaint()
                else:
                    self.coords_lb.setText('')
                #time.sleep(0.1)
                self.available = True
            except AttributeError:  # when no image is displayed yet
                print(traceback.format_exception(*sys.exc_info()))

    def single_fn(self):
        if self.connected:
            self.single_btn.setEnabled(False)
            self.grab_btn.setEnabled(False)
            self.load_btn.setEnabled(False)
            self.save_current_btn.setEnabled(False)
            self.exposure_le.setEnabled(False)
            self.grab_btn.repaint()  # when forcing this button to repaint, the other widgets do as well

            self.single_thread = Thread(target=self.single_thread_callback)
            self.single_thread.setDaemon(True)
            self.single_thread.start()
            self.single_thread.join()
            if self.thresh_bool:
                self.im[self.im <= self.cor[1]] = np.uint16(0)
                self.im[self.im > self.cor[1]] -= self.cor[0]
            if self.substract_bool:
                self.im = np.int32(self.im) - np.int32(self.bkg) # to have also negative values,
                # otherwise -1 becomes 65535 in uint16 for example
            if not self.levels_auto_cb.isChecked():
                self.image_view.setLevels(self.levels_min, self.levels_max)
                self.image.setImage(self.im, autoLevels=False,
                                     levels=(self.levels_min, self.levels_max))
            else:
                self.image.setImage(self.im)
            # self.image.setImage(self.im)  # doesn't work for exposure times >1000 ms
            max_im = np.int32(self.im.max())
            # im3 = np.delete(im2, np.where(im2 == im2.max()))
            avg = np.int32(np.around(np.average(self.im)))
            self.stat_lb.setText('max = {:}\navg = {:}'.format(max_im, avg))

            if self.with_abel_bool and self.abel_precalc_bool:
                self.abel_invert()

            self.single_btn.setEnabled(True)
            self.grab_btn.setEnabled(True)
            self.load_btn.setEnabled(True)
            self.exposure_le.setEnabled(True)

            self.image_available_fn()

        else:
            print('Error: self.connected = False\n Camera not connected')

    def single_thread_callback(self):
        self.cam.arm_camera() # Arm camera
        print('Camera armed')
        self.cam.allocate_buffer(1)  # Allocate buffers, default = 4 buffers
        image = self.cam.record_single()
        self.im = image.T # putting the image in the right direction
        self.im = self.im[:, ::-1]
        iRet = self.cam.PCO_SetRecordingState(self.cam.cam, 0)
        self.cam.buffer_numbers, self.cam.buffer_pointers, self.cam.buffer_events = (
            [], [], [])
        self.cam.armed = False

    def grab2_fn(self, pressed):
        """ working quite well """
        if pressed:
            self.alive = True

            self.single_btn.setEnabled(False)
            self.load_btn.setEnabled(False)
            self.save_current_btn.setEnabled(False)
            self.exposure_le.setEnabled(False)
            if self.noise_combo.currentIndex() == 2:
                if self.set_current_bkg_btn.isEnabled():
                    self.set_current_bkg_btn.setEnabled(False)

            self.th = Grab(self)
            self.th.start()
        else:
            self.alive = False
            self.th.stop()

            self.single_btn.setEnabled(True)
            self.grab_btn.setEnabled(True)
            self.load_btn.setEnabled(True)
            self.exposure_le.setEnabled(True)
            if self.noise_combo.currentIndex() == 2:
                if not self.set_current_bkg_btn.isEnabled():
                    self.set_current_bkg_btn.setEnabled(True)

            self.image_available_fn()

    def grab_fn(self, pressed):
        """ Not working well and not used """
        if self.connected:
            if pressed:
                self.alive = True
                self.single_btn.setEnabled(False)
                self.load_btn.setEnabled(False)
                self.save_current_btn.setEnabled(False)
                self.exposure_le.setEnabled(False)
                self.levels_min_le.setEnabled(False)
                self.levels_max_le.setEnabled(False)
                try:
                    self.cam.arm_camera()  # Arm camera
                    print('Camera armed')
                    self.cam.start_recording()  # Set recording status to 1
                    self.cam.allocate_buffer(4)  # Allocate buffers, default = 4 buffers
                    self.cam._prepare_to_record_to_memory(grab_bool=True)

                    self.record_live_thread = Thread(target=self.cam.record_live)
                    self.record_live_thread.setDaemon(True)
                    self.record_live_thread.start()
                    print('acquisition started')
                    self.live_view_bool = True
                    self.image_view_thread = ViewImage(self)
                    self.image_view_thread.start()
                    print('view started')
                except Exception:
                    print(traceback.format_exception(*sys.exc_info()))
                    self.stop_callback()

            else:
                self.stop_callback()
                self.single_btn.setEnabled(True)
                self.load_btn.setEnabled(True)
                self.exposure_le.setEnabled(True)
                self.levels_min_le.setEnabled(True)
                self.levels_max_le.setEnabled(True)

                self.image_available_fn()

        else:
            print('Error: self.connected = False\n Camera not connected')

    def stop_callback(self):
        """
        Stops live preview, goes with grab_fn
        :return:
        """
        self.alive = False

        if self.live_view_bool:
            self.live_view_bool = False
            self.cam.live = False  # stop loop that is producing frames

            self.image_view_thread.stop()
            self.image_view_thread.join()
            del self.image_view_thread

            self.record_live_thread.join()
            del self.record_live_thread

            self.cam.disarm_camera() # disarm camera
            print('acquisition stopped')

        return

    def load_fn(self):
        path = str(QFileDialog.getOpenFileName(self, 'Import data', self.default_path)[0])
        if path == "":
            print('loading aborted by user')
        else:
            try:
                self.im = np.load(path)
                self.image.setImage(self.im)
                self.image_available_fn()
            except Exception:
                print(traceback.format_exception(*sys.exc_info()))

    def save_current_fn(self):
        path = str(QFileDialog.getSaveFileName(self, 'Import data', self.default_path)[0])
        if path == "":
            print('saving aborted by user')
        else:
            if self.substract_bool:
                im = np.uint16(self.im + self.bkg)
                bkg = np.uint16(self.bkg)
                print('Saving background')
                save_thread = Save(path+"_bkg", bkg)
                save_thread.start()
            else:
                im = np.uint16(self.im)
            print('Saving raw image')
            save_thread = Save(path, im)
            save_thread.start()

    def threshold_fn(self, pressed):
        if pressed:
            self.thresh_bool = True
        else:
            self.thresh_bool = False


class Grab(Thread):
    """This class is used for displaying single images recursively.
    It goes with the grab2_fn function of the class above (CameraWidget)"""
    def __init__(self, parent):
        Thread.__init__(self)
        self._stop_event = threading.Event()
        self.parent = parent
        self.setDaemon(True)
        self.exposure_time_s = self.parent.exposure_time / 1000
        self.cor = self.parent.cor

    def run(self):
        self.parent.cam.arm_camera()  # Arm camera
        print('Camera armed')
        self.parent.cam.allocate_buffer(1)  # Allocate buffers, default = 4 buffers
        while True:
            if self._stop_event.is_set():
                self.parent.cam.disarm_camera()
                break
            th = Thread(target=self.single_rec)
            th.start()
            th.join()
            self.parent.im = self.parent.im.T  # putting the image in the right direction
            self.parent.im = self.parent.im[:,::-1]
            if self.parent.thresh_bool:
                self.parent.im[self.parent.im <= self.cor[1]] = np.uint16(0)
                self.parent.im[self.parent.im > self.cor[1]] -= self.cor[0]
            if self.parent.substract_bool:
                self.parent.im = np.int32(self.parent.im) - np.int32(self.parent.bkg)  # to have also negative values,
                # otherwise -1 becomes 65535 in uint16 for example
            if not self.parent.levels_auto_cb.isChecked():
                self.parent.image_view.setLevels(self.parent.levels_min,
                                                 self.parent.levels_max)
                self.parent.image.setImage(self.parent.im, autoLevels=False,
                                           levels=(self.parent.levels_min, self.parent.levels_max))
            else:
                self.parent.image.setImage(self.parent.im)
            max_im = np.int32(self.parent.im.max())
            # im3 = np.delete(im2, np.where(im2 == im2.max()))
            avg = np.int32(np.around(np.average(self.parent.im)))
            self.parent.stat_lb.setText('max = {:}\navg = {:}'.format(max_im, avg))
            if self.parent.with_abel_bool and self.parent.abel_precalc_bool:
                self.parent.abel_invert()
            else:
                time.sleep(max(0.5, self.exposure_time_s))

    def single_rec(self):
        self.parent.im = self.parent.cam.record_single()

    def stop(self):
        self._stop_event.set()


class ViewImage(Thread):
    """Not used right now"""
    """This class is used for displaying the images stored on self.cam.q
    It goes with the grab_fn function of the class above (CameraWidget)"""
    def __init__(self, parent):
        Thread.__init__(self)
        self._stop_event = threading.Event()
        self.parent = parent
        self.isRunning = False
        self.setDaemon(True)
        self.exposure_time_s = self.parent.exposure_time/1000

    def run(self):
        # time.sleep(max(self.exposure_time_s*3, 0.5))
        corr1 = np.uint16(self.parent.cor[0])
        corr2 = np.uint16(self.parent.cor[1])

        while True:
            if self._stop_event.is_set():
                self.parent.im = deepcopy(im)
                break
            try:

                # get newest frame from queue. Transpose it so that is fits the coordinates convention
                im = self.parent.cam.q.get().T
                im = im[:,::-1]
                if self.parent.thresh_bool:
                    im[im <= corr2] = np.uint16(0)
                    im[im > corr2] -= corr1
                self.parent.image.setImage(im)
                max_im = np.uint16(im.max())
                avg = np.uint16(np.around(np.average(im)))
                self.parent.stat_lb.setText('max = {:}\navg = {:}'.format(max_im, avg))
                #self.parent.im = im

            except Exception:
                print(traceback.format_exception(*sys.exc_info()))

            time.sleep(max(0.5, self.exposure_time_s))  # you can decrease 0.5, but the fps will stay low anyway

    def stop(self):
        self._stop_event.set()


class Save(Thread):
    """This class is used for saving images to .npy file"""
    def __init__(self, path, image, parent=CameraWidget):
        Thread.__init__(self)
        self.parent = parent
        self.path = path
        self.im = image

    def run(self):
        np.save(self.path, self.im)
        print("image saved")


class Precalculate_abel(Thread):
    def __init__(self, parent=None):
        Thread.__init__(self)
        self.parent = parent

    def run(self):
        self.parent.abel_obj.precalculate()
        self.parent.abel_precalc_bool = True
        self.parent.with_abel_cb.setEnabled(True)
        if self.parent.connected:
            self.parent.grab_btn.setEnabled(True)


if __name__ == '__main__':

    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle('PCO Acquisition by Dom')

    pco_ui = CameraWidget(parent=None)
    window.setCentralWidget(pco_ui.central_widget)
    window.resize(1000, 500)
    window.show()
    sys.exit(app.exec_())
