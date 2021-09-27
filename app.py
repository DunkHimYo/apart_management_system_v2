from PyQt5 import QtWidgets, uic
from PyQt5.QtGui import *
from PyQt5.QtCore import QTimer
import sys
from clinet import WebsocketClient
import json
from functools import partial
import datetime

TOKEN = None

def widget_management(remove_current_page=False, remove_all_page=False):
    """위젯 관리"""
    def func_management(func):
        def method_management(self):
            next_page_widget = func(self)

            if next_page_widget is not None:
                widget.addWidget(next_page_widget)
                widget.setCurrentWidget(next_page_widget)

            if remove_current_page:
                widget.removeWidget(self)
                widget.setCurrentIndex(widget.currentIndex())

            if remove_all_page:
                for i in range(len(widget), 0, -1):
                    widget.removeWidget(widget.widget(i))
                widget.setCurrentIndex(widget.currentIndex())
            print(widget.__len__())

        return method_management

    return func_management


class startPage(QtWidgets.QMainWindow):
    """로그인 전 시작 프레임"""
    def __init__(self):
        super().__init__()
        uic.loadUi('./ui/startPage.ui', self)

        self.signUp_button.clicked.connect(self._click_signUp)
        self.find_id_ps_button.clicked.connect(self._click_find_id_ps)
        self.question_button.clicked.connect(self._click_question)
        self.login_button.clicked.connect(self._click_logIn)

    @widget_management()
    def _click_signUp(self):
        """회원가입 클릭 시"""
        return signUp_part1()

    @widget_management()
    def _click_find_id_ps(self):
        """ID/PW 찾기 클릭 시"""
        return findIdPw()

    @widget_management()
    def _click_question(self):
        """질문 게시판 클릭 시"""
        return question()

    @widget_management(remove_current_page=True)
    def _click_logIn(self):
        """로그인 클릭 시"""
        global TOKEN
        params = {'id': self.id_line.text(), 'pw': self.pw_line.text()}
        rcv=websocket.send_request('logIn', params)
        print(rcv)
        TOKEN=rcv['params']
        return side_remote_controller(logIn())


class signUp_part1(QtWidgets.QMainWindow):
    """회원 가입 1단계 프레임"""

    def __init__(self):
        super().__init__()
        uic.loadUi('./ui/signUp_part1.ui', self)
        self.checkButton.clicked.connect(self._click_checkButton)
        self.cancelButton.clicked.connect(self._cancel_checkButton)

    @widget_management(remove_current_page=True)
    def _click_checkButton(self):
        return SignUp_part2(self.comboBox.currentText())

    @widget_management(remove_current_page=True)
    def _cancel_checkButton(self):
        return None


class SignUp_part2(QtWidgets.QMainWindow):
    """회원가입 2단계 프레임"""

    def __init__(self,type):
        super().__init__()
        uic.loadUi('./ui/signUp_part2.ui', self)
        self.type=type
        self.checkButton.clicked.connect(self._click_checkButton)
        self.cancelButton.clicked.connect(self._cancel_checkButton)

    def _click_checkButton(self):
        params = {'id': self.id_line.text(), 'pw': self.pw_line.text(), 'type':self.type,'name': self.name_line.text(),
                  'phone_number': self.number_line.text(), 'address': self.address_line.text()}

        print(websocket.send_request('signUp', params))

        self._cancel_checkButton()

    @widget_management(remove_current_page=True)
    def _cancel_checkButton(self):
        return None


class findIdPw(QtWidgets.QMainWindow):
    """ID/PW 찾는 프레임"""
    def __init__(self):
        super().__init__()
        uic.loadUi('./ui/find_Id_Pw.ui', self)
        self.checkButton.clicked.connect(self._click_checkButton)
        self.cancelButton.clicked.connect(self._click_cancelButton)
        header = self.tableWidget
        size = self.geometry()
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        twidth = header.width() + (screen.width() - size.width())
        self.tableWidget.setColumnWidth(0, twidth / 2 * 0.2)
        self.tableWidget.setColumnWidth(1, twidth / 2 * 0.8)

    def _click_checkButton(self):
        params = {'name': self.name_line.text(),
                  'phone_number': self.number_line.text(), 'address': self.address_line.text()}

        rcv_data = websocket.send_request(self.__class__.__name__, params)

        self.tableWidget.setItem(0, 0, QtWidgets.QTableWidgetItem(rcv_data['params']['id']))
        self.tableWidget.setItem(0, 1, QtWidgets.QTableWidgetItem(rcv_data['params']['pw']))

    @widget_management(remove_current_page=True)
    def _click_cancelButton(self):
        return None


class question(QtWidgets.QMainWindow):
    """질문 사항 전송 프레임"""
    def __init__(self):
        super().__init__()
        uic.loadUi('./ui/question_board.ui', self)
        self.checkButton.clicked.connect(self._click_checkButton)
        self.cancelButton.clicked.connect(self._click_cancelButton)

    def _click_checkButton(self):
        params = {'questionNumber':f'{datetime.datetime.utcnow().timestamp()}','title': self.title_line.text(),
                  'contents': self.contents_line.toPlainText()}

        data = websocket.send_request(self.__class__.__name__, params)
        print(data)
        self._click_cancelButton()

    @widget_management(remove_current_page=True)
    def _click_cancelButton(self):
        return None


