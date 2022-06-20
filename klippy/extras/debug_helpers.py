import logging, traceback

class DebugHelpers:
    def __init__(self, config):
        self.printer = config.get_printer()

        # Register commands
        self.gcode = self.printer.lookup_object('gcode')
        self.gcode.register_command(
            "DEBUG_RELOAD_GCODE_MACROS", self.cmd_DEBUG_RELOAD_GCODE_MACROS,
            desc=self.cmd_DEBUG_RELOAD_GCODE_MACROS_help)

    cmd_DEBUG_RELOAD_GCODE_MACROS_help = "Reload all G-Code macros from config"
    def cmd_DEBUG_RELOAD_GCODE_MACROS(self, gcmd):
        configfile = self.printer.lookup_object('configfile')
        config = configfile.read_main_config()
        gcode = self.printer.lookup_object('gcode')
        gcode_macro = self.printer.lookup_object('gcode_macro')
        for section_config in config.get_prefix_sections('gcode_macro '):
            macro = self.printer.lookup_object(section_config.get_name())
            try:
                macro.template = gcode_macro.load_template(section_config, 'gcode')
            except Exception as e:
                msg = traceback.format_exception_only(type(e), e)[-1]
                gcode.respond_info(msg)

def load_config(config):
    return DebugHelpers(config)
