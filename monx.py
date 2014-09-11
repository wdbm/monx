#!/usr/bin/python

"""
################################################################################
#                                                                              #
# monx                                                                         #
#                                                                              #
################################################################################
#                                                                              #
# LICENCE INFORMATION                                                          #
#                                                                              #
# The program monx can monitor events and execute corresponding actions.       #
#                                                                              #
# copyright (C) 2014 William Breaden Madden                                    #
#                                                                              #
# This software is released under the terms of the GNU General Public License  #
# version 3 (GPLv3).                                                           #
#                                                                              #
# This program is free software: you can redistribute it and/or modify it      #
# under the terms of the GNU General Public License as published by the Free   #
# Software Foundation, either version 3 of the License, or (at your option)    #
# any later version.                                                           #
#                                                                              #
# This program is distributed in the hope that it will be useful, but WITHOUT  #
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or        #
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for    #
# more details.                                                                #
#                                                                              #
# For a copy of the GNU General Public License, see                            #
# <http://www.gnu.org/licenses/>.                                              #
#                                                                              #
################################################################################

The configuration (file) should feature a Markdown list of the following form:

- event-execution-map
   - <event, e.g. shift-left>
      - description: <natural language description, e.g. say hello world>
      - command: <command, e.g. echo "hello world" | festival --tts>

Usage:
    monx.py [options]

Options:
    -h, --help                 Show this help message.
    --version                  Show the version and exit.
    -c, --configuration=CONF   configuration (file) [default: ~/.ucom]
"""

version = "2014-09-11T2035"

import os
import sys
from time import sleep, time
import ctypes as ctypes
from ctypes.util import find_library
from docopt import docopt
import logging
import pyrecon as pyrecon

def main(options):
    global program
    global keyboard
    program = Program(options = options)
    keyboard = Keyboard()
    keyboard.logLoop()

class Program(object):

    def __init__(
        self,
        parent = None,
        options = None # docopt options
        ):
        # logging
        global logger
        logger = logging.getLogger(__name__)
        logging.basicConfig()
        logger.level = logging.INFO
        # configuration
        configurationFileName = options["--configuration"]
        self.configuration = pyrecon.openConfiguration(configurationFileName)

