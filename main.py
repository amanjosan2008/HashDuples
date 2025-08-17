#!/usr/bin/env python3
# Dependancy:
## sudo pip3 install send2trash --break-system-packages
## sudo apt-get install python3-pil.imagetk
from tkinter import *
import json, os, sys, subprocess
from send2trash import send2trash as st
from tkinter import filedialog
from random import randint
import shutil
from threading import Thread
import logging
from collections import defaultdict
from hashlib import md5

# Location parameters
loc = "/home/aman/"
loc_mem = "/data"
loc_mem2 = "/home/aman/"

# Logging setup
LOG_FILE = "activity_hd.log"
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(message)s')
logging.getLogger("paramiko").setLevel(logging.CRITICAL)
logging.getLogger("paramiko.transport").setLevel(logging.CRITICAL)

# Root Frame
root = Tk()
root.geometry("550x300+300+150")
root.resizable(width=True, height=True)

# main frame
frame = Frame(root)
frame.pack(fill=BOTH, expand=1)

# canvas
canvas = Canvas(frame)
canvas.pack(side=LEFT, fill=BOTH, expand=1)

# scrollbar
scrollbar = Scrollbar(frame, orient=VERTICAL, command=canvas.yview)
scrollbar.pack(side=RIGHT, fill=Y)
scrollbar2 = Scrollbar(frame, orient=HORIZONTAL, command=canvas.xview)
scrollbar2.pack(side=BOTTOM, fill=X)

# configure the canvas
canvas.configure(yscrollcommand=scrollbar.set,xscrollcommand=scrollbar2.set)
canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

second_frame = Frame(canvas, width = 1000, height = 100)

# Statusbar
statusbar = Label(root, anchor=W, text="loading.." )
statusbar.pack(fill=X, side=BOTTOM)

canvas.create_window((0, 0), window=second_frame, anchor="nw")

def hashed_data(new_file_name):
    afile = open(new_file_name, 'rb')
    hasher = md5()
    buf = afile.read(65536)
    while len(buf) > 0:
        hasher.update(buf)
        buf = afile.read(65536)
    afile.close()
    hashed = hasher.hexdigest()
    return hashed

def walker():
    # --- Settings ---
    scan_path = filedialog.askdirectory(parent=frame, initialdir=loc, title='Please select a directory')
    max_group_size = 5  # max items in a group (including duplicates)

    # Grouped results: { imagehash: {filepath: size} }
    grouped = defaultdict(dict)

    # Walk through the given path
    for root, _, files in os.walk(scan_path):
        for fname in files:
            fpath = os.path.join(root, fname)
            fhash = str(hashed_data(fpath))
            size = os.path.getsize(fpath)
            grouped[fhash][fpath] = size

    # Keep only groups with duplicates and limit to max_group_size
    filtered = [
        v for v in grouped.values()
        if 2 <= len(v) <= max_group_size
    ]

    # Reformat to numeric keys
    info = {i + 1: file_dict for i, file_dict in enumerate(filtered)}
    finfo = list(info.items())

    '''
    # Example printout
    for idx, files_dict in finfo:
        print(f"Group {idx}:")
        for path, size in files_dict.items():
            print(f"  {path} ({size} bytes)")
    '''
    return finfo

finfo = walker()
statusbar.config(text='Loading done..')

#max items per page
chunk_size = 10
start_index = 0
total_pages = int(len(finfo)/chunk_size)

def restart():
    python = sys.executable
    os.execl(python, python, * sys.argv)

def about():
    return None
    
# Menu Configuration
menu = Menu(root)

item1 = Menu(menu, tearoff=0)
item1.add_command(label='Restart', command=restart)
item1.add_separator()
item1.add_command(label='Exit', command=root.quit)

item2 = Menu(menu, tearoff=0)
item2.add_command(label='About', command=about)

menu.add_cascade(label='File', menu=item1)
menu.add_cascade(label='Help', menu=item2)

root.config(menu=menu)


statusbar.config(text='Total Sets: ' + str(len(finfo)) + " Total Pages: " + str(total_pages))

