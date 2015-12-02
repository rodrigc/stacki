# @SI_Copyright@
#                             www.stacki.com
#                                  v2.0
# 
#      Copyright (c) 2006 - 2015 StackIQ Inc. All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#  
# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#  
# 2. Redistributions in binary form must reproduce the above copyright
# notice unmodified and in its entirety, this list of conditions and the
# following disclaimer in the documentation and/or other materials provided 
# with the distribution.
#  
# 3. All advertising and press materials, printed or electronic, mentioning
# features or use of this software must display the following acknowledgement: 
# 
# 	 "This product includes software developed by StackIQ" 
#  
# 4. Except as permitted for the purposes of acknowledgment in paragraph 3,
# neither the name or logo of this software nor the names of its
# authors may be used to endorse or promote products derived from this
# software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY STACKIQ AND CONTRIBUTORS ``AS IS''
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL STACKIQ OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# @SI_Copyright@

import sys
import socket
import string
import stack.commands

class Command(stack.commands.report.host.command):
        """
        Generate the /etc/resolv.conf for a host

	<arg optional='0' repeat='1' type='string' name='host'>
	Host name of machine
	</arg>
	"""

	def run(self, params, args):

		self.beginOutput()

                zones = {}
		dns = {}	
                for row in self.call('list.network'):
                        zones[row['network']] = row['zone']
			dns[row['network']] = row['dns']
                        
		for host in self.getHostnames(args):

                        self.addOutput(host,'<file name="/etc/resolv.conf">')

                        search = []
                        for zone in zones.values():
                        	if zone not in search:
                                        search.append(zone)
			if search:
				self.addOutput(host,
					'search %s' % string.join(search))
                        
                        # The default search path should always have the
                        # hosts default network first in the list, after
                        # that go by whatever ordering list.network returns.
                        #
                        # If the default network is 'public' use the
                        # public DNS rather that the server on the boss.

			#
			# or
			#

			#
			# if any network has 'dns' set to true, then the frontend
			# is serving DNS for that network, so make sure the
			# frontend is listed as the first DNS server, then list
			# the public DNS server
			#
                	for row in self.call('list.host.interface', [ host ]):
				network = row['network']
				if network in dns and dns[network]:
					frontend = self.db.getHostAttr(host,
						'Kickstart_PrivateAddress')
					self.addOutput(host, 'nameserver %s' %
						frontend)
					break

			remotedns = self.db.getHostAttr(host,
				'Kickstart_PublicDNSServers')
			if not remotedns:
				remotedns = self.db.getHostAttr(host,
					'Kickstart_PrivateDNSServers')
			if remotedns:
				servers = remotedns.split(',')
				for server in servers:
					self.addOutput(host, 'nameserver %s' % server.strip())

			self.addOutput(host,'</file>')

		self.endOutput(padChar='')

