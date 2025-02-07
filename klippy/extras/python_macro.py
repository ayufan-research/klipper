# Add ability to define custom g-code macros
#
# Copyright (C) 2018-2021  Kevin O'Connor <kevin@koconnor.net>
#
# This file may be distributed under the terms of the GNU GPLv3 license.
import traceback, logging

######################################################################
# Python macro
######################################################################

class PythonMacro:
    def __init__(self, config):
        if len(config.get_name().split()) > 2:
            raise config.error(
                    "Name of section '%s' contains illegal whitespace"
                    % (config.get_name()))
        name = config.get_name().split()[1]
        self.alias = name.upper()
        self.printer = printer = config.get_printer()
        self.cmd_desc = config.get("description", "Python macro")
        self.gcode.register_command(self.alias, self.cmd,
                                    desc=self.cmd_desc)
        self.in_script = False
        self.reload_config(config)
    def get_status(self, eventtime):
        return {}
    def reload_config(self, config):
        self.code = config.get("code", None)
    def cmd(self, gcmd):
        if self.in_script:
            raise gcmd.error("Macro %s called recursively" % (self.alias,))
        self.in_script = True
        try:
            eval(self.code, { 'printer': self.printer })
        finally:
            self.in_script = False

def load_config_prefix(config):
    return PythonMacro(config)
