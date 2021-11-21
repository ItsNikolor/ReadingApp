import re
import sys

from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QEvent, QTimer, QSettings
from PyQt5.QtGui import QResizeEvent
from PyQt5.QtWidgets import QApplication, QLabel, QFrame, QVBoxLayout, QWidget, \
    QScrollArea, QHBoxLayout

from dark_fusion import dark_fusion
import save


class ScrollFrame(QFrame):
    def __init__(self, settings, words, progress_label, *args):
        super().__init__(*args)

        if settings.contains('saved'):
            self.font_size = settings.value('font size')
            self.current_line = settings.value('current line')
        else:
            self.font_size = 15
            self.current_line = 0

        self.scroll = None
        self.speed = None
        self.pause_counter = 0
        self.words = words
        self.progress_label = progress_label

        self.pause = True
        self.font_family = 'Verdana'  # Open Sans

        self.highlight_line = 5
        self.highlight_line_style = 'background-color:black;'

        self.INITIAL_LINES = 20
        self.frames = [ExpandFrame(settings, frame_id, words) for frame_id in range(self.INITIAL_LINES)]
        self.updateProgressBar()

        self.setStyleSheet(f'font-size: {self.font_size}pt;'
                           f'font-family: {self.font_family};')
        # self.jump(33065)

    def setScroll(self, scroll):
        self.scroll = scroll

    def fill(self):
        end = self.frames[self.current_line].begin

        for i, frame in enumerate(self.frames[:self.current_line][::-1]):
            begin, counter = frame.fillReversed(end)
            if counter != 0:
                for j in range(self.current_line - i, self.current_line + 1):
                    self.frames[j].begin += counter
                    self.frames[j].end += counter
            end = begin

        begin = self.frames[self.current_line].begin
        for i, frame in enumerate(self.frames[self.current_line:]):
            end = frame.fill(begin)
            begin = end

    def jump(self, position):
        self.frames[self.current_line].begin = position
        # self.adjustSize()
        # self.fill()

    def increaseFontSize(self):
        self.font_size = min(40, self.font_size + 5)
        self.setStyleSheet(f'font-size: {self.font_size}pt;'
                           f'font-family: {self.font_family};')
        self.fill()

    def decreaseFontSize(self):
        self.font_size = max(10, self.font_size - 5)
        self.setStyleSheet(f'font-size: {self.font_size}pt;'
                           f'font-family: {self.font_family};')
        self.fill()

    def updateProgressBar(self):
        self.progress_label.setText(
            f"Прогресс = {self.frames[self.current_line].begin / len(self.words) * 100:.2f}%")

    def moveDown(self):
        if self.frames[self.current_line].begin == len(self.words):
            self.pause = True
            return

        last_frame = self.frames[self.current_line]
        last_frame.labels[last_frame.highlight_position].setStyleSheet('')
        last_frame.highlight_position = 0

        if self.current_line < self.highlight_line:
            self.current_line += 1
            self.frames[self.current_line - 1].setStyleSheet('')
            self.frames[self.current_line].setStyleSheet(self.highlight_line_style)
            self.updateProgressBar()

            self.frames[self.current_line].labels[1].setStyleSheet(ExpandFrame.highlight_word_style)
            self.frames[self.current_line].highlight_position = 1
            return

        self.frames[self.current_line].highlight_position = 1
        for i in range(len(self.frames) - 1):
            self.frames[i].populate(self.frames[i + 1].begin, self.frames[i + 1].end)

        self.frames[-1].fill(self.frames[-1].end)
        self.updateProgressBar()

    def moveUp(self):
        if self.frames[self.current_line].begin == 0:
            return

        last_frame = self.frames[self.current_line]
        last_frame.labels[last_frame.highlight_position].setStyleSheet('')
        last_frame.highlight_position = 0

        if self.frames[0].begin == 0:
            self.current_line -= 1
            self.frames[self.current_line + 1].setStyleSheet('')
            self.frames[self.current_line].setStyleSheet(self.highlight_line_style)
            self.updateProgressBar()
            self.frames[self.current_line].labels[1].setStyleSheet(ExpandFrame.highlight_word_style)
            self.frames[self.current_line].highlight_position = 1
            return

        self.frames[self.current_line].highlight_position = 1
        for i in range(len(self.frames) - 1, 0, -1):
            self.frames[i].populate(self.frames[i - 1].begin, self.frames[i - 1].end)

        begin, counter = self.frames[0].fillReversed(self.frames[0].begin)
        if counter != 0:
            for i in range(1, len(self.frames)):
                self.frames[i].begin += counter
                self.frames[i].end += counter
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

        def run(captured_self, captured_counter):
            if captured_counter != captured_self.pause_counter or captured_self.pause:
                return

            if captured_self.frames[captured_self.current_line].step():
                captured_self.moveDown()
            captured_self.firstRun(captured_counter)

        timer.timeout.connect(lambda: run(self, counter))

        ratio = 60 * 1000 / self.speed
        timer.start(int(ratio) + 1)

    def construct(self):
        self.frames[self.current_line].setStyleSheet(self.highlight_line_style)
        for frame in self.frames:
            self.layout().addWidget(frame)
        self.layout().addStretch()


