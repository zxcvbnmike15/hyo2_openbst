from datetime import datetime
import hashlib
import logging
from pathlib import Path
from netCDF4 import Dataset, date2num, num2date
import numpy as np

from hyo2.openbst.lib import lib_info
from hyo2.openbst.lib.nc_helper import NetCDFHelper

logger = logging.getLogger(__name__)


class ProjectInfo:

    def __init__(self, prj_path: Path) -> None:
        self._path = prj_path.joinpath("info.nc")
        self._i = None
        self._raws_name = "raws"
        self._products_name = "products"
        self._nc()

    @property
    def path(self) -> Path:
        return self._path

    @property
    def name(self) -> str:
        return self._path.name

    @property
    def project_path(self) -> Path:
        return self._path.parent

    @property
    def conventions(self) -> str:
        return self._i.Conventions

    @property
    def time_units(self) -> str:
        return self._i.variables["time"].units

    @property
    def time_calendar(self) -> str:
        return self._i.variables["time"].calendar

    @property
    def version(self) -> str:
        return self._i.version

    @property
    def created(self) -> datetime:
        return num2date(self._i.created, units=self.time_units, calendar=self.time_calendar)

    @property
    def modified(self):
        return num2date(self._i.modified, units=self.time_units, calendar=self.time_calendar)

    @property
    def raws(self):
        return self._i.groups[self._raws_name].variables

    @property
    def products(self):
        return self._i.groups[self._products_name].variables

    def _nc(self) -> None:
        if self._path.exists():
            open_mode = "a"
        else:
            open_mode = "w"
        self._i = Dataset(filename=self._path, mode=open_mode)

        NetCDFHelper.init(ds=self._i)
        # logger.debug("conventions: %s" % self.conventions)
        # logger.debug("time: %s [%s]" % (self.time_units, self.time_calendar))
        # logger.debug("version: %s" % self.version)
        # logger.debug("created: %s" % self.created)
        # logger.debug("modified: %s" % self.modified)

        NetCDFHelper.groups(ds=self._i, names=[self._raws_name, self._products_name])

        logger.info("open in '%s' mode: [v.%s] %s" % (open_mode, self.version, self.path))

    def updated(self):
        NetCDFHelper.update_modified(self._i)

    @classmethod
    def hash_string(cls, input_str: str) -> str:
        return hashlib.sha256(input_str.encode('utf-8')).hexdigest()

    # # ### RAWS ###
    #
    # def valid_raws(self) -> list:
    #     valid_raws = list()
    #     for raw_key, raw in self._raws.variables.items():
    #         if raw.deleted == 0:
    #             valid_raws.append(raw_key)
    #     return valid_raws
    #
    # def add_raw(self, path: str) -> bool:
    #     self.progress.start(title="Reading", text="Ongoing reading. Please wait!",
    #                         init_value=10)
    #
    #     path = os.path.normpath(path)
    #     if not os.path.exists(path=path):
    #         logger.warning("The source does not exist: %s" % path)
    #         self.progress.end()
    #         return False
    #
    #     path_hash = self.hash_string(path)
    #     if path_hash in self._raws.variables.keys():
    #         self._raws.variables[path_hash].source_path = path
    #         if self._raws.variables[path_hash].deleted == 1:
    #             self._raws.variables[path_hash].deleted = 0
    #             logger.info("Raw entry was deleted: %s" % path)
    #     else:
    #         path_var = self._raws.createVariable(path_hash, 'u1')
    #         path_var.source_path = path
    #         path_var.deleted = 0
    #         logger.debug("Raw entry was added: %s" % path)
    #
    #     self.progress.end()
    #     return True
    #
    # def remove_raw(self, path: str) -> bool:
    #     self.progress.start(title="Deleting", text="Ongoing deleting. Please wait!",
    #                         init_value=10)
    #
    #     path_hash = self.hash_string(path)
    #     if path_hash not in self._raws.variables.keys():
    #         logger.info("File already removed: %s" % path)
    #         return False
    #
    #     self._raws[path_hash].deleted = 1
    #     logger.debug("removed: %s" % path)
    #
    #     self.progress.update(40)
    #
    #     self.progress.end()
    #     return True
    #
    # # ### PRODUCTS ###
    #
    # def valid_products(self) -> list:
    #     valid_products = list()
    #     for product_key, product in self._products.variables.items():
    #         if product.deleted == 0:
    #             valid_products.append(product_key)
    #     return valid_products
    #
    # def add_product(self, path: str) -> bool:
    #     self.progress.start(title="Reading", text="Ongoing reading. Please wait!",
    #                         init_value=10)
    #
    #     path = os.path.normpath(path)
    #     if not os.path.exists(path=path):
    #         logger.warning("The source does not exist: %s" % path)
    #         self.progress.end()
    #         return False
    #
    #     path_hash = self.hash_string(path)
    #     if path_hash in self._products.variables.keys():
    #         self._products.variables[path_hash].source_path = path
    #         if self._products.variables[path_hash].deleted == 1:
    #             self._products.variables[path_hash].deleted = 0
    #             logger.info("Product entry was deleted: %s" % path)
    #     else:
    #         path_var = self._products.createVariable(path_hash, 'u1')
    #         path_var.source_path = path
    #         path_var.deleted = 0
    #         logger.debug("Product entry added: %s" % path)
    #
    #     product = Product(project_folder=self.project_path, product_name=path_hash,
    #                       source_path=path)
    #     product.close()
    #
    #     self.progress.end()
    #     return True
    #
    # def remove_product(self, path: str) -> bool:
    #     self.progress.start(title="Deleting", text="Ongoing deleting. Please wait!",
    #                         init_value=10)
    #
    #     path_hash = self.hash_string(path)
    #     if path_hash not in self._products.variables.keys():
    #         logger.info("File already removed: %s" % path)
    #         return False
    #
    #     self._products[path_hash].deleted = 1
    #     logger.debug("Product entry removed: %s" % path)
    #
    #     self.progress.update(40)
    #     product_path = Product.make_product_path(project_folder=self.project_path,
    #                                              product_name=path_hash)
    #     os.remove(product_path)
    #     self.progress.end()
    #     return True
    #
    # # @classmethod
    # # def is_product_vr(cls, path: str) -> bool:
    # #
    # #     data_source_types = Product.retrieve_layer_and_format_types(path)
    # #     if len(data_source_types) == 0:
    # #         return False
    # #
    # #     if list(data_source_types.values())[0] != ProductFormatType.BAG:
    # #         return False
    # #
    # #     return ProductFormatBag.is_vr(path=path)
    # #
    # # @property
    # # def product_layers_dict(self) -> dict:
    # #     return self._product_layers_dict
    # #
    # # @property
    # # def product_layers_list(self) -> list:
    # #     return self._product_layers_list
    # #
    # # @property
    # # def ordered_product_layers_list(self) -> list:
    # #     layers_list = list()
    # #
    # #     basename_list = list()
    # #     last_name = None
    # #
    # #     for lk in list(reversed(self._product_layers_list)):
    # #
    # #         cur_token, cur_name = lk.split(":")
    # #         # logger.debug("%s : %s" % (cur_token, cur_name))
    # #
    # #         if last_name is None:
    # #             last_name = cur_name
    # #
    # #         if cur_name != last_name:
    # #             layers_list += basename_list
    # #             basename_list.clear()
    # #
    # #         if cur_token == "BAT":  # to have the bathymetry as latest
    # #             basename_list.insert(0, lk)
    # #         else:
    # #             basename_list.append(lk)
    # #
    # #     layers_list += basename_list
    # #
    # #     return layers_list
    # #
    # # @property
    # # def product_layer_paths_dict(self) -> dict:
    # #     return self._product_layer_paths_dict
    # #
    # # def product_layer_keys_by_basename(self, basename: str) -> list:
    # #     layer_keys = list()
    # #     key_list = list(self._product_layers_dict.keys())
    # #
    # #     for layer_key in key_list:
    # #
    # #         if basename == layer_key.split(":")[-1]:
    # #             layer_keys.append(layer_key)
    # #
    # #     return layer_keys
    # #
    # # def other_product_layers_for_key(self, layer_key: str):
    # #     other_layers = list()
    # #     key_list = list(self._product_layers_dict.keys())
    # #     layer_basename = layer_key.split(":")[-1]
    # #
    # #     for key in key_list:
    # #         if layer_key == key:
    # #             continue
    # #
    # #         if layer_basename == key.split(":")[-1]:
    # #             if self._product_layers_dict[key].is_raster():
    # #                 other_layers.append(self._product_layers_dict[key])
    # #
    # #     return other_layers
    # #
    # # def load_product_from_source(self, path: str,
    # #                              hint_type: ProductLayerType = ProductLayerType.UNKNOWN,
    # #                              exclude_types: Optional[list] = None) -> bool:
    # #     layer_format_types = Product.retrieve_layer_and_format_types(path, hint_type)
    # #
    # #     if exclude_types is not None:
    # #         logging.debug("filtering data types: %s " % (exclude_types,))
    # #         temp_raster_types = layer_format_types
    # #         layer_format_types = dict()
    # #         for raster_data_type in temp_raster_types.keys():
    # #
    # #             if raster_data_type in exclude_types:
    # #                 continue
    # #             layer_format_types[raster_data_type] = temp_raster_types[raster_data_type]
    # #
    # #     self.progress.start(title="Loading", text="Ongoing loading. Please wait!",
    # #                         init_value=10)
    # #
    # #     actual_layers = Product.load(input_path=path,
    # #                                  layer_types=list(layer_format_types.keys()),
    # #                                  input_format=list(layer_format_types.values())[0])
    # #
    # #     self.progress.update(value=60)
    # #
    # #     progress_quantum = 40 / (len(layer_format_types) + 1)
    # #
    # #     for layer_type in layer_format_types.keys():
    # #
    # #         layer_key = Product.make_layer_key(path=path, data_type=layer_type)
    # #         logger.debug("raster key: %s" % layer_key)
    # #
    # #         # if already exists, first close existing layer
    # #         self.close_product_layer_by_key(layer_key=layer_key)
    # #
    # #         if layer_type not in actual_layers.keys():
    # #             logging.warning("skipping unretrieved %s layer" % layer_type)
    # #             continue
    # #
    # #         # actually add the layer to the dicts and to the list
    # #         self._product_layers_dict[layer_key] = actual_layers[layer_type]
    # #         self._product_layers_list.append(layer_key)
    # #         self._product_layer_paths_dict[layer_key] = path
    # #
    # #         self.progress.add(quantum=progress_quantum)
    # #
    # #     self.progress.end()
    # #     return True
    # #
    # # def has_product_layers(self) -> bool:
    # #
    # #     return len(self._product_layers_list) != 0
    # #
    # # def has_modified_product_layers(self) -> bool:
    # #
    # #     for layer_key, layer in self._product_layers_dict.items():
    # #
    # #         if layer.modified:
    # #             logger.debug("%s was modified" % layer_key)
    # #             return True
    # #
    # #     return False
    # #
    # # def close_product_layer_by_key(self, layer_key: str) -> bool:
    # #     if layer_key not in self.product_layers_dict.keys():
    # #         return False
    # #
    # #     del self._product_layers_dict[layer_key]
    # #     del self._product_layer_paths_dict[layer_key]
    # #     self._product_layers_list.remove(layer_key)
    # #     return True
    # #
    # # def close_product_layer_by_basename(self, layer_basename: str) -> bool:
    # #
    # #     layers_key = self.product_layer_keys_by_basename(basename=layer_basename)
    # #
    # #     for layer_key in layers_key:
    # #         self.close_product_layer_by_key(layer_key)
    # #
    # #     return True
    # #
    # # def close_product_layers(self) -> None:
    # #     self._product_layers_dict.clear()
    # #     self._product_layers_list.clear()
    # #     self._product_layer_paths_dict.clear()
    # #
    # # def save_product_layer_by_key(self, layer_key: str, output_path: str, open_folder: bool = False) -> bool:
    # #
    # #     # first check whether the layer key is a valid one
    # #     if layer_key not in self._product_layers_dict.keys():
    # #         logger.warning("missing layer key: %s" % layer_key)
    # #         return False
    # #
    # #     # retrieve the input path and make a copy
    # #     input_path = self._product_layer_paths_dict[layer_key]
    # #     output_folder = os.path.dirname(output_path)
    # #     try:
    # #         shutil.copyfile(input_path, output_path)
    # #
    # #         # .prj file
    # #         prj_path = os.path.splitext(input_path)[0] + '.prj'
    # #         if os.path.exists(prj_path):
    # #             prj_basename = os.path.basename(prj_path)
    # #             prj_copy = os.path.join(output_folder, prj_basename)
    # #             shutil.copyfile(prj_path, prj_copy)
    # #
    # #     except Exception as e:
    # #         logger.error("unable to copy from %s to %s -> %s"
    # #                      % (input_path, output_path, e))
    # #         return False
    # #
    # #     # retrieve all the layer keys interested by the saving operations
    # #     layer_basename = layer_key.split(":")[-1]
    # #     output_layer_keys = self.product_layer_keys_by_basename(basename=layer_basename)
    # #     logger.debug("saving %s with keys %s" % (layer_basename, output_layer_keys))
    # #
    # #     # retrieve the layers interested by the saving operations
    # #     output_layers = dict()
    # #     output_format = None
    # #     for output_layer_key in output_layer_keys:
    # #         if output_layer_key not in self._product_layers_dict.keys():
    # #             continue
    # #         output_layers[self._product_layers_dict[output_layer_key].layer_type] = \
    # #             self._product_layers_dict[output_layer_key]
    # #         output_format = self._product_layers_dict[output_layer_key].format_type
    # #     # check if at least a layer was identified
    # #     if len(output_layers) == 0:
    # #         logger.warning("no layers to save")
    # #         return False
    # #
    # #     saved = Product.save(output_path=output_path, output_layers=output_layers, output_format=output_format)
    # #     if open_folder and saved:
    # #         Helper.explore_folder(os.path.dirname(output_path))
    # #
    # #     return True

    # ### OTHER ###

    def __repr__(self):
        msg = "<%s>\n" % self.__class__.__name__
        msg += "  <name: %s>\n" % self.name
        msg += "  <project path: %s>\n" % self.project_path
        msg += "  <conventions: %s>\n" % self.conventions
        msg += "  <time: %s [%s]>\n" % (self.time_units, self.time_calendar)
        msg += "  <version: %s>\n" % self.version
        msg += "  <created: %s>\n" % self.created
        msg += "  <modified: %s>\n" % self.modified
        msg += "  <raws: %d>\n" % len(self.raws)
        for raw_key, raw in self.raws.items():
            msg += "    <%s[D%s]: %s>\n" \
                   % (raw_key, raw.deleted, raw.source_path)
        msg += "  <products: %d>\n" % len(self.products)
        for product_key, product in self.products.items():
            msg += "    <%s[D%s]: %s>\n" \
                   % (product_key, product.deleted, product.source_path)
        return msg