#!/usr/bin/python
# -*- coding: UTF-8 -*-
import ContextBroker
from typing import List

class SubscriptionManager(object):
	def __init__(self):
		self._unnamed_ContextBroker_ : ContextBroker = None

