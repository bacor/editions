# -*- coding: utf-8 -*-
# -------------------------------------------------------------------
# Author: Bas Cornelissen
# Copyright © 2024 Bas Cornelissen
# -------------------------------------------------------------------
import unittest

# Local imports
from collection import Collection


class TestManager(unittest.TestCase):

    def test_init(self):
        collection = Collection("albert_h")
        print(collection.works)
        collection.export()
        print("asdfadf")