class ExpandFrame(QFrame):
    highlight_word_style = 'color: red'

    def __init__(self, settings, frame_id, words, *args):
        super().__init__(*args)
        self.words = words

        self.hbox = QHBoxLayout(self)

        self.space_label = QLabel(' ')
        self.labels = [self.space_label]
        self.hbox.addWidget(self.labels[0], 0)

        self.hbox.setSpacing(0)

        self.begin = 0#33065
        self.end = 0

        if settings.contains('saved'):
            self.width = settings.value('width')
            begin = settings.value(f'frame {frame_id} begin')
            end = settings.value(f'frame {frame_id} end')
            self.highlight_position = settings.value(f'frame {frame_id} position')
            self.populate(begin, end)
        else:
            self.width = None
            self.highlight_position = 0

    def step(self):
        if self.begin == len(self.words):
            return True
        self.labels[self.highlight_position].setStyleSheet('')
        self.highlight_position += 1
        if self.highlight_position == len(self.labels) - 1:
            return True
        self.labels[self.highlight_position].setStyleSheet(self.highlight_word_style)
        return False

    def get_width(self, text):
        return self.space_label.fontMetrics().width(text)

    def populate(self, begin, end, force_render=False):
        if self.begin != begin or self.end != end or force_render:
            self.begin = begin
            self.end = end
            for _ in range(len(self.labels) - 1):
                self.hbox.removeWidget(self.labels[-1])
                self.labels[-1].destroy()
                self.labels.pop()

            for i in range(begin, end):
                self.labels.append(QLabel(self.words[i] + ' '))
                self.labels[-1].setAlignment(Qt.AlignCenter)
                self.hbox.addWidget(self.labels[-1], 1)

            self.labels.append(QLabel(' '))
            self.hbox.addWidget(self.labels[-1], 0)

            if self.highlight_position > 0:
                self.highlight_position = min(len(self.labels) - 2, self.highlight_position)
                self.labels[self.highlight_position].setStyleSheet(self.highlight_word_style)

    def fill(self, begin):
        if begin == len(self.words):
            self.populate(begin, begin)
            return begin

        cur = begin
        # self.space_label.adjustSize()

        cur_width = 3 * self.get_width(' ') + self.get_width(self.words[begin] + ' ')
        cur += 1

        while cur_width <= self.width and cur < len(self.words):
            cur_width += self.get_width(self.words[cur] + ' ')
            cur += 1

        if cur_width > self.width:
            cur -= 1

        if cur == begin:
            word = self.words[begin]

            # size = word.index('-') if '-' in word else len(word) // 2
            # if word[size] == '-':
            #     word = word[:size] + word[size + 1:]

            size = len(word) // 2

            self.words[begin] = word[:size] + '-'
            self.words.insert(begin + 1, word[size:])
            return self.fill(begin)
        else:
            force_render = False
            i = begin

            while i != cur - 1:
                if self.words[i][-1] == '-':
                    self.words[i] = self.words[i][:-1] + self.words[i + 1]
                    cur -= 1
                    del self.words[i + 1]
                    force_render = True
                    continue
                else:
                    i += 1

        self.populate(begin, cur, force_render)
        return cur

    def fillReversed(self, end):
        if end == 0:
            print('Wtf why end = 0')
            self.populate(end, end)
            return end, 0

        cur = end - 1
        self.space_label.adjustSize()

        cur_width = self.get_width(' ') + self.get_width(self.words[cur] + ' ')
        cur -= 1

        while cur_width <= self.width and cur >= 0:
            cur_width += self.get_width(self.words[cur] + ' ')
            cur -= 1

        if cur_width > self.width:
            cur += 1

        if cur + 1 == end:
            word = self.words[end - 1]

            # size = word.index('-') if '-' in word else len(word) // 2
            #
            # if word[size] == '-':
            #     word = word[:size] + word[size + 1:]

            size = len(word) // 2

            self.words[end - 1] = word[:size] + '-'
            self.words.insert(end, word[size:])

            ans, counter = self.fillReversed(end + 1)
            return ans, counter + 1
        else:
            counter = 0
            force_render = False
            i = cur + 1

            while i != end - 1:
                if self.words[i][-1] == '-':
                    self.words[i] = self.words[i][:-1] + self.words[i + 1]
                    end -= 1
                    del self.words[i + 1]
                    counter -= 1
                    force_render = True
                    continue
                else:
                    i += 1

        self.populate(cur + 1, end, force_render)
        return cur + 1, counter


