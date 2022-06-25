import os
import os.path

from box import PuzzleGenerator

from PIL import Image

from kivy.uix.behaviors import focus
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.textinput import TextInput
from kivy.graphics.texture import Texture
from kivy.graphics import Rectangle
from kivy.core.window import Window
from kivy.config import Config

Config.set('graphics', 'resizable', False)
TILE_SIZE = 5
WINDOW_HEIGHT = 8 * 16 * TILE_SIZE + 40
WINDOW_WIDTH = 8 * 16 * TILE_SIZE
Window.size = (WINDOW_WIDTH, WINDOW_HEIGHT)
Window.clearcolor = (0.5, 0.5, 0.5, 1)

script_dir = os.path.dirname(os.path.abspath(__file__))
im = Image.open(os.path.join(script_dir, 'all_char.png'), 'r')
all_char_img = list(im.getdata())

def get_texture(kx, ky):
    '''load each tile, kx and ky are the coord in the resource img'''
    texture = Texture.create(size=(16*TILE_SIZE, 16*TILE_SIZE))
    buf = [0] * (4 * ((16*TILE_SIZE) ** 2))
    for i in range(16):
        for j in range(16):
            b = all_char_img[(kx*16+15-i)*16*6+j+16*ky]
            for ii in range(TILE_SIZE):
                for jj in range(TILE_SIZE):
                    a = ((i*TILE_SIZE+ii)*16*TILE_SIZE+j*TILE_SIZE+jj) * 4
                    buf[a], buf[a+1], buf[a+2], buf[a+3] = b[0], b[1], b[2], b[3]
    texture.blit_buffer(bytes(buf), colorfmt='rgba', bufferfmt='ubyte')
    return texture

texture_floor = get_texture(3, 0)
texture_player = get_texture(0, 0)
texture_wall = get_texture(2, 5)
texture_box = get_texture(2, 3)
texture_target = get_texture(3, 4)

class PlayGround(Widget):
    def __init__(self, **kwargs):
        super(PlayGround, self).__init__(**kwargs)
        self.bind(pos=self.update_canvas)
        self.bind(size=self.update_canvas)
        self.puzzle = PuzzleGenerator()
        self.level = 0
        self.init_next_level()
        self.mouse_pos = (-1, -1)
        Window.bind(mouse_pos=self.on_mouse_pos)

    def init_next_level(self):
        self.level += 1
        self.puzzle.loadLevel(self.level-1)
        show_lv = 1 + (self.level - 1) % len(self.puzzle.all_levels)
        App.get_running_app().title = 'Sokoban  level: '+str(show_lv)+''
        self.update_canvas()

    def restart_level(self):
        self.level -= 1
        self.init_next_level()

    def draw_texture(self, x, y, _texture):
        Rectangle(texture=_texture, pos=(y*16*TILE_SIZE, WINDOW_HEIGHT -
                  (x+1)*16*TILE_SIZE), size=(16*TILE_SIZE, 16*TILE_SIZE))

    def update_canvas(self, *args):
        self.canvas.clear()
        with self.canvas:
            for i in range(self.puzzle.h):
                for j in range(self.puzzle.w):
                    self.draw_texture(i, j, texture_floor)
            for (i, j) in self.puzzle.target_pos:
                self.draw_texture(i, j, texture_target)
            self.draw_texture(
                self.puzzle.player_pos[0], self.puzzle.player_pos[1], texture_player)
            for (i, j) in self.puzzle.wall_pos:
                self.draw_texture(i, j, texture_wall)
            for (i, j) in self.puzzle.box_pos:
                self.draw_texture(i, j, texture_box)

    def on_touch_down(self, touch):
        a, b = int(touch.pos[0] // TILE_SIZE // 16), \
            int((WINDOW_HEIGHT-touch.pos[1]) // TILE_SIZE // 16)
        self.puzzle.try_push((b, a))
        self.update_canvas()
        if set(self.puzzle.box_pos) == set(self.puzzle.target_pos):
            self.init_next_level()

    def on_mouse_pos(self, _, pos):
        a, b = int(pos[0] // TILE_SIZE // 16), \
            int((WINDOW_HEIGHT-pos[1]) // TILE_SIZE // 16)
        new_pos = (b, a)
        if new_pos != self.mouse_pos:
            self.mouse_pos = new_pos
            if self.puzzle.is_adjacent(new_pos, self.puzzle.player_pos) \
                and new_pos in self.puzzle.floor_pos \
                    and new_pos not in self.puzzle.box_pos:
                self.puzzle.player_pos = new_pos
                self.update_canvas()

class LevelInput(TextInput):
    '''A custom text input for choosing level, only allow digits'''
    def insert_text(self, substring, from_undo=False):
        if substring.isdecimal():
            filtered_substring = substring
        else:
            filtered_substring = ''
        return super().insert_text(filtered_substring, from_undo=from_undo)

class MyApp(App):
    def build(self):
        root = BoxLayout(orientation='vertical')
        pg = PlayGround(size_hint=(1, 16/17))
        root.add_widget(pg)
        btns = BoxLayout(orientation='horizontal', size_hint=(1, 1/17))
        root.add_widget(btns)
        restart_btn = Button(text="restart", size_hint=(.25, 1))
        previous_level_btn = Button(text="previous level", size_hint=(.25, 1))
        next_level_btn = Button(text="next level", size_hint=(.25, 1))
        choose_level_btn = Button(text="choose level", size_hint=(.25, 1))

        # popup window for choosing level
        popup_content = BoxLayout(orientation='vertical')
        popup_content.add_widget(Label(text='Type the level index (1~{}):'.format(len(pg.puzzle.all_levels))))
        textinput_lv = LevelInput(text='', multiline=False, input_type='number')
        confirmBtn_lv = Button(text="OK")
        cancelBtn_lv = Button(text="Cancel")
        popup_content.add_widget(textinput_lv)
        popup_content.add_widget(confirmBtn_lv)
        popup_content.add_widget(cancelBtn_lv)
        level_popup = Popup(title="choose level", content=popup_content, size_hint=(
            None, None), size=(300, 300))

        def on_click_restart_btn(_):
            pg.restart_level()

        def on_click_previous_level_btn(_):
            pg.level -= 1
            pg.restart_level()

        def on_click_next_level_btn(_):
            pg.level += 1
            pg.restart_level()

        def on_click_choose_level_btn(_):
            level_popup.open()

        def on_click_OK_level_btn(_):
            selected_lv = int(textinput_lv.text)
            pg.level = selected_lv
            pg.restart_level()
            print("choose lv {}".format(selected_lv))
            level_popup.dismiss()
        
        def on_click_cancel_level_btn(_):
            level_popup.dismiss()

        restart_btn.bind(on_press=on_click_restart_btn)
        previous_level_btn.bind(on_press=on_click_previous_level_btn)
        next_level_btn.bind(on_press=on_click_next_level_btn)
        choose_level_btn.bind(on_press=on_click_choose_level_btn)
        confirmBtn_lv.bind(on_press=on_click_OK_level_btn)
        cancelBtn_lv.bind(on_press=on_click_cancel_level_btn)
        btns.add_widget(restart_btn)
        btns.add_widget(previous_level_btn)
        btns.add_widget(next_level_btn)
        btns.add_widget(choose_level_btn)
        return root

MyApp().run()
