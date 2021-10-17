
import sys
from PyQt5.uic import loadUi
from PyQt5 import QtWidgets,QtSerialPort
from PyQt5.QtCore import QThread, QTimer
from PyQt5.QtWidgets import QDialog, QApplication, QMessageBox
import json
import pandas as pd
from datetime import datetime
import time
import serial
from struct import unpack, pack

class SerialThread(QThread):
    def __init__(self, baudrate=9600):
        super(SerialThread, self).__init__()
        self.baudrate = baudrate
        print('init thread')
        # print(port)
        self.PORT = ''

    def setPort(self,port):
        self.PORT = port

    def run(self):
        self.ser = serial.Serial(self.PORT, self.baudrate)
        print('run')
        while True:
            dataRaw = self.ser.read(2) #1 short data
            self.IDCARD = unpack("h", dataRaw)[0] #hasil dari unpack merupakan tuple
            time.sleep(0.1)
            self.transaction(self.IDCARD)
    
    def sendData(self, data):
        dataPacket = pack("h", data)
        self.ser.write(dataPacket)
        time.sleep(0.1)

    def transaction(self, ID):
        newItem = dict()
        self.istransaction = False
        self.idtransaction = 0
        with open ('database/user_database.json') as f:
            data = json.load(f)
        for item in data['kendaraan']:
            if item['ID'] == str(ID):
                if int(item['Saldo']) - int(item['Tarif']) <= 0:
                    self.istransaction = False #transaksi GAGAL
                    break
                else:
                    self.istransaction = True

                if self.istransaction:
                    saldo = int(item['Saldo']) - int(item['Tarif'])
                    item['Saldo'] = str(saldo)
                    
                    #ambil data dari item ke newitem
                    newItem['ID'] = item['ID']
                    newItem['Nomor Kendaraan'] = item['Nomor Kendaraan']
                    newItem['Golongan'] = item['Golongan']
                    newItem['Tarif'] = item['Tarif']
                    newItem['Saldo Awal'] = str(saldo + int(item['Tarif']))
                    newItem['Saldo Akhir'] = item['Saldo']
                    newItem['Waktu'] = datetime.now().strftime("%Y-%B-%d:::%H:%M:%S")
                
                break #break item in data['kendaraan]
        
        if self.istransaction:
            with open ('database/user_database.json', 'w') as w:
                json.dump(data, w, indent=2)

            with open ('database/transaction_history.json') as r:
                dataChanged = json.load(r)
            
            dataChanged['kendaraan'].append(newItem) #append itu menambah data ke dataChanged yg mana dataChanged adalah atabase transaksi
        
            with open ('database/transaction_history.json', 'w') as w:
                json.dump(dataChanged, w, indent=2)

            #ngirim lampu hujau
            self.sendData(data=1)
            print(f'ID transaksi {self.IDCARD} berhasil')
        else:
            #ngirim lampu merah
            self.sendData(data=2)
            print(f'ID transaksi {self.IDCARD} gagal')

class LoginForm(QDialog):
    def __init__(self):
        super(LoginForm, self).__init__()
        loadUi('ui/login.ui', self)
        self.resize(600, 200)
        self.addSerial()
        self.LoginButton.clicked.connect(self.login)
        self.RefreshButton.clicked.connect(self.addSerial)
        self.SerialButton.clicked.connect(self.chooseButton)
        self.PORT = ''
        self.serialThread = SerialThread()
    
    def chooseButton(self):
        self.PORT = self.comboBox.currentText()

    def addSerial(self):
        self.comboBox.clear()
        for info in QtSerialPort.QSerialPortInfo.availablePorts():
            self.comboBox.addItem(info.portName())
    
    def getPORT(self):
        return self.PORT

    def login(self):
        self.PORT = self.comboBox.currentText()
        self.isPORTOK = len(self.PORT) > 1
        self.log = self.userText.text() == 'User' and self.passwordText.text() == '1234'
        # print(len(self.PORT))
        
        #berhasil masuk dan USB terkoneksi
        if self.log and self.isPORTOK:
            widget.setCurrentIndex(widget.currentIndex()+1) #ke menu utama
        
            '''Serial Thread Input from Arduino'''
            self.serialThread.setPort(self.PORT)
            self.serialThread.start()
        
        #warning to choose USB PORT
        elif self.log and not self.isPORTOK:
            title = "USB CONNECTION FAIL"
            content = "Sambungkan Alat dan pilih PORT USB"
            self.msgBox(title=title, content=content)
            
        #warning to choose USB PORT
        elif not self.log and self.isPORTOK:
            title = "Login Fail"
            content = "Username atau Password Salah"
            self.msgBox(title=title, content=content)
        
        else:
            title = "Fail to Login and USB CONNECTION FAIL"
            content = "Username atau Password Salah dan Sambungkan Alat serta pilih PORT USB"
            self.msgBox(title=title, content=content)
                     
    def msgBox(self, title, content):
        msg = QMessageBox()
        msg.setWindowTitle(title)
        msg.setText(content)
        msg.setIcon(QMessageBox.Critical)
        x = msg.exec_()  # this will show our messagebox


