#!/usr/bin/python3
# -*- coding: utf-8 -*-

import configparser
import serial
from serial.tools.list_ports import comports
import json
import time
import os
import tkinter as tk
import tkinter.ttk as ttk
import pygubu
import math
import numpy as np
from scipy.interpolate import make_interp_spline, BSpline
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FigureCanvas
import csv
from svg import Parser, Rasterizer, SVG
from PIL import Image, ImageTk

try:
    path = sys._MEIPASS
except Exception:
    try:
        path = os.path.abspath(os.path.dirname(__file__))
    except NameError:
        path = os.path.dirname(os.path.abspath(sys.argv[0]))


imgpath = os.path.join(path, 'images')

config = configparser.ConfigParser()
config.read(path + "/xray.ini")

ser = serial.Serial()
ser.baudrate = 115200
ser.timeout = 1
ser.write_timeout = 1

counts = []

startsteps = -1
stepsize = -1
stepsperangle = -1
measurementstotal = -1
time = -1
d = -1

do_plot = False
do_lambda = False
do_persecond = False
do_subtractbackground = False
do_smooth = False
do_zoom = False

saving = False

class MyApplication():

    def __init__(self):
        self.about_dialog = None
        self.d_dialog = None
        
        self.builder = b = pygubu.Builder()
        b.add_from_file(os.path.join(path, 'xray.ui'))
        
        self.mainwindow = b.get_object('Mainwindow_1')

        self.mainmenu = menu = b.get_object('mainmenu', self.mainwindow)
        self.mainwindow.config(menu=menu)

        self.pages = {}
        self.pages["ChooseSerial"] = b.get_object('mw1_frame')
        self.pages["ZeroCounter"] = b.get_object('mw2_frame')
        self.pages["ZeroCrystal"] = b.get_object('mw3_frame')
        self.pages["SetMax"] = b.get_object('mw4_frame')
        self.pages["SetParams"] = b.get_object('mw5_frame')
        self.pages["Measure"] = b.get_object('mw6_frame')
        self.pages["TurnOn"] = b.get_object('mw7_frame')
        self.pages["Save"] = b.get_object('mw8_frame')
        self.pages["Table"] = b.get_object('plot_table')
        self.pages["Plot"] = b.get_object('plot_plot')

        self.pages["ChooseSerial"].tkraise()

        setSerialPort(self)
        loadRecentParamters(self)
        loadConstants(self)
        self.img_zerocounter = rasterize("xray/zerocounter.svg", 2)
        b.get_object("Zerocounter").config(image=self.img_zerocounter)
        self.img_zerocrystal = rasterize("xray/zerocrystal.svg", 2)
        b.get_object("Zerocrystal").config(image=self.img_zerocrystal)
        self.img_setmax = rasterize("xray/setmax.svg", 2)
        b.get_object("SetMax").config(image=self.img_setmax)
        self.img_turnon = rasterize("xray/turnon.svg", 2)
        b.get_object("Turnon").config(image=self.img_turnon)
        self.img_save = rasterize("xray/save.svg")

        self.img_fastup = rasterize("xray/arrow-double-up.svg")
        b.get_object("StepperFastUp_1").config(image=self.img_fastup)
        b.get_object("StepperFastUp_2").config(image=self.img_fastup)
        self.img_slowup = rasterize("xray/arrow-single-up.svg")
        b.get_object("StepperSlowUp_1").config(image=self.img_slowup)
        b.get_object("StepperSlowUp_2").config(image=self.img_slowup)
        self.img_slowdown = rasterize("xray/arrow-single-down.svg")
        b.get_object("StepperSlowDown_1").config(image=self.img_slowdown)
        b.get_object("StepperSlowDown_2").config(image=self.img_slowdown)
        self.img_fastdown = rasterize("xray/arrow-double-down.svg")
        b.get_object("StepperFastDown_1").config(image=self.img_fastdown)
        b.get_object("StepperFastDown_2").config(image=self.img_fastdown)

        loadPlotButtonIcons(self)
        iconizePlotButtons(self)
        b.get_object("btn_plot_1").config(image=self.img_plot)
        b.get_object("btn_table_1").config(image=self.img_table)
        b.get_object("btn_plot_7").config(image=self.img_save)
        b.get_object("btn_table_5").config(image=self.img_save)

        self.mainwindow.protocol("WM_DELETE_WINDOW", self.quit)
        
        b.connect_callbacks(self)

    def on_about_clicked(self):
        if self.about_dialog is None:
            dialog = self.builder.get_object("dialog_about", self.mainwindow)
            self.about_dialog = dialog
            
            def dialog_btnclose_clicked():
                dialog.close()

            btnclose = self.builder.get_object("About_Close")
            btnclose["command"] = dialog_btnclose_clicked
            
            dialog.run()
        else:
            self.about_dialog.show()

    def on_set_d_clicked(self):
        if self.d_dialog is None:
            dialog = self.builder.get_object("Window_set_d", self.mainwindow)
            self.d_dialog = dialog
            
            def dialog_btnclose_clicked():
                try:
                    config["Crystal"]["d"] = self.builder.get_object("D_Entry").get()
                except KeyError:
                    config["Crystal"] = {}
                    config["Crystal"]["d"] = self.builder.get_object("D_Entry").get()
                d = abs(float(config["Crystal"]["d"]))
                dialog.close()

            def validateFloat(value_new, value_old):
                allowed = False
                try:
                    float(value_new)
                    btnclose.config(state="normal")
                    allowed = True
                except ValueError:
                    try:
                        float(value_old)
                        btnclose.config(state="normal")
                        allowed = False
                    except ValueError:
                        btnclose.config(state="disabled")
                    if len(value_new) < len(value_old):
                        btnclose.config(state="disabled")
                        allowed = True
                    if value_new[-1:] == "e":
                        try:
                            float(value_new[:-1])
                            btnclose.config(state="disabled")
                            allowed = True
                        except ValueError:
                            pass
                    elif value_new[-2:] == "e-" or value_new[-2:] == "e+":
                        try:
                            float(value_new[:-2])
                            btnclose.config(state="disabled")
                            allowed = True
                        except ValueError:
                            pass
                return allowed

            entry_d = self.builder.get_object("D_Entry")
            entry_d.delete(0, tk.END)
            entry_d.insert(0, "{:0.3e}".format(d))
            entry_d["validatecommand"] = (entry_d.register(validateFloat), "%P", "%s")
            entry_d["validate"] = "key"
            btnclose = self.builder.get_object("Set_D_Button")
            btnclose["command"] = dialog_btnclose_clicked
            
            dialog.run()
        else:
            entry_d = self.builder.get_object("D_Entry")
            entry_d.delete(0, tk.END)
            entry_d.insert(0, "{:0.3e}".format(d))
            self.d_dialog.show()

    def on_resetmax_clicked(self):
        config["Stepper"] = {}
        resetHints(self)
        self.pages["ChooseSerial"].tkraise()

    def on_reset_clicked(self):
        global config
        global do_plot, do_lambda, do_persecond, do_subtractbackground, do_smooth, do_zoom
        os.remove(path + "/xray.ini")
        config = configparser.ConfigParser()
        config.read(path + "/xray.ini")
        resetHints(self)
        resetParameters(self)
        do_plot = False
        do_lambda = False
        do_persecond = False
        do_subtractbackground = False
        do_smooth = False
        do_zoom = False
        self.pages["ChooseSerial"].tkraise()
    
    def btn_ok1_clicked(self):
        serial_selected = None
        selection_string = self.builder.get_object('SerialCombo').current()
        for s in comports():
            if s.device == selection_string:
                serial_selected = s
        if serial_selected and serial_selected.vid and serial_selected.pid:
            config["Serial"] = {}
            config["Serial"]["vid"] = str(serial_selected.vid)
            config["Serial"]["pid"] = str(serial_selected.pid)
        self.pages["ZeroCounter"].tkraise()
    def btn_ok2_clicked(self):
        self.pages["ZeroCrystal"].tkraise()
    def btn_ok3_clicked(self):
        serialWrite(b'{"command":"sethome"}')
        try:
            try:
                int(config["Stepper"]["maximum"])
                float(config["Stepper"]["angle"])
                self.pages["SetParams"].tkraise()
                return
            except KeyError:
                pass
        except ValueError:
            pass
        self.pages["SetMax"].tkraise()
    def btn_ok4_clicked(self):
        try:
            serialWrite(b'{"command":"position"}')
            data = json.loads(serialRead())
            config["Stepper"] = {}
            config["Stepper"]["maximum"] = str(data["position"])	
            config["Stepper"]["angle"] = self.builder.get_object('MaxAngle').get()
            cmd = '{"command":"goto", "steps":' + str(-int(config["Stepper"]["maximum"])) + ', "velocity":"2000"}'
            serialWrite(cmd.encode("utf-8"))
        except json.decoder.JSONDecodeError:
            pass
        self.pages["SetParams"].tkraise()
    def btn_ok5_clicked(self):
        self.builder.get_object("btn_ok_parameters").config(state="disabled")
        self.pages["Measure"].tkraise()
    def btn_ok6_clicked(self):
        countsentry = self.builder.get_object('CountsEntry')
        if len(counts) == 0:
            counts.append(abs(int(countsentry.get())))
            countsentry.delete(0, tk.END)
            self.builder.get_object("btn_ok_measure").config(state="disabled")
            cmd = '{"command":"goto", "steps":' + str(startsteps) + ', "velocity":"2000"}'
            serialWrite(cmd.encode("utf-8"))
            self.pages["TurnOn"].tkraise()
            self.builder.get_object('hint_label_measure').config(text="Messung durchführen.")
        elif len(counts) < measurementstotal:
            counts.append(abs(int(countsentry.get())))
            countsentry.delete(0, tk.END)
            self.builder.get_object("btn_ok_measure").config(state="disabled")
            cmd = '{"command":"goto", "steps":' + str(stepsize) + ', "velocity":"2000"}'
            serialWrite(cmd.encode("utf-8"))
        else:
            counts.append(abs(int(countsentry.get())))
            countsentry.delete(0, tk.END)
            self.builder.get_object("btn_ok_measure").config(state="disabled")
            try:
                serialWrite(b'{"command":"position"}')
                data = json.loads(serialRead())
                cmd = '{"command":"goto", "steps":' + str(-data["position"]) + ', "velocity":"2000"}'
                serialWrite(cmd.encode("utf-8"))
            except json.decoder.JSONDecodeError:
                pass
            self.pages["Save"].tkraise()
    def btn_ok7_clicked(self):
        self.pages["Measure"].tkraise()
    def btn_ok8_clicked(self):
        filepath = self.builder.get_object("pathchooserinput").cget("path") + "/" + self.builder.get_object("filenameentry").get()
        if not saving:
            if not filepath[-4:] == ".dat":
                filepath = filepath + ".dat"
            savefile = configparser.ConfigParser()
            savefile.read(filepath)
            savefile["Parameters"] = {}
            savefile["Parameters"]["stepsize"] = str(stepsize)
            savefile["Parameters"]["time"] = str(time)
            savefile["Parameters"]["startsteps"] = str(startsteps)
            savefile["Parameters"]["stepsperangle"] = str(stepsperangle)
            savefile["Parameters"]["d"] = config["Crystal"]["d"]
            savefile["Data"] = {}
            savefile["Data"]["counts"] = str(counts)
            with open(filepath, "w") as save:
                savefile.write(save)
            self.pages["Table"].tkraise()
            drawTable(self)
        else:
            if do_plot:
                if filepath[-4:] == ".svg":
                    drawPlot(self, filepath)
                elif filepath[-4:] == ".png":
                    drawPlot(self, filepath)
                elif filepath[-4:] == ".jpg":
                    drawPlot(self, filepath)
                elif filepath[-5:] == ".jpeg":
                    drawPlot(self, filepath)
                else:
                    drawPlot(self, filepath + ".png")
                self.pages["Plot"].tkraise()
            else:
                if filepath[-4:] == ".csv":
                    drawTable(self, filepath)
                else:
                    drawTable(self, filepath + ".csv")
                self.pages["Table"].tkraise()

    def btn_show_table(self):
        self.builder.get_object("btn_show_table").config(state="disabled")
        self.pages["Table"].tkraise()
        drawTable(self)

    def btn_fast_up(self, event=None):
        serialWrite(b'{"command":"move", "direction":"up", "velocity":"1000"}')
    def btn_slow_up(self, event=None):
        serialWrite(b'{"command":"move", "direction":"up", "velocity":"4000"}')
    def btn_slow_down(self, event=None):
        serialWrite(b'{"command":"move", "direction":"down", "velocity":"4000"}')
    def btn_fast_down(self, event=None):
        serialWrite(b'{"command":"move", "direction":"down", "velocity":"1000"}')
    def btn_move_released(self, event=None):
        serialWrite(b'{"command":"stop"}')

    def serialcombo_selected(self, event=None):
        success = False
        if ser.is_open:
            ser.close()
        ser.port = self.builder.get_object('SerialCombo').current()
        try:
            ser.open()
            ser.write(b'{"command":"ping"}')
            if ser.readline() == b'pong\r\n':
                success = True
                self.builder.get_object('ErrorLabelSerial').config(text="")
        except serial.SerialException:
            pass
        if not success:
            self.builder.get_object('ErrorLabelSerial').config(text="Achtung: kein Arduino an ausgewähltem Port!")
            updateSerialCombo(self)

    def loadpath_selected(self, event=None):
        global stepsize, time, startsteps, stepsperangle, d, counts
        filepath = self.builder.get_object('loaddatapath').cget("path")
        success = False
        try:
            try:
                try:
                    try: 
                        loadfile = configparser.ConfigParser()
                        loadfile.read(filepath)
                        stepsize = float(loadfile["Parameters"]["stepsize"])
                        time = float(loadfile["Parameters"]["time"])
                        startsteps = float(loadfile["Parameters"]["startsteps"])
                        stepsperangle = float(loadfile["Parameters"]["stepsperangle"])
                        d = float(loadfile["Parameters"]["d"])
                        config["Crystal"]["d"] = loadfile["Parameters"]["d"]
                        counts = json.loads(loadfile["Data"]["counts"])

                        self.builder.get_object('ErrorLabelLoad').config(text="")
                        self.builder.get_object("btn_show_table").config(state="normal")
                        success = True
                    except KeyError:
                        pass
                except ValueError:
                    pass
            except configparser.Error:
                pass
        except json.decoder.JSONDecodeError:
                pass
        if not success:
            self.builder.get_object('ErrorLabelLoad').config(text="Achtung: Datei konnte nicht gelesen werden.")
            self.builder.get_object("btn_show_table").config(state="disabled")

    def btn_plot(self):
        global do_plot, do_lambda, do_persecond, do_subtractbackground, do_smooth, do_zoom
        if do_plot:
            do_plot = False
            do_lambda = False
            do_persecond = False
            do_subtractbackground = False
            do_smooth = False
            do_zoom = False
            drawTable(self)
            self.pages["Table"].tkraise()
        else:
            do_plot = True
            do_lambda = True
            do_persecond = True
            do_subtractbackground = True
            do_smooth = True
            do_zoom = True
            drawPlot(self)
            self.pages["Plot"].tkraise()
        iconizePlotButtons(self)

    def btn_lambda(self):
        global do_lambda
        if do_lambda:
            do_lambda = False
        else:
            do_lambda = True
        if do_plot:
            drawPlot(self)
        else:
            drawTable(self)
        iconizePlotButtons(self)
            
    def btn_persecond(self):
        global do_persecond
        if do_persecond:
            do_persecond = False
        else:
            do_persecond = True
        if do_plot:
            drawPlot(self)
        else:
            drawTable(self)
        iconizePlotButtons(self)

    def btn_background(self):
        global do_subtractbackground
        if do_subtractbackground:
            do_subtractbackground = False
        else:
            do_subtractbackground = True
        if do_plot:
            drawPlot(self)
        else:
            drawTable(self)
        iconizePlotButtons(self)

    def btn_smooth(self):
        global do_smooth
        if do_smooth:
            do_smooth = False
        else:
            do_smooth = True
        if do_plot:
            drawPlot(self)
        else:
            drawTable(self)
        iconizePlotButtons(self)

    def btn_zoom(self):
        global do_zoom
        if do_zoom:
            do_zoom = False
        else:
            do_zoom = True
        if do_plot:
            drawPlot(self)
        else:
            drawTable(self)
        iconizePlotButtons(self)

    def btn_save(self):
        global saving
        saving = True
        self.builder.get_object("hint_label_save").config(text="Auswertung speichern.")
        if do_plot:
            self.builder.get_object("filenameentry").delete(0, tk.END)
            self.builder.get_object("filenameentry").insert(0, "spektrum.png")
        else:
            self.builder.get_object("filenameentry").delete(0, tk.END)
            self.builder.get_object("filenameentry").insert(0, "spektrum.csv")
        self.pages["Save"].tkraise()


    def quit(self, event=None):
        with open(path + "/xray.ini", "w") as configfile:
            config.write(configfile)
        if ser.is_open:
            ser.close()
        self.mainwindow.quit()

    def run(self):
        self.mainwindow.mainloop()

    def validateParameters(self, event=None):
        calculateParameters(self)

    def validateFloat(self, value_new, value_old, btn = None):
        if btn:
            btn_obj = self.builder.get_object(btn)
        allowed = False
        try:
            float(value_new)
            if btn:
                btn_obj.config(state="normal")
            allowed = True
        except ValueError:
            try:
                float(value_old)
                if btn:
                    btn_obj.config(state="normal")
                allowed = False
            except ValueError:
                if btn:
                    btn_obj.config(state="disabled")
            if len(value_new) < len(value_old):
                if btn:
                    btn_obj.config(state="disabled")
                allowed = True
        return allowed

    def validateInt(self, value_new, value_old, btn = None):
        if btn:
            btn_obj = self.builder.get_object(btn)
        allowed = False
        try:
            int(value_new)
            if btn:
                btn_obj.config(state="normal")
            allowed = True
        except ValueError:
            try:
                int(value_old)
                if btn:
                    btn_obj.config(state="normal")
                allowed = False
            except ValueError:
                if btn:
                    btn_obj.config(state="disabled")
            if len(value_new) < len(value_old):
                if btn:
                    btn_obj.config(state="disabled")
                allowed = True
        return allowed

