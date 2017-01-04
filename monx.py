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
# copyright (C) 2014 2015 William Breaden Madden                               #
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
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for     #
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
    -h, --help                display help message
    --version                 display version and exit
    -v, --verbose             verbose logging
    -u, --username=USERNAME   username
    -c, --configuration=CONF  configuration (file) [default: ~/.ucom]
"""

name    = "monx"
version = "2017-01-04T1318Z"

import os
import sys
import time
import ctypes
import ctypes.util
import docopt
import logging

import technicolor
import shijian
import pyprel

def main(options):

    global program
    program = Program(options = options)

    keyboard = Keyboard()
    keyboard.log_loop()

class Keyboard:

    def __init__(
        self,
        parent = None
        ):
        # X11 interface
        self.X11 = ctypes.cdll.LoadLibrary(ctypes.util.find_library("X11"))
        self.displayX11 = self.X11.XOpenDisplay(None)
        # keyboard
        # Store the keyboard state, which is characterised by 32 bytes, with
        # each bit representing the state of a single key.
        self.keyboardState = (ctypes.c_char * 32)()
        self.stateCapsLock = 0
        # Define special keys (byte, byte value).
        self.shiftKeys = ((6, 4), (7, 64))
        self.modifiers = {
            "left shift":  (6,   4),
            "right shift": (7,  64),
            "left ctrl":   (4,  32),
            "right ctrl":  (13,  2),
            "left alt":    (8,   1),
            "right alt":   (13, 16)
        }
        self.lastPressed         = set()
        self.lastPressedAdjusted = set()
        self.stateLastModifier   = {}
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
                0b00000001: ("<pageup>",   "shift-pageup"),
                0b00000010: ("<left>",     "shift-left"),
                0b00000100: ("<right>",    "shift-right"),
                0b00001000: ("<end>",      "shift-end"),
                0b00010000: ("<down>",     "shift-down"),
                0b00100000: ("<pagedown>", "shift-PgDn"),
                0b01000000: ("<insert>",   "shift-insert")
            },
        }

    def access_keys(self):
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
                time.sleep(0.1)
                log.info("\ndetected keystroke code: {i}, {o}".format(
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
        # stateChanged: Boolean
        # stateModifier: dictionary of status of available modifiers, e.g.:
        # {
        #     'left shift':  True,
        #     'right alt':   False,
        #     'right shift': False,
        #     'left alt':    False,
        #     'left ctrl':   False,
        #     'right ctrl':  False
        # }
        # pressedKeys: string of key detected, e.g. e.
        return (stateChanged, stateModifier, pressedKeys)

    def log_loop(self):
        while True:
            time.sleep(0.005)
            stateChanged, stateModifier, pressedKeys = self.access_keys()
            if stateChanged and pressedKeys is not None:
                log.info("detected keystroke: {key}".format(
                    key = pressedKeys
                ))
                self.detect_event(pressedKeys)

    def detect_event(
        self,
        pressedKeys
        ):
        # If the pressed keys are specified as an event in the configuration,
        # execute the command corresponding to the event.
        if pressedKeys in program.configuration["event-execution-map"]:
            # log
            if "description" in program.configuration["event-execution-map"][pressedKeys]:
                log.info("event detected: {description}".format(description = program.configuration["event-execution-map"][pressedKeys]["description"]))
            else:
                log.info("event detected".format(
                    key = pressedKeys
                ))
            # execute command
            command = program.configuration["event-execution-map"][pressedKeys]["command"]
            self.execute_command(command)

    def execute_command(
        self,
        command
        ):
        os.system(command)

class Program(object):

    def __init__(
        self,
        parent  = None,
        options = None
        ):

        # internal options
        self.displayLogo           = True

        # clock
        global clock
        clock = shijian.Clock(name = "program run time")

        # name, version, logo
        if "name" in globals():
            self.name              = name
        else:
            self.name              = None
        if "version" in globals():
            self.version           = version
        else:
            self.version           = None
        if "logo" in globals():
            self.logo              = logo
        elif "logo" not in globals() and hasattr(self, "name"):
            self.logo              = pyprel.renderBanner(
                                         text = self.name.upper()
                                     )
        else:
            self.displayLogo       = False
            self.logo              = None

        # options
        self.options               = options
        self.userName              = self.options["--username"]
        self.verbose               = self.options["--verbose"]

        # default values
        if self.userName is None:
            self.userName = os.getenv("USER")

        # configuration
        configurationFileName      = self.options["--configuration"]
        self.configuration = shijian.open_configuration(
            filename = configurationFileName
        )

        # logging
        global log
        log = logging.getLogger(__name__)
        logging.root.addHandler(technicolor.ColorisingStreamHandler())

        # logging level
        if self.verbose:
            logging.root.setLevel(logging.DEBUG)
        else:
            logging.root.setLevel(logging.INFO)

        self.engage()

    def engage(
        self
        ):
        pyprel.printLine()
        # logo
        if self.displayLogo:
            log.info(pyprel.centerString(text = self.logo))
            pyprel.printLine()
        # engage alert
        if self.name:
            log.info("initiate {name}".format(
                name = self.name
            ))
        # version
        if self.version:
            log.info("version: {version}".format(
                version = self.version
            ))
        log.info("initiation time: {time}".format(
            time = clock.startTime()
        ))

    def terminate(
        self
        ):
        clock.stop()
        log.info("termination time: {time}".format(
            time = clock.stopTime()
        ))
        log.info("time statistics report:\n{report}".format(
            report = shijian.clocks.report()
        ))
        log.info("terminate {name}".format(
            name = self.name
        ))
        pyprel.printLine()
        sys.exit()

if __name__ == "__main__":
    options = docopt.docopt(__doc__)
    if options["--version"]:
        print(version)
        exit()
    main(options)
