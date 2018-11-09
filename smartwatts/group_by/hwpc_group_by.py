"""
HWPC group by rules utilities

"""

from enum import IntEnum
from smartwatts.group_by import AbstractGroupBy


class HWPCDepthLevel(IntEnum):
    """Enumeration that specify which report level use to group by the reports
    """

    ROOT = 3
    SOCKET = 2
    CORE = 1


class HWPCGroupBy(AbstractGroupBy):
    """
    Group by rule for HWPC report

    Attributes:
        extract(fun Report -> [(tuple, Report)])
    """
    def __init__(self, depth, primary=False):
        """
        Parameters:
            depth:(HWPCDepthLevel)
        """
        AbstractGroupBy.__init__(self, primary)
        self.depth = depth
        self.fields = ['sensor', 'socket', 'core'][:(4 - depth)]

    def extract(self, report):
        return _extract(report, self.depth)


def _extract(report, depth):
    def extract_aux(report, current_depth):
        if current_depth == depth:
            return [((report.hw_id,), report)]

        extracted_reports = []
        for packed_report in report.get_child_reports():

            extracted_reports += extract_aux(packed_report,
                                             current_depth - 1)

        final_reports = []
        if current_depth == HWPCDepthLevel.ROOT:
            # merge group
            final_reports = {}
            for (report_id, socket_report) in extracted_reports:
                if report_id not in final_reports:
                    final_reports[report_id] = report.cut_child()
                key = socket_report.hw_id
                final_reports[report_id].set_child_report(key,
                                                          socket_report)

            result = []
            for (final_report_id, final_report) in final_reports.items():
                result.append(((final_report.sensor,) + final_report_id,
                               final_report))
            return result

        for (report_id, extracted_report) in extracted_reports:
            final_report = report.cut_child()
            final_report.set_child_report(extracted_report.hw_id,
                                          extracted_report)
            final_reports.append(
                ((final_report.hw_id,) + report_id, final_report)
            )
        return final_reports
    return extract_aux(report, HWPCDepthLevel.ROOT)