from PyQt5.QtCore import QSettings

import read
from main import MainUI, ScrollFrame


def delete_save(version, filename=''):
    if filename:
        settings = QSettings('ReadingAppQt', f'{filename}_{version}')
    else:
        settings = QSettings('ReadingAppQt', f'Main_{version}')
    settings.clear()


def save(main_ui: MainUI):
    settings = QSettings('ReadingAppQt', f'Main_{main_ui.version}')
    settings.setValue('saved', True)
    settings.setValue('window size', main_ui.size())
    settings.setValue('window position', main_ui.pos())
    settings.setValue('last directory', main_ui.last_directory)
    settings.setValue('last filename', main_ui.filename)
    settings.setValue('recent files', main_ui.recent_files)

    settings = QSettings('ReadingAppQt', f'{main_ui.filename}_{main_ui.version}')
    settings.setValue('saved', True)
    save_scroll_frame(main_ui.main_frame.scroll_frame, settings)


def save_scroll_frame(scroll_frame: ScrollFrame, settings: QSettings):
    settings.setValue('font size', scroll_frame.font_size)
    settings.setValue('speed', scroll_frame.speed)
    settings.setValue('current line', scroll_frame.current_line)
    settings.setValue('width', scroll_frame.frames[0].width)

    settings.setValue('position', scroll_frame.frames[scroll_frame.current_line].begin)
    settings.setValue('highlight', scroll_frame.frames[scroll_frame.current_line].highlight_position)


def load(main_ui: MainUI):
    settings = QSettings('ReadingAppQt', f'Main_{main_ui.version}')
    if not settings.contains('saved'):
        return
    main_ui.last_directory = settings.value('last directory')
    main_ui.filename = settings.value('last filename')
    main_ui.recent_files = settings.value('recent files')

    main_ui.resize(settings.value('window size'))
    main_ui.move(settings.value('window position'))

    load_scroll_frame(main_ui)


def load_scroll_frame(main_ui: MainUI):
    settings = QSettings('ReadingAppQt', f'{main_ui.filename}_{main_ui.version}')
    if not settings.contains('saved'):
        return

    print('Loaded')
    scroll_frame = main_ui.main_frame.scroll_frame

    scroll_frame.speed = settings.value('speed')
    main_ui.speed_label.setText(f"Скорость = {scroll_frame.speed} слов в минуту")
    main_ui.font_label.setText(f'Шрифт = {settings.value("font size")}')

    words = read.read(main_ui.filename)
    main_ui.populate(words)
    scroll_frame = main_ui.main_frame.scroll_frame

    scroll_frame.font_size = settings.value('font size')
    scroll_frame.setStyleSheet(f'font-size: {scroll_frame.font_size}pt;'
                               f'font-family: {scroll_frame.font_family};')

    scroll_frame.frames[scroll_frame.current_line].setStyleSheet('')
    scroll_frame.current_line = settings.value('current line')
    if words:
        scroll_frame.frames[scroll_frame.current_line].setStyleSheet(scroll_frame.highlight_line_style)
    for frame in scroll_frame.frames:
        frame.width = settings.value('width')
    scroll_frame.jump(settings.value('position'), settings.value('highlight'))
