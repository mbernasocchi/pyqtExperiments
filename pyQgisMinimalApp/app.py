import sys
import os

from PyQt4.QtGui import QApplication
from qgis.core import QgsApplication
from mainwindow import MainWindow

# Path to local QGIS install
QGIS_PREFIX = os.environ['QGIS_PREFIX']
#QGIS_PREFIX='/usr/local/qgis-master'


# Main entry to program.  Set up the main app and create a new window.
def main(argv):

    # create Qt application
    app = QApplication(argv, True)

    # Set the app style

    # initialize qgis libraries
    QgsApplication.setPrefixPath(QGIS_PREFIX, True)
    QgsApplication.initQgis()

    # create main window
    wnd = MainWindow()
    wnd.show()

    # Start the app up
    retval = app.exec_()

    # We got an exit signal so time to clean up
    QgsApplication.exitQgis()

    sys.exit(retval)


if __name__ == '__main__':
    main(sys.argv)
