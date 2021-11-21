from PyQt5.QtCore import QSettings

from main import MainUI, ScrollFrame


def delete_save(filename, version):
    settings = QSettings('ReadingAppQt', f'{filename}_{version}')
    settings.clear()


def save(main_ui: MainUI):
    settings = QSettings('ReadingAppQt', f'{main_ui.filename}_{main_ui.version}')

    settings.setValue('saved', True)
    settings.setValue('window size', main_ui.size())
    settings.setValue('window position', main_ui.pos())

    save_scroll_frame(main_ui.main_frame.scroll_frame, settings)


def save_scroll_frame(scroll_frame: ScrollFrame, settings: QSettings):
    settings.setValue('font size', scroll_frame.font_size)
    settings.setValue('speed', scroll_frame.speed)
    settings.setValue('current line', scroll_frame.current_line)
    settings.setValue('width', scroll_frame.frames[0].width)

    settings.setValue('position', scroll_frame.frames[scroll_frame.current_line].begin)
    settings.setValue('highlight', scroll_frame.frames[scroll_frame.current_line].highlight_position)


def load(main_ui: MainUI):
    settings = QSettings('ReadingAppQt', f'{main_ui.filename}_{main_ui.version}')
    if not settings.contains('saved'):
        return

    print('Loaded')
    scroll_frame = main_ui.main_frame.scroll_frame
    main_ui.resize(settings.value('window size'))
    main_ui.move(settings.value('window position'))

    scroll_frame.speed = settings.value('speed')
    main_ui.speed_label.setText(f"Скорость = {scroll_frame.speed} слов в минуту")

    scroll_frame.font_size = settings.value('font size')
    scroll_frame.setStyleSheet(f'font-size: {scroll_frame.font_size}pt;'
                               f'font-family: {scroll_frame.font_family};')
    main_ui.font_label.setText(f'Шрифт = {scroll_frame.font_size}')

    scroll_frame.frames[scroll_frame.current_line].setStyleSheet('')
    scroll_frame.current_line = settings.value('current line')
    scroll_frame.frames[scroll_frame.current_line].setStyleSheet(scroll_frame.highlight_line_style)
    scroll_frame.jump(settings.value('position'), settings.value('highlight'))
