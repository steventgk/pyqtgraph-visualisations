import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import re
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets
from glob import glob
from natsort import natsorted
from tqdm import tqdm
from scipy.ndimage import convolve

__author__ = "Steven Gough-Kelly"
__copyright__ = ""
__credits__ = ["Steven Gough-Kelly"]
__license__ = "MIT"
__version__ = "1.0.1"
__maintainer__ = "Steven Gough-Kelly"
__email__ = "sgoughkelly@gmail.com"
__status__ = "Production"

def gaussian_2d_psf(size=9, sigma=1.2):
    """2D Gaussian Kernal"""
    ker = np.linspace(-(size // 2), size // 2, size)
    xx, yy = np.meshgrid(ker, ker)
    psf = np.exp(-(xx**2 + yy**2) / (2. * sigma**2))
    return psf / psf.sum()

def vertical_psf(height=50, sigma=3.0):
    """Vertical Gaussian Kernal"""
    y = np.arange(height)
    center = height // 2
    psf = np.exp(-0.5 * ((y - center) / sigma)**2)
    return psf / psf.sum()

def clean_element(s):
    """Remove characters from numbers"""
    if isinstance(s, float) and np.isnan(s):
        return np.nan
    match = re.match(r'^-?[\d.]+', str(s))
    return float(match.group()) if match else np.nan

def wavelength_to_rgb(wavelength, gamma=0.8):
    ''' taken from http://www.noah.org/wiki/Wavelength_to_RGB_in_Python
    This converts a given wavelength of light to an
    approximate RGB color value. The wavelength must be given
    in nanometers in the range from 380 nm through 750 nm
    (789 THz through 400 THz).

    Based on code by Dan Bruton
    http://www.physics.sfasu.edu/astro/color/spectra.html
    Additionally alpha value set to 0.5 outside range
    '''
    wavelength = float(wavelength)
    if wavelength >= 380 and wavelength <= 750:
        A = 1.
    else:
        A = 0.5
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
    return (R, G, B, A)

# Define colours per wavelength
clim = (380, 750)
norm = plt.Normalize(*clim)
wl = np.arange(clim[0], clim[1] + 1, 2)
colorlist = list(zip(norm(wl), [wavelength_to_rgb(w,gamma=0.3) for w in wl]))
spectralmap = mpl.colors.LinearSegmentedColormap.from_list("spectrum", colorlist)

# Initialise pyqtgraph
app = QtWidgets.QApplication([])
w = QtWidgets.QWidget()
w.setWindowTitle('Element Spectrum Viewer')

listWidget = QtWidgets.QListWidget()

plot = pg.PlotWidget()
plot.setLabel('bottom','wavelength (nm)')
plot.hideAxis('left')
plot.showAxis('top')
plot.setLogMode(False, False)
plot.setXRange(370, 760, padding=0)
plot.setLimits(yMin=0, yMax=1)
plot.setMouseEnabled(x=True, y=False)

plot2 = pg.PlotWidget()
plot2.setLabel('bottom','wavelength (nm)')
plot2.hideAxis('left')
plot2.showAxis('top')
plot2.setLogMode(False, False)
plot2.setXRange(370, 760, padding=0)
plot2.setLimits(yMin=0, yMax=1)
plot2.setMouseEnabled(x=True, y=False)

plot3 = pg.PlotWidget()
plot3.setLabel('bottom','wavelength (nm)')
plot3.hideAxis('left')
plot3.showAxis('top')
plot3.setLogMode(False, False)
plot3.setXRange(370, 760, padding=0)
plot3.setLimits(yMin=0, yMax=1)
plot3.setMouseEnabled(x=True, y=False)

plot4 = pg.PlotWidget()
plot4.setLabel('bottom','wavelength (nm)')
plot4.setLabel('left','Intensity')
plot4.setLabel('right','Intensity')
plot4.showAxis('top')
plot4.setLogMode(False, False)
plot4.setXRange(370, 760, padding=0)
plot4.setMouseEnabled(x=True, y=False)

plot.setXLink(plot2)
plot2.setXLink(plot3)
plot3.setXLink(plot4)

table = pg.TableWidget()

# Layout
layout = QtWidgets.QGridLayout()
layout.setColumnStretch(0, 1)
layout.setColumnStretch(1, 4)

layout.setRowStretch(0, 1)
layout.setRowStretch(1, 1)
layout.setRowStretch(2, 1)
layout.setRowStretch(3, 1)
layout.setRowStretch(4, 1)

w.setLayout(layout)

layout.addWidget(listWidget, 1, 0, 4, 1)
layout.addWidget(table, 0, 1, 1, 1)
layout.addWidget(plot, 1, 1, 1, 1)
layout.addWidget(plot2, 3, 1, 1, 1)
layout.addWidget(plot3, 2, 1, 1, 1) 
layout.addWidget(plot4, 4, 1, 1, 1) 


##############################################################
# Import available elements
files = sorted(glob('NIST/*.npy'))
elements = [f.split('/')[1].split('.')[0].split('-')[0]+'-'+f.split('/')[1].split('.')[0].split('-')[1] for f in files]
elements = natsorted(elements)

for idx in elements:
    tmpitem = QtWidgets.QListWidgetItem(idx)
    listWidget.addItem(tmpitem)
listWidget.setCurrentItem(tmpitem)

##############################################################

def update_plot():
    element = listWidget.currentItem().text()
    
    plot.clear()
    plot2.clear()
    plot3.clear()
    plot4.clear()
    table.clear()
    
    # Load selected element
    tmp = pd.DataFrame(np.load('NIST/'+element+'-lines.npy',allow_pickle=True))
    _wavs = tmp['obs_wl_vac(nm)'].values
    _amps = tmp['intens'].values
    _amps2 = np.array([clean_element(i) for i in _amps], dtype=float)

    keep = np.isfinite(_wavs)&np.isfinite(_amps2)&(_wavs>380)&(_wavs<750)

    _wavsX = _wavs[keep]
    _ampsY = _amps2[keep]/np.max(_amps2[keep])

    ampscut = _ampsY>0.01
    ampsY = _ampsY[ampscut]
    wavsX = _wavsX[ampscut]

    # set table data
    table.setData(tmp.to_records(index=False)[keep][ampscut])

    # add spectral lines
    for i in tqdm(range(0,len(wavsX))):

        _col = spectralmap(norm(wavsX[i]))

        # col = (_col[0]*255,_col[1]*255,_col[2]*255,1.*255)
        col = (_col[0]*255,_col[1]*255,_col[2]*255,ampsY[i]*255)
        col2 = (255,255,255,ampsY[i]*255)

        line = pg.InfiniteLine(movable=False, angle=90, pen=pg.mkPen(col))
        line.setPos([wavsX[i],1])
        plot.addItem(line)

        line2 = pg.InfiniteLine(movable=False, angle=90, pen=pg.mkPen(col2))
        line2.setPos([wavsX[i],1])
        plot4.addItem(line2)

    plot.setLabel('bottom','wavelength (nm)')
    plot.hideAxis('left')
    plot.showAxis('top')
    plot.setLogMode(False, False)
    plot.setXRange(370, 760, padding=0)
    plot.setLimits(yMin=0, yMax=1)
    plot.setMouseEnabled(x=True, y=False)

    ####################

    # 2D Spectrum with PSF - intensity
    wavelengths = np.linspace(380, 750, 1000)
    spec_1d = np.zeros(len(wavelengths))
    for i in range(0,len(wavsX)):
        spectrum_tmp = ampsY[i]*np.exp(-0.5 * ((wavelengths - wavsX[i]) / 2)**2)  # Gaussian line
        spec_1d += spectrum_tmp
    spatial_psf = vertical_psf(height=100, sigma=40.0)
    spectrum_2d = np.zeros((100, 1000))
    for i, flux in enumerate(spec_1d):
        spectrum_2d[:, i] += flux * spatial_psf  # vertically spread each column
    psf_2d = gaussian_2d_psf(size=20, sigma=50.)
    mock_2d_spectrum = convolve(spectrum_2d, psf_2d, mode='reflect')

    im1 = pg.ImageItem(image=mock_2d_spectrum, axisOrder='row-major')

    transform = pg.QtGui.QTransform()
    transform.translate(380, 0)
    transform.scale((750-380)/1000, 1)
    im1.setTransform(transform)
    plot2.addItem(im1)

    plot2.setLabel('bottom','wavelength (nm)')
    plot2.hideAxis('left')
    plot2.showAxis('top')

    ####################

    # 2D Spectrum with PSF - coloured by wavelength
    h, w = mock_2d_spectrum.shape
    rgba_image = np.zeros((h, w, 4))

    for i in range(w):
        color = spectralmap(norm(wavelengths[i]))
        alpha_col = mock_2d_spectrum[:, i]/np.max(mock_2d_spectrum)
        rgba_image[:, i, :3] = color[:3]  # RGB
        rgba_image[:, i, 3] = alpha_col   # Alpha
    

    im2 = pg.ImageItem(image=rgba_image, axisOrder='row-major')
    im2.setTransform(transform)

    plot3.addItem(im2)

    plot3.setLabel('bottom','wavelength (nm)')
    plot3.hideAxis('left')
    plot3.showAxis('top')

    ####################

    # 1D Spectrum from 2D mock
    intensity = np.sum(mock_2d_spectrum,axis=0)

    white = (255,255,255,255)
    plot4.plot(wavelengths, intensity, pen=white)

    ####################

##############################################################

##############################################################
selected = listWidget.findItems('1-H', QtCore.Qt.MatchContains)[0]
listWidget.setCurrentItem(selected)
update_plot()

listWidget.itemSelectionChanged.connect(update_plot)

##############################################################
w.show()
##############################################################
if __name__ == '__main__':
    pg.exec()