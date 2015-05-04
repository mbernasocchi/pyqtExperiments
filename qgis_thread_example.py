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

    
    this was inspired by:
    http://snorf.net/blog/2013/12/07/multithreading-in-qgis-python-plugins/
    http://eli.thegreenplace.net/2011/04/25/passing-extra-arguments-to-pyqt-slot
    http://gis.stackexchange.com/questions/64831/how-do-i-prevent-qgis-from-being-detected-as-not-responding-when-running-a-hea/64928#64928
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


###########################################################################
# This is what you need to call when you want to start a work in a thread #
###########################################################################
def run_example_worker():
    # create a new worker instance that does 7 steps
    worker = ExampleWorker(7)
    start_worker(worker, self.iface, 'testing the worker')


###########################################################################
# This could be in a separate file example_worker.py                      #
###########################################################################
class ExampleWorker(AbstractWorker):
    """worker, implement the work method here and raise exceptions if needed"""

    def __init__(self, steps):
        AbstractWorker.__init__(self)
        self.steps = steps
        # if a worker cannot define the length of the work it can set an 
        # undefined progress by using
        # self.toggle_show_progress.emit(False)

    def work(self):
        if randint(0, 100) > 70:
            raise RuntimeError('This is a random mistake during the '
                               'calculation')
        
        self.toggle_show_progress.emit(False)   
        self.set_message.emit(
            'NOT showing the progress because we dont know the length')
        sleep(randint(0, 10))  
         
        
        self.toggle_show_progress.emit(True)        
        self.set_message.emit(
            'Doing long running job while showing the progress')
        for i in range(1, self.steps+1):
            if self.killed:
                self.cleanup()
                raise UserAbortedNotification('USER Killed')

            # wait one second
            time.sleep(1)
            self.progress.emit(i * 100/self.steps)

        return True
        
    def cleanup(self):
        print "cleanup here"


###########################################################################
# This could be in a separate file abstract_worker.py                     #
###########################################################################
class AbstractWorker(QtCore.QObject):
    """Abstract worker, ihnerit from this and implement the work method"""

    # available signals
    finished = QtCore.pyqtSignal(object)
    error = QtCore.pyqtSignal(Exception, basestring)
    progress = QtCore.pyqtSignal(float)
    toggle_show_progress = QtCore.pyqtSignal(bool)
    set_message = QtCore.pyqtSignal(str)
    
    # private signal, don't use in concrete workers this is automatically
    # emitted if the result is not None
    successfully_finished = QtCore.pyqtSignal(object)

    def __init__(self):
        QtCore.QObject.__init__(self)
        self.killed = False

    def run(self):
        try:
            result = self.work()
            self.finished.emit(result)
        except UserAbortedNotification:
            self.finished.emit(None)
        except Exception, e:
            # forward the exception upstream
            self.error.emit(e, traceback.format_exc())
            self.finished.emit(None)

    def work(self):
        """ Reimplement this putting your calculation here
            available are:
                self.progress.emit(0-100)
                self.killed
            :returns a python object - use None if killed is true
        """

        raise NotImplementedError

    def kill(self):
        self.is_killed = True
        self.set_message.emit('Aborting...')
        self.toggle_show_progress.emit(False)


class UserAbortedNotification(Exception):
    pass


def start_worker(worker, iface, message, with_progress=True):
    # configure the QgsMessageBar
    message_bar = iface.messageBar().createMessage(message)
    progress_bar = QProgressBar()
    progress_bar.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    if not with_progress:
        progress_bar.setMinimum(0)
        progress_bar.setMaximum(0)
    cancel_button = QPushButton()
    cancel_button.setText('Cancel')
    cancel_button.clicked.connect(worker.kill)
    message_bar.layout().addWidget(progress_bar)
    message_bar.layout().addWidget(cancel_button)
    iface.messageBar().pushWidget(message_bar, iface.messageBar().INFO)

    # start the worker in a new thread
    # let Qt take ownership of the QThread
    thread = QThread(iface.mainWindow())
    worker.moveToThread(thread)
    
    worker.set_message.connect(lambda message: set_worker_message(
        message, message_bar_item))

    worker.toggle_show_progress.connect(lambda show: toggle_worker_progress(
        show, progress_bar))
    worker.finished.connect(lambda result: worker_finished(
        result, thread, worker, iface, message_bar))
    worker.error.connect(lambda e, exception_str: worker_error(
        e, exception_str, iface))
    worker.progress.connect(progress_bar.setValue)
    thread.started.connect(worker.run)
    thread.start()
    return thread, message_bar


def worker_finished(result, thread, worker, iface, message_bar):
        # remove widget from message bar
        iface.messageBar().popWidget(message_bar)
        if result is not None:
            # report the result
            iface.messageBar().pushMessage('The result is: %s.' % result)
            worker.successfully_finished.emit(result)
            
        # clean up the worker and thread
        worker.deleteLater()
        thread.quit()
        thread.wait()
        thread.deleteLater()        
        

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


def set_worker_message(message, message_bar_item):
    message_bar_item.setText(message)


def toggle_worker_progress(show_progress, progress_bar):
    progress_bar.setMinimum(0)
    if show_progress:
        progress_bar.setMaximum(100)
    else:
        # show an undefined progress
        progress_bar.setMaximum(0)

