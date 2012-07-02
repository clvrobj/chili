#!/usr/bin/env python2
# -*- encoding:utf-8 -*-

from flask import Flask
from flaskext.actions import Manager
from chili import app

manager = Manager(app, default_server_actions=True)

if __name__ == "__main__":
    manager.run()

