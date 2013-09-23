#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2013 Tristan Fischer (sphere@dersphere.de)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import random
import json

import xbmc
import xbmcaddon
import xbmcgui

addon = xbmcaddon.Addon()
ADDON_NAME = addon.getAddonInfo('name')
ADDON_PATH = addon.getAddonInfo('path')


class BaseScreensaver(xbmcgui.WindowDialog):

    IMAGE_CONTROL_COUNT = 10
    FAST_IMAGE_COUNT = 0
    NEXT_IMAGE_TIME = 2000
    BACKGROUND_IMAGE = 'table.jpg'

    class ExitMonitor(xbmc.Monitor):

        def __init__(self, exit_callback):
            self.exit_callback = exit_callback

        def onScreensaverDeactivated(self):
            self.exit_callback()

    def __init__(self):
        self.log('__init__')
        self.exit_requested = False
        self.background_control = None
        self.preload_control = None
        self.image_controls = []
        self.exit_monitor = self.ExitMonitor(self._exit)
        super(BaseScreensaver, self).show()
        self._init_controls()

    def start(self):
        image_pool = self.get_images()
        image_url = random.choice(image_pool)
        image_controls_cycle = cycle(self.image_controls)
        image_count = 0
        while not self.exit_requested:
            image_control = image_controls_cycle.next()
            self.process_image(image_control, image_url)
            image_url = random.choice(image_pool)
            self._preload_image(image_url)
            if image_count < self.FAST_IMAGE_COUNT:
                image_count += 1
            else:
                self._wait()

    def get_images(self):
        query = {
            'jsonrpc': '2.0',
            'id': 0,
            'method': 'VideoLibrary.GetMovies',
            'params': {
                'properties': ['fanart']
            }
        }
        response = json.loads(xbmc.executeJSONRPC(json.dumps(query)))
        images = [
            movie['fanart'] for movie
            in response.get('result', {}).get('movies', [])
        ]
        self.image_aspect_ratio = 16.0 / 9.0
        return images

    def process_image(self, image_control, image_url):
        # Needs to be implemented in child class
        raise NotImplementedError

    def stack_controls(self):
        # add controls to the window in same order as image_controls list
        # so any next image will be in front of all previous
        self.addControls(self.image_controls)

    def _preload_image(self, image_url):
        # set the next image to an unvisible image-control for caching
        self.preload_control.setImage(image_url)

    def _wait(self):
        # wait in chunks of 500ms to react earlier on exit request
        for i in xrange(self.NEXT_IMAGE_TIME / 500):
            if self.exit_requested:
                self.log('_wait aborted')
                return
            xbmc.sleep(500)

    def _init_controls(self):
        self.log('_init_controls start')
        bg_img = xbmc.translatePath('/'.join((
            ADDON_PATH, 'resources', 'media', self.BACKGROUND_IMAGE
        )))
        self.background_control = xbmcgui.ControlImage(0, 0, 1280, 720, bg_img)
        self.addControl(self.background_control)
        # Place preload control at invisible location
        self.preload_control = xbmcgui.ControlImage(-1, -1, 1, 1, '')
        self.addControl(self.preload_control)
        for i in xrange(self.IMAGE_CONTROL_COUNT):
            img_control = xbmcgui.ControlImage(0, 0, 0, 0, '')
            self.image_controls.append(img_control)
        self.stack_controls()
        self.log('_init_controls end')

    def _del_controls(self):
        self.log('_del_controls start')
        self.removeControls(self.image_controls + [self.preload_control])
        del self.preload_control
        while self.image_controls:
            img = self.image_controls.pop()
            del img
        self.log('_del_controls end')

    def _exit(self):
        self.log('_exit')
        self.exit_requested = True
        self.exit_monitor = None

    def log(self, msg):
        xbmc.log(u'%s: %s' % (ADDON_NAME, msg))

    def __del__(self):
        self._del_controls()