def serialWrite(msg):
    try:
        ser.write(msg)
    except serial.SerialException:
        pass

def serialRead():
    try:
        return ser.readline().decode("utf-8")
    except serial.SerialException:
        return ""

def resetHints(self):
    self.builder.get_object('hint_label_measure').config(text="Hintergrundstrahlung messen.")
    self.builder.get_object('ErrorLabelLoad').config(text="")
    self.builder.get_object('ErrorLabelSerial').config(text="")
    self.builder.get_object("hint_label_save").config(text="Messergebnisse speichern.")
    setSerialPort(self)
    self.builder.get_object('MaxAngle').delete(0, tk.END)

def resetParameters(self):
    #self.builder.get_object('loaddatapath').cget("path")
    #self.builder.get_object("pathchooserinput").cget("path")
    self.builder.get_object('StepsizeEntry').delete(0, tk.END)
    self.builder.get_object('TimeEntry').delete(0, tk.END)
    self.builder.get_object('StartangleEntry').delete(0, tk.END)
    self.builder.get_object('EndangleEntry').delete(0, tk.END)

def updateSerialCombo(self):
    ports = []
    for s in comports():
        ports.append(s.device)
    self.builder.get_object('SerialCombo').config(values=ports)

def rasterize(vectorgraphic, scale = 1):
    svg = Parser.parse_file(os.path.join(imgpath, vectorgraphic))
    rast = Rasterizer()
    buff = rast.rasterize(svg, int(svg.width * scale), int(svg.height * scale), scale)
    im = Image.frombytes('RGBA', (int(svg.width * scale), int(svg.height * scale)), buff)
    return ImageTk.PhotoImage(im)

