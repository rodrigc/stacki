# @SI_Copyright@
# @SI_Copyright@
# @SI_Copyright@
import pyipmi
from pyipmi.bmc import LanBMC
from pyipmi import make_bmc
import pyipmi.server
from pyipmi.server import Server
import stack.api
import stack.commands
from stack.exception import *

class command(stack.commands.set.host.command):
	MustBeRoot = 0


class Command(command):
	"""
	Turn the power for a host on or off.

	<arg type='string' name='host' repeat='1'>
	One or more host names.
	</arg>

	<param type='string' name='action'>
	The power setting. This must be one of 'on', 'off', 'hard_reset'
	or 'power_cycle'. Reset does a warm boot. Cycle completely powers 
	off the machine then powers it back on, which has the server 
	go through a cold boot.
	</param>
		
	<example cmd='set host power compute-0-0 action=on'>
	Turn on the power for compute-0-0.
	</example>
	"""
	def run(self, params, args):
		(action, ) = self.fillParams([
			('action', ),
			])
		
		if not len(args):
			raise ArgRequired(self, 'host')
		host = args[0]

		if action not in [ 'on', 'off', 'hard_reset', 'power_cycle' ]:
			raise ParamError(self, 'action', 'must be one of "on"' \
				'"off", "power_cycle", or "hard_reset"')
		# Get ipmi interface from db for this host
		output = self.call('list.host.interface', [ host ])
		ipmi_ip = None
		for o in output:
			if o['interface'] == 'ipmi':
				ipmi_ip = o['ip']
		if not ipmi_ip:
			raise CommandError(self, 'No ipmi interface found for ' \
				'host ' + host)

		# Get the ipmi uname, pwd
		r = stack.api.Call("list.host.attr", 
			[host,"attr=ipmi_uname"])
		if not r:
			raise CommandError(self, 'ipmi uname not found in' \
				' the database')
		uname = r[0]['value']

		r = stack.api.Call("list.host.attr",
			[host,"attr=ipmi_pwd"])
		if not r:
			raise CommandError(self, 'ipmi password not found ' \
				'in the database')
		pwd = r[0]['value']

		bmc = make_bmc(LanBMC,
			hostname=ipmi_ip,
			username=uname,
			password=pwd)
		server = Server(bmc)

		if action == 'on':
			server.power_on()
		elif action == 'off':
			server.power_off()
		elif action == 'hard_reset':
			server.hard_reset()
		else:
			server.power_cycle()
