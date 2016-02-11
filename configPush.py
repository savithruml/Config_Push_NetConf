#!/usr/bin/env python
import os
import sys
import logging
import paramiko
import xml.etree.ElementTree as etree
import xml.parsers.expat
from time import sleep

logging.basicConfig(level=logging.INFO, filename='netconf.log',
                        format='%(asctime)s %(message)s')

hello = '''<XML FILE HERE>'''

def main():

    """Main program to accept user input & setup a SSH session"""

    print """*** WELCOME TO LAB 6 (VALIDATION TOOL)***\n\n*** SAVITHRU_LOKANATH | KRISHNA_PRABHU ***\n"""

    valid_list = check_valid_ip()
    #print valid_list

    for router_ip in valid_list:

        hostname = router_ip
        username = ''
        password = ''

        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, 22, username, password,
                        allow_agent=False, look_for_keys=False)
        logging.info('Host {} succesfully connected'.format(hostname))

        transport = client.get_transport()
        channel = transport.open_channel('session')
        channel.invoke_subsystem('netconf')

        data = ""
        while True:
            if data.find(']]>]]>') != -1:
                data = data.replace(']]>]]>', '')
                break

            data = channel.recv(1024)

        #print data.strip()

        channel.send(hello)
        channel.send(get_config_request)

        data = ""
        while True:
            if data.find(']]>]]>') != -1:
                data = data.replace(']]>]]>', '')
                break

            data += channel.recv(1024)

        #print data.strip()

        try:
            tree = etree.fromstring(data)
            print '\n\n\nSCANNING CONFIG FOR ROUTER: ' + hostname
            time_bar()
            print '\n'
            find_user(tree, channel, push_data)
            find_service(tree, channel, push_data)
            find_mtu(tree, channel, push_data)
            find_snmp(tree, channel, push_data)
            client.close()

        except xml.parsers.expat.ExpatError, ex:
            print ex


def time_bar():

    """Function to display status bar"""

    for i in range(21):
        sys.stdout.write('\r')
        sys.stdout.write("[%-20s] %d%%" % ('='*i, 5*i))
        sys.stdout.flush()
        sleep(0.03)


def check_valid_ip():

    """Function to check if the IP address is valid"""

    ip_list = []

    ip_input = raw_input('Enter the IP address of the Router OR ' +
                            '[Press "A" to autopopulate]\n>').lower()

    if ip_input == 'a':
        ip_list = ['<IP_LIST>']

    else:
        ip_list.append(ip_input)

    return ip_list


def find_user(tree, channel, push_data):

    """Function to check if the desired user is present"""

    for user in tree.findall('.//user'):
        name = user.find('name').text

        if name == '<Username>':
            channel.send(push_data)
            print '> User "<Username>" exists on the host. Removing host....'
            logging.info('User <Username> exists on this host')

        else:
            pass


def find_service(tree,channel, push_data):

    """Function to check if HTTP service is enabled or not"""

    for services in tree.findall('.//services'):
        http = services.find('http')

        if http == None or http == ' ':
            channel.send(push_data)
            print '> HTTP service Disabled'
            logging.info('HTTP service is Disabled')

        else:
            pass
            #print '\nHTTP service enabled\n'


def find_mtu(tree, channel, push_data):

    """Function to check if MTU size is 1500 or not"""

    for interface in tree.findall('.//interface'):
        try:
            interface_type = interface.find('name').text

            if tree.find('.//mtu').text == '1500':
                pass
                #print 'MTU Size 1500 on ' + interface_type

            else:
                print '> Set MTU size equal to 1500 on ' + interface_type
                logging.info('MTU size not equal to 1500 on {}'.format(
                              interface_type))


        except:
            pass


def find_snmp(tree,channel, push_data):

    """Function to check if community string is set & authorization"""

    for snmp in tree.findall('.//community'):
        try:
            auth = snmp.find('authorization').text
            comm_string = snmp.find('name').text
            #print ('SNMP Community string is: ' + comm_string +
            #' with authorization: ' + auth)

            if auth != 'read-only':
                print ('> Set SNMP Community String: ' + comm_string +
                        ' to be authorized as read-only')
                channel.send(push_data)
                logging.info('SNMP Community String {} to be authorized as '
                                + 'read-only'.format(comm_string))

        except:
            pass


if __name__ == '__main__':
    sys.exit(main())

