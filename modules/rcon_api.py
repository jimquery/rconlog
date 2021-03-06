#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from modules import rcon_core as core
from sqlalchemy import exc
from modules import rcon_log as logger
import getpass
from sqlalchemy_filters import apply_filters
from modules.rcon_client import utils
import glob, os
from modules import rconlog_config as config
import ipaddress

# TODO: Implement filters


class RconAPI(object):

    @staticmethod
    def load_custom_subnets(session):
        subnets = []
        try:
            _subnets = session.query(core.CustomSubnet.subnet).all()
            subnets = [value for value, in _subnets]
        except Exception as e:
            logger.logging.error('Can\'t get custom subnets: {error}'.format(error=str(e)))
            exit(1)

        net_dir = config.default['FW_CUSTOM_PATH']

        os.chdir(net_dir)
        for file in glob.glob("*.net"):
            try:
                abs_fname = "{}/{}".format(net_dir,file)
                with open(abs_fname) as f:
                    for net in f:
                        try:
                            ip_net = ipaddress.ip_network(net.rstrip())
                            if not str(ip_net) in subnets:
                                subnet = core.CustomSubnet(str(ip_net))
                                session.add(subnet)
                        except Exception as e:
                            logger.logging.error('Can\'t parse custom subnet: {error}'.format(error=str(e)))
                            continue
            except Exception as e:
                logger.logging.error('Can\'t parse custom subnet file: {error}'.format(error=str(e)))
                continue

        session.commit()

        return 'Subnets loaded successful'

    @staticmethod
    def list_custom_subnets(session, args=None, filter=None):
        if filter is None:
            filter = []

        subnets = None
        try:
            subnets = session.query(core.CustomSubnet)
            subnets = apply_filters(subnets, filter)
            subnets = subnets.all()
        except Exception as e:
            err_msg = 'Can\'t get custom subnets: {error}'.format(error=str(e))
            logger.logging.error(err_msg)
            print(err_msg)
            exit(1)

        return subnets


    @staticmethod
    def del_rcon_server(session, args):
        s = None
        try:
            s = session.query(core.RconServer).filter_by(id=args.id).first()
            if s is not None:
                session.delete(s)
                session.commit()
        except Exception as e:
            logger.logging.error('Can\'t delete RCON server: {error}'.format(error=str(e)))
            print('Can\'t delete RCON server: {error}'.format(error=str(e)))
            exit(1)
        return 'Server {id} successful deleted'.format(id=s.id)

    # ------------------

    @staticmethod
    def get_rcon_server(session, args):
        s = None
        try:
            s = session.query(core.RconServer).filter_by(id=args.id).first()
        except Exception as e:
            logger.logging.error('Can\'t get RCON server: {error}'.format(error=str(e)))
            print('Can\'t get RCON server: {error}'.format(error=str(e)))
            exit(1)
        return s

    # ------------------

    @staticmethod
    def test_rcon_server(session, args):
        s = None
        try:
            s = session.query(core.RconServer).filter_by(id=args.id).first()
        except Exception as e:
            logger.logging.error('Can\'t get RCON server: {error}'.format(error=str(e)))
            print('Can\'t get RCON server: {error}'.format(error=str(e)))
            exit(1)

        stat = ''
        try:
            stat = utils.send_rcon_command(
                s.rcon_host,
                int(s.rcon_port),
                s.rcon_password,
                s.rcon_proto,
                'status'
            )
        except Exception as e:
            err_msg = 'Critical error with RCON server ID {id}: {error}'.format(error=str(e), id=s.id)
            logger.logging.error(err_msg)
            print(err_msg)
            exit(1)

        return stat

    # ------------------

    @staticmethod
    def passwd_rcon_server(session, args):
        s = None
        try:
            s = session.query(core.RconServer).filter_by(id=args.id).first()

            if not hasattr(args, 'passwd'):
                passwd = getpass.getpass('Enter rcon_password: ')
                passwd2 = getpass.getpass('Confirm rcon_password: ')
                if passwd != passwd2:
                    raise Exception('Passwords not match.')
                args.passwd = passwd

            s.rcon_password = args.passwd
            session.commit()

        except Exception as e:
            logger.logging.error('Can\'t change password for RCON server: {error}'.format(error=str(e)))
            print('Can\'t change password for RCON server: {error}'.format(error=str(e)))
            exit(1)
        return 'Password for server ID: {id} successful changed'.format(id=s.id)

    # ------------------

    @staticmethod
    def enable_rcon_server(session, args):
        s = None
        try:
            s = session.query(core.RconServer).filter_by(id=args.id).first()
            s.enabled = True
            session.commit()
        except Exception as e:
            logger.logging.error('Can\'t enable RCON server: {error}'.format(error=str(e)))
            print('Can\'t enable RCON server: {error}'.format(error=str(e)))
            exit(1)

        return 'Server {id} successful enabled'.format(id=s.id)

    # ------------------

    @staticmethod
    def disable_rcon_server(session, args):
        s = None
        try:
            s = session.query(core.RconServer).filter_by(id=args.id).first()
            s.enabled = False
            session.commit()
        except Exception as e:
            logger.logging.error('Can\'t disable RCON server: {error}'.format(error=str(e)))
            print('Can\'t disable RCON server: {error}'.format(error=str(e)))
            exit(1)

        return 'Server {id} successful disabled'.format(id=s.id)

    # ------------------

    @staticmethod
    def protect_rcon_server(session, args):
        s = None
        try:
            s = session.query(core.RconServer).filter_by(id=args.id).first()
            s.protected = args.protected.lower() == 'on'
            session.commit()
        except Exception as e:
            msg_error = 'Can\'t set protect property to RCON server: {error}'.format(error=str(e))
            logger.logging.error(msg_error)
            print(msg_error)
            exit(1)

        return 'Server {id} protect set successful'.format(id=s.id)

    # ------------------

    # TODO: replace attrs to filter
    @staticmethod
    def list_rcon_server(session, args, filter=None):
        if filter is None:
            filter = []

        if args is None:
            args = []

        servers = None
        try:
            servers = session.query(core.RconServer)
            servers = apply_filters(servers, filter)

            if hasattr(args, 'enabled') and args.enabled:
                servers = servers.filter_by(enabled=True).all()
            elif hasattr(args, 'disabled') and args.disabled:
                servers = servers.filter_by(enabled=False).all()
            else:
                servers = servers.all()
        except Exception as e:
            logger.logging.error('Can\'t get RCON servers: {error}'.format(error=str(e)))
            print('Can\'t get RCON servers: {error}'.format(error=str(e)))
            exit(1)

        return servers

    # ------------------

    @staticmethod
    def list_rcon_users(session, args, filter=None):
        if filter is None:
            filter = []

        users = None
        try:
            users = session.query(core.RconServer.username,core.RconServer.enabled,core.RconServer.protected)
            users = apply_filters(users, filter)
            users = users.group_by(core.RconServer.username,core.RconServer.enabled,core.RconServer.protected).all()
        except Exception as e:
            logger.logging.error('Can\'t get RCON users: {error}'.format(error=str(e)))
            print('Can\'t get RCON users: {error}'.format(error=str(e)))
            exit(1)

        return users

    # ------------------

    @staticmethod
    def create_rcon_server(session, args):
        try:
            server = core.RconServer(args.username,
                                     str(args.host),
                                     args.port,
                                     args.passwd,
                                     args.proto,
                                     args.enabled)
            session.add(server)
            session.commit()
        except Exception as e:
            logger.logging.error('Can\'t create new RCON server: {error}'.format(error=str(e)))
            print('Can\'t create new RCON server: {error}'.format(error=str(e)))
            exit(1)

        return 'Created successful'

    # ------------------

    @staticmethod
    def list_rcon_updates(session, args, filter=None):
        if filter is None:
            filter = []

        updates = None
        try:
            updates = session.query(core.Updates)
            updates = apply_filters(updates, filter)

            updates = updates.all()
        except Exception as e:
            logger.logging.error('Can\'t get updates: {error}'.format(error=str(e)))
            exit(1)

        return updates

    # TODO: Implement filter by array of conditions
    @staticmethod
    def get_rcon_update(session, args, _filter=None):
        if _filter is None:
            _filter = []
        u = None
        try:
            u = session.query(core.Updates)
            u = apply_filters(u, _filter)
            u = u.first()
        except Exception as e:
            logger.logging.error('Can\'t get RCON server: {error}'.format(error=str(e)))
            print('Can\'t get RCON update: {error}'.format(error=str(e)))
            exit(1)
        return u

    @staticmethod
    def create_rcon_update(session, args, commit=True):
        try:
            update = core.Updates(
                args.gamehost,
                args.gameport,
                args.ipaddr,
                args.rcon_server_id)

            session.add(update)
            if commit:
                session.commit()
        except Exception as e:
            logger.logging.error('Can\'t create RCON update record: {error}'.format(error=str(e)))
            print('Can\'t create RCON update record: {error}'.format(error=str(e)))
            exit(1)

        return 'Created successful'

    @staticmethod
    def flush_user_rules(session, username):
        fw_name = config.default['FW_NAME']

        _filter = [
            {'field': 'username', 'op': '==', 'value': username},
        ]
        try:
            rules = session.query(core.FirewallRule)
            rules = apply_filters(rules, _filter)
            rules.update({fw_name: False}, synchronize_session=False)
            session.commit()
        except Exception as e:
            msg_error = 'Can\'t flush firewall rules: {error}'.format(error=str(e))
            logger.logging.error(msg_error)
            exit(1)


    @staticmethod
    def create_rcon_firewall(session, args):
        try:
            firewall = core.Firewall(
                args.host,
                args.name,
                args.type,
                args.enabled)

            session.add(firewall)
            session.commit()
        except Exception as e:
            msg_error = 'Can\'t create firewall: {error}'.format(error=str(e))
            logger.logging.error(msg_error)
            print(msg_error)
            exit(1)

        return 'Created successful'


    @staticmethod
    def del_rcon_firewall(session, args):
        f = None
        try:
            f = session.query(core.Firewall).filter_by(id=args.id).first()
            if f is not None:
                session.delete(f)
                session.commit()
        except Exception as e:
            msg_error = 'Can\'t delete firewall: {error}'.format(error=str(e))
            logger.logging.error(msg_error)
            print(msg_error)
            exit(1)
        return 'Server {id} successful deleted'.format(id=f.id)

    # ------------------

    @staticmethod
    def get_rcon_firewall(session, args):
        f = None
        try:
            f = session.query(core.Firewall).filter_by(id=args.id).first()
        except Exception as e:
            msg_error = 'Can\'t get firewall: {error}'.format(error=str(e))
            logger.logging.error(msg_error)
            print(msg_error)
            exit(1)
        return f


    @staticmethod
    def list_rcon_firewall(session, args, filter=None):
        if filter is None:
            filter = []

        firewalls = None
        try:
            firewalls = session.query(core.Firewall)
            firewalls = apply_filters(firewalls, filter)

            updates = firewalls.all()
        except Exception as e:
            logger.logging.error('Can\'t get firewalls: {error}'.format(error=str(e)))
            exit(1)

        return firewalls
    # ------------------

    @staticmethod
    def enable_rcon_firewall(session, args):
        f = None
        try:
            f = session.query(core.Firewall).filter_by(id=args.id).first()
            f.enabled = True
            session.commit()
        except Exception as e:
            logger.logging.error('Can\'t enable RCON server: {error}'.format(error=str(e)))
            print('Can\'t enable RCON server: {error}'.format(error=str(e)))
            exit(1)

        return 'Server {id} successful enabled'.format(id=f.id)

    # ------------------

    @staticmethod
    def disable_rcon_firewall(session, args):
        f = None
        try:
            f = session.query(core.Firewall).filter_by(id=args.id).first()
            f.enabled = False
            session.commit()
        except Exception as e:
            logger.logging.error('Can\'t disable RCON server: {error}'.format(error=str(e)))
            print('Can\'t disable RCON server: {error}'.format(error=str(e)))
            exit(1)

        return 'Server {id} successful disabled'.format(id=f.id)

    # -- Database methods
    @staticmethod
    def get_rcon_rule(session, args):
        r = None
        try:
            r = session.query(core.FirewallRule).filter_by(id=args.id).first()
        except Exception as e:
            msg_error = 'Can\'t get firewall rule: {error}'.format(error=str(e))
            logger.logging.error(msg_error)
            print(msg_error)
            exit(1)
        return r

    @staticmethod
    def list_rcon_rule(session, args, filter=None):
        if filter is None:
            filter = []

        rules = None
        try:
            rules = session.query(core.FirewallRule)
            rules = apply_filters(rules, filter)
            rules = rules.all()

        except Exception as e:
            err_msg = 'Can\'t get firewall rules: {error}'.format(error=str(e))
            logger.logging.error(err_msg)
            print(err_msg)
            exit(1)

        return rules

    @staticmethod
    def update_rcon_rule(session, id, updates):
        rule = session.query(core.FirewallRule).filter_by(id=id)
        for update in updates:
            rule.update(update, synchronize_session=False)

    @staticmethod
    def create_firewall_rule(session, args, commit=True):
        try:
            rule = core.FirewallRule(args.gamehost,
                                     args.gameport,
                                     args.username,
                                     args.subnet)
            session.add(rule)
            if commit:
                session.commit()
            logger.logging.info('Create subnet {}'.format(args.subnet))
        except Exception as e:
            logger.logging.error('Can\'t create firewall rule: {error}'.format(error=str(e)))
            exit(1)

        return 'Created successful'

    @staticmethod
    def sync_rcon_db(session, args):
        # get updates
        updates = RconAPI.list_rcon_updates(session, args)

        # get rules
        rules = RconAPI.list_rcon_rule(session,args)
        rules_list = []
        for rule in rules:
            rules_list.append(rule.subnet)

        # get RCON servers
        servers = RconAPI.list_rcon_server(session, args)

        # check subnet exist in firewall rules
        for ip in updates:
            subnet = '{}.0/24'.format('.'.join(str(ip.ipaddr).split('.')[:3]))
            if not subnet in rules_list:
                srv = next(server for server in servers if server.id == ip.rcon_server_id)
                rule = core.FirewallRule(ip.gamehost,
                                         ip.gameport,
                                         srv.username,
                                         subnet)
                try:
                    RconAPI.create_firewall_rule(session, rule, commit=False)
                    logger.logging.info('Create subnet {}'.format(subnet))
                except Exception as e:
                    logger.logging.error('Can\'t synchronize database: {error}'.format(error=str(e)))
                    exit(1)
                try:
                    session.commit()
                except Exception as e:
                    logger.logging.error('Can\'t commit changes: {error}'.format(error=str(e)))
                    exit(1)

        # load custom subnets to database
        RconAPI.load_custom_subnets(session)

        print('Database successful synchronized')
    # ------------------
# RCON API Functions

# create_rcon_server
# del_rcon_server
# update_rcon_server
# get_rcon_server(id)
# list_rcon_servers
# enable
# disable

# create_firewall
# del_firewall
# update_firewall
# get_firewall(id)
# list_firewalls

# create_subnet
# del_subnet
# update_subnet
# get_subnet(id)
# list_subnets

# create_iptables_rule
# del_iptables_rule
# update_iptables_rule
# get_iptables_rule(id)
# list_iptables_rules

# create_ipset_rule
# del_ipset_rule
# update_ipset_rule
# get_ipset_rule(id)
# list_ipset_rules