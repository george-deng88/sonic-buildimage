#############################################################################
# PDDF
# Module contains an implementation of SONiC Chassis API
#
#############################################################################

try:
    import subprocess
    import sys
    import syslog
    from sonic_platform_pddf_base.pddf_chassis import PddfChassis
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

class Chassis(PddfChassis):
    """
    PDDF Platform-specific Chassis class
    """

    def __init__(self, pddf_data=None, pddf_plugin_data=None):
        PddfChassis.__init__(self, pddf_data, pddf_plugin_data)

    def _getstatusoutput(self, cmd):
        try:
            data = subprocess.check_output(cmd, shell=True,
                    universal_newlines=True, stderr=subprocess.STDOUT)
            status = 0
        except subprocess.CalledProcessError as ex:
            data = ex.output
            status = ex.returncode
        result = data.replace('\n', '')
        return status, result


    def get_sfp(self, index):
        """
        Retrieves sfp represented by (1-based) index <index>
        For Quanta the index in sfputil.py starts from 1, so override
        Args:
            index: An integer, the index (1-based) of the sfp to retrieve.
            The index should be the sequence of a physical port in a chassis,
            starting from 1.
        Returns:
            An object dervied from SfpBase representing the specified sfp
        """
        sfp = None

        try:
            if (index == 0):
                raise IndexError
            sfp = self._sfp_list[index-1]
        except IndexError:
            sys.stderr.write("override: SFP index {} out of range (1-{})\n".format(
                index, len(self._sfp_list)))

        return sfp
    # Provide the functions/variables below for which implementation is to be overwritten

    def get_reboot_cause(self):
        """
        Retrieves the cause of the previous reboot
        Returns:
            A tuple (string, string) where the first element is a string
            containing the cause of the previous reboot. This string must be
            one of the predefined strings in this class. If the first string
            is "REBOOT_CAUSE_HARDWARE_OTHER", the second string can be used
            to pass a description of the reboot cause.
        """
        hw_reboot_cause = ""
        status, hw_reboot_cause = self._getstatusoutput("i2cget -y -f 104 0x0d 0x06 b")
        if status != 0:
            pass

        if hw_reboot_cause == "0x11":
            reboot_cause = self.REBOOT_CAUSE_POWER_LOSS
            description = 'Power Off Reset'
        elif hw_reboot_cause == "0x22":
            reboot_cause = self.REBOOT_CAUSE_NON_HARDWARE
            description = 'Soft-Set Warm Reset'
        elif hw_reboot_cause == "0x33":
            reboot_cause = self.REBOOT_CAUSE_NON_HARDWARE
            description = 'Soft-Set Cold Reset'
        elif hw_reboot_cause == "0x44":
            reboot_cause = self.REBOOT_CAUSE_NON_HARDWARE
            description = 'CPU Warm Reset'
        elif hw_reboot_cause == "0x55":
            reboot_cause = self.REBOOT_CAUSE_HARDWARE_OTHER
            description = 'CPU Cold Reset'
        elif hw_reboot_cause == "0x66":
            reboot_cause = self.REBOOT_CAUSE_WATCHDOG
            description = 'GPIO Watchdog Reset'
        elif hw_reboot_cause == "0x77":
            reboot_cause = self.REBOOT_CAUSE_POWER_LOSS
            description = 'Power Cycle Reset'
        elif hw_reboot_cause == "0x88":
            reboot_cause = self.REBOOT_CAUSE_WATCHDOG
            description = 'Hardware Watchdog Reset'
        else:
            reboot_cause = self.REBOOT_CAUSE_HARDWARE_OTHER
            description = 'Hardware reason'

        return (reboot_cause, description)

    def get_watchdog(self):
        try:
            if self._watchdog is None:
                from sonic_platform.cpldwatchdog import Watchdog
                #Create the watchdog instance form cpld watchdog
                self._watchdog = Watchdog()
        except Exception as e:
            syslog.syslog(syslog.LOG_ERR, "Fail to load watchdog due to {}".format(e))
        return self._watchdog
