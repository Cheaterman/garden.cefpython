#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Cef Keyboard Manager.
Cef Keyboard management is complex, so we outsourced it to this file for
better readability.
'''

__all__ = ('CEFKeyboardManager')

from kivy.core.window import Window
from kivy.uix.vkeyboard import VKeyboard
from lib.cefpython import cefpython


class CEFKeyboardManagerSingleton():
    # Kivy does not provide modifiers in on_key_up, but these
    # must be sent to CEF as well.
    is_shift1 = False
    is_shift2 = False
    is_ctrl1 = False
    is_ctrl2 = False
    is_alt1 = False
    is_alt2 = False

    def __init__(self, *largs, **dargs):
        pass
    
    def reset_all_modifiers(self):
        self.is_shift1 = False
        self.is_shift2 = False
        self.is_ctrl1 = False
        self.is_ctrl2 = False
        self.is_alt1 = False
        self.is_alt2 = False

    def kivy_keyboard_on_textinput(self, browser, window, text):
        """ Kivy ~ > 1.9.2 with SDL2 window, uses on_textinput instead of
        on_key_down
        """
        modifiers = list()
        keycode = (ord(text), text)
        self.process_key_down(browser, None, keycode, text, modifiers)
    
    def kivy_on_key_down(self, browser, keyboard, keycode, text, modifiers):
        whitelist = (8, 27)
        if Window.__class__.__module__ == 'kivy.core.window.window_sdl2' and \
                (keycode[0] not in whitelist):
            return
        self.process_key_down(browser, keyboard, keycode, text, modifiers)

    def process_key_down(self, browser, keyboard, keycode, text, modifiers):
        # print "\non_key_down:", keycode, text, modifiers
        if keycode[0] == 27:
            # On escape release the keyboard, see the injected
            # javascript in OnLoadStart().
            browser.GetFocusedFrame().ExecuteJavascript(
                    "__kivy__on_escape()")
            return

        cef_modifiers = cefpython.EVENTFLAG_NONE
        if "shift" in modifiers:
            cef_modifiers |= cefpython.EVENTFLAG_SHIFT_DOWN
        if "ctrl" in modifiers:
            cef_modifiers |= cefpython.EVENTFLAG_CONTROL_DOWN
        if "alt" in modifiers:
            cef_modifiers |= cefpython.EVENTFLAG_ALT_DOWN
        if "capslock" in modifiers:
            cef_modifiers |= cefpython.EVENTFLAG_CAPS_LOCK_ON

        # print("on_key_down(): cefModifiers = %s" % cefModifiers)
        cef_key_code = self.translate_to_cef_keycode(keycode[0])
        event_type = cefpython.KEYEVENT_KEYDOWN

        # Only send KEYEVENT_KEYDOWN if it is a special key (tab, return ...)
        # Convert every other key to it's utf8 int value
        if cef_key_code == keycode[0] and text:
            cef_key_code = ord(text)
            # print("keycode convert: %s -> %s" % (text, cef_key_code))
            
            # We have to convert the apostrophes as the utf8 key-code
            # somehow isn't recognized by cef
            if cef_key_code == 96:
                cef_key_code = 39
            if cef_key_code == 8220:
                cef_key_code = 34
            
            event_type = cefpython.KEYEVENT_CHAR

        # When the key is the return key,
        # send it as a KEYEVENT_CHAR as it will not work in textinputs
        if cef_key_code == 65293:
            event_type = cefpython.KEYEVENT_CHAR

        key_event = {"type": event_type,
                     "native_key_code": cef_key_code,
                     "modifiers": cef_modifiers
                     }
        print("keyDown keyEvent: %s" % key_event)
        browser.SendKeyEvent(key_event)

        if keycode[0] == 304:
            self.is_shift1 = True
        elif keycode[0] == 303:
            self.is_shift2 = True
        elif keycode[0] == 306:
            self.is_ctrl1 = True
        elif keycode[0] == 305:
            self.is_ctrl2 = True
        elif keycode[0] == 308:
            self.is_alt1 = True
        elif keycode[0] == 313:
            self.is_alt2 = True

    def kivy_on_key_up(self, browser, keyboard, keycode):
        #print("\non_key_up(): keycode = %s" % (keycode,))
        cef_modifiers = cefpython.EVENTFLAG_NONE
        if self.is_shift1 or self.is_shift2:
            cef_modifiers |= cefpython.EVENTFLAG_SHIFT_DOWN
        if self.is_ctrl1 or self.is_ctrl2:
            cef_modifiers |= cefpython.EVENTFLAG_CONTROL_DOWN
        if self.is_alt1:
            cef_modifiers |= cefpython.EVENTFLAG_ALT_DOWN

        cef_key_code = self.translate_to_cef_keycode(keycode[0])

        # Only send KEYEVENT_KEYUP if its a special (enter, tab ...)
        if not cef_key_code == keycode[0]:
            key_event = {"type": cefpython.KEYEVENT_KEYUP,
                         "native_key_code": cef_key_code,
                         "modifiers": cef_modifiers}
            print("keyUp keyEvent: %s" % key_event)
            browser.SendKeyEvent(key_event)

        if keycode[0] == 304:
            self.is_shift1 = False
        elif keycode[0] == 303:
            self.is_shift2 = False
        elif keycode[0] == 306:
            self.is_ctrl1 = False
        elif keycode[0] == 305:
            self.is_ctrl2 = False
        elif keycode[0] == 308:
            self.is_alt1 = False
        elif keycode[0] == 313:
            self.is_alt2 = False

    def translate_to_cef_keycode(self, keycode):
        cef_keycode = keycode
        other_keys_map = {
            # Escape
            "27":65307,
            # F1-F12
            "282":65470, "283":65471, "284":65472, "285":65473,
            "286":65474, "287":65475, "288":65476, "289":65477,
            "290":65478, "291":65479, "292":65480, "293":65481,
            # Tab
            "9":65289,
            # Left Shift, Right Shift
            "304":65505, "303":65506,
            # Left Ctrl, Right Ctrl
            "306":65507, "305": 65508,
            # Left Alt, Right Alt
            "308":65513, "313":65027,
            # Backspace
            "8":65288,
            # Enter
            "13":65293,
            # PrScr, ScrLck, Pause
            "316":65377, "302":65300, "19":65299,
            # Insert, Delete,
            # Home, End,
            # Pgup, Pgdn
            "277":65379, "127":65535,
            "278":65360, "279":65367,
            "280":65365, "281":65366,
            # Arrows (left, up, right, down)
            "276":65361, "273":65362, "275":65363, "274":65364,
        }
        if str(keycode) in other_keys_map:
            cef_keycode = other_keys_map[str(keycode)]
        return cef_keycode


CEFKeyboardManager = CEFKeyboardManagerSingleton()
