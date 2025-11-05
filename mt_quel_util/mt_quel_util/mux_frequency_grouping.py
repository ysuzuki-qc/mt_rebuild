from tunits.units import GHz
from mt_util.tunits_util import FrequencyType
import pydantic

@pydantic.validate_call
def _get_frequency_group_with_width(channel_to_frequency: dict[str, FrequencyType], width_max: FrequencyType) -> tuple[list[list[str]], FrequencyType]:
    sorted_channel_freq_pair = sorted(channel_to_frequency.items(),key= lambda x: x[1])
    grouping: list[list[str]] = [[sorted_channel_freq_pair[0][0]], ]
    width_largest = 0*GHz
    for channel, freq in sorted_channel_freq_pair:
        width = freq - channel_to_frequency[grouping[-1][0]]
        if width <= width_max:
            grouping[-1].append(channel)
            width_largest = max(width, width_largest)
        else:
            grouping.append([channel])
    return grouping, width_largest

@pydantic.validate_call
def get_frequency_group(channel_to_frequency: dict[str, FrequencyType], accuracy: FrequencyType, num_dac_channel: int) -> dict[str, int]:
    result: dict[str, int] = {}
    if len(channel_to_frequency) <= num_dac_channel:
        # one-to-one assignment
        for index, channel in enumerate(channel_to_frequency):
            result[channel] = index
    else:
        # find best grouping with bisec search
        width_bisec_min = 1e-9 * GHz
        width_bisec_max = max(channel_to_frequency.values()) - min(channel_to_frequency.values()) + 1e-9 *GHz
        while (width_bisec_max - width_bisec_min) > accuracy:
            width_bisec = (width_bisec_max + width_bisec_min)/2
            grouping, width_largest = _get_frequency_group_with_width(channel_to_frequency, width_bisec)
            if len(grouping) > num_dac_channel:
                width_bisec_min = width_bisec
            else:
                width_bisec_max = width_largest + 1e-9*GHz

        # create grouping
        grouping, _ = _get_frequency_group_with_width(channel_to_frequency, width_bisec_max)
        assert(len(grouping) <= num_dac_channel)
        for index, group in enumerate(grouping):
            for channel in group:
                result[channel] = index
    return result