def loadPlotButtonIcons(self):
    self.img_plot = rasterize("plot/plot.svg")
    self.img_table = rasterize("plot/table.svg")
    self.img_do_lambda = rasterize("plot/lambda.svg")
    self.img_dont_lambda = rasterize("plot/theta.svg")
    self.img_do_persecond = rasterize("plot/persecond.svg")
    self.img_dont_persecond = rasterize("plot/pertime.svg")
    self.img_do_subtractbackground = rasterize("plot/back.svg")
    self.img_dont_subtractbackground = rasterize("plot/noback.svg")
    self.img_do_smooth = rasterize("plot/smooth.svg")
    self.img_dont_smooth = rasterize("plot/sharp.svg")
    self.img_do_zoom = rasterize("plot/zoom.svg")
    self.img_dont_zoom = rasterize("plot/nozoom.svg")

def iconizePlotButtons(self):
    if do_lambda:
        self.builder.get_object("btn_table_2").config(image=self.img_do_lambda)
        self.builder.get_object("btn_plot_2").config(image=self.img_do_lambda)
    else:
        self.builder.get_object("btn_table_2").config(image=self.img_dont_lambda)
        self.builder.get_object("btn_plot_2").config(image=self.img_dont_lambda)
    if do_persecond:
        self.builder.get_object("btn_table_3").config(image=self.img_do_persecond)
        self.builder.get_object("btn_plot_3").config(image=self.img_do_persecond)
    else:
        self.builder.get_object("btn_table_3").config(image=self.img_dont_persecond)
        self.builder.get_object("btn_plot_3").config(image=self.img_dont_persecond)
    if do_subtractbackground:
        self.builder.get_object("btn_table_4").config(image=self.img_do_subtractbackground)
        self.builder.get_object("btn_plot_4").config(image=self.img_do_subtractbackground)
    else:
        self.builder.get_object("btn_table_4").config(image=self.img_dont_subtractbackground)
        self.builder.get_object("btn_plot_4").config(image=self.img_dont_subtractbackground)
    if do_smooth:
        self.builder.get_object("btn_plot_5").config(image=self.img_do_smooth)
    else:
        self.builder.get_object("btn_plot_5").config(image=self.img_dont_smooth)
    if do_zoom:
        self.builder.get_object("btn_plot_6").config(image=self.img_do_zoom)
    else:
        self.builder.get_object("btn_plot_6").config(image=self.img_dont_zoom)