class TableDropScreenSaver(BaseScreensaver):

    IMAGE_CONTROL_COUNT = 20
    FAST_IMAGE_COUNT = 3
    NEXT_IMAGE_TIME = 1500
    MIN_WIDTH = 500
    MAX_WIDTH = 700

    def process_image(self, image_control, image_url):
        ROTATE_ANIMATION = (
            'effect=rotate start=0 end=%d center=auto time=%d '
            'delay=0 tween=circle condition=true'
        )
        DROP_ANIMATION = (
            'effect=zoom start=%d end=100 center=auto time=%d '
            'delay=0 tween=circle condition=true'
        )
        FADE_ANIMATION = (
            'effect=fade start=0 end=100 time=200 '
            'condition=true'
        )
        # hide the image
        image_control.setVisible(False)
        # re-stack it (to be on top)
        self.removeControl(image_control)
        self.addControl(image_control)
        # calculate all parameters and properties
        width = random.randint(self.MIN_WIDTH, self.MAX_WIDTH)
        height = int(width / self.image_aspect_ratio)
        x_position = random.randint(0, 1280 - width)
        y_position = random.randint(0, 720 - height)
        drop_height = random.randint(360, 600)
        drop_duration = random.randint(500, 1000)
        rotation_degrees = random.uniform(-20, 20)
        rotation_duration = drop_duration
        animations = [
            ('conditional', FADE_ANIMATION),
            ('conditional',
             ROTATE_ANIMATION % (rotation_degrees, rotation_duration)),
            ('conditional',
             DROP_ANIMATION % (drop_height, drop_duration)),
        ]
        # set all parameters and properties
        image_control.setImage(image_url)
        image_control.setPosition(x_position, y_position)
        image_control.setWidth(width)
        image_control.setHeight(height)
        image_control.setAnimations(animations)
        # show the image
        image_control.setVisible(True)


class StarWarsScreenSaver(BaseScreensaver):

    IMAGE_CONTROL_COUNT = 6
    NEXT_IMAGE_TIME = 2800

    def process_image(self, image_control, image_url):
        TILT_ANIMATION = (
            'effect=rotatex start=0 end=50 center=auto time=0 '
            'condition=true'
        )
        MOVE_ANIMATION = (
            'effect=slide start=0,1100 end=0,-1100 time=10400 '
            'tween=linear condition=true center=auto'
        )
        # hide the image
        image_control.setVisible(False)
        # re-stack it (to be on top)
        self.removeControl(image_control)
        self.addControl(image_control)
        # calculate all parameters and properties
        width = 1280
        height = 720
        x_position = 0
        y_position = 510
        animations = [
            ('conditional', TILT_ANIMATION),
            ('conditional', MOVE_ANIMATION),
        ]
        # set all parameters and properties
        image_control.setImage(image_url)
        image_control.setPosition(x_position, y_position)
        image_control.setWidth(width)
        image_control.setHeight(height)
        image_control.setAnimations(animations)
        # show the image
        image_control.setVisible(True)


class RandomZoomInScreenSaver(BaseScreensaver):

    IMAGE_CONTROL_COUNT = 7
    NEXT_IMAGE_TIME = 2000

    def process_image(self, image_control, image_url):
        ZOOM_ANIMATION = (
            'effect=zoom start=1 end=100 center=%d,%d time=5000 '
            'tween=quadratic condition=true'
        )
        # hide the image
        image_control.setVisible(False)
        # re-stack it (to be on top)
        self.removeControl(image_control)
        self.addControl(image_control)
        # calculate all parameters and properties
        width = 1280
        height = 720
        x_position = 0
        y_position = 0
        zoom_x = random.randint(0, 1280)
        zoom_y = random.randint(0, 720)
        animations = [
            ('conditional', ZOOM_ANIMATION % (zoom_x, zoom_y)),
        ]
        # set all parameters and properties
        image_control.setImage(image_url)
        image_control.setPosition(x_position, y_position)
        image_control.setWidth(width)
        image_control.setHeight(height)
        image_control.setAnimations(animations)
        # show the image
        image_control.setVisible(True)