class DashboardForm(QDialog):
    def __init__(self):
        super(DashboardForm, self).__init__()
        loadUi('ui/dahsboard.ui', self)
        self.setFixedWidth(1000)
        self.setFixedHeight(600)
        self.CardManagerButton.clicked.connect(self.gotoManager)
        self.TransactionHistoryButton.clicked.connect(self.gotoHistory)
        self.TopupButton.clicked.connect(self.gotoTopup)

    def gotoTopup(self):
        widget.setCurrentIndex(widget.currentIndex()+3) #ke menu topup form manager
    def gotoManager(self):
        widget.setCurrentIndex(widget.currentIndex()+2) #ke menu card manager
    
    def gotoHistory(self):
        widget.setCurrentIndex(widget.currentIndex()+1) #ke menu card manager        

class TransactionForm(QDialog):
    def __init__(self):
        super(TransactionForm, self).__init__()
        loadUi('ui/transaction-history.ui', self)
        self.setFixedWidth(950)
        self.setFixedHeight(600)
        self.showTable()
        
        self.loadCombo()
        self.HomeButton.clicked.connect(self.gotoHome)
        self.SaveButton.clicked.connect(self.save)
        self.RefreshButton.clicked.connect(self.showTable)

        #auto refresh table data
        self.qTimer = QTimer()
        self.qTimer.setInterval(1000) #auto refresh every 1 sec
        self.qTimer.timeout.connect(self.showTable)
        self.qTimer.start()

    def loadCombo(self):
        with open ('database/user_database.json') as f:
            data = json.load(f)
        for item in data['kendaraan']:
            self.comboBox.addItem(item['ID'])

    def showTable(self):
        with open ('database/transaction_history.json') as f:
            self.table = json.load(f)
        row=0
        self.tableWidget.setRowCount(len(self.table['kendaraan']))
        self.tableWidget.setColumnCount(len(self.table['kendaraan'][0]))

        for data in self.table['kendaraan']:
            column = 0
            for key in data.keys():
                self.tableWidget.setItem(row, column, QtWidgets.QTableWidgetItem(data[key]))
                column +=1
            row +=1

    def save(self):
        df = pd.read_json(r'database/user_database.json')
        time = datetime.now().strftime("%Y-%B-%d:::%H:%M:%S")
        time = 'report/'+time+'.csv'
        df.to_csv(time, index=None)
        
    def gotoHome(self):
        widget.setCurrentIndex(widget.currentIndex()-1) #goto dashboard    