def main():
    global start_index
    end_index = start_index + chunk_size

    r=0
    for count,val in finfo[start_index:end_index]:
        x = {k: v for k, v in sorted(val.items(), key=lambda item: item[1], reverse=True)}
        for i,size in x.items():
            #print(fullname)

            if size > 1024*1024:
                sz = str(round(size/(1024*1024),2)) + 'MB'
            else:
                sz = str(round(size/(1024),2)) + 'kb'
            details = i + " (" + sz + ")"
            
            label = Label(second_frame, text=details, compound='right', wraplength=1200, justify="left")
            label.grid(row=r, column=0, columnspan=1, sticky=W)

            btn1 = Button(second_frame, text='open image', command=(lambda i=i: open_img(i)), compound='left')
            btn1.grid(row=r, column=2, columnspan=1, sticky=W)
            btn2 = Button(second_frame, text='open dir', command=(lambda i=i: open_dir(i)), compound='left')
            btn2.grid(row=r, column=3, columnspan=1, sticky=W)
            btn3 = Button(second_frame, text='delete', command=(lambda i=i: delete(i)), compound='left')
            btn3.grid(row=r, column=4, columnspan=1, sticky=W)
            btn4 = Button(second_frame, text='moveto', command=(lambda i=i: moveto(i,loc_mem)), compound='left')
            btn4.grid(row=r, column=5, columnspan=1, sticky=W)
            btn5 = Button(second_frame, text='movetodr', command=(lambda i=i: moveto(i,loc_mem2)), compound='left')
            btn5.grid(row=r, column=6, columnspan=1, sticky=W)
                #btn1.config(state=DISABLED)
                #btn2.config(state=DISABLED)
                #btn3.config(state=DISABLED)
                #btn4.config(state=DISABLED)
                #btn5.config(state=DISABLED)
            r = r + 1
        
        # Add Space
        spacer1 = Label(second_frame, width = 150, height = 1, highlightbackground="black", background= "black", highlightthickness=1)
        spacer1.grid(row=r, column=0, columnspan=6)
        '''
        btn6 = Button(second_frame, text='Ignore Set:' + str(count), command=(lambda val=val: ignore_set(val)), compound='left')
        btn6.grid(row=r, column=1)'''
        r = r + 1
            
        # Disable buttons at edges
        prev_button["state"] = NORMAL if start_index > 0 else DISABLED
        next_button["state"] = NORMAL if end_index < len(finfo) else DISABLED
    
    # Ensure scroll region updates
    second_frame.update_idletasks()
    canvas.configure(scrollregion=canvas.bbox("all"))

def open_img(i):
    #os.system('eog -n "%s"' %i)
    subprocess.check_call(['xdg-open', i])
    statusbar.config(text='Opened file: ' + str(i))

def open_dir(i):
    global t
    t = Thread(target=opendir, args=(i,))
    t.daemon = True
    t.start()
    root.after(1, check_dir_thread)

def check_dir_thread():
    if t.is_alive():
        root.after(1, check_dir_thread)

def opendir(i):
    if not os.path.isfile(i):
        i = os.path.dirname(i)
        statusbar.config(text='Opened Dir (file deleted): ' + str(i))
    else:
        statusbar.config(text='Opened Dir: ' + str(i))
    os.system('nautilus "%s"' %i)

def delete(i):
    try:
        st("%s" %i)
        statusbar.config(text='Deleted: ' + i)
        logging.info(f"Deleted: {i}")
    except OSError:
        error('Exception: Not Found: ' + str(i.split('/')[-1]))
        statusbar.config(text='Exception: Not Found: ' + i)