def calculateParameters(self):
    try:
        global startsteps, stepsize, stepsperangle, measurementstotal, time
        stepangle = float(self.builder.get_object('StepsizeEntry').get())
        time = float(self.builder.get_object('TimeEntry').get())
        startangle = float(self.builder.get_object('StartangleEntry').get())
        endangle = float(self.builder.get_object('EndangleEntry').get())

        stepsperangle = abs(int(config["Stepper"]["maximum"])) // abs(float(config["Stepper"]["angle"]))
        stepsize = stepsperangle * stepangle
        startsteps = stepsperangle * startangle
        stepstotal = stepsperangle * abs(endangle - startangle)
        measurementstotal = stepstotal // stepsize
        timetotal = measurementstotal * time
        config["Parameters"] = {"stepangle": str(stepangle), "time": str(time), "startangle": str(startangle), "endangle": str(endangle)}
        self.builder.get_object('N_Measurements').config(text="Messungen: " + str(measurementstotal))
        self.builder.get_object('TimeTotal').config(text="Zeit: " + str(timetotal) + "s")
        self.builder.get_object("btn_ok_parameters").config(state="normal")
    except ValueError:
        self.builder.get_object("btn_ok_parameters").config(state="disabled")

def loadRecentParamters(self):
    try:
        try:
            stepangle = float(config["Parameters"]["stepangle"])
            time = float(config["Parameters"]["time"])
            startangle = float(config["Parameters"]["startangle"])
            endangle = float(config["Parameters"]["endangle"])

            self.builder.get_object('StepsizeEntry').insert(0, str(stepangle))
            self.builder.get_object('TimeEntry').insert(0, str(time))
            self.builder.get_object('StartangleEntry').insert(0, str(startangle))
            self.builder.get_object('EndangleEntry').insert(0, str(endangle))

            calculateParameters(self)
        except KeyError:
            pass
    except ValueError:
        pass