class AppleTVLikeScreenSaver(BaseScreensaver):

    BACKGROUND_IMAGE = 'black.jpg'
    IMAGE_CONTROL_COUNT = 35
    FAST_IMAGE_COUNT = 3
    NEXT_IMAGE_TIME = 3500

    def stack_controls(self):
        # randomly generate a zoom in percent as betavariant
        # between 10 and 70 and assign calculated width to control.
        # Remove all controls from window and re-add sorted by size.
        # This is needed because the bigger (=nearer) ones need to be in front
        # of the smaller ones.
        # Then shuffle image list again to have random size order.
        for image_control in self.image_controls:
            zoom = int(random.betavariate(2, 2) * 60) + 10
            #zoom = int(random.randint(10, 70))
            width = 1280 / 100 * zoom
            image_control.setWidth(width)
        self.image_controls = sorted(
            self.image_controls, key=lambda c: c.getWidth()
        )
        self.addControls(self.image_controls)
        random.shuffle(self.image_controls)

    def process_image(self, image_control, image_url):
        MOVE_ANIMATION = (
            'effect=slide start=0,720 end=0,-720 center=auto time=%s '
            'tween=linear delay=0 condition=true'
        )
        image_control.setVisible(False)
        # calculate all parameters and properties based on the already set
        # width. We can not change the size again because all controls need
        # to be added to the window in size order.
        width = image_control.getWidth()
        zoom = width * 100 / 1280
        height = int(width / self.image_aspect_ratio)
        # let images overlap max 1/4 left or right
        x_position = random.randint(0 - width / 4, 1080 - width + width / 4)
        y_position = 0

        time = 15000 / zoom * 100

        animations = [
            ('conditional', MOVE_ANIMATION % time),
        ]
        # set all parameters and properties
        image_control.setImage(image_url)
        image_control.setPosition(x_position, y_position)
        image_control.setWidth(width)
        image_control.setHeight(height)
        image_control.setAnimations(animations)
        # show the image
        image_control.setVisible(True)


class GridSwitchScreenSaver(BaseScreensaver):

    BACKGROUND_IMAGE = ''

    ROWS_AND_COLUMNS = 4
    NEXT_IMAGE_TIME = 1000

    IMAGE_CONTROL_COUNT = ROWS_AND_COLUMNS ** 2
    FAST_IMAGE_COUNT = IMAGE_CONTROL_COUNT

    def stack_controls(self):
        # Set position and dimensions based on position.
        # Shuffle image list to have random order.
        super(GridSwitchScreenSaver, self).stack_controls()
        for i, image_control in enumerate(self.image_controls):
            current_row, current_col = divmod(i, self.ROWS_AND_COLUMNS)
            width = 1280 / self.ROWS_AND_COLUMNS
            height = 720 / self.ROWS_AND_COLUMNS
            x_position = width * current_col
            y_position = height * current_row
            image_control.setPosition(x_position, y_position)
            image_control.setWidth(width)
            image_control.setHeight(height)
        random.shuffle(self.image_controls)

    def process_image(self, image_control, image_url):
        image_control.setImage(image_url)
        ROTATE_ANIMATION = (
            'effect=fade start=0 end=100 center=auto time=1000 condition=true'
        )
        animations = [
            ('conditional', ROTATE_ANIMATION),
        ]
        image_control.setAnimations(animations)


def cycle(iterable):
    saved = []
    for element in iterable:
        yield element
        saved.append(element)
    while saved:
        for element in saved:
            yield element

if __name__ == '__main__':
    classes = (
        TableDropScreenSaver,
        StarWarsScreenSaver,
        RandomZoomInScreenSaver,
        AppleTVLikeScreenSaver,
        GridSwitchScreenSaver,
    )
    chosen_screensaver = int(addon.getSetting('mode'))
    cls = classes[chosen_screensaver]
    screensaver = cls()
    screensaver.start()
    del screensaver
    sys.modules.clear()
