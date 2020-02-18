import ipywidgets as widgets
from IPython.display import display

import logging


class OutputWidgetHandler(logging.Handler):
    """ Custom logging handler sending logs to an output widget """

    def __init__(self, *args, **kwargs):
        super(OutputWidgetHandler, self).__init__(*args, **kwargs)
        layout = {
            'width': '100%',
            'height': '160px',
            'border': '1px solid black'
        }
        self.out = widgets.Output(layout=layout)

    def emit(self, record):
        """ Overload of logging.Handler method """
        formatted_record = self.format(record)
        new_output = {
            'name': 'stdout',
            'output_type': 'stream',
            'text': formatted_record+'\n'
        }
        self.out.outputs = (new_output, ) + self.out.outputs

    def show_logs(self):
        """ Show the logs """
        display(self.out)

    def clear_logs(self):
        """ Clear the current logs """
        self.out.clear_output()


ns_list=["hyo2.openbst", ]

default_logging = logging.WARNING
hyo2_logging = logging.INFO
lib_logging = logging.DEBUG

logging.basicConfig(
    level=default_logging,
    format="%(levelname)-9s %(name)s.%(funcName)s:%(lineno)d > %(message)s"
)
logging.getLogger("hyo2").propagate = False
logging.getLogger("hyo2").setLevel(hyo2_logging)
handler = OutputWidgetHandler()
handler.setFormatter(logging.Formatter("%(levelname)-9s %(name)s.%(funcName)s:%(lineno)d > %(message)s"))
logging.getLogger("hyo2").addHandler(handler)

main_ns = "__main__"
if ns_list is None:
    ns_list = [main_ns, ]
if main_ns not in ns_list:
    ns_list.append(main_ns)

for ns in ns_list:
    # print(ns)
    logging.getLogger(ns).setLevel(lib_logging)