class logIn(QtWidgets.QMainWindow):
    """로그인 후 프레임"""
    def __init__(self):
        super().__init__()
        uic.loadUi('./ui/login.ui', self)
        header = self.tableWidget
        size = self.geometry()
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        twidth = header.width() + 1.3 * (screen.width() - size.width())

        self.tableWidget.setColumnWidth(0, twidth * 0.05)
        self.tableWidget.setColumnWidth(1, twidth * 0.2)
        self.tableWidget.setColumnWidth(2, twidth * 0.75)

    def showEvent(self, event):
        self.timer = self.startTimer(1)


class inquire(QtWidgets.QMainWindow):
    """요청 사항 프레임"""
    def __init__(self):
        super().__init__()
        uic.loadUi('./ui/inquire_board.ui', self)
        self.checkButton.clicked.connect(self._click_checkButton)
        self.cancelButton.clicked.connect(self._click_cancelButton)

    def _click_checkButton(self):
        params = {'token':TOKEN,'title': self.title_line.text(),
                  'contents': self.contents_line.toPlainText()}

        data = websocket.send_request(self.__class__.__name__, params)
        self._click_cancelButton()

    @widget_management(remove_current_page=True)
    def _click_cancelButton(self):
        return None


class notice(QtWidgets.QMainWindow):
    """공지 사항 프레임"""
    def __init__(self):
        super().__init__()
        uic.loadUi('./ui/notice_board.ui', self)
        header = self.tableWidget
        size = self.geometry()
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        twidth = header.width() + 2.5*(screen.width() - size.width())

        self.tableWidget.setColumnWidth(0, twidth * 0.05)
        self.tableWidget.setColumnWidth(1, twidth * 0.2)
        self.tableWidget.setColumnWidth(2, twidth * 0.75)
        self.write.clicked.connect(self._click_writeButton)

    @widget_management()
    def _click_writeButton(self):
        return side_remote_controller(notice_write())

class communicationBoard(QtWidgets.QMainWindow):
    """주민 소통 프레임"""
    def __init__(self):
        super().__init__()
        uic.loadUi('./ui/communication_board.ui', self)
        header = self.tableWidget
        size = self.geometry()
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        twidth = header.width() + 2.5*(screen.width() - size.width())

        self.tableWidget.setColumnWidth(0, twidth * 0.05)
        self.tableWidget.setColumnWidth(1, twidth * 0.2)
        self.tableWidget.setColumnWidth(2, twidth * 0.75)

        self.write.clicked.connect(self._click_writeButton)

    @widget_management()
    def _click_writeButton(self):
        return side_remote_controller(notice_write())

class talkingRoom(QtWidgets.QMainWindow):
    """대화방 프레임"""
    def __init__(self):
        super().__init__()
        uic.loadUi('./ui/talking_room.ui', self)

class notice_write(QtWidgets.QMainWindow):
    """공지 사항 작성 프레임"""
    def __init__(self):
        super().__init__()
        uic.loadUi('./ui/write_page.ui', self)
        self.checkButton.clicked.connect(self._click_checkButton)
        self.cancelButton.clicked.connect(self._click_cancelButton)

    def _click_checkButton(self):
        params = {'title': self.title_line.text(),
                  'contents': self.contents_line.toPlainText()}

        data = websocket.send_request(self.__class__.__name__, params)
        self._click_cancelButton()

    @widget_management(remove_current_page=True)
    def _click_cancelButton(self):
        return None

def side_remote_controller(cls):
    """슬리이드 리모컨 부착 위젯"""
    remove_current_page = False if cls.__class__.__name__=='logIn' else True

    @widget_management(remove_all_page=True)
    def _click_homeButton(self=None):
        return None

    @widget_management(remove_current_page=True)
    def _click_logOutButton(self=None):
        """질문 게시판 클릭 시"""
        return startPage()

    @widget_management(remove_current_page=remove_current_page)
    def _click_inquireButton(self=None):
        """질문 게시판 클릭 시"""
        return side_remote_controller(inquire())

    @widget_management(remove_current_page=remove_current_page)
    def _click_noticeButton(self=None):
        """질문 게시판 클릭 시"""
        return side_remote_controller(notice())

    @widget_management(remove_current_page=remove_current_page)
    def _click_communicationButton(self=None):
        """질문 게시판 클릭 시"""
        return side_remote_controller(communicationBoard())

    @widget_management(remove_current_page=remove_current_page)
    def _click_talkingButton(self=None):
        """질문 게시판 클릭 시"""
        return side_remote_controller(talkingRoom())

    cls.log_out.clicked.connect(partial(_click_logOutButton,cls))
    cls.home.clicked.connect(partial(_click_homeButton,cls))
    cls.inquire.clicked.connect(partial(_click_inquireButton,cls))
    cls.notice.clicked.connect(partial(_click_noticeButton,cls))
    cls.communication.clicked.connect(partial(_click_communicationButton, cls))
    cls.talking.clicked.connect(partial(_click_talkingButton, cls))

    return cls

if __name__ == '__main__':
    websocket = WebsocketClient('ws://localhost:3000', check_response=True)
    app = QtWidgets.QApplication(sys.argv)
    widget = QtWidgets.QStackedWidget()
    widget.addWidget(startPage())
    widget.showMaximized()
    app.exec_()
