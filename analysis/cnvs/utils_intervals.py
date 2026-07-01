def get_intervals_from_overlap(cds_overlap_dict: dict) -> list:
    """Get a list of tuples that describe the intervals of coding sequence
    overlap with a given variant

    :param cds_overlap_dict: A dictionary of contating feature overlap
        information
    :return: a list of (start, stop) tuples for the intervals of coding
        sequence overlap with the given variant"""
    return [
        (
            v["overlap"]["start"],
            v["overlap"]["end"],
        )
        for feature_overlap in cds_overlap_dict["feature_overlap"].values()
        for v in feature_overlap
    ]

def canonicalize(intervals: list) -> list:
    """Process start/stop tuples for downstream analysis

    :param intervals: A list of start/stop tuples
    :return: A list of deduplicated, sorted, consolidated start/stop tuples"""
    intervals_deduplicated = sorted(set([(a, b) for a, b in intervals]))
    intervals_merged = []

    for a, b in intervals_deduplicated:
        if not intervals_merged:  # initialize; if no intervals yet, put one in
            intervals_merged.append([a, b])
        else:
            prev_a, prev_b = intervals_merged[-1]
            if (
                a <= prev_b
            ):  # if the current position lies in the previous rightmost interval, extend the previous interval
                intervals_merged[-1][-1] = b
            else:
                intervals_merged.append(
                    [a, b]
                )  # if the current position is outside the last interval, start a new interval

    return intervals_merged

def calculate_size_of_intervals(intervals: list) -> int:
    """Determine the size of the union of the intervals

    :param intervals: A list of start/stop tuples
    :return: The number of base pairs included in the union of those intervals
    """
    return sum(
        [
            b - a + 1
            for (a, b) in canonicalize(intervals)
            if (a is not None) and (b is not None)
        ]
    )


# the first function weaves the two interval ranges together so the start and stop positions can be read in numerical order,
# tracking which intervals begin and end overlap regions for each variant
def make_interlaced_endpoints(intervals1: list, intervals2: list) -> list:
    """Weave interval ranges together to allow for the intersection to be
    computed downstream

    :param intervals1: A list of start/stop tuples
    :param intervals2: A list of start/stop tuples
    :return: A list of position/is_stop/input_number tuples"""
    # auxiliary function for computing operations on lists of intervals
    if not isinstance(intervals1, list):
        intervals1 = []
    if not isinstance(intervals2, list):
        intervals2 = []
    intervals1_tag = [(interval[0], 0, 0) for interval in intervals1] + [
        (interval[-1], 1, 0) for interval in canonicalize(intervals1)
    ]
    intervals2_tag = [(interval[0], 0, 1) for interval in intervals2] + [
        (interval[-1], 1, 1) for interval in canonicalize(intervals2)
    ]
    return sorted(intervals1_tag + intervals2_tag)

# the second function calculates the intersection of the two
def calculate_intersection_of_overlap_intervals(
    intervals1: list, intervals2: list
) -> list:
    """Compute the intersection between the processed intervals

    :param intervals1: A list of interlaced start/stop tuples
    :param intervals2: A list of interlaced start/stop tuples
    :return: The intersection of both lists of intervals, which is also a
        list of intervals"""
    interlaced_endpoints = make_interlaced_endpoints(intervals1, intervals2)
    result_intervals = []
    state, prev_state = 0, 0
    state1, state2 = 0, 0
    a, b = None, None
    for pos, end, inp in interlaced_endpoints:
        if (
            inp == 0
        ):  # only change state1 if we're looking at an interval from intervals1
            state1 = (
                1 - end
            )  # activate state 1 if we're opening an interval, otherwise deactivate

        if (
            inp == 1
        ):  # only change state1 if we're looking at an interval from intervals2
            state2 = (
                1 - end
            )  # activate state 2 if we're opening an interval, otherwise deactivate

        prev_state = state
        state = (
            state1 * state2
        ) % 2  # does the current position belong to both intervals1 AND intervals2?

        if (
            state > prev_state
        ):  # if the state has increased, we've reached part of the intersection; this is an intersection interval start pos
            a = pos

        elif (
            state < prev_state
        ):  # if the state has decreased, we've left part of the intersection; this is an intersection interval stop pos
            b = pos
            result_intervals.append((a, b))

    return result_intervals

def calculate_cds_jaccard(var1_overlap: dict, var2_overlap: dict) -> float:
    """Calculate CDS Jaccard score for two variants

    :param var1_overlap: A CDS overlap dictionary
    :param var2_overlap: A CDS overlap dictionary
    :return: The CDS jaccard similarity score between the two variants"""
    var1_fo = var1_overlap.get("feature_overlap")
    var2_fo = var2_overlap.get("feature_overlap")
    if (var1_fo is None) or (
        var2_fo is None
    ):  # check: both vars have nonzero coding overlap
        return 0
    if (
        len(set(var1_fo) & set(var2_fo)) == 0
    ):  # check:vars overlap on coding regions in the same gene
        return 0
    intervals1 = get_intervals_from_overlap(var1_overlap)
    intervals2 = get_intervals_from_overlap(var2_overlap)

    intersection_size = calculate_size_of_intervals(
        calculate_intersection_of_overlap_intervals(intervals1, intervals2)
    )
    union_size = calculate_size_of_intervals(canonicalize(intervals1 + intervals2))
    return intersection_size / union_size

def calculate_cds_overlap_fraction(start: int, stop: int, overlap_dict: dict) -> float:
    """Calculate CDS overlap fraction

    :param start: The start position
    :param stop: The end position
    :param overlap_dict: A CDS overlap dictionary
    :return: A float describing the computed overlap fraction"""
    feature_overlap = overlap_dict.get("feature_overlap")
    if feature_overlap is None:
        return 0
    return calculate_size_of_intervals(get_intervals_from_overlap(overlap_dict)) / (
        stop - start + 1
    )