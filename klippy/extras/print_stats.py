# Virtual SDCard print stat tracking
#
# Copyright (C) 2020  Eric Callahan <arksine.code@gmail.com>
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import os

class PrintStats:
    def __init__(self, config):
        printer = config.get_printer()
        self.gcode_move = printer.load_object(config, 'gcode_move')
        self.reactor = printer.get_reactor()
        self.reset()

        # Register commands
        self.gcode = printer.lookup_object('gcode')
        self.gcode.register_command('PRINT_STATS_START', self.cmd_PRINT_STATS_START)
        self.gcode.register_command('PRINT_STATS_PAUSE', self.cmd_PRINT_STATS_PAUSE)
        self.gcode.register_command('PRINT_STATS_ERROR', self.cmd_PRINT_STATS_ERROR)
        self.gcode.register_command('PRINT_STATS_CANCEL', self.cmd_PRINT_STATS_CANCEL)
        self.gcode.register_command('PRINT_STATS_COMPLETE', self.cmd_PRINT_STATS_COMPLETE)
        self.gcode.register_command('PRINT_STATS_RESET', self.cmd_PRINT_STATS_RESET)
    def cmd_PRINT_STATS_START(self, gcmd):
        if self.state in ["printing"]:
            gcmd.respond_info("Print is already started")
            return
        elif not self.state in ["paused", "error", "standby"]:
            gcmd.respond_info("Print is not reset to start")
            return
        self.note_start()
    def cmd_PRINT_STATS_PAUSE(self, gcmd):
        if not self.state in ["printing", "error"]:
            gcmd.respond_info("Print is not currently printing")
            return
        self.note_pause()
    def cmd_PRINT_STATS_ERROR(self, gcmd):
        if not self.state in ["printing", "paused"]:
            gcmd.respond_info("Print is not currently printing")
            return
        error = gcmd.get("ERROR", None)
        self.note_complete("error", error)
    def cmd_PRINT_STATS_CANCEL(self, gcmd):
        if not self.state in ["printing", "paused"]:
            gcmd.respond_info("Print is not currently printing")
            return
        self.note_complete("cancel")
    def cmd_PRINT_STATS_COMPLETE(self, gcmd):
        if not self.state in ["printing", "paused"]:
            gcmd.respond_info("Print is not currently printing")
            return
        self.note_complete("complete")
    def cmd_PRINT_STATS_RESET(self, gcmd):
        self.reset()
        filename = gcmd.get("FILENAME", None)
        if filename:
            self.filename = os.path.basename(filename)
    def _update_filament_usage(self, eventtime):
        gc_status = self.gcode_move.get_status(eventtime)
        cur_epos = gc_status['position'].e
        self.filament_used += (cur_epos - self.last_epos) \
            / gc_status['extrude_factor']
        self.last_epos = cur_epos
    def note_start(self):
        curtime = self.reactor.monotonic()
        if self.print_start_time is None:
            self.print_start_time = curtime
        elif self.last_pause_time is not None:
            # Update pause time duration
            pause_duration = curtime - self.last_pause_time
            self.prev_pause_duration += pause_duration
            self.last_pause_time = None
        # Reset last e-position
        gc_status = self.gcode_move.get_status(curtime)
        self.last_epos = gc_status['position'].e
        self.state = "printing"
        self.error_message = ""
    def note_pause(self):
        if self.last_pause_time is None:
            curtime = self.reactor.monotonic()
            self.last_pause_time = curtime
            # update filament usage
            self._update_filament_usage(curtime)
        if self.state != "error":
            self.state = "paused"
    def note_complete(self, state, error_message = ""):
        self.state = state
        eventtime = self.reactor.monotonic()
        self.total_duration = eventtime - self.print_start_time
        if self.filament_used < 0.0000001:
            # No positive extusion detected during print
            self.init_duration = self.total_duration - \
                self.prev_pause_duration
        self.print_start_time = None
        self.error_message = message
    def reset(self):
        self.filename = self.error_message = ""
        self.state = "standby"
        self.prev_pause_duration = self.last_epos = 0.
        self.filament_used = self.total_duration = 0.
        self.print_start_time = self.last_pause_time = None
        self.init_duration = 0.
    def get_status(self, eventtime):
        time_paused = self.prev_pause_duration
        if self.print_start_time is not None:
            if self.last_pause_time is not None:
                # Calculate the total time spent paused during the print
                time_paused += eventtime - self.last_pause_time
            else:
                # Accumulate filament if not paused
                self._update_filament_usage(eventtime)
            self.total_duration = eventtime - self.print_start_time
            if self.filament_used < 0.0000001:
                # Track duration prior to extrusion
                self.init_duration = self.total_duration - time_paused
        print_duration = self.total_duration - self.init_duration - time_paused
        return {
            'filename': self.filename,
            'total_duration': self.total_duration,
            'print_duration': print_duration,
            'filament_used': self.filament_used,
            'state': self.state,
            'message': self.error_message
        }

def load_config(config):
    return PrintStats(config)
