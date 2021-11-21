from PyQt5.QtCore import QSettings

from main import MainUI, ExpandFrame, ScrollFrame


def delete_save(filename, version):
    settings = QSettings('ReadingAppQt', f'{filename}_{version}')
    settings.clear()


def save(main_ui: MainUI):
    settings = QSettings('ReadingAppQt', f'{main_ui.filename}_{main_ui.version}')

    settings.setValue('saved', True)
    settings.setValue('window size', main_ui.size())
    settings.setValue('window position', main_ui.pos())

    save_scroll_frame(main_ui.main_frame.scroll_frame, settings)


def save_expand_frame(frame: ExpandFrame, settings: QSettings, frame_id):
    settings.setValue(f'frame {frame_id} begin', frame.begin)
    settings.setValue(f'frame {frame_id} end', frame.end)
    settings.setValue(f'frame {frame_id} position', frame.highlight_position)


def save_scroll_frame(scroll_frame: ScrollFrame, settings: QSettings):
    settings.setValue('font size', scroll_frame.font_size)
    settings.setValue('speed', scroll_frame.speed)
    settings.setValue('current line', scroll_frame.current_line)
    settings.setValue('width', scroll_frame.frames[0].width)

    for frame_id, frame in enumerate(scroll_frame.frames):
        save_expand_frame(frame, settings, frame_id)
