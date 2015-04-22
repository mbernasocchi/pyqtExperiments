# -*- coding: utf-8 -*-
"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    
    this was inspired by 
    http://snorf.net/blog/2013/12/07/multithreading-in-qgis-python-plugins/
    http://eli.thegreenplace.net/2011/04/25/passing-extra-arguments-to-pyqt-slot
"""


__author__ = 'marco@opengis.ch'

import time
import traceback
from random import randint

from PyQt4 import QtCore
from PyQt4.QtCore import QThread, Qt
from PyQt4.QtGui import QProgressBar, QPushButton

from qgis.core import QgsMessageLog
from qgis.gui import QgsMessageBar


class AbstractWorker(QtCore.QObject):
    """Example worker for thread"""

    # available signals
    finished = QtCore.pyqtSignal(object)
    error = QtCore.pyqtSignal(Exception, basestring)
    progress = QtCore.pyqtSignal(float)

    def __init__(self):
        QtCore.QObject.__init__(self)
        self.killed = False

    def run(self):
        result = None
        try:
            result = self.work()
        except Exception, e:
            # forward the exception upstream
            self.error.emit(e, traceback.format_exc())
        self.finished.emit(result)

    def work(self):
        """ Reimplement this putting your calculation here
            available are:
                self.progress.emit(0-100)
                self.killed
            :returns a python object - Don't use None
                    as it is used to signal user abortion
        """

        raise NotImplementedError

    def kill(self):
        self.killed = True


class ExampleWorker(AbstractWorker):
    """Example worker for thread"""

    def __init__(self, steps):
        AbstractWorker.__init__(self)
        self.steps = steps

    def work(self):
        if randint(0, 100) > 70:
            raise RuntimeError('This is a random mistake during the '
                               'calculation')

        for i in range(1, self.steps+1):
            if self.killed:
                return None

            # wait one second
            time.sleep(1)
            self.progress.emit(i * 100/self.steps)

        return True


def start_worker(worker, iface, message):
    # configure the QgsMessageBar
    message_bar = iface.messageBar().createMessage(message)
    progress_bar = QProgressBar()
    progress_bar.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    cancel_button = QPushButton()
    cancel_button.setText('Cancel')
    cancel_button.clicked.connect(worker.kill)
    message_bar.layout().addWidget(progress_bar)
    message_bar.layout().addWidget(cancel_button)
    iface.messageBar().pushWidget(message_bar, iface.messageBar().INFO)

    # start the worker in a new thread
    thread = QThread()
    worker.moveToThread(thread)
    worker.finished.connect(lambda result: worker_finished(
        result, thread, worker, iface, message_bar))
    worker.error.connect(lambda e, exception_str: worker_error(
        e, exception_str, iface))
    worker.progress.connect(progress_bar.setValue)
    thread.started.connect(worker.run)
    thread.start()
    return thread, worker, message_bar


def worker_finished(result, thread, worker, iface, message_bar):
        # clean up the worker and thread
        worker.deleteLater()
        thread.quit()
        thread.wait()
        thread.deleteLater()
        # remove widget from message bar
        iface.messageBar().popWidget(message_bar)
        if result is not None:
            # report the result
            iface.messageBar().pushMessage('The result is: %s.' % result)


def worker_error(e, exception_string, iface):
    # notify the user that something went wrong
    iface.messageBar().pushMessage(
        'Something went wrong! See the message log for more information.',
        level=QgsMessageBar.CRITICAL,
        duration=3)
    QgsMessageLog.logMessage(
        'Worker thread raised an exception: %s' % exception_string,
        'SVIR worker',
        level=QgsMessageLog.CRITICAL)


###########################################################################
# This is what you need to call when you want to start a work in a thread #
###########################################################################
def run_example_worker():
    # create a new worker instance that does 7 steps
    worker = ExampleWorker(7)
    start_worker(worker, self.iface, 'testing the worker')
