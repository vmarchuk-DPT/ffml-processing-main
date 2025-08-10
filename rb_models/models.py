# A class to classify paths by behavioural features
# in a rule based manner.
class Model(object):

    def certainty(self, result):

        if not result.norm_features:
            raise ValueError("Path features must be normalized.")

        confidence = 0.0

        # Certainty is proxied by less hovering, faster
        # trajectories, straighter trajectories, fewer
        # switches of focus--relative to the peer group.
        truths = [
            "averageDivergence_below_1sd",
            "averageSpeed_above_avg",
            "averageSpeed_above_1sd",
            "cumulativeDivergence_below_1sd",
            "lateSpeed_above_avg",
            "lateSpeed_above_1sd",
            "maxDivergence_below_1sd",
            "numBackAndForth_below_1sd",
            "pathCrossing_below_1sd",
            "quadMaxDistance_below_1sd",
            "quadTotalDistance1_below_1sd",
            "quadTotalDistance2_below_1sd",
            "quadTotalDistance3_below_1sd",
            "quadTotalDistance4_below_1sd",
            "totalDistance_below_1sd",
            "variance_below_1sd",
        ]

        falses = [
            "averageDivergence_above_avg",
            "cumulativeDivergence_above_avg",
            "maxDivergence_above_avg",
            "numBackAndForth_above_avg",
            "numHover_above_avg",
            "otherHover",
            "upperHover",
            "otherQuadLate",
            "pathCrossing_above_avg",
            "quadMaxDistance_above_avg",
            "quadTotalDistance1_above_avg",
            "quadTotalDistance2_above_avg",
            "quadTotalDistance3_above_avg",
            "quadTotalDistance4_above_avg",
            "targetHover",
            "totalDistance_above_avg",
            "variance_above_avg",
        ]

        certain = 0

        for i in truths:
            if result.norm_features.get(i):
                certain += 1

        for i in falses:
            if not result.norm_features.get(i):
                certain += 1

        # Now calculate the other side: uncertainty.
        truths = [
            "averageDivergence_above_1sd",
            "averageSpeed_below_1sd",
            "cumulativeDivergence_above_1sd",
            "lateSpeed_below_1sd",
            "maxDivergence_above_1sd",
            "numBackAndForth_above_1sd",
            "pathCrossing_above_1sd",
            "quadMaxDistance_above_1sd",
            "quadTotalDistance1_above_1sd",
            "quadTotalDistance2_above_1sd",
            "quadTotalDistance3_above_1sd",
            "quadTotalDistance4_above_1sd",
            "totalDistance_above_1sd",
            "variance_above_1sd",
            "averageDivergence_above_avg",
            "cumulativeDivergence_above_avg",
            "maxDivergence_above_avg",
            "numBackAndForth_above_avg",
            "numHover_above_avg",
            "otherHover",
            "upperHover",
            "otherQuadLate",
            "pathCrossing_above_avg",
            "quadMaxDistance_above_avg",
            "quadTotalDistance1_above_avg",
            "quadTotalDistance2_above_avg",
            "quadTotalDistance3_above_avg",
            "quadTotalDistance4_above_avg",
            "targetHover",
            "totalDistance_above_avg",
            "variance_above_avg",
        ]

        falses = ["averageSpeed_above_avg", "lateSpeed_above_avg"]

        uncertain = 0

        for i in truths:

            if result.norm_features.get(i):
                uncertain += 1

        for i in falses:

            if not result.norm_features.get(i):
                uncertain += 1

        return certain - uncertain

        # All code below is never called.
        '''
        if certain > uncertain:

            if certain - uncertain > 10:
                # High confidence
                confidence = 1.0

            elif certain - uncertain > 6:
                # Medium
                confidence = 0.8

            elif certain - uncertain > 3:
                # Low
                confidence = 0.6

        else:

            if uncertain - certain > 10:
                # High confidence
                confidence = 0.0

            elif uncertain - certain > 6:
                # Medium
                confidence = 0.2

            elif uncertain - certain > 3:
                # Low
                confidence = 0.4

        return confidence '''

    def veracity(self, result):

        if not result.norm_features:

            raise ValueError("Path features must be normalized.")

        confidence = 0.0

        return confidence

    def facility(self, result):

        if not result.norm_features:

            raise ValueError("Path features must be normalized.")

        confidence = 0.0

        return confidence
