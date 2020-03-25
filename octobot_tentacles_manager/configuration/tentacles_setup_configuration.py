#  Drakkar-Software OctoBot-Tentacles-Manager
#  Copyright (c) Drakkar-Software, All rights reserved.
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3.0 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.
from copy import copy

from octobot_commons.logging.logging_util import get_logger
from octobot_tentacles_manager.configuration.config_file import read_config, write_config
from octobot_tentacles_manager.constants import USER_TENTACLE_CONFIG_FILE_PATH, DEFAULT_TENTACLE_CONFIG, \
    ACTIVATABLE_TENTACLES
from octobot_tentacles_manager.loaders.tentacle_loading import get_tentacle_classes


class TentaclesSetupConfiguration:
    TENTACLE_ACTIVATION_KEY = "tentacle_activation"

    def __init__(self, config_path=USER_TENTACLE_CONFIG_FILE_PATH):
        self.logger = get_logger(self.__class__.__name__)
        self.config_path = config_path
        self.tentacles_activation = {}

        # TODO: add user tentacle packages (previously stored in config.json as an URL/path list)
        self.user_tentacles = {}

    async def fill_tentacle_config(self, tentacles, default_tentacle_config=DEFAULT_TENTACLE_CONFIG,
                                   remove_missing_tentacles=True):
        activatable_tentacles_in_list = [tentacle_class_name
                                         for tentacle in tentacles
                                         if tentacle.get_simple_tentacle_type() in ACTIVATABLE_TENTACLES
                                         for tentacle_class_name in tentacle.tentacle_class_names]
        await self._update_tentacles_setup_config(activatable_tentacles_in_list,
                                                  default_tentacle_config_file=default_tentacle_config,
                                                  remove_missing_tentacles=remove_missing_tentacles)

    def upsert_tentacle_activation(self, new_config):
        # merge new_config into self.tentacles_activation (also replace conflicting values)
        self.tentacles_activation = {**self.tentacles_activation, **new_config}

    def replace_tentacle_activation(self, new_config):
        self.tentacles_activation = copy(new_config)

    async def read_config(self):
        try:
            self._from_dict(await read_config(self.config_path))
        except Exception as e:
            self.logger.error(f"Error when reading tentacles global configuration file ({e}), "
                              "resetting this file with default values. This will not change "
                              "any specific tentacle configuration.")
            activatable_tentacles_in_list = [tentacle_class_name
                                             for tentacle_class_name, tentacle in get_tentacle_classes().items()
                                             if tentacle.get_simple_tentacle_type() in ACTIVATABLE_TENTACLES]
            await self._update_tentacles_setup_config(activatable_tentacles_in_list)
            await self.save_config()

    async def save_config(self):
        await write_config(self.config_path, self._to_dict())

    async def _update_tentacles_setup_config(self,
                                             activatable_tentacles_in_list,
                                             default_tentacle_config_file=DEFAULT_TENTACLE_CONFIG,
                                             remove_missing_tentacles=True):

        default_config = await read_config(default_tentacle_config_file)
        default_activation_config = default_config[self.TENTACLE_ACTIVATION_KEY] \
            if self.TENTACLE_ACTIVATION_KEY in default_config else {}
        for tentacle in activatable_tentacles_in_list:
            self._update_tentacle_activation(tentacle, default_activation_config)
        if remove_missing_tentacles:
            self._filter_tentacle_activation(activatable_tentacles_in_list)

    def _update_tentacle_activation(self, tentacle, default_config):
        if tentacle not in self.tentacles_activation:
            if tentacle in default_config:
                self.tentacles_activation[tentacle] = default_config[tentacle]
            else:
                self.tentacles_activation[tentacle] = False

    def _filter_tentacle_activation(self, activatable_tentacles_in_list):
        for key in list(self.tentacles_activation.keys()):
            if key not in activatable_tentacles_in_list:
                self.tentacles_activation.pop(key)

    def _from_dict(self, input_dict):
        if self.TENTACLE_ACTIVATION_KEY in input_dict:
            self.tentacles_activation = input_dict[self.TENTACLE_ACTIVATION_KEY]

    def _to_dict(self):
        return {
            self.TENTACLE_ACTIVATION_KEY: self.tentacles_activation
        }
