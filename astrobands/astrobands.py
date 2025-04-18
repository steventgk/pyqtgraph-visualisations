import numpy as np
from pyqtgraph.Qt import QtWidgets, QtCore
import pyqtgraph as pg
from glob import glob

__author__ = "Steven Gough-Kelly"
__copyright__ = ""
__credits__ = ["Steven Gough-Kelly"]
__license__ = "MIT"
__version__ = "1.0.1"
__maintainer__ = "Steven Gough-Kelly"
__email__ = "sgoughkelly@gmail.com"
__status__ = "Production"

filters = glob('./filters/observatories/**/*.dat',recursive=True)

FILTER_DATA = {}
for f in filters:
    tmp = np.genfromtxt(f)
    name = f.split('/')[-1].split('.')[0]
    FILTER_DATA[name] = tmp

def wavelength_to_color(wavelength, gamma=0.8):
    if wavelength >= 380 and wavelength <= 750:
        A = 1.
    else:
        A = 0.7
    if wavelength < 380:
        wavelength = 380.
    if wavelength > 750:
        wavelength = 750.
    if 380 <= wavelength <= 440:
        attenuation = 0.3 + 0.7 * (wavelength - 380) / (440 - 380)
        R = ((-(wavelength - 440) / (440 - 380)) * attenuation) ** gamma
        G = 0.0
        B = (1.0 * attenuation) ** gamma
    elif 440 <= wavelength <= 490:
        R = 0.0
        G = ((wavelength - 440) / (490 - 440)) ** gamma
        B = 1.0
    elif 490 <= wavelength <= 510:
        R = 0.0
        G = 1.0
        B = (-(wavelength - 510) / (510 - 490)) ** gamma
    elif 510 <= wavelength <= 580:
        R = ((wavelength - 510) / (580 - 510)) ** gamma
        G = 1.0
        B = 0.0
    elif 580 <= wavelength <= 645:
        R = 1.0
        G = (-(wavelength - 645) / (645 - 580)) ** gamma
        B = 0.0
    elif 645 <= wavelength <= 750:
        attenuation = 0.3 + 0.7 * (750 - wavelength) / (750 - 645)
        R = (1.0 * attenuation) ** gamma
        G = 0.0
        B = 0.0
    else:
        R = 0.0
        G = 0.0
        B = 0.0
    return (R*255, G*255, B*255, A*255)

class FilterViewer(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Astrobands")

        self.layout = QtWidgets.QHBoxLayout(self)
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel('left', 'Throughput [%]')
        self.plot_widget.setLabel('bottom', 'Wavelength (nm)')

        self.filter_curves = {}
        self.label_items = {}

        self.layout.addWidget(self.plot_widget, stretch=3)

        sidebar = QtWidgets.QVBoxLayout()

        self.fill_checkbox = QtWidgets.QCheckBox("Fill under curve?")
        self.fill_checkbox.setChecked(False)
        self.fill_checkbox.stateChanged.connect(self.update_plot)

        self.filter_list = QtWidgets.QListWidget()
        self.filter_list.setSelectionMode(QtWidgets.QListWidget.MultiSelection)
        for i, name in enumerate(FILTER_DATA):
            item = QtWidgets.QListWidgetItem(name)
            self.filter_list.addItem(item)
            if i==0:
                item.setSelected(True)
            else:
                item.setSelected(False)
        self.filter_list.itemSelectionChanged.connect(self.update_plot)

        self.clear_button = QtWidgets.QPushButton("Clear All")
        self.clear_button.clicked.connect(self.clear_selection)

        sidebar.addWidget(self.fill_checkbox)
        sidebar.addWidget(self.filter_list)
        sidebar.addWidget(self.clear_button)
        sidebar.addStretch()

        self.layout.addLayout(sidebar, stretch=1)

    def clear_selection(self):
        self.filter_list.clearSelection()
        self.update_plot()

    def update_plot(self):
        self.plot_widget.clear()
        self.plot_widget.addLegend(**{'labelTextSize':'16pt'})
        self.filter_curves.clear()
        self.label_items.clear()

        for i in range(self.filter_list.count()):
            item = self.filter_list.item(i)
            name = item.text()
            if not item.isSelected():
                continue

            wavelengths, throughput = FILTER_DATA[name].T
    
            center = wavelengths[np.argmax(throughput)]
            color = wavelength_to_color(center)
            pen = pg.mkPen(color=color, width=4)

            curve = self.plot_widget.plot(wavelengths, throughput, pen=pen, name=name)

            if self.fill_checkbox.isChecked():
                fill = pg.FillBetweenItem(curve, pg.PlotDataItem(wavelengths, np.zeros_like(throughput)))
                fill.setBrush(pg.mkBrush(color[:-1] + (80,)))
                self.plot_widget.addItem(fill)

            peak_index = np.argmax(throughput)
            peak_x = wavelengths[peak_index]
            peak_y = throughput[peak_index]
            text = pg.TextItem(name, anchor=(0.5, 0.8), color=color)
            text.setPos(peak_x, peak_y)
            self.plot_widget.addItem(text)

            self.filter_curves[name] = curve
            self.label_items[name] = text

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    viewer = FilterViewer()
    viewer.resize(1400, 800)
    viewer.show()
    pg.exec()
