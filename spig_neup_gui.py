#!/usr/bin/env python
# -*- coding: utf-8 -*-  
import os
import re
import core
from Tkinter import *
import tkMessageBox
import tkFileDialog

###################################################
class NeUpForm(object):
    def __init__(self):
        self.top = Tk()
        self.top.geometry('+800+600')
        self.top.title('neup')
        
        self.lbl_ip = Label(self.top, text='host')
        
        self.txt_ip = Entry(self.top, width=30)
        self.txt_ip.insert(END,'192.168.20.45')
        self.txt_ip.bind('<Return>', self.submit)
        
        self.lbl_path = Label(self.top, text='file')
        self.txt_path = Entry(self.top, width=30)
        self.txt_path.insert(END, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'update.tar.gz'))
        self.btn_browse = Button(self.top, text='browse...', command=self.browse)
        
        self.var = IntVar()
        self.chk_backup = Checkbutton(self.top, text='backup', variable=self.var)
        
        self.btn_submit = Button(self.top, text='update', command=self.submit)
        self.btn_quit = Button(self.top, text='quit', command=self.top.quit)
        
        self.lbl_ip.grid(row=0, pady=10, sticky=E)
        self.txt_ip.grid(row=0, column=1, pady=10)
        
        self.lbl_path.grid(row=1, pady=10, sticky=E)
        self.txt_path.grid(row=1, column=1, pady=10)
        self.btn_browse.grid(row=1, column=2, pady=10)
        
        self.chk_backup.grid(row=2, column=1, pady=10, sticky=W)
        
        self.btn_submit.grid(row=3, column=1, pady=10, sticky=W)
        self.btn_quit.grid(row=3, column=2, pady=10)
        
        self.file_opt = {}
        self.file_opt['defaultextension'] = ''
        self.file_opt['filetypes'] = [('tar.gz files', '.tar.gz'), ('all files', '.*')]
        self.file_opt['initialdir'] = './'
        self.file_opt['initialfile'] = 'update.tar.gz'
        self.file_opt['parent'] = self.top 
        self.file_opt['title'] = 'Open file'

    def browse(self, event=None):
        filename = tkFileDialog.askopenfilename(**self.file_opt)
        self.txt_path.delete(0, END)
        self.txt_path.insert(END, filename)
        
    def submit(self, event=None):      
        ip = self.txt_ip.get()
        if not ip or not core.check_ip(ip):
            tkMessageBox.showwarning('neup', 'Invalid ip address!')
            return
            
        p = self.txt_path.get()
        if not p or not os.path.exists(p):
            tkMessageBox.showwarning('neup', 'Invalid package path!')
            return
        
        b = self.var.get()  
        nu = core.NeUp(ip, ip, p, b)
        try:
            nu.update()
        except Exception, e:
            tkMessageBox.showerror('neup', e)
            return

        tkMessageBox.showinfo('neup', 'update success!')

if __name__ == '__main__':
    NeUpForm()
    mainloop()
