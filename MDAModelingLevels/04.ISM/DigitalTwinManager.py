#!/usr/bin/python
# -*- coding: UTF-8 -*-
import FeedbackTrafficLight
import SumoSimulator
import DigitalShadowManager
from typing import List

class DigitalTwinManager(object):
	def __init__(self):
		self._unnamed_FeedbackTrafficLight_ : FeedbackTrafficLight = None
		self._unnamed_SumoSimulator_ : SumoSimulator = None
		"""# @AssociationMultiplicity 1
		# @AssociationKind Aggregation"""
		self._unnamed_DigitalShadowManager_ : DigitalShadowManager = None
		"""# @AssociationMultiplicity 1
		# @AssociationKind Aggregation"""

