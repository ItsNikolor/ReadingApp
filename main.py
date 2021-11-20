import re
import sys

from PyQt5.QtCore import Qt, QEvent, QTimer
from PyQt5.QtGui import QPalette, QColor, QResizeEvent
from PyQt5.QtWidgets import QApplication, QLabel, QFrame, QVBoxLayout, QWidget, \
    QScrollArea, QHBoxLayout


class ScrollFrame(QFrame):
    def __init__(self, words, progress_label, *args):
        super().__init__(*args)

        self.scroll = None
        self.speed = None
        self.pause_counter = 0
        self.words = words
        self.progress_label = progress_label

        self.pause = True
        self.font_size = 15
        self.font_family = 'Verdana'#Open Sans

        self.highlight_line = 6
        self.highlight_style = 'background-color:black;' \
                               'color:red;'
        self.current_line = 0

        self.INITIAL_LINES = 40
        self.labels = [ExpandLabel(words) for _ in range(self.INITIAL_LINES)]
        self.positions = [(0, 0)] * len(self.labels)

        self.setStyleSheet(f'font-size: {self.font_size}pt;'
                           f'font-family: {self.font_family};')

    def setScroll(self, scroll):
        self.scroll = scroll

    def fill(self):
        end = self.positions[self.current_line][0]
        for i, l in enumerate(self.labels[:self.current_line][::-1]):
            begin, counter = l.fillReversed(end)
            self.positions[self.current_line - i - 1] = (begin - counter, end)
            if counter != 0:
                for j in range(self.current_line - i - 1, self.current_line + 1):
                    self.positions[j] = (self.positions[j][0] + counter, self.positions[j][1] + counter)
            end = begin

        begin = self.positions[self.current_line][0]
        for i, l in enumerate(self.labels[self.current_line:]):
            end = l.fill(begin)
            self.positions[i + self.current_line] = (begin, end)
            begin = end

    def increaseFontSize(self):
        self.font_size = min(60, self.font_size + 5)
        self.setStyleSheet(f'font-size: {self.font_size}pt')
        self.fill()

    def decreaseFontSize(self):
        self.font_size = max(10, self.font_size - 5)
        self.setStyleSheet(f'font-size: {self.font_size}pt')
        self.fill()

    def updateProgressBar(self):
        self.progress_label.setText(
            f"Прогресс = {self.positions[self.current_line][0] / len(self.words) * 100:.2f}%")

    def moveDown(self):
        if self.positions[self.current_line][0] == len(self.words):
            self.pause = True
            return

        if self.current_line < self.highlight_line:
            self.current_line += 1
            self.labels[self.current_line - 1].setStyleSheet('')
            self.labels[self.current_line].setStyleSheet(self.highlight_style)
            self.updateProgressBar()
            return

        for i in range(len(self.positions) - 1):
            self.labels[i].setText(self.labels[i + 1].text())
            self.positions[i] = self.positions[i + 1]

        self.positions[-1] = (self.positions[-1][1], self.labels[-1].fill(self.positions[-1][1]))
        self.updateProgressBar()

    def moveUp(self):
        if self.positions[min(self.highlight_line, self.current_line)][0] == 0:
            return

        if self.positions[0][0] == 0:
            self.current_line -= 1
            self.labels[self.current_line + 1].setStyleSheet('')
            self.labels[self.current_line].setStyleSheet(self.highlight_style)
            self.updateProgressBar()
            return
        for i in range(len(self.positions) - 1, 0, -1):
            self.labels[i].setText(self.labels[i - 1].text())
            self.positions[i] = self.positions[i - 1]

        begin, counter = self.labels[0].fillReversed(self.positions[0][0])
        self.positions[0] = (begin - counter, self.positions[0][0])
        if counter != 0:
            for i in range(len(self.positions)):
                self.positions[i] = (self.positions[i][0] + counter, self.positions[i][1] + counter)
        self.updateProgressBar()

    def start(self):
        self.pause = (self.pause + 1) & 1
        self.pause_counter += 1

        if not self.pause:
            self.firstRun(self.pause_counter)

    def firstRun(self, counter):
        if self.pause:
            return
        timer = QTimer(self)
        timer.setSingleShot(True)

        def run(self, counter):
            if counter != self.pause_counter or self.pause:
                return
            self.moveDown()
            self.firstRun(counter)

        timer.timeout.connect(lambda: run(self, counter))

        ratio = 60 * 1000 / self.speed
        timer.start(int((self.positions[self.current_line][1] - self.positions[self.current_line][0]) * ratio))

    def construct(self):
        self.labels[0].setStyleSheet(self.highlight_style)
        for label in self.labels:
            label.setAlignment(Qt.AlignCenter)
            self.layout().addWidget(label)
        self.layout().addStretch()