def moveto(fullpath,loc):
    try:
        mvdir = filedialog.askdirectory(parent=frame, initialdir=loc, title='Please select a directory')
        if os.path.isdir(mvdir):
            try:
                if os.path.isfile(fullpath):
                    shutil.move(fullpath, mvdir)
                    statusbar.config(text="Moved: " + fullpath + " => "+mvdir)
                    logging.info(f"Moved:   {fullpath} => {mvdir}")
                else:
                    text="Error: Source file does not exist: " + (fullpath).split('/')[-1]
                    statusbar.config(text)
                    error(text)
            except shutil.Error:
                text="Error: " + (fullpath).split('/')[-1]+": already exists at destination: " + mvdir
                statusbar.config(text)
                error(text)
            except FileNotFoundError:
                text="Error: File not found: " + (fullpath).split('/')[-1]
                statusbar.config(text)
                error(text)
            except IndexError:
                text="Error: No file in Directory"
                statusbar.config(text)
                error(text)
        else:
            text="Error: Directory does not exist: " + mvdir
            statusbar.config(text)
            error(text)
    except TypeError:
        text="Info: Move Directory operation canceled by User"
        statusbar.config(text)
        #error(text)
    except NameError:
        text="Error: Directory is empty or invalid"
        statusbar.config(text)
        error(text)

# Function to show the next 5 items
def show_first():
    global start_index
    
    for widget in second_frame.winfo_children():
        widget.destroy()
        
    start_index = 0
    main()    
    
    canvas.yview_moveto(0)
    statusbar.config(text='Page: ' + str(int(start_index/chunk_size) + 1) + " / " + str(total_pages))
    
# Function to show the next 5 items
def show_next():
    global start_index
    
    for widget in second_frame.winfo_children():
        widget.destroy()
    
    if start_index + chunk_size < len(finfo):
        start_index += chunk_size
    main()
    
    canvas.yview_moveto(0)
    statusbar.config(text='Page: ' + str(int(start_index/chunk_size) + 1) + " / " + str(total_pages))

# Function to show the previous 5 items
def show_prev():
    global start_index
    
    for widget in second_frame.winfo_children():
        widget.destroy()
        
    if start_index - chunk_size >= 0:
        start_index -= chunk_size
    else:
        start_index = 0
    main()
    
    canvas.yview_moveto(0)
    statusbar.config(text='Page: ' + str(int(start_index/chunk_size) + 1) + " / " + str(total_pages))
    
def show_last():
    global start_index
    
    for widget in second_frame.winfo_children():
        widget.destroy()
    
    start_index = len(finfo)-1
    main()
    
    canvas.yview_moveto(0)
    statusbar.config(text='Page: ' + str(int(start_index/chunk_size) + 1) + " / " + str(total_pages))

def show_custom():
    global start_index
    
    for widget in second_frame.winfo_children():
        widget.destroy()
    
    rand = randint(0,len(finfo)-1)
    start_index = rand
    main()
    
    canvas.yview_moveto(0)
    statusbar.config(text='Page: ' + str(int(rand/chunk_size) + 1) + " / " + str(total_pages))

# Navigation buttons
nav_frame = Frame(root)
nav_frame.pack(fill=X, side=BOTTOM)

first_button = Button(nav_frame, text="|< First", command=show_first)
first_button.grid(row=0, column=0, sticky="e", padx=5)

prev_button = Button(nav_frame, text="<< Prev", command=show_prev)
prev_button.grid(row=0, column=1, sticky="e", padx=5)

custom_button = Button(nav_frame, text="< Random >", command=show_custom)
custom_button.grid(row=0, column=2, sticky="e", padx=5)

next_button = Button(nav_frame, text="Next >>", command=show_next)
next_button.grid(row=0, column=3, sticky="w", padx=5)

last_button = Button(nav_frame, text="Last >|", command=show_last)
last_button.grid(row=0, column=4, sticky="w", padx=5)

# Error
def error(text):
    win2 = Toplevel()
    win2.attributes('-topmost','true')
    win2.title("Error")
    
    frame5 = Frame(win2, height=100, width=300, bd=3)
    frame5.grid()
    Label(frame5, text=text).grid(row=0, sticky=W)

# Initial main function
main()

root.bind('<Button-4>', lambda e: canvas.yview_scroll(int(-1*e.num), 'units'))
root.bind('<Button-5>', lambda e: canvas.yview_scroll(int(e.num), 'units'))

root.title("Imagehash Explorer")
root.mainloop()
