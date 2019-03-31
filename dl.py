#!/usr/bin/python3
# General Downloader
#
# v3 2018-12-06

import better_exceptions
import urllib.request
import argparse
import time
import queue
import threading
import os,sys
#
def download():
    global broken_links, internal_error, failed,files
    while not qq.empty():
        mydata = threading.local()
        mydata.name, mydata.url = qq.get()
        mydata.keep_going, mydata.skip, mydata.retry = (True, False, 0)
        if mydata.name in files:continue
        while mydata.keep_going:
            try:
                mydata.html = urllib.request.urlopen(urllib.request.Request(mydata.url,headers={'User-Agent' : "Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11"}),timeout=120)
            except urllib.error.HTTPError as HERR:
                if HERR.code == 404 or HERR.code == 500:
                    broken_links += 1
                    mydata.keep_going = False
                    mydata.skip = True
            except:
                mydata.retry += 1
                if mydata.retry > 5:
                    mydata.keep_going = False
                    mydata.skip = True
            break
        if mydata.skip:continue
        while True:
            try:
                mydata.image = mydata.html.read()
                open(mydata.name,'wb').write(mydata.image)
                break
            except:
                mydata.retry += 1
                if mydata.retry > 10:
                    #os.remove(mydata.name)
                    break
#        print("INFO : Downloaded",mydata.name)

def mkqueue_album_gen():
    fhand = open(args.fname,'r')
    links  = []
    queued = []
    i , j = (args.FROM,1)
    for each in fhand:
        if each.startswith(args.identify):
            i = i + 1
            j = 1
        if each.startswith('#') or len(each) < 10:continue
        if not args.ORIGINAL_NAME:
            fname = "R"+str(i)+ "_" + str(j).zfill(4) + "." + each.strip().split('.')[-1]
        else:
            fname = "R"+str(i)+ "_" + each.strip().split('/')[-1]
        links.append((fname,each.strip()))
        j = j + 1
    for each in links:qq.put(each)
    fhand.close()

def mkqueue_no_album():
    global files
    fhand = open(args.fname,'r')
    queued_urls   = []
    queued_names  = []
    i = 0
    for each in fhand:
        if each.startswith('#') or len(each) < 10:continue
        if args.ORIGINAL_NAME:fname = each.strip().split('/')[-1]
        else:
            i = i + 1
            fname = args.prefix+str(i).zfill(5) + "." + each.strip().split('.')[-1]
        if each.strip() in queued_urls:continue
        queued_urls.append(each.strip())
        if args.ORIGINAL_NAME:
            if fname in queued_names:
                x = 1
                while True:
                    new_name = '.'.join(fname.split('.')[:-1])+"_{}".format(x)+fname.split('.')[-1]
                    x += 1
                    if new_name not in queued_names:
                        fname = new_name
                        break
            queued_names.append(fname)
        if fname not in files:qq.put((fname,each.strip()))
    fhand.close()

def mkqueue_get_album():
    ref = dict()
    queued = []
    fhand = open(args.fname,'r')
    for each in fhand:
        if each.startswith(args.identify):
            i = each.split('album=')[-1].strip()#.zfill(4)
            if i not in ref.keys():ref[i] = 1001
        if each.startswith('#') or len(each) < 10:continue
        if args.ORIGINAL_NAME:
            fname = i+ "_" + each.strip().split('/')[-1]
        else:
            fname = str(i).zfill(4)+ "_" + str(ref[i]).zfill(4) + "." + each.strip().split('.')[-1]
        if each.strip() in queued:continue
        queued.append(each.strip())
        qq.put((fname,each.strip()))
        ref[i] = ref[i] + 1
    fhand.close()

def enqueue():
    if qq.qsize() != 0:print("\n WARNING: Queue was not empty. ")
    for name,url in failed:
        qq.put((name,url))

def init_threads():
    for i in range(args.threads):
        t = threading.Thread(target=download)
        threads.append(t)
        t.start()

def update_progress():
    progress = 100 - int((100*qq.qsize()) / total)
    te = time.strftime("%H:%M:%S",time.gmtime(time.time()-started))
    pbar = "\r {:0>3}% [{:<50}] ({},{}) Time Elapsed : {} ".format(progress, '#'*int((progress/2)), (total-qq.qsize()), total, te)
    sys.stdout.write(pbar)
    sys.stdout.flush()

#

parser = argparse.ArgumentParser(description='Start Tao Downloader.')
parser.add_argument('fname', type=str,
                    help='The File containing list of links.')
parser.add_argument('--dir', dest='directory', type = str, default = None, required = False,
                    help='The directory to download files in.')
parser.add_argument('--threads', dest='threads', type = int, default = 4, required = False,
                    help='No. of threads to use.')
parser.add_argument('--identify', dest='identify', type = str, default = "#!!!", required = False,
                    help='Identifier that seperate group of links belonging to different albums.')
parser.add_argument('-o', dest='ORIGINAL_NAME', action='store_true', required = False,
                    help='Use the original file names')
parser.add_argument('-s', dest='SINGLE_ALBUM', action='store_true', required = False,
                    help='Invoke Single Album Mode')
parser.add_argument('--preix', dest='prefix', type = str, default = "R", required = False,
                    help='Prefix to file names  [Used with single album mode]')
parser.add_argument('-g', dest='GENERATE_ALBUM_NO', action='store_true', required = False,
                    help='Invoke Auto-Generation of Album No')
parser.add_argument('--from', dest='FROM', type = int, default = 100, required = False,
                    help='Start Album no from here [Used with auto generation of album no]')
args = parser.parse_args()

#
qq = queue.Queue()
started = time.time()
threads = []
failed  = []
broken_links    = 00
internal_error  = 00

files = os.listdir(os.getcwd())
#tmp = os.scandir(os.getcwd())
#for each in tmp:
#    if each.is_dir():files = files + os.listdir(each)

if args.GENERATE_ALBUM_NO:mkqueue_album_gen()
elif args.SINGLE_ALBUM:mkqueue_no_album()
else:mkqueue_get_album()
total = qq.qsize()
print(str(total),"Files queued for download.")

"""
while not qq.empty():
    name, url = qq.get()
    print(name,url)
quit()  #DEBUG 
"""

if args.directory is not None:
    if not os.path.exists(args.directory):os.makedirs(args.directory)
    os.chdir(args.directory)

init_threads()
while not qq.empty():
    update_progress()
    time.sleep(5)
for t in threads:t.join()

if len(failed) > 0:
    print("\n INFO : Download failed for {} Items. Trying Again ...".format(len(failed)))
    enqueue()
    failed.clear()
    init_threads()
    for t in threads:t.join()
    print("\n INFO:",len(failed),"Downloads Failed.")


print(" \n ============================ \n    Time Taken : {} \n Files Downloaded : {} \n    Failed Downloads\
    : {} \n    Broken Links : {}  \n ===============================================================".format(\
    time.strftime("%H:%M:%S",time.gmtime(time.time()-started)), total-len(failed),len(failed),broken_links))
#