class ExpandLabel(QLabel):
    def __init__(self, words, *args):
        super().__init__(*args)
        self.words = words
        self.width = None

    def fill(self, begin):
        cur = begin
        self.setText('')
        while self.fontMetrics().boundingRect(self.text()).width() < self.width and cur <= len(self.words):
            cur += 1
            self.setText(' '.join(self.words[begin:cur]))

        if begin == len(self.words):
            self.setText('')
            return cur - 1

        if begin == cur - 1:
            word = self.words[begin]
            size = word.index('-') if '-' in word else len(word) // 2

            if word[size] == '-':
                word = word[:size] + word[size + 1:]

            self.words[begin] = word[:size] + '-'
            self.words.insert(begin + 1, word[size:])
            return self.fill(begin)
        else:
            i = begin
            while i != cur - 2:
                if self.words[i][-1] == '-':
                    self.words[i] = self.words[i][:-1] + self.words[i + 1]
                    cur -= 1
                    del self.words[i + 1]
                    continue
                else:
                    i += 1
        self.setText(' '.join(self.words[begin:cur - 1]))
        return cur - 1

    def fillReversed(self, end):
        cur = end
        self.setText('')
        while self.fontMetrics().boundingRect(self.text()).width() < self.width and cur != -1:
            cur -= 1
            self.setText(' '.join(self.words[cur:end]))

        if end == 0:
            self.setText('')
            return cur + 1, 0

        if end == cur + 1:
            word = self.words[end - 1]
            size = word.index('-') if '-' in word else len(word) // 2

            if word[size] == '-':
                word = word[:size] + word[size + 1:]

            self.words[end - 1] = word[:size] + '-'
            self.words.insert(end, word[size:])

            ans, counter = self.fillReversed(end + 1)
            return ans, counter + 1
        else:
            i = cur + 1
            counter = 0
            while i != end - 1:
                if self.words[i][-1] == '-':
                    self.words[i] = self.words[i][:-1] + self.words[i + 1]
                    end -= 1
                    del self.words[i + 1]
                    counter -= 1
                    continue
                else:
                    i += 1

        self.setText(' '.join(self.words[cur + 1:end]))
        return cur + 1, counter


class MainFrame(QFrame):
    class MyScroller(QScrollArea):
        def wheelEvent(self, ev):
            if ev.type() == QEvent.Wheel:
                ev.ignore()

    def __init__(self, words, progress_bar):
        super(MainFrame, self).__init__()

        self.progress_bar = progress_bar
        self.margin = 16

        self.vbox = QVBoxLayout()
        self.vbox.setContentsMargins(0, 0, 0, 0)
        self.vbox.setSpacing(0)

        self.scroll_frame = ScrollFrame(words, self.progress_bar, self)
        self.scroll_frame.setLayout(self.vbox)

        self.scroll = MainFrame.MyScroller(self)
        self.scroll.setWidget(self.scroll_frame)
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollBar {height:0px;}")
        layout = QVBoxLayout(self)
        layout.addWidget(self.scroll)

        layout.setContentsMargins(*[self.margin] * 4)

        self.scroll_frame.setScroll(self.scroll)
        self.scroll_frame.construct()

        self.cur_width = self.size().width()

    def resizeEvent(self, a0: QResizeEvent) -> None:
        super(MainFrame, self).resizeEvent(a0)

        if self.cur_width == self.size().width():
            return
        self.cur_width = self.size().width()

        for label in self.scroll_frame.labels:
            label.width = self.cur_width - 2 * self.margin - 2
        self.scroll_frame.fill()


