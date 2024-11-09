#!/usr/bin/python
# -*- coding: UTF-8 -*-
import DataModelManager
import DatabaseManager
from typing import List

class DataManager(object):
	def __init__(self):
		self._unnamed_DataModelManager_ : DataModelManager = None
		"""# @AssociationKind Aggregation"""
		self._unnamed_DatabaseManager_ : DatabaseManager = None
		"""# @AssociationKind Aggregation"""