class Keyboard:

    def __init__(
        self,
        parent = None
        ):
        # X11 interface
        self.X11 = ctypes.cdll.LoadLibrary(find_library("X11"))
        self.displayX11 = self.X11.XOpenDisplay(None)
        # keyboard
        # Store the keyboard state, which is characterised by 32 bytes, with
        # each bit representing the state of a single key.
        self.keyboardState = (ctypes.c_char * 32)()
        self.stateCapsLock = 0
        # Define special keys (byte, byte value).
        self.shiftKeys = ((6,4), (7,64))
        self.modifiers = {
            "left shift":  (6,   4),
            "right shift": (7,  64),
            "left ctrl":   (4,  32),
            "right ctrl":  (13,  2),
            "left alt":    (8,   1),
            "right alt":   (13, 16)
        }
        self.lastPressed = set()
        self.lastPressedAdjusted = set()
        self.stateLastModifier = {}
        # Define a dictionary of key byte numbers and key values.
        self.keyMapping = {
            1: {
                0b00000010: "<esc>",
                0b00000100: ("1", "!"),
                0b00001000: ("2", "@"),
                0b00010000: ("3", "#"),
                0b00100000: ("4", "$"),
                0b01000000: ("5", "%"),
                0b10000000: ("6", "^"),
            },
            2: {
                0b00000001: ("7", "&"),
                0b00000010: ("8", "*"),
                0b00000100: ("9", "("),
                0b00001000: ("0", ")"),
                0b00010000: ("-", "_"),
                0b00100000: ("=", "+"),
                0b01000000: "<backspace>",
                0b10000000: "<tab>",
            },
            3: {
                0b00000001: ("q", "Q"),
                0b00000010: ("w", "W"),
                0b00000100: ("e", "E"),
                0b00001000: ("r", "R"),
                0b00010000: ("t", "T"),
                0b00100000: ("y", "Y"),
                0b01000000: ("u", "U"),
                0b10000000: ("i", "I"),
            },
            4: {
                0b00000001: ("o", "O"),
                0b00000010: ("p", "P"),
                0b00000100: ("[", "{"),
                0b00001000: ("]", "}"),
                0b00010000: "<enter>",
                0b00100000: "<left ctrl>",
                0b01000000: ("a", "A"),
                0b10000000: ("s", "S"),
            },
            5: {
                0b00000001: ("d", "D"),
                0b00000010: ("f", "F"),
                0b00000100: ("g", "G"),
                0b00001000: ("h", "H"),
                0b00010000: ("j", "J"),
                0b00100000: ("k", "K"),
                0b01000000: ("l", "L"),
                0b10000000: (";", ":"),
            },
            6: {
                0b00000001: ("'", "\""),
                0b00000010: ("`", "~"),
                0b00000100: "<left shift>",
                0b00001000: ("\\", "|"),
                0b00010000: ("z", "Z"),
                0b00100000: ("x", "X"),
                0b01000000: ("c", "C"),
                0b10000000: ("v", "V"),
            },
            7: {
                0b00000001: ("b", "B"),
                0b00000010: ("n", "N"),
                0b00000100: ("m", "M"),
                0b00001000: (",", "<"),
                0b00010000: (".", ">"),
                0b00100000: ("/", "?"),
                0b01000000: "<right shift>",
            },
            8: {
                0b00000001: "<left alt>",
                0b00000010: "<space>",
                0b00000100: "<caps lock>",
            },
            9: {
                0b00000001: ("F6", "shift-F6"),
                0b00000010: ("F7", "shift-F7"),
                0b00000100: ("F8", "shift-F8"),
                0b00001000: ("F9", "shift-F9"),
            },
            13: {
                0b00000010: "<right ctrl>",
                0b00010000: "<right alt>",
                0b10000000: ("<up>", "shift-up")
            },
            14: {
                0b00000001: ("<pageup>", "shift-pageup"),
                0b00000010: ("<left>", "shift-left"),
                0b00000100: ("<right>", "shift-right"),
                0b00001000: ("<end>", "shift-end"),
                0b00010000: ("<down>", "shift-down"),
                0b00100000: ("<pagedown>", "shift-PgDn"),
                0b01000000: ("<insert>", "shift-insert")
            },
        }

    def accessKeys(self):
        # Access raw keypresses.
        # The function XQueryKeymap returns a bit vector for the logical state
        # of the keyboard for each bit set to 1 indicates that the corresponding
        # key is pressed down currently. The vector is represented by 32 bytes.
        self.X11.XQueryKeymap(self.displayX11, self.keyboardState)
        rawKeypresses = self.keyboardState
        # Check the states of key modifiers (Ctrl, Alt, Shift).
        stateModifier = {}
        for modifier, (i, byte) in self.modifiers.iteritems():
            stateModifier[modifier] = bool(ord(rawKeypresses[i]) & byte)
        # Detect Shift.
        shift = 0
        for i, byte in self.shiftKeys:
            if ord(rawKeypresses[i]) & byte:
                shift = 1
                break
        # Detect Caps Lock.
        if ord(rawKeypresses[8]) & 4:
            self.stateCapsLock = int(not self.stateCapsLock)
        # Aggregate pressed keys.
        pressedKeys = []
        for i, k in enumerate(rawKeypresses):
            o = ord(k)
            if o:
                sleep(0.1)
                logger.info("detected keystroke code: {i}, {o}".format(
                    i = i,
                    o = o
                ))
                for byte, key in self.keyMapping.get(i, {}).iteritems():
                    if byte & o:
                        if isinstance(key, tuple):
                            key = key[shift or self.stateCapsLock]
                        pressedKeys.append(key)
        tmp = pressedKeys
        pressedKeys = list(set(pressedKeys).difference(self.lastPressed))
        stateChanged = tmp != self.lastPressed and (pressedKeys or self.lastPressedAdjusted)
        self.lastPressed = tmp
        self.lastPressedAdjusted = pressedKeys
        if pressedKeys:
            pressedKeys = pressedKeys[0]
        else:
            pressedKeys = None
        stateChanged = self.stateLastModifier and (stateChanged or stateModifier != self.stateLastModifier)
        self.stateLastModifier = stateModifier
        return (stateChanged, stateModifier, pressedKeys)

    def logLoop(self):
        while True:
            sleep(0.005)
            changed, stateModifier, pressedKeys = self.accessKeys()
            if changed and pressedKeys is not None:
                logger.info("detected keystroke: {key}".format(
                    key = pressedKeys
                ))
                self.detectEvent(pressedKeys)

    def detectEvent(
        self,
        pressedKeys
    ):
        # If the pressed keys are specified as an event in the configuration,
        # execute the command corresponding to the event.
        if pressedKeys in program.configuration["event-execution-map"]:
            # log
            if "description" in program.configuration["event-execution-map"][pressedKeys]:
                logger.info("event detected: {description}".format(description = program.configuration["event-execution-map"][pressedKeys]["description"]))
            else:
                logger.info("event detected".format(
                    key = pressedKeys
                ))
            # execute command
            command = program.configuration["event-execution-map"][pressedKeys]["command"]
            self.executeCommand(command)

    def executeCommand(
        self,
        command
    ):
        os.system(command)

if __name__ == "__main__":
    options = docopt(__doc__)
    if options["--version"]:
        print(version)
        exit()
    main(options)
