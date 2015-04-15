#!/usr/bin/env python2
"""Contains PyWall class, the main class for our Python firewall."""

from __future__ import print_function
from packets import IPPacket

import os

import netfilterqueue as nfq

_NFQ_INIT = 'iptables -I INPUT -j NFQUEUE --queue-num %d'
_NFQ_CLOSE = 'iptables -D INPUT -j NFQUEUE --queue-num %d'


class PyWall(object):
    """The main class for PyWall.

    This class contains all rules for the firewall.  Furthermore, it waits on
    NetfilterQueue for packets, runs them through rules, and ultimately accepts
    or drops the packets.
    """

    def __init__(self, queue_num=1, default='DROP'):
        """Create a PyWall object, specifying NFQueue queue number."""
        self.queue_num = queue_num
        self.chains = {'INPUT': [], 'ACCEPT': None, 'DROP': None}
        self.default = default
        self._start = 'INPUT'
        self._old_handler = None

    def add_chain(self, chain_name):
        """Add a new, empty chain."""
        self.chains[chain_name] = []

    def add_rule(self, chain, rule):
        """Add a rule to a chain."""
        self.chains[chain].append(rule)

    def _apply_chain(self, chain, packet):
        """Run the packet through a chain."""
        if chain == 'ACCEPT':
            packet.accept()
        elif chain == 'DROP':
            packet.drop()
        else:
            # Match against every rule:
            for rule in self.chains[chain]:
                result = rule(packet)
                # If it matches, execute the rule.
                if result:
                    return self._apply_chain(result, packet)
            # If no matches, run the default rule.
            return self._apply_chain(self.default, packet)

    def callback(self, packet):
        """Accept packets from NFQueue."""
        self._apply_chain(self._start, packet)

    def run(self):
        """Run the PyWall!"""
        # Setup firewall rule.
        setup = _NFQ_INIT % self.queue_num
        os.system(setup)
        print('Set up IPTables: ' + setup)

        # Bind and run NFQ.
        nfqueue = nfq.NetfilterQueue()
        nfqueue.bind(self.queue_num, self.callback)
        try:
            nfqueue.run()
        finally:
            # Always remove the firewall rule when we're done.
            teardown = _NFQ_CLOSE % self.queue_num
            os.system(teardown)
            print('\nTore down IPTables: ' + teardown)


def print_ip_packet(packet):
    """Prints out packet information at the IP level."""
    ip_packet = IPPacket(packet.get_payload())
    print(unicode(ip_packet))
    print(unicode(ip_packet.get_payload()))
    return False


if __name__ == '__main__':
    # A firewall that will accept everything.  Which is really a pretty poor
    # firewall.
    the_wall = PyWall(default='ACCEPT')
    the_wall.add_rule('INPUT', print_ip_packet)
    the_wall.run()
