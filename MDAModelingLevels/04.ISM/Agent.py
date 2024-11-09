#!/usr/bin/python
# -*- coding: UTF-8 -*-
import ContextBroker
from typing import List

class Agent(object):
	def __init__(self):
		self._northbound_traffic : ContextBroker = None