class MainFrame(QFrame):
    class MyScroller(QScrollArea):
        def wheelEvent(self, ev):
            if ev.type() == QEvent.Wheel:
                ev.ignore()

    def __init__(self, settings, words, progress_bar):
        super(MainFrame, self).__init__()

        self.progress_bar = progress_bar
        self.margin = 16

        self.vbox = QVBoxLayout()
        self.vbox.setContentsMargins(0, 0, 0, 0)
        self.vbox.setSpacing(0)

        self.scroll_frame = ScrollFrame(settings, words, self.progress_bar, self)
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

        for frame in self.scroll_frame.frames:
            frame.width = self.cur_width - 2 * self.margin - 2
        self.scroll_frame.fill()


class MainUI(QWidget):
    version = 0

    def __init__(self, filename, screen_width, screen_height, titlebar_height):
        super().__init__()

        self.filename = filename
        with open(filename, 'r', encoding='utf-8') as f:
            lines = [re.sub('[^\w!"#$%&\'()*+,-./:;<=>?@[\]^_`{|}~]+', ' ', line) for line in f]
        words = [word for line in lines for word in line.split()]

        for i in range(len(words)):
            if words[i]=='ДРАКА-ДРАКА':#33065
                print(i)

        settings = QSettings('ReadingAppQt', f'{filename}_{self.version}')
        if settings.contains('saved'):
            print('Loaded')
            speed = settings.value('speed')
            self.resize(settings.value('window size'))
            self.move(settings.value('window position'))
        else:
            self.setGeometry(screen_width // 3, titlebar_height, screen_width // 3, screen_height - titlebar_height)
            speed = 200

        vbox = QVBoxLayout(self)
        self.info_frame = QFrame()
        self.initialize_info(speed)

        self.main_frame = MainFrame(settings, words, self.progress_label)
        self.font_label.setText(f'Шрифт = {self.main_frame.scroll_frame.font_size}')
        self.main_frame.scroll_frame.speed = speed
        vbox.addWidget(self.info_frame)
        vbox.addWidget(self.main_frame)

        self.setChildrenFocusPolicy(Qt.NoFocus)
        # self.show()

    def initialize_info(self, SPEED):
        hbox = QHBoxLayout(self.info_frame)

        self.speed_label = QLabel(f"Скорость = {SPEED} слов в минуту")
        self.progress_label = QLabel(f"Прогресс = 0%")
        self.font_label = QLabel(f'Шрифт = 0')

        for label in [self.speed_label, self.progress_label, self.font_label]:
            label.setAlignment(Qt.AlignCenter)
            hbox.addWidget(label)
        self.info_frame.setStyleSheet('font-family: Arial')

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
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

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        save.save(self)


def initialize():
    app = QApplication([])
    dark_fusion(app)

    screen = app.primaryScreen()
    screen_height, screen_width = screen.availableGeometry().height(), screen.availableGeometry().width()
    titlebar_height = 40

    # save.delete_save('text.txt',0)
    ex = MainUI('text.txt', screen_width, screen_height, titlebar_height)
    ex.show()

    sys.exit(app.exec_())


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    initialize()
