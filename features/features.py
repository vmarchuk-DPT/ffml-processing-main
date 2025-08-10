import math

import geometry as geo

##############################################################################
#
# Classes to extract and represent features of paths.
#
##############################################################################


class PathFeatures(object):

    # Run all of the extractors on the path
    # to return a feature set describing
    # the given path.
    def extract(self, path):

        features = {}

        if not path:
            return features

        features["diverge"] = self.divergence(path)
        features["hover"] = self.hover(path)
        features["speed"] = self.speed(path)
        features["shape"] = self.shape(path)

        return features

    # To what extent is the path to the final
    # decision not straight?
    def divergence(self, path):

        # Invariants

        # total time taken to answer
        total_time = path[-1][2]
        # Early actions are in the first third of overall time
        early = total_time / 3
        # late actions in the last third
        late = early * 2
        # The target quadrant.
        homeQuad = 1 if path[-1][0] > 0 else 4

        # Features to extract
        cumulativeDivergence = 0
        averageDivergence = 0
        totalDistance = 0
        pathCrossing = 0
        maxDivergence = 0

        otherQuadrant = False
        otherQuadEarly = False
        otherQuadLate = False
        quadTotalDistance = [0, 0, 0, 0]
        quadMaxDistance = 0
        quadMaxIndex = 0

        numBackAndForth = 0

        # Origin, assumed.
        a = geo.Point(0, 0)
        b = geo.Point(path[-1][0], path[-1][1])
        last = a

        segments = []
        quadrants = []  # 1,2,3,4 clockwise from top right.

        # Keep track of distance within a quadrant from
        # entry to exit (not multiple visits).
        quadDistance = 0

        for point in path:

            c = geo.Point(point[0], point[1])

            clock = point[2]

            divr = geo.pointToLine(a, b, c)
            dist = geo.pointToPoint(c, last)

            cumulativeDivergence += divr
            averageDivergence += divr
            totalDistance += dist

            if divr > maxDivergence:
                maxDivergence = divr

            # Do we intersect with any previous part of the path?
            # Exclude the last segment which is naturally touching
            # the start point of the current one.
            for seg in segments[:-1]:

                if geo.doIntersect(seg[0], seg[1], last, c):
                    pathCrossing += 1

            segments.append((last, c))

            # Check whether we have changed quadrant
            currentQuad = 1
            if c.x >= 0 and c.y < 0.5:
                currentQuad = 2
            elif c.x < 0 and c.y < 0.5:
                currentQuad = 3
            elif c.x < 0 and c.y >= 0.5:
                currentQuad = 4

            quadTotalDistance[currentQuad - 1] += dist

            if len(quadrants):

                if quadrants[-1] != currentQuad:
                    quadrants.append(currentQuad)

                    if homeQuad == 1 and currentQuad in [3, 4]:
                        otherQuadrant = True

                        if clock < early:
                            otherQuadEarly = True

                        if clock > late:
                            otherQuadLate = True

                    quadDistance = dist

                else:
                    quadDistance += dist

                if quadDistance > quadMaxDistance:
                    quadMaxDistance = quadDistance
                    quadMaxIndex = currentQuad

            else:
                quadrants.append(currentQuad)
                quadDistance = dist
                quadMaxDistance = dist
                quadMaxIndex = currentQuad

            last = c

        last = None

        for quad in quadrants:
            if not last:
                last = quad
                continue

            if (quad in [1, 2] and last in [3, 4]) or (
                last in [1, 2] and quad in [3, 4]
            ):

                numBackAndForth += 1

            last = quad

        return {
            "cumulativeDivergence": [cumulativeDivergence, "series"],
            "averageDivergence": [averageDivergence / len(path), "series"],
            "totalDistance": [totalDistance, "series"],
            "pathCrossing": [pathCrossing, "series"],
            "maxDivergence": [maxDivergence, "series"],
            "otherQuadrant": [otherQuadrant, "bool"],
            "otherQuadEarly": [otherQuadEarly, "bool"],
            "otherQuadLate": [otherQuadLate, "bool"],
            "quadTotalDistance1": [quadTotalDistance[0], "series"],
            "quadTotalDistance2": [quadTotalDistance[1], "series"],
            "quadTotalDistance3": [quadTotalDistance[2], "series"],
            "quadTotalDistance4": [quadTotalDistance[3], "series"],
            "quadMaxDistance": [quadMaxDistance, "series"],
            "quadMaxIndex": [quadMaxIndex, "class"],
            "numBackAndForth": [numBackAndForth, "series"],
        }

    # Did she hover over the stimulus?
    def hover(self, path):

        # Features to extract
        earlyHover = False
        lateHover = False
        numHover = 0
        stimulusHover = False
        targetHover = False  # The selected answer
        otherHover = False  # The other answer
        upperHover = False
        lowerHover = False
        otherQuadHover = False

        # We define a hover period to be more than
        # 1 second in a tight set of coordinates.
        hoverPeriod = 1000

        # We define a tight set of coordinates to
        # be within 0.05 radius in our 1x2 system.
        hoverSpace = 0.05

        # We define the distance from an object
        # that counts as association as 0.1.
        # We only choose the closest object.
        assocDist = 0.1

        # Early and late defined as first and
        # last thirds of total time.
        early = path[-1][2] / 3
        late = early * 2

        # The stimulus
        stimulus = geo.Point(0, 0)

        # The targets
        target = None
        other = None
        homeQuad = None
        if path[-1][0] > 0:
            target = geo.Point(1, 1)
            other = geo.Point(-1, 1)
            homeQuad = 1
        else:
            target = geo.Point(-1, 1)
            other = geo.Point(1, 1)
            homeQuad = 4

        startIndex = 0
        index = 0

        lastHover = None

        while startIndex < len(path) and index < len(path):
            if path[index][2] - path[startIndex][2] <= hoverPeriod:
                index += 1
                continue

            while path[index][2] - path[startIndex][2] > hoverPeriod:
                # index marks the end of a set of points
                # within the allowable time frame of a hover
                clusterCenter = None
                avg_x = 0
                avg_y = 0

                isHover = True

                for point in path[startIndex : index + 1]:
                    avg_x += point[0]
                    avg_y += point[1]

                avg_x = avg_x / (index - startIndex)
                avg_y = avg_y / (index - startIndex)

                clusterCenter = geo.Point(avg_x, avg_y)

                for point in path[startIndex : index + 1]:
                    current = geo.Point(point[0], point[1])
                    if geo.pointToPoint(current, clusterCenter) > hoverSpace:
                        isHover = False
                        startIndex += 1
                        break

                if isHover:
                    if lastHover:
                        if geo.pointToPoint(lastHover, clusterCenter) < assocDist:
                            startIndex += 1
                            continue

                    # We have a new hover event to analyze
                    numHover += 1

                    if (path[startIndex][2] + path[index][2]) / 2 < early:
                        earlyHover = True

                    if (path[startIndex][2] + path[index][2]) / 2 > late:
                        lateHover = True

                    if geo.pointToPoint(stimulus, clusterCenter) < assocDist:
                        stimulusHover = True

                    if geo.pointToPoint(target, clusterCenter) < assocDist:
                        targetHover = True

                    if geo.pointToPoint(other, clusterCenter) < assocDist:
                        otherHover = True

                    currentQuad = 1
                    if clusterCenter.x >= 0 and clusterCenter.y < 0.5:
                        currentQuad = 2
                    elif clusterCenter.x < 0 and clusterCenter.y < 0.5:
                        currentQuad = 3
                    elif clusterCenter.x < 0 and clusterCenter.y >= 0.5:
                        currentQuad = 4

                    if currentQuad in [1, 4]:
                        upperHover = True

                    if currentQuad in [2, 3]:
                        lowerHover = True

                    if upperHover and homeQuad != currentQuad:
                        otherQuadHover = True

                    # Housekeeping for next set
                    startIndex += 1
                    lastHover = clusterCenter

        return {
            "earlyHover": [earlyHover, "bool"],
            "lateHover": [lateHover, "bool"],
            "numHover": [numHover, "series"],
            "stimulusHover": [stimulusHover, "bool"],
            "targetHover": [targetHover, "bool"],
            "otherHover": [otherHover, "bool"],
            "upperHover": [upperHover, "bool"],
            "lowerHover": [lowerHover, "bool"],
            "otherQuadHover": [otherQuadHover, "bool"],
        }

    # How does the speed behave?
    def speed(self, path):

        # Features to extract
        earlySpeed = 0
        lateSpeed = 0
        averageSpeed = 0
        maxSpeed = 0
        variance = 0

        # We calculate speeds across path segments
        speeds = []

        lastTime = 0
        lastPoint = geo.Point(0, 0)

        for point in path:

            current = geo.Point(point[0], point[1])

            dist = geo.pointToPoint(lastPoint, current)
            time = point[2] - lastTime

            time = 1 if time == 0 else time

            speeds.append(((dist / time), lastTime + (point[2] - lastTime / 2)))

        # Early and late defined as first and
        # last thirds of total time.
        early = path[-1][2] / 3
        late = early * 2

        earlySpeeds = 0
        lateSpeeds = 0

        for speed in speeds:

            if speed[1] < early:
                earlySpeed += speed[0]
                earlySpeeds += 1

            if speed[1] > late:
                lateSpeed += speed[0]
                lateSpeeds += 1

            averageSpeed += speed[0]

            if speed[0] > maxSpeed:
                maxSpeed = speed[0]

        averageSpeed = averageSpeed / len(speeds)

        for speed in speeds:
            variance += pow(speed[0] - averageSpeed, 2)

        variance = variance / len(speeds)

        return {
            "earlySpeed": [earlySpeed / earlySpeeds, "series"],
            "lateSpeed": [lateSpeed / lateSpeeds, "series"],
            "averageSpeed": [averageSpeed, "series"],
            "maxSpeed": [maxSpeed, "series"],
            "variance": [variance, "series"],
        }

    # What shape was the path?
    def shape(self, path):

        # A grid with the origin at 21,3
        # and the targets at 3/39,21
        # This gives some space around to
        # represent path drift. Also, a natural
        # representation for 3x3 sliding windows.
        grid = [[0 for y in range(25)] for x in range(43)]

        lastPoint = None

        # Put the path into the grid
        for point in path:

            x = (
                int(point[0] * 18) + 21
                if abs(point[0] * 18) < 21
                else 42 if point[0] > 0 else 0
            )
            y = int(point[1] * 18) + 3 if point[1] * 18 < 21 else 24

            if y < 0:
                y = 0

            grid[x][y] = 1

            if lastPoint:
                diffx = x - lastPoint.x
                diffy = y - lastPoint.y

                if diffx < 2 and diffy < 2:
                    lastPoint = geo.Point(x, y)
                    continue

                # 1. Straight line up
                if diffx == 0:
                    for i in range(min(lastPoint.y, y) + 1, max(lastPoint.y, y)):
                        grid[x][i] = 1

                # 2. Straight line across
                elif diffy == 0:
                    for i in range(min(lastPoint.x, x) + 1, max(lastPoint.x, x)):
                        grid[i][y] = 1

                # 3. A slope
                else:
                    ratio = float(min(abs(diffx), abs(diffy))) / float(
                        max(abs(diffx), abs(diffy))
                    )

                    # There are 4 possibilities:
                    #   /: lastpoint x and y both lower than current
                    # 	/: current x and y both lower than lastpoint
                    # 	\: current x is higher than lastpoint, but y is lower
                    # 	\: lastpoint x is higher than current, but y is lower
                    #
                    # Why so much code?? Because we are sampling along the
                    # path between two points of interest, so must move
                    # along it by at most 1 unit at a time. This
                    # complicates the code by branching two cases for
                    # each of the slopes. This could be factored into
                    # 2 cases rather than 4, but 4 is easier to read.
                    if lastPoint.x < x and lastPoint.y < y:
                        if abs(diffx) > abs(diffy):
                            for a in range(0, abs(diffx)):
                                new_x = lastPoint.x + a
                                new_y = int(lastPoint.y + a * ratio)
                                grid[new_x][new_y] = 1
                        else:
                            for b in range(0, abs(diffy)):
                                new_y = lastPoint.y + b
                                new_x = int(lastPoint.x + b * ratio)
                                grid[new_x][new_y] = 1

                    elif x < lastPoint.x and y < lastPoint.y:
                        if abs(diffx) > abs(diffy):
                            for a in range(0, abs(diffx)):
                                new_x = x + a
                                new_y = int(y + a * ratio)
                                grid[new_x][new_y] = 1
                        else:
                            for b in range(0, abs(diffy)):
                                new_y = y + b
                                new_x = int(x + b * ratio)
                                grid[new_x][new_y] = 1

                    elif x > lastPoint.x and y < lastPoint.y:
                        if abs(diffx) > abs(diffy):
                            for a in range(0, abs(diffx)):
                                new_x = lastPoint.x + a
                                new_y = int(lastPoint.y - a * ratio)
                                grid[new_x][new_y] = 1
                        else:
                            for b in range(0, abs(diffy)):
                                new_y = lastPoint.y - b
                                new_x = int(lastPoint.x + b * ratio)
                                grid[new_x][new_y] = 1

                    elif lastPoint.x > x and lastPoint.y < y:
                        if abs(diffx) > abs(diffy):
                            for a in range(0, abs(diffx)):
                                new_x = lastPoint.x - a
                                new_y = int(lastPoint.y + a * ratio)
                                grid[new_x][new_y] = 1
                        else:
                            for b in range(0, abs(diffy)):
                                new_y = lastPoint.y + b
                                new_x = int(lastPoint.x - b * ratio)
                                grid[new_x][new_y] = 1

            lastPoint = geo.Point(x, y)

        # We may now extract 3x3 sliding windows
        # with a minimum of 3 lit squares.
        # We represent them as 111111111 for
        # row row row left to right, top to bottom.
        # 112121211 would be:
        #
        #   | * |   |   |
        #   |   | * |   |
        #   |   |   | * |
        #

        patterns = {}
        pattern = 0
        marked = 0

        for y in range(23):
            for x in range(41):
                for b in range(y, y + 3):
                    for a in range(x, x + 3):
                        pattern = (pattern + grid[a][b] + 1) * 10
                        marked += grid[a][b]
                if marked >= 3:
                    pattern = pattern / 10
                    if pattern not in patterns:
                        patterns[pattern] = [1, "class"]
                    else:
                        patterns[pattern][0] += 1
                pattern = 0
                marked = 0

        return patterns