class MainUI(QWidget):
    def __init__(self, screen_width, screen_height, titlebar_height):
        super().__init__()

        self.setGeometry(screen_width // 3, titlebar_height, screen_width // 3, screen_height - titlebar_height)

        speed = 200
        vbox = QVBoxLayout(self)
        self.info_frame = QFrame()
        self.initialize_info(speed)

        with open('text.txt', 'r', encoding='utf-8') as f:
            lines = [re.sub('[^\w!"#$%&\'()*+,-./:;<=>?@[\]^_`{|}~]+', ' ', line) for line in f]
        words = [word for line in lines for word in line.split()]

        # words[20] = 'Очень-Очень-ОченьДлинноеСлово'

        self.main_frame = MainFrame(words[400:5000], self.progress_label)
        self.font_label.setText(f'Шрифт = {self.main_frame.scroll_frame.font_size}')
        self.main_frame.scroll_frame.speed = speed
        vbox.addWidget(self.info_frame)
        vbox.addWidget(self.main_frame)

        self.setChildrenFocusPolicy(Qt.NoFocus)
        self.show()

    def initialize_info(self, SPEED):
        hbox = QHBoxLayout(self.info_frame)

        self.speed_label = QLabel(f"Скорость = {SPEED} слов в минуту")
        self.progress_label = QLabel(f"Прогресс = 0%")
        self.font_label = QLabel(f'Шрифт = 0')

        for label in [self.speed_label, self.progress_label, self.font_label]:
            label.setAlignment(Qt.AlignCenter)
            hbox.addWidget(label)
        self.info_frame.setStyleSheet('font-family: Open Sans')

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.deleteLater()
        elif event.key() in [Qt.Key_Enter, Qt.Key_Space, Qt.Key_Return]:
            self.main_frame.scroll_frame.start()
        elif event.key() == Qt.Key_Equal:
            self.main_frame.scroll_frame.increaseFontSize()
            self.font_label.setText(f'Шрифт = {self.main_frame.scroll_frame.font_size}')
        elif event.key() == Qt.Key_Minus:
            self.main_frame.scroll_frame.decreaseFontSize()
            self.font_label.setText(f'Шрифт = {self.main_frame.scroll_frame.font_size}')
        elif event.key() == Qt.Key_Right:
            self.main_frame.scroll_frame.speed += 10
            self.speed_label.setText(f"Скорость = {self.main_frame.scroll_frame.speed} слов в минуту")
        elif event.key() == Qt.Key_Left:
            self.main_frame.scroll_frame.speed = max(self.main_frame.scroll_frame.speed - 10, 10)
            self.speed_label.setText(f"Скорость = {self.main_frame.scroll_frame.speed} слов в минуту")
        elif event.key() == Qt.Key_Down:
            self.main_frame.scroll_frame.moveDown()
        elif event.key() == Qt.Key_Up:
            self.main_frame.scroll_frame.moveUp()
        event.accept()

    def setChildrenFocusPolicy(self, policy):
        def recursiveSetChildFocusPolicy(parentQWidget):
            for childQWidget in parentQWidget.findChildren(QWidget):
                childQWidget.setFocusPolicy(policy)
                recursiveSetChildFocusPolicy(childQWidget)

        recursiveSetChildFocusPolicy(self)


def initialize():
    app = QApplication([])
    dark_fusion(app)

    # font_db = QFontDatabase()
    # font_id = font_db.addApplicationFont("OpenSans-Regular.ttf")
    # families = font_db.applicationFontFamilies(font_id)
    # QFontDatabase.addApplicationFont('OpenSans-Regular.ttf')

    screen = app.primaryScreen()
    screen_height, screen_width = screen.availableGeometry().height(), screen.availableGeometry().width()
    titlebar_height = 40

    ex = MainUI(screen_width, screen_height, titlebar_height)

    sys.exit(app.exec_())


def dark_fusion(qApp):
    qApp.setStyle("Fusion")

    dark_palette = QPalette()

    dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)

    qApp.setPalette(dark_palette)

    qApp.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    initialize()
