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
#
# @Copyright@
#  				Rocks(r)
#  		         www.rocksclusters.org
#  		         version 5.4 (Maverick)
#  
# Copyright (c) 2000 - 2010 The Regents of the University of California.
# All rights reserved.	
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
# 	"This product includes software developed by the Rocks(r)
# 	Cluster Group at the San Diego Supercomputer Center at the
# 	University of California, San Diego and its contributors."
# 
# 4. Except as permitted for the purposes of acknowledgment in paragraph 3,
# neither the name or logo of this software nor the names of its
# authors may be used to endorse or promote products derived from this
# software without specific prior written permission.  The name of the
# software includes the following terms, and any derivatives thereof:
# "Rocks", "Rocks Clusters", and "Avalanche Installer".  For licensing of 
# the associated name, interested parties should contact Technology 
# Transfer & Intellectual Property Services, University of California, 
# San Diego, 9500 Gilman Drive, Mail Code 0910, La Jolla, CA 92093-0910, 
# Ph: (858) 534-5815, FAX: (858) 534-7345, E-MAIL:invent@ucsd.edu
#  
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS''
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# @Copyright@

import os
import time
import stack.commands
from stack.commands.sync.host import Parallel
from stack.commands.sync.host import timeout

class Command(stack.commands.sync.host.command):
	"""
	Reconfigure and optionally restart the network for the named hosts.

	<param type='boolean' name='restart'>
	If "yes", then restart the network after the configuration files are
	applied on the host.
	The default is: yes.
	</param>

	<example cmd='sync host network compute-0-0'>
	Reconfigure and restart the network on compute-0-0.
	</example>
	"""

	def run(self, params, args):
		restart, = self.fillParams([ ('restart', 'yes') ])

		restartit = self.str2bool(restart)

		hosts = self.getHostnames(args, managed_only=1)

		me = self.db.getHostname('localhost')

		threads = []
		for host in hosts:

			#
			# get the attributes for the host
			#
			attrs = self.db.getHostAttrs(host)

			cmd = '/opt/stack/bin/stack report host interface '
			cmd += '%s | ' % host
			cmd += '/opt/stack/bin/stack report script '
			cmd += 'attrs="%s" | ' % attrs
			if host != me:
				cmd += 'ssh -T -x %s ' % host
			cmd += 'bash > /dev/null 2>&1 '

			cmd += '; /opt/stack/bin/stack report host network '
			cmd += '%s | ' % host
			cmd += '/opt/stack/bin/stack report script '
			cmd += 'attrs="%s" | ' % attrs
			if host != me:
				cmd += 'ssh -T -x %s ' % host
			cmd += 'bash > /dev/null 2>&1 '

			cmd += '; /opt/stack/bin/stack report host route '
			cmd += '%s | ' % host
			cmd += '/opt/stack/bin/stack report script '
			cmd += 'attrs="%s" | ' % attrs
			if host != me:
				cmd += 'ssh -T -x %s ' % host
			cmd += 'bash > /dev/null 2>&1 '

			p = Parallel(cmd)
			threads.append(p)
			p.start()

		#
		# collect the threads
		#
		for thread in threads:
			thread.join(timeout)

		self.command('sync.host.firewall',
			[ 'restart=%s' % restart ] + hosts)

		self.runPlugins(hosts)

		if restartit:
			#
			# after all the configuration files have been rewritten,
			# restart the network
			#
			threads = []
			for host in hosts:
				cmd = '/sbin/service network restart '
				cmd += '> /dev/null 2>&1 ; '
				cmd += '/sbin/service ipmi restart > '
				cmd += '/dev/null 2>&1'
				if host != me:
					cmd = 'ssh %s "%s"' % (host, cmd)

				p = Parallel(cmd)
				threads.append(p)
				p.start()

			#
			# collect the threads
			#
			for thread in threads:
				thread.join(timeout)

		#
		# if IP addresses change, we'll need to sync the config (e.g.,
		# update /etc/hosts, /etc/dhcpd.conf, etc.).
		#
		self.command('sync.config')

		#
		# hack for ganglia on the frontend
		#
		if me in hosts and os.path.exists('/etc/ganglia/gmond.conf'):
			os.system('service gmond restart > /dev/null 2>&1')

