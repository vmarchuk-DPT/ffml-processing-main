import math

############################################################################
#
# The FeatureStats class maintains a mapping of features
# to a set of statistics that can be used to relaivize
# the attributes of a particular person with respect to
# a reference group of interest.
#
############################################################################


class FeatureStats(object):

    # Maintain mappings to be able to calculate
    # average, median, range, std dev, variance
    # for each variable, where applicable.
    def __init__(self):

        # 'label' -> {type:'a',		  // 'bool','series','class'
        # 			  'trueCount':n,  // For boolean variable type
        # 			  'falseCount':k, // "
        # 			  '
        self.features = {}

        # Is the stats object valid for normalization?
        self.ready = False

    # Update the feature stats based on a new
    # observation instance.
    def add_result(self, result):

        # Adding a result invalidates certain aggregate stats
        self.ready = False
        try:

            for t in result.features:

                for f in result.features[t]:
                    if f =='first_movement_delay':
                        continue

                    if result.features[t][f][1] == "bool":
                        self.type_bool(f, result.features[t][f][0])
                    elif result.features[t][f][1] == "series":
                        self.type_series(f, result.features[t][f][0])
                    elif result.features[t][f][1] == "class":
                        self.type_class(f, result.features[t][f][0])

        except TypeError as err:
            print(err)

    # Populate the normalized features
    # for a particular path.
    def normalize(self, result):

        # Ensure the stats object is valid.
        if self.ready == False:
            self.prepare_stats()
            self.ready = True

        for t in result.features:

            # Update result.norm_features with the
            # set of normalized distributional
            # features.
            for f in result.features[t]:
                if f == 'first_movement_delay':
                    continue

                result.norm_features.update(
                    self.retrieve_features(f, result.features[t][f][0])
                )

    ###############################################
    # The following functions manage the building
    # of the 'features' map in the stats object.
    ###############################################

    # Calculate specific bool info
    def type_bool(self, label, value):

        if label not in self.features:

            self.features[label] = {"type": "bool", True: 0, False: 0}

        self.features[label][value] += 1

    # Calculate specific count info
    def type_series(self, label, value):

        if label not in self.features:

            self.features[label] = {
                "type": "series",
                "values": [],
                "avg": 0,
                "sdv": 0,
                "var": 0,
                "vsd": 0,
            }

        self.features[label]["values"].append(value)

    # Calculate specific class info
    def type_class(self, label, value):

        if label not in self.features:

            self.features[label] = {"type": "class", "classes": set()}

        if value not in self.features[label]:

            self.features[label][value] = 0
            self.features[label]["classes"].add(value)

        self.features[label][value] += 1

    # Calculate all aggregate stats in order to
    # use the stats object to normalize paths.
    def prepare_stats(self):

        for l in self.features:

            if self.features[l]["type"] == "series":

                avg = sum(self.features[l]["values"]) / len(self.features[l]["values"])

                # Standard deviation of values
                sdv = 0

                # Variance of values
                var = 0

                # List of deviations from mean
                var_list = []

                # Standard deviation of deviations from mean
                vsd = 0

                for i in self.features[l]["values"]:

                    var_list.append((avg - i) * (avg - i))
                    var += (avg - i) * (avg - i)

                if len(self.features[l]["values"]) == 1:
                    print('опа, бля')
                    continue

                var = var / (len(self.features[l]["values"]) - 1) ######!!@!!!!!
                sdv = math.sqrt(var)

                var_avg = sum(var_list) / len(var_list)

                for i in var_list:
                    vsd += (var_avg - i) * (var_avg - i)

                vsd = math.sqrt(vsd / (len(var_list) - 1))

                self.features[l]["avg"] = avg
                self.features[l]["var"] = var
                self.features[l]["sdv"] = sdv
                self.features[l]["vsd"] = vsd

    ###############################################
    # Convert raw features into normalized
    # relative features.
    ###############################################

    def retrieve_features(self, label, value):

        if self.features[label]["type"] == "bool":

            return self.get_bool(label, value)

        elif self.features[label]["type"] == "series":

            return self.get_series(label, value)

        elif self.features[label]["type"] == "class":

            return self.get_class(label, value)

    def get_bool(self, label, value):

        features = {}

        features[label] = value  # Binary true/false
        features[label + "_predominant"] = (
            True
            if self.features[label][value] > self.features[label][not value]
            else False
        )

        return features

    def get_series(self, label, value):

        features = {}

        avg = self.features[label]["avg"]
        sdv = self.features[label]["sdv"]
        var = self.features[label]["var"]
        vsd = self.features[label]["vsd"]

        features[label + "_above_avg"] = True if value > avg else False
        features[label + "_above_1sd"] = True if value > avg + sdv else False
        features[label + "_above_2sd"] = True if value > avg + 2 * sdv else False
        features[label + "_below_1sd"] = True if value < avg - sdv else False
        features[label + "_below_2sd"] = True if value < avg - 2 * sdv else False
        features[label + "_above_var"] = True if value > var else False
        features[label + "_above_var_1sd"] = True if value > var + vsd else False
        features[label + "_above_var_2sd"] = True if value > var + 2 * vsd else False
        features[label + "_below_var_1sd"] = True if value < var - vsd else False
        features[label + "_below_var_2sd"] = True if value < var - 2 * vsd else False

        return features

    def get_class(self, label, value):

        features = {}

        maxi = 0

        for c in self.features[label]["classes"]:

            features[str(label)] = True if c == value else False

            if self.features[label][c] > maxi:
                maxi = self.features[label][c]

        if self.features[label][value] == maxi:
            features[str(label) + "_predominant"] = True
        else:
            features[str(label) + "_predominant"] = False

        return features
