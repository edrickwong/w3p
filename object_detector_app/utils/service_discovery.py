import os
import sys
import platform

LINUX_PLATFORMS = ['Linux']
MAC_PLATFORMS = ['Darwin']
WIN_PLATFORMS = ['']

class CameraServiceDiscovery(object):
    DEFAULT = -1

    @classmethod
    def find_camera_source(cls, interface_type='pci', default=0):
        cur_platform_system = platform.system()
        if cur_platform_system in LINUX_PLATFORMS:
            return cls.find_linux_camera_source(interface_type)
        elif cur_platform_system in MAC_PLATFORMS:
            return cls.find_mac_camera_source(interface_type)
        elif cur_platform_system in WIN_PLATFORMS:
            raise NotImplementedError('Not supported for Windows Platforms')
        else:
            if default:
                print 'Unable to find camera source, returning specified default'
                return default
            else:
                print 'Unable to find camera source, returning pre-defined default'
                return cls.DEFAULT

    @classmethod
    def find_linux_camera_source(cls, interface_type):
        return cls.DEFAULT

    @classmethod
    def find_mac_camera_source(cls, interface_type):
        # I don't have access to a mac right now, so no idea how
        # to differentiate usb/pci devices, so just returning
        # default 0
        return cls.DEFAULT
