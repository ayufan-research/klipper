import logging, traceback

class DebugHelpers:
    def __init__(self, config):
        self.printer = config.get_printer()

        # Register commands
        self.gcode = self.printer.lookup_object('gcode')
        self.gcode.register_command(
            "DEBUG_RELOAD", self.cmd_DEBUG_RELOAD,
            desc=self.cmd_DEBUG_RELOAD_help)

    cmd_DEBUG_RELOAD_help = "Reload all G-Code macros from config"
    def cmd_DEBUG_RELOAD(self, gcmd):
        configfile = self.printer.lookup_object('configfile')
        config = configfile.read_main_config(False)
        for section in config.get_prefix_sections(''):
            name = section.get_name()
            obj = self.printer.lookup_object(name, None)
            if not hasattr(obj, "reload_config"):
                continue

            # Reload only if config changed
            options = {}
            for option in section.get_prefix_options(''):
                options[option] = section.get(option, note_valid=False)
            if options == configfile.status_raw_config[name]:
                continue

            try:
                obj.reload_config(section)

                # Update config values
                configfile.status_raw_config[name] = options
                for (section, option), value in config.access_tracking.items():
                    if not section == name:
                        continue
                    configfile.status_settings.setdefault(section, {})[option] = value
                gcmd.respond_info("Reloaded %s" % (name))
            except Exception as e:
                msg = traceback.format_exception_only(type(e), e)[-1]
                gcmd.respond_info("%s: %s" % (name, msg))

def load_config(config):
    return DebugHelpers(config)
