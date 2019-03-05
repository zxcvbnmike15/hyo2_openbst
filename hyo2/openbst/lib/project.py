import logging
import os
import shutil
from typing import Optional

from hyo2.abc.lib.helper import Helper
from hyo2.abc.lib.progress.abstract_progress import AbstractProgress
from hyo2.abc.lib.progress.cli_progress import CliProgress

from hyo2.openbst.lib import lib_info
from hyo2.openbst.lib.source import Source, LayerType, FormatType
from hyo2.openbst.lib.sources.bag import Bag

logger = logging.getLogger(__name__)


class Project:

    def __init__(self, output_folder: Optional[str] = None,
                 progress: AbstractProgress = CliProgress(use_logger = True)):

        # output folder
        self._output_folder = None  # the project's output folder
        if (output_folder is None) or (not os.path.exists(output_folder)):
            output_folder = self.default_output_folder()
            logger.debug("using default output folder: %s" % output_folder)
        self._output_folder = output_folder

        self.progress = progress

        self._layer_paths_dict = dict()
        self._layers_dict = dict()
        self._layers_list = list()

    # ### OUTPUT FOLDER ###

    @classmethod
    def default_output_folder(cls):

        output_folder = Helper(lib_info=lib_info).package_folder()
        if not os.path.exists(output_folder):  # create it if it does not exist
            os.makedirs(output_folder)

        return output_folder

    @property
    def output_folder(self):
        return self._output_folder

    @output_folder.setter
    def output_folder(self, output_folder):
        if not os.path.exists(output_folder):
            raise RuntimeError("the passed output folder does not exist: %s" % output_folder)
        self._output_folder = output_folder

    def open_output_folder(self):
        Helper.explore_folder(self.output_folder)

    # ### TEMP FOLDER ###

    @property
    def temp_folder(self):
        temp_folder = os.path.join(self.output_folder, "temp")
        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder)

        return temp_folder

    def is_temp_folder_empty(self) -> bool:
        return len(os.listdir(self.temp_folder)) == 0

    def clear_temp_folder(self) -> None:

        if self.is_temp_folder_empty():
            return

        try:
            shutil.rmtree(self.temp_folder)

        except PermissionError as e:
            logger.info("unable to clean the temp folder: %s" % e)
            return

        logger.debug("cleared: %s" % self.temp_folder)

    # ### EXPORT FOLDER ###

    @property
    def export_folder(self) -> str:
        export_folder = os.path.join(self.output_folder, "export")
        if not os.path.exists(export_folder):
            os.makedirs(export_folder)

        return export_folder

    # ### LAYERS ###

    @classmethod
    def is_vr(cls, path: str) -> bool:

        data_source_types = Source.retrieve_layer_and_format_types(path)
        if len(data_source_types) == 0:
            return False

        if list(data_source_types.values())[0] != FormatType.BAG:
            return False

        return Bag.is_vr(path=path)

    @property
    def layers_dict(self) -> dict:
        return self._layers_dict

    @property
    def layers_list(self) -> list:
        return self._layers_list

    @property
    def ordered_layers_list(self) -> list:
        layers_list = list()

        basename_list = list()
        last_name = None

        for lk in list(reversed(self._layers_list)):

            cur_token, cur_name = lk.split(":")
            # logger.debug("%s : %s" % (cur_token, cur_name))

            if last_name is None:
                last_name = cur_name

            if cur_name != last_name:
                layers_list += basename_list
                basename_list.clear()

            if cur_token == "BAT":  # to have the bathymetry as latest
                basename_list.insert(0, lk)
            else:
                basename_list.append(lk)

        layers_list += basename_list

        return layers_list

    @property
    def layer_paths_dict(self) -> dict:
        return self._layer_paths_dict

    def layer_keys_by_basename(self, basename: str) -> list:
        layer_keys = list()
        key_list = list(self._layers_dict.keys())

        for layer_key in key_list:

            if basename == layer_key.split(":")[-1]:
                layer_keys.append(layer_key)

        return layer_keys

    def other_raster_layers_for_key(self, layer_key: str):
        other_layers = list()
        key_list = list(self._layers_dict.keys())
        layer_basename = layer_key.split(":")[-1]

        for key in key_list:
            if layer_key == key:
                continue

            if layer_basename == key.split(":")[-1]:
                if self._layers_dict[key].is_raster():
                    other_layers.append(self._layers_dict[key])

        return other_layers

    def load_from_source(self, path: str,
                         hint_type: LayerType = LayerType.UNKNOWN,
                         exclude_types: Optional[list] = None) -> bool:
        layer_format_types = Source.retrieve_layer_and_format_types(path, hint_type)

        if exclude_types is not None:
            logging.debug("filtering data types: %s " % (exclude_types, ))
            temp_raster_types = layer_format_types
            layer_format_types = dict()
            for raster_data_type in temp_raster_types.keys():

                if raster_data_type in exclude_types:
                    continue
                layer_format_types[raster_data_type] = temp_raster_types[raster_data_type]

        self.progress.start(title="Loading", text="Ongoing loading. Please wait!",
                            init_value=10)

        actual_layers = Source.load(input_path=path,
                                    layer_types=list(layer_format_types.keys()),
                                    input_format=list(layer_format_types.values())[0])

        self.progress.update(value=60)

        progress_quantum = 40 / (len(layer_format_types) + 1)

        for layer_type in layer_format_types.keys():

            layer_key = Source.make_layer_key(path=path, data_type=layer_type)
            logger.debug("raster key: %s" % layer_key)

            # if already exists, first close existing layer
            self.close_layer_by_key(layer_key=layer_key)

            if layer_type not in actual_layers.keys():
                logging.warning("skipping unretrieved %s layer" % layer_type)
                continue

            # actually add the layer to the dicts and to the list
            self._layers_dict[layer_key] = actual_layers[layer_type]
            self._layers_list.append(layer_key)
            self._layer_paths_dict[layer_key] = path

            self.progress.add(quantum=progress_quantum)

        self.progress.end()
        return True

    def has_layers(self) -> bool:

        return len(self._layers_list) != 0

    def has_modified_layers(self) -> bool:

        for layer_key, layer in self._layers_dict.items():

            if layer.modified:
                logger.debug("%s was modified" % layer_key)
                return True

        return False

    def close_layer_by_key(self, layer_key: str) -> bool:
        if layer_key not in self.layers_dict.keys():
            return False

        del self._layers_dict[layer_key]
        del self._layer_paths_dict[layer_key]
        self._layers_list.remove(layer_key)
        return True

    def close_layer_by_basename(self, layer_basename: str) -> bool:

        layers_key = self.layer_keys_by_basename(basename=layer_basename)

        for layer_key in layers_key:

            self.close_layer_by_key(layer_key)

        return True

    def close_layers(self) -> None:
        self._layers_dict.clear()
        self._layers_list.clear()
        self._layer_paths_dict.clear()
        self.clear_temp_folder()

    def save_layer_by_key(self, layer_key: str, output_path: str, open_folder: bool = False) -> bool:

        # first check whether the layer key is a valid one
        if layer_key not in self._layers_dict.keys():
            logger.warning("missing layer key: %s" % layer_key)
            return False

        # retrieve the input path and make a copy
        input_path = self._layer_paths_dict[layer_key]
        output_folder = os.path.dirname(output_path)
        try:
            shutil.copyfile(input_path, output_path)

            # .prj file
            prj_path = os.path.splitext(input_path)[0] + '.prj'
            if os.path.exists(prj_path):
                prj_basename = os.path.basename(prj_path)
                prj_copy = os.path.join(output_folder, prj_basename)
                shutil.copyfile(prj_path, prj_copy)

        except Exception as e:
            logger.error("unable to copy from %s to %s -> %s"
                         % (input_path, output_path, e))
            return False

        # retrieve all the layer keys interested by the saving operations
        layer_basename = layer_key.split(":")[-1]
        output_layer_keys = self.layer_keys_by_basename(basename=layer_basename)
        logger.debug("saving %s with keys %s" % (layer_basename, output_layer_keys))

        # retrieve the layers interested by the saving operations
        output_layers = dict()
        output_format = None
        for output_layer_key in output_layer_keys:
            if output_layer_key not in self._layers_dict.keys():
                continue
            output_layers[self._layers_dict[output_layer_key].layer_type] = \
                self._layers_dict[output_layer_key]
            output_format = self._layers_dict[output_layer_key].format_type
        # check if at least a layer was identified
        if len(output_layers) == 0:
            logger.warning("no layers to save")
            return False

        saved = Source.save(output_path=output_path, output_layers=output_layers,
                            output_format=output_format)
        if open_folder and saved:
            Helper.explore_folder(os.path.dirname(output_path))

        return True

    # ### OTHER ###

    def __repr__(self):
        msg = "<%s>\n" % self.__class__.__name__

        msg += "  <output folder: %s>\n" % self.output_folder
        msg += "  <temp folder: %s>\n" % self.temp_folder
        msg += "  <layers: %s>\n" % len(self._layer_paths_dict)

        return msg