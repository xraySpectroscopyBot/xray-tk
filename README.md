# xray-tk

## 1. Installation
### 1. Downloading prepackaged executables
To use xraySpectroscopyBot, you need to build the [hardware](https://github.com/xraySpectroscopyBot/xray-hardware), connect the [arduino](https://github.com/xraySpectroscopyBot/xray-arduino) and either download the proper [build](https://github.com/xraySpectroscopyBot/xray-tk/releases) for your platform, package yourself or download python and run the program directly.
### 2. Python
Download [python](https://python.org) and xray-tk.
Use pip to install all dependencies.
Run `python3 xray.spec`
### 3. Packaging using pyinstaller
Follow the instructions for running in python.
When the program works, install [pyinstaller](http://www.pyinstaller.org/).
Run `pyinstaller xray.spec` to create a package for your current platform.

## 2. Usage
### 1. Prepare and take a measurement
* Fix the Stepper to your Xray-Machine, connect the Arduino to your PC and start the program.

![Set the lattice constant of your crystal](https://github.com/xraySpectroscopyBot/xray-tk/blob/master/screenshots/setd.png)
* To be able to display the wavelength, you need to set the lattice constant of your crystal. Click the settings menu, choose to set the lattice constant and either enter the desired value manually or choose one of the preprogrammed values.

![Choose the Serial device](https://github.com/xraySpectroscopyBot/xray-tk/blob/master/screenshots/homescreen.png)
* Choose the correct Serial device. Xray-tk will display an error message if the selected port does not have an Arduino. This setting is saved in the *xray.ini* configfile and restored, when you restart the program.
* Use the buttons on the screen to rotate the crystal in to it's zero position.
* Move the Geiger-Müller counter in to it's zero position manually. The program will prompt you to do this.

![Set the maximum position](https://github.com/xraySpectroscopyBot/xray-tk/blob/master/screenshots/setmax.png)
* Use the buttons on the screen to rotate the crystal in to it's maximum position. The buttons in the middle will move the stepper slowly, the ones on the outside faster. Put the angle of the crystal *(theta)* in to the entry. After pressing *ok*, the Stepper will move back to it's home position.

![Set the parameters](https://github.com/xraySpectroscopyBot/xray-tk/blob/master/screenshots/setparameters.png)
* Enter the angle difference between measurements, the angle to start the measurement with, the maximum angle and the time for the integrated stopwatch.
* Take a measurement of the natural background radiation.
* Turn on the Xray-Machine.
* Take all the measurements. Use the button to start the stopwatch and stop the measurement when the stopwatch reaches 0.
* Save the measurement at your desired location.
### 2. Visualize / Export data
* Once you've taken a measurement or opened a file from the first screen of the program, you can view the data as a table or as a plot.

![The plot](https://github.com/xraySpectroscopyBot/xray-tk/blob/master/screenshots/plot.png)
* The first button in the bottom row switches between plot and table view. The second one toggles between wavelength and angle, the third one between counts per second and raw counts and the next one selects if the background radiation should be subtracted.

* The next two buttons are only visible while viewing the plot and select if the plot should be interpolated and if the view should be zoomed in.

* The save icon saves the current representation of the data.
### 3. Recalibrate
* You can use the settings menu to recalibrate the maximum position or to delete all settings. You will be prompted to confirm this choice.