def loadConstants(self):
    success = False
    try:
        try:
            d = float(config["Crystal"]["d"])
        except KeyError:
            pass
    except ValueError:
        pass
    if not success:
        config["Crystal"] = {}
        d = str(2.01*10**-10)
        config["Crystal"]["d"] = d

def setSerialPort(self):
    updateSerialCombo(self)
    try:
        for s in comports():
            if str(s.vid) == config["Serial"]["vid"]:
                if str(s.pid) == config["Serial"]["pid"]:
                    self.builder.get_object('SerialCombo').current(s.device)
                    return
        self.builder.get_object('ErrorLabelSerial').config(text="Achtung: gespeicherter Arduino nicht gefunden!")
    except KeyError:
        pass

def calculateValues(self):
    background = int(counts[0])

    anglesize = stepsize / stepsperangle

    x = []
    y = []

    angle = np.empty(len(counts) - 1)
    for i in range(len(angle)):
        angle[i] = startsteps / stepsperangle + i * anglesize
    x = angle

    if do_lambda:
        wavelength = np.empty(len(x))
        for i in range(len(x)):
            wavelength[i] = 2*d*math.sin(math.radians(angle[i]))
        x = wavelength

    counts_normalized = np.empty(len(x))
    for i in range(1, len(counts)):
        counts_normalized[i - 1] = int(counts[i])
        if do_subtractbackground:
            counts_normalized[i - 1] = counts_normalized[i - 1] - background
        if do_persecond:
            counts_normalized[i - 1] = counts_normalized[i - 1] / time
    y = counts_normalized

    if do_smooth:
        xinterpolated = np.linspace(x.min(),x.max(),300)
        spl = make_interp_spline(x, y, k=3)
        ysmoothed = spl(xinterpolated)
        x = xinterpolated
        y = ysmoothed

    return [x, y]

