"""
    This is just a sample for a xmlrpc plugin
"""

def execute(xmlrpcobj, *args):
    str = args[0]
    return xmlrpcobj._outstr("Hello World!\n" + str)

