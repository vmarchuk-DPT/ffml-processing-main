import features as feats
import geometry as geo

from ua_parser import user_agent_parser

import os
import pprint
import datetime
import csv

from dateutil.relativedelta import relativedelta

# import uszipcode

# Static var zip code search engine.
# search = uszipcode.ZipcodeSearchEngine()

#############################################################################
#
# 	A necessary utility for accessing the data local to the installation.
#
#############################################################################

_ROOT = os.path.abspath(os.path.dirname(__file__))


def get_data(path):
    return os.path.join(_ROOT, "data", path)


##############################################################################
#
# Result is a class to describe a single survey question
# preprocessed with the extracted features.
#
##############################################################################
class Result(object):
    def __init__(
        self,
        unique_id,
        participant,
        features,
        question_type,
        question_stimulus,
        response,
        qlabel,
    ):
        self.unique_id = unique_id
        self.participant: str = participant
        self.features = features
        self.norm_features = {}
        self.question_type = question_type
        self.question_stimulus = question_stimulus
        self.response = response
        self.qlabel = qlabel


##############################################################################
#
# Person is a class to hold sets of survey data for analysis.
#
# Paths are multiple Path instances that are linked by
# a feature (or features) of interest. In this case a uid.
#
##############################################################################
class Person(object):

    # Create a lookup table for the question ID
    # to the question short name and category.
    question_key = None

    @classmethod
    def qk(cls, qkey):

        if not cls.question_key:

            cls.question_key = qkey

        else:
            raise RuntimeError("Tried to change Person static 'question_key'")

    def __init__(self, identifier, qkey):

        self.id = identifier

        # Attributes from answers
        # Expected to include:
        # 	demographics
        # 	voting
        # 	president perception
        # 	outlook
        self.profile = {}

        # All of the paths for an individual.
        self.results = {}

        # Instantiate the class level question key
        # handler--so it is not held over and over
        # again by instances.
        if not Person.question_key:
            Person.qk(qkey)

    # Add a new enriched path to the paths object
    def add_result(self, result: Result):

        if result.participant != self.id:
            raise ValueError("Incorrect Participant ID, not merging.")

        self.results[result.qlabel] = result

        if result.qlabel in Person.question_key: # question_stimulus

            cat = Person.question_key[result.qlabel][1]
            var = Person.question_key[result.qlabel][0]

            if cat not in self.profile:
                self.profile[cat] = {}

            self.profile[cat][var] = {"answer": result.response}

    # Add the results from modelling to the profile
    # to allow filtering and analysis.
    def add_certainty(self, identifier, confidence):

        if identifier in self.question_key:

            cat = Person.question_key[identifier][1]
            var = Person.question_key[identifier][0]

            self.profile[cat][var]["certainty"] = confidence

    # Add an indicator for uncertainty relative to within-person benchmarks.
    def add_relative(self, benchmark, identifier):

        if identifier in self.question_key and benchmark:

            cat = Person.question_key[identifier][1]
            var = Person.question_key[identifier][0]

            if "certainty" in self.profile[cat][var]:

                rel = self.profile[cat][var]["certainty"] / benchmark

                self.profile[cat][var]["relative"] = rel

    def __str__(self):

        out = (
            "========PERSON========\n"
            + "Identifier: "
            + self.id
            + "\n\n"
            + pprint.pformat(self.profile)
        )

        return out

    def __repr__(self):

        return str(self)