def drawTable(self, filename = ""):
    x, y = calculateValues(self)

    xText = ""
    yText = ""

    for value in x:
        if do_lambda:
            xText = xText + "{:0.3e}".format(value) + "\n"
        else:
            xText = xText + str(value) + "\n"
    for value in y:
        yText = yText + str(value) + "\n"
    self.builder.get_object('x_text').config(text=xText)
    self.builder.get_object('y_text').config(text=yText)

    if do_lambda:
        self.builder.get_object('x_label').config(text="Wellenlänge in m")
    else :
        self.builder.get_object('x_label').config(text="Glanzinkel in °")
    if do_subtractbackground:
        back = " (ohne Hintergrundstrahlung)"
    else:
        back = ""
    if do_persecond:
        self.builder.get_object('y_label').config(text="Zählrahte in 1/s" + back)
    else:
        self.builder.get_object('y_label').config(text="Zählrahte in 1/" + str(time) + "s" + back)

    self.builder.get_object('D_Label').config(text="d = {:0.3e}".format(d))
    self.builder.get_object('Background_Label').config(text="Hintergrundstrahlung: " + str(counts[0]) + " / " + str(time) + "s")

    if filename != "":
        with open(filename, "w", newline="") as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=",", quotechar="|", quoting=csv.QUOTE_MINIMAL)
            for i in range(len(x)):
                if do_lambda:
                    csvwriter.writerow(["{:0.3e}".format(x[i]), str(y[i])])
                else:
                    csvwriter.writerow([str(x[i]), str(y[i])])