class ManagerForm(QDialog):
    def __init__(self):
        super(ManagerForm, self).__init__()
        loadUi('ui/card-manager.ui', self)
        self.setFixedWidth(955)
        self.setFixedHeight(415)
        self.showTable()
        
        self.loadCombo()
        self.tableWidget.setColumnWidth(0,25)
        self.tableWidget.setColumnWidth(1,150)
        self.tableWidget.setColumnWidth(2,110)
        self.tableWidget.setColumnWidth(3,100)
        self.tableWidget.setColumnWidth(4,100)
        
        self.HomeButton.clicked.connect(self.gotoHome)
        self.SaveButton.clicked.connect(self.save)
        self.SearchButton.clicked.connect(self.search)
        self.RemoveButton.clicked.connect(self.remove)
        self.RefreshButton.clicked.connect(self.showTable)

    def search(self):
        with open ('database/user_database.json') as f:
            self.table = json.load(f)
        
        PLATNOMOR = self.NomorKendaraanText.text()

        self.tableWidget.setRowCount(1)
        self.tableWidget.setColumnCount(len(self.table['kendaraan'][0]))

        for data in self.table['kendaraan']:
            column = 0
            if data['Nomor Kendaraan'] == PLATNOMOR:
                for key in data.keys():
                    self.tableWidget.setItem(0, column, QtWidgets.QTableWidgetItem(data[key]))
                    column +=1

    def loadCombo(self):
        with open ('database/user_database.json') as f:
            data = json.load(f)
        self.comboBox.clear()
        for item in data['kendaraan']:
            self.comboBox.addItem(item['ID'])

    def remove(self):
        ID = self.comboBox.currentText()
        with open ('database/user_database.json') as f:
            data = json.load(f)
        itemID = 0
        for item in data['kendaraan']:
            if item['ID'] == ID:
                break
            itemID +=1
        del data['kendaraan'][itemID] #manghapus ID
        
        with open ('database/user_database.json','w') as w:
            json.dump(data, w, indent=2)
        self.showTable()
            
    def gotoHome(self):
        widget.setCurrentIndex(widget.currentIndex()-2) #goto Dashboard

    def save(self):
        
        with open ('database/user_database.json') as f:
            self.data = json.load(f)
        
        self.isExist = False
        for isexist in self.data['kendaraan']:
            if isexist['ID'] == self.IDText.text():
                self.isExist = True
                break

        if not self.isExist:
            self.data['kendaraan'].append(
                {
                    "ID": self.IDText.text(),
                    "Nomor Kendaraan": self.NomorKendaraanText.text(),
                    "Golongan": self.GolonganText.text(),
                    "Tarif": self.TarifText.text(),
                    "Saldo": self.SaldoText.text()
                }
            )
            with open ('database/user_database.json', 'w') as f:
                json.dump(self.data, f, indent=2)
            self.showTable()
        else:
            #popup window that ID is exist
            msg = QMessageBox()
            msg.setWindowTitle("Data ID is already exist")
            msg.setText("ID yang Anda masukan sudah ada di sistem, silahkan hubungi pihak Teknologi Informasi Perusahaan")
            msg.setIcon(QMessageBox.Critical)
            x = msg.exec_()  # this will show our messagebox
        
    def showTable(self):
        self.loadCombo()
        with open ('database/user_database.json') as f:
            self.table = json.load(f)
        
        row=0
        self.tableWidget.setRowCount(len(self.table['kendaraan']))
        self.tableWidget.setColumnCount(len(self.table['kendaraan'][0]))

        for data in self.table['kendaraan']:
            column = 0
            for key in data.keys():
                self.tableWidget.setItem(row, column, QtWidgets.QTableWidgetItem(data[key]))
                column +=1
            row +=1

class TopupForm(QDialog):
    def __init__(self):
        super(TopupForm, self).__init__()
        loadUi('ui/topup.ui', self)
        self.setFixedWidth(610)
        self.setFixedHeight(285)
        self.loadCombo()
        self.SaveButton.clicked.connect(self.save)
        self.HomeButton.clicked.connect(self.gotoHome)

    def loadCombo(self):
        with open ('database/user_database.json') as f:
            data = json.load(f)
        for item in data['kendaraan']:
            self.comboBox.addItem(item['ID'])

    def save(self):
        self.ID = self.comboBox_ID.currentText()
        self.topup = self.comboBox_topup.currentText()
        
        with open ('database/user_database.json') as f:
            data = json.load(f)
        for item in data['kendaraan']:
            if item['ID'] == self.ID:
                saldo = int(item['Saldo']) + int(self.topup)
                item['Saldo'] = str(saldo)
                break
        with open ('database/user_database.json', 'w') as w:
            json.dump(data, w, indent=2)

    def gotoHome(self):
        widget.setCurrentIndex(widget.currentIndex()-3) #goto dashboard  

app = QApplication(sys.argv)
widget = QtWidgets.QStackedWidget()

widget.addWidget(LoginForm())
widget.addWidget(DashboardForm())
widget.addWidget(TransactionForm())
widget.addWidget(ManagerForm())
widget.addWidget(TopupForm())
widget.show()

try:
    sys.exit(app.exec_())
except:
    print('Exiting')