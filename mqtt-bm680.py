import getmac
import vscp
import vscphelper
import paho.mqtt.client as mqtt

def getGUID(id):
  return 'FF:FF:FF:FF:FF:FF:FF:FE:' + \
  	getmac.get_mac_address().upper() + \
  	":{0:02X}:{1:02X}".format(int(id/256),id & 0xff)

print(getGUID(512))

# New vscp helper library session
h1 = vscphelper.newSession()
if (0 == h1 ):
    vscphelper.closeSession(h1)
    raise ValueError('Unable to open vscphelp library session')

print("\n\nConnection in progress...")
rv = vscphelper.open(h1,"192.168.1.7:9598","admin","secret")
if vscp.VSCP_ERROR_SUCCESS == rv :
    print("Command success: open on channel 1")
else:
    vscphelper.closeSession(h1)
    raise ValueError('Command error: open on channel 1  Error code=%d' % rv )

if ( vscp.VSCP_ERROR_SUCCESS == vscphelper.isConnected(h1) ):
    print("CONNECTED!")
else:
    print("DISCONNECTED!")

rv = vscphelper.noop( h1 )
if vscp.VSCP_ERROR_SUCCESS != rv :
    vscphelper.closeSession(h1)
    raise ValueError('Command error: ''noop''  Error code=%d' % rv )

rv = vscphelper.close(h1)
if vscp.VSCP_ERROR_SUCCESS != rv :
    vscphelper.closeSession(h1)
    raise ValueError('Command error: close  Error code=%d' % rv )

vscphelper.closeSession(h1)
