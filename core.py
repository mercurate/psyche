#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import time
import ftplib
import telnetlib

def check_ip(ip):
    return re.match('^((1?\d?\d|(2([0-4]\d|5[0-5])))\.){3}(1?\d?\d|(2([0-4]\d|5[0-5])))$', ip)

def printe(s):
    #print time.ctime(), '%s' % s
    print '%s' % s
        

class NeUp:
    def __init__(self, master, slave, filename, backup):
        self.ip = self.ip1 = master
        self.ip2 = slave
        self.filename = filename
        self.b = backup
        self.board_no = '-1'
        
        here = os.path.dirname(os.path.abspath(__file__))
        self.home = os.path.join(here, self.ip)
        if not os.path.exists(self.home):
            os.mkdir(self.home)
    
    def login(self):
        printe('try to login to %s...' % self.ip)
        self.ftp = ftplib.FTP(self.ip, timeout = 10)
        self.ftp.login('root', 'root')
        printe('ftp login ok')
        
        self.sh = telnetlib.Telnet(self.ip, timeout = 10)
        self.sh.read_until('login:')    
        self.telnet_write('user', 'Password:')
        self.telnet_write('user', '$')
        self.telnet_write('su', 'Password:')
        self.telnet_write('root')
        printe('telnet 23 login ok')
        
        self.ne_alive = True
        s = self.telnet_write('ps | grep HRM')
        m = re.search(r'HRM ([67])', s)
        if m:
            self.board_no = m.group(1)
            printe('master board is %s' % self.board_no)
        else:
            self.ne_alive = False     

        try:
            self.cli = telnetlib.Telnet(self.ip, 2628, timeout = 10)
            self.cli.read_until('Username:')    
            self.cli_write('root', 'Password:')
            self.cli_write('root', '>')
            self.cli_write('en')
            printe('telnet 2628 login ok')
        except Exception, e:
            printe('fail to login to 2628 port: %s' % str(e))
            self.ne_alive = False
        
    def tn_write(self, tn, write, read, timeout):
        tn.write(write + '\n')
        printe('>> cpm %s: %s' % (self.board_no, write))
        r = tn.read_until(read, timeout)
        printe('<< cpm %s: %s' % (self.board_no, r))
        return r
        
    def telnet_write(self, write, read = '#', timeout = 180):
        return self.tn_write(self.sh, write, read, timeout)
    
    def cli_write(self, write, read = '#', timeout = 180):
        return self.tn_write(self.cli, write, read, timeout)
        
    def has_slave(self):
        s = self.cli_write('show board')
        m1 = re.search(r'Slot : 6\s+Card type: CPM\s+Status : Normal', s)
        m2 = re.search(r'Slot : 7\s+Card type: CPM\s+Status : Normal', s)
        return m1 and m2

    def backup(self):
        if not self.b:
            printe('backup is skipped')
            return
        printe('backup begin...')
        self.telnet_write('cd /mnt/usrfs')
        printe('Package files...')
        self.telnet_write('tar -czf /var/tmp/backup.tar.gz ./**')
        printe('Backup files...')
        self.ftp.retrbinary('RETR /var/tmp/backup.tar.gz', open('%s/backup.tar.gz' % self.ip, 'wb').write)
        self.telnet_write('rm -rf /var/tmp/backup.tar.gz')
        printe('backup ok')
        
    def upload(self):    
        printe('gen userconfig.sh...')
        stream = self.telnet_write('ifconfig eth0')
        ip_match = re.search(r'((1?\d?\d|(2([0-4]\d|5[0-5])))\.){3}(1?\d?\d|(2([0-4]\d|5[0-5])))', stream)
        f = open('%s/userconfig.sh' % self.home, 'wb')
        f.write('#!/bin/sh\nifconfig eth0 %s netmask 255.255.255.0\n' % ip_match.group())
        f.close()
        
        printe('upload userconfig.sh and %s...' % self.filename)
        self.ftp.storbinary('STOR /var/tmp/%s' % os.path.basename(self.filename), open(self.filename, 'rb'))    
        self.ftp.storbinary('STOR /var/tmp/userconfig.sh', open('%s/userconfig.sh' % self.home, 'rb'))
        printe('MD5 checksum...')       
        ret_str = self.telnet_write('md5sum /var/tmp/%s' % os.path.basename(self.filename))
        md5_str = ret_str.splitlines()[1].split(' ')[0]
        md5_file = open('%s.md5' % self.filename, 'rb').read().rstrip()
        if 0 != cmp(md5_file, md5_str):
            raise Exception, 'MD5 checksum error！'
            
        printe('Extract update package...')
        self.telnet_write('tar -xzf /var/tmp/%s -C /var/tmp' % os.path.basename(self.filename))
        printe('Remove update package...')
        self.telnet_write('rm -rf /var/tmp/%s' % os.path.basename(self.filename))
        printe('Remove old files...')
        self.telnet_write('cd /mnt/usrfs')
        self.telnet_write('ls | grep -v ins | grep -v Module | grep -v userconfig.sh | xargs rm -rf')
        printe('Move files to /mnt/usrfs...')
        self.telnet_write('mv /var/tmp/ppc/** /mnt/usrfs')
        self.telnet_write('mv /var/tmp/userconfig.sh /mnt/usrfs/')
    
    
    # 执行倒换， 登录到新的主CPM， 重启备板CPM， 并等待
    def switch(self):
        printe('begin switch...')
        self.cli_write('tickout')
        self.cli_write('con t')
        self.cli_write('hrm')
        try:
            self.cli_write('mtn id 0 board %s cmd ms' % self.board_no, timeout = 10) # 倒换命令
        except Exception, e:
            pass
            
        self.ip = self.ip2 if self.ip == self.ip1 else self.ip1# 倒换后立即变更ip和板位号
        self.board_no = '7' if self.board_no == '6' else '6'
        printe('switch finish, sleep for 10 seconds...')
        time.sleep(10)
    
    def reboot_master(self):
        self.telnet_write('reboot')
        printe('success, only master board is updated.')
            
    # 重启备板， 并等待。 返回bool值
    def reboot_slave(self):
        printe('begin reboot slave...')
        self.cli_write('tickout')
        self.cli_write('con t')
        self.cli_write('reboot board %s' % ('7' if self.board_no == '6' else '6'))
        self.cli_write('exit')
        printe('waiting...')
        time.sleep(20)       
        for i in range(50): # 反复查询备板重启后是否Normal
            printe('waiting for slave reboot %d...' % i) 
            time.sleep(3)  
            ret = self.cli_write('show board')
            m1 = re.search(r'Slot : 6\s+Card type: CPM\s+Status : Normal', ret)
            m2 = re.search(r'Slot : 7\s+Card type: CPM\s+Status : Normal', ret)
            if m1 and m2:# 重启后状态Normal， 至此， 倒换完成
                return
                    
        raise Exception('reboot slave failed!')
    
    def update(self):
        self.login()
        self.backup()
        self.upload()
        
        if not self.ne_alive:
            printe('ne is not alive, reboot self directly.')
            self.reboot_master()
            return
            
        if not self.has_slave():# 没有备板， 直接重启自己， 升级完成
            printe('no slave board, reboot self directly.')
            self.reboot_master()
            return
            
        self.switch()
        self.login()
        self.reboot_slave()
        self.upload()
        self.switch()
        self.login()
        self.reboot_slave()
        printe('update success!')
    

