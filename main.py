# 4/24/2023
#Damir Zababuryn
import os
import subprocess
import re
import sys
import pandas as pd

from PyQt6.QtCore import QObject, QThread, pyqtSignal, Qt, QMutex
from PyQt6.QtWidgets import QApplication, QFileDialog, QMainWindow
from PyQt6.uic import loadUi


class pingRange(QObject):
    finished = pyqtSignal()
    sendTextSignal = pyqtSignal(str)  # text appended to textEdit various places
    dataSignal = pyqtSignal(
        list)  # create a dataSignal here that will be used to emit the list at the end of the scanRange() method

    def __init__(self, netAddr, startOctet, endOctet):
        super().__init__()
        self.netAddr = netAddr  # first three octets
        self.startOctet = startOctet  # first ip #
        self.endOctet = endOctet  # last ip #
        self.status = -1  # -1 is flag for not tried

        # see if windows os
        if os.name == "nt":
            self.unreachable = re.compile(r"unreachable.")
            self.lifeline = re.compile(r"Received = (\d)")
        # else linux or macos
        else:
            self.timeout = re.compile(r"Request timeout")
            self.unreachable = re.compile(r"Unreachable.")
            self.lifeline = re.compile(r"(\d) received")
            self.lifeline1 = re.compile(r"(\d)")

    def pingOne(self, ip):

        # see if windows os
        if os.name == "nt":
            # pingProcess = os.popen("ping -n 2 "+ ip,"r")
            args = ['ping', '-n', '2', ip]
        # else linux or macos
        else:
            args = ['ping', '-c', '2', ip]

        try:
            pingProcess = subprocess.Popen(args, stdout=subprocess.PIPE)
        except OSError:
            print("error: popen")
            return 0  # 0 is no answers out of 2 pings

        pingProcess.wait()  # wait for process to complete
        output, err = pingProcess.communicate()  # get results

        if err:  # if error happened notify and exit function
            print("Error!")
            return 0  # 0 is no answers out of 2 pings

        # convert byte array returned into a string
        line = output.decode('utf-8')
        print("line:", line)
        if not line:
            print("No result line string")
            iGot = ["0"]  # unreachable
        elif len(re.findall(self.unreachable, line)) > 0:
            iGot = ["0"]  # unreachable
        elif len(re.findall(self.timeout, line)) > 0:
            iGot = ["0"]  # timeout macos
        elif len(re.findall(self.lifeline, line)) > 0:
            iGot = re.findall(self.lifeline, line)  # search line string for # in results
        else:  # macos reply
            iGot = re.findall(self.lifeline1, line)

        if iGot:
            return int(iGot[0])  # return status of host just pinged
            # note about status... it will be
            # 0 if no answers out of 2
            # 1 if one out of two   partial response
            # 2 if both pings got an answer

    def scanRange(self):
        data = []
        report = ("No response\n", "Partial Response\n", "Alive\n")
        text = 'Starting Ping Scan at address: {}\n'.format(self.netAddr + '.' + str(self.startOctet))
        self.sendTextSignal.emit(text)  # update plainTextEdit widget text EMIT
        for host in range(self.startOctet, self.endOctet + 1):
            ip = self.netAddr + '.' + str(host)
            current_scan = self.pingOne(ip)
            text = ip + " " + report[current_scan]
            self.sendTextSignal.emit(text)  # update plainTextEdit widget text EMIT
            data.append([ip, report[current_scan]])
        # need to emit the new signals created right here (outside the for loop)
        self.dataSignal.emit(data)
        self.finished.emit()


class MyForm(QMainWindow):

    def __init__(self):
        super().__init__()
        loadUi('pingscan_Damir_Zababuryn.ui', self)
        self.pushButtonRunScan1.clicked.connect(self.run_scan1)
        self.pushButtonRunScan2.clicked.connect(self.run_scan2)
        self.pushButtonSave.clicked.connect(self.save)
        self.data = []
        self.mutex = QMutex()  # Create a QMutex for data locking
        self.show()

    def run_scan1(self):
        self.obj1 = pingRange('152.41.205', 2, 10)
        self.obj1.dataSignal.connect(self.obtain_results1)  # connect signal to data collection method
        self.objThread1 = QThread()
        self.obj1.moveToThread(self.objThread1)
        self.obj1.finished.connect(self.objThread1.quit)
        self.obj1.sendTextSignal.connect(self.plainTextEditScan1.insertPlainText, Qt.ConnectionType.QueuedConnection)
        self.objThread1.started.connect(self.obj1.scanRange)
        self.objThread1.start()

    def run_scan2(self):
        self.obj2 = pingRange('152.41.205', 11, 20)
        self.obj2.dataSignal.connect(self.obtain_results2)  # connect signal to data collection method
        self.objThread2 = QThread()
        self.obj2.moveToThread(self.objThread2)
        self.obj2.finished.connect(self.objThread2.quit)
        self.obj2.sendTextSignal.connect(self.plainTextEditScan2.insertPlainText, Qt.ConnectionType.QueuedConnection)
        self.objThread2.started.connect(self.obj2.scanRange)
        self.objThread2.start()

    def obtain_results1(self, data):
        self.mutex.lock()  # Lock the data to prevent corruption or loss
        self.data += data  # list of ping scan results
        self.mutex.unlock()  # Unlock the data

    def obtain_results2(self, data):
        self.mutex.lock()  # Lock the data to prevent corruption or loss
        self.data += data  # list of ping scan results
        self.mutex.unlock()  # Unlock the data

    def save(self, data):
        file, _ = QFileDialog.getSaveFileName(self, 'Select file to save ping scan results', '', '(*.csv)')
        if file:
            df = pd.DataFrame(self.data)
            df.to_csv(file, sep=';', index=False, encoding='utf-8')


# the code below should not be changed and is constant for all GUI programs
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyForm()
    window.show()
    sys.exit(app.exec())