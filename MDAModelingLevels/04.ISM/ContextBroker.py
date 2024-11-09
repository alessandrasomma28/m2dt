#!/usr/bin/python
# -*- coding: UTF-8 -*-
import SubscriptionManager
import Agent
from typing import List

class ContextBroker(object):
	def __init__(self):
		self._subscriptions : SubscriptionManager = None
		self._southbound_traffic : Agent = None