def drawPlot(self, filename = ""):
    scrolledframe = self.builder.get_object('plot_frame')
    figure = Figure(figsize=(8, 8), dpi=80)
    axis = figure.add_subplot(111)
    x, y = calculateValues(self)
    axis.plot(x, y)
    if do_zoom:
        last = y[0]
        for i in range(len(y)):
            if y[i] > last:
                break
            last = y[i]
        axis.set_ylim(top=y[i:].max() + abs(y[i:].max() * 0.075), bottom=y[i:].min() - abs(y[i:].min() * 0.075))
    else:
        axis.set_ylim(top=y.max() + abs(y.max() * 0.075), bottom=y.min() - abs(y.min() * 0.075))
    if do_lambda:
        axis.set_xlabel("Wellenlänge in m")
    else :
        axis.set_xlabel("Glanzinkel in °")
    if do_persecond:
        axis.set_ylabel("Zählrahte in 1/s")
    else:
        axis.set_ylabel("Zählrahte in 1/" + str(time) + "s")
    axis.set_title("Röntgenspektrum")
    canvas = FigureCanvas(figure, master=scrolledframe)
    canvas.draw()
    canvas.get_tk_widget().grid(row=0, column=0, sticky='nsew')

    if filename != "":
        figure.savefig(filename)

if __name__ == '__main__':
    app = MyApplication()
    app.run();
